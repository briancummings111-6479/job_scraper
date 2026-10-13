"""
Review Expired Jobs Engine
==========================
Audits job postings in the Google Sheet ("Redding Area Job Postings" tab)
sourced from Indeed, Snagajob, Glassdoor, ZipRecruiter, and other job portals.
Checks whether each job is still active or expired.
In Column P (Column 16), writes "Expired" if the job is no longer active.
Jobs where Source == "Company" are strictly skipped.
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_sync import get_gspread_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("ReviewExpiredJobs")

DEFAULT_SPREADSHEET_ID = "1uGL7w8fpb5P0D-kNIPces9nOK4Ctt6Bfg5jlA6J-_CU"
DEFAULT_TAB_NAME = "Automated_Posts"
TARGET_GID = 280720545

EXPIRED_PHRASES = [
    "this job has expired on indeed",
    "the employer is not accepting applications",
    "employer is not accepting applications",
    "this job has expired",
    "job has expired",
    "job is no longer available",
    "the job below is no longer available",
    "this job is no longer available",
    "is no longer available",
    "we couldn't find the job",
    "couldn't find the job",
    "position has been filled",
    "job is closed",
    "posting has closed",
    "no longer accepting applications",
    "this listing has expired",
    "this posting is no longer active",
    "job is no longer active",
    "job vacancy expired",
    "this vacancy is closed",
    "applications are now closed",
    "job expired",
    "not actively hiring",
    "is reviewing applications",
    "this job has closed",
    "job opening has closed",
    "page not found",
    "404 not found",
    "we can't find this page",
    "page doesn't exist",
]

import re

async def solve_turnstile_if_present(page) -> bool:
    """
    Checks if a Cloudflare Turnstile challenge frame is present on the page
    and clicks the verification checkbox if found.
    """
    try:
        title = (await page.title()).lower()
        if "just a moment" not in title and "security check" not in title:
            # Also check if any turnstile frame exists
            has_cf = any("challenges.cloudflare.com" in f.url for f in page.frames)
            if not has_cf:
                return False

        # Wait briefly for Turnstile iframe to finish layout
        await page.wait_for_timeout(2000)
        for f in page.frames:
            if "challenges.cloudflare.com" in f.url:
                try:
                    box = await f.locator("body").bounding_box()
                    if box:
                        await page.mouse.click(box["x"] + 28, box["y"] + box["height"] / 2)
                        logger.info("Clicked Cloudflare Turnstile checkbox; waiting for clearance...")
                        await page.wait_for_timeout(4500)
                        return True
                except Exception:
                    pass
    except Exception:
        pass
    return False


async def warm_indeed_session(context) -> None:
    """
    Opens an Indeed search results page once to establish session cookies and
    pass Cloudflare Turnstile before worker tasks run.
    """
    page = await context.new_page()
    try:
        logger.info("Warming Indeed session on search page...")
        await page.goto(
            "https://www.indeed.com/jobs?q=driver&l=Redding,+CA",
            wait_until="domcontentloaded",
            timeout=20000
        )
        await page.wait_for_timeout(2500)
        await solve_turnstile_if_present(page)
        title = await page.title()
        logger.info(f"Indeed session warmed (Title: '{title[:60]}')")
    except Exception as e:
        logger.warning(f"Warning during Indeed session warmup: {e}")
    finally:
        try:
            await page.close()
        except Exception:
            pass


def extract_indeed_jk(url: str) -> Optional[str]:
    """Extracts the 16-char hex job key (jk) from an Indeed URL if present."""
    if "indeed.com" not in url.lower():
        return None
    m = re.search(r"[?&](?:jk|vjk)=([a-f0-9]{16})", url, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


async def check_job_url(context, job: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
    """
    Visits a job URL using an existing Playwright context and evaluates
    whether the job is still active or expired.
    """
    row_idx = job["row_index"]
    source = job.get("source", "").strip()
    title = job.get("title", "").strip()
    company = job.get("company", "").strip()
    url = job.get("url", "").strip()

    # Rule: Do not review jobs from source: Company
    if source.lower() == "company":
        return {
            "row_index": row_idx,
            "source": source,
            "title": title,
            "company": company,
            "status": job.get("existing_status", ""),
            "is_expired": False,
            "skipped": True,
            "reason": "Skipped (Source: Company)"
        }

    # If missing or invalid URL
    if not url or not url.startswith("http"):
        return {
            "row_index": row_idx,
            "source": source,
            "title": title,
            "company": company,
            "status": "Expired",
            "is_expired": True,
            "skipped": False,
            "reason": "Missing or invalid URL"
        }

    page = None
    last_err = None
    indeed_jk = extract_indeed_jk(url)
    target_url = (
        f"https://www.indeed.com/jobs?q=driver&l=Redding,+CA&vjk={indeed_jk}"
        if indeed_jk else url
    )

    for attempt in range(max_retries + 1):
        try:
            page = await context.new_page()

            # Navigate with generous timeout
            resp = await page.goto(
                target_url,
                wait_until="domcontentloaded",
                timeout=20000
            )

            # Short wait for client-side rendering / banner display
            await page.wait_for_timeout(1600)

            # If Cloudflare Turnstile appeared, solve it once
            if await solve_turnstile_if_present(page):
                await page.wait_for_timeout(2000)

            status_code = resp.status if resp else 0
            final_url = page.url.lower()
            page_title = (await page.title()).lower()

            # Special handling for Indeed vjk right-pane inspection
            if indeed_jk:
                pane = page.locator("#jobsearch-ViewjobPaneWrapper, div.jobsearch-JobComponent, .jobsearch-RightPane")
                pane_count = await pane.count()
                if pane_count > 0:
                    pane_text = (await pane.first.inner_text()).lower().strip()
                else:
                    pane_text = ""

                if not pane_text:
                    # Wait a bit longer in case right pane is still hydrating
                    await page.wait_for_timeout(2000)
                    await solve_turnstile_if_present(page)
                    pane_count = await pane.count()
                    if pane_count > 0:
                        pane_text = (await pane.first.inner_text()).lower().strip()

                if not pane_text:
                    body_check = (await page.inner_text("body")).lower()
                    if any(ph in body_check for ph in EXPIRED_PHRASES):
                        await page.close()
                        return {
                            "row_index": row_idx,
                            "source": source,
                            "title": title,
                            "company": company,
                            "status": "Expired",
                            "is_expired": True,
                            "skipped": False,
                            "reason": "Indeed page not found / expired"
                        }
                    await page.close()
                    if attempt < max_retries:
                        await asyncio.sleep(2)
                        continue
                    return {
                        "row_index": row_idx,
                        "source": source,
                        "title": title,
                        "company": company,
                        "status": "Expired",
                        "is_expired": True,
                        "skipped": False,
                        "reason": "Indeed job pane empty or listing removed"
                    }

                for phrase in EXPIRED_PHRASES:
                    if phrase in pane_text:
                        await page.close()
                        return {
                            "row_index": row_idx,
                            "source": source,
                            "title": title,
                            "company": company,
                            "status": "Expired",
                            "is_expired": True,
                            "skipped": False,
                            "reason": f"Detected expired phrase in Indeed pane: '{phrase}'"
                        }

                await page.close()
                return {
                    "row_index": row_idx,
                    "source": source,
                    "title": title,
                    "company": company,
                    "status": "Active",
                    "is_expired": False,
                    "skipped": False,
                    "reason": "Active Indeed listing confirmed in job pane"
                }

            body_text = (await page.inner_text("body")).lower()

            # 1. Direct HTTP 404 / 410 or missing resource
            if status_code in (404, 410):
                await page.close()
                return {
                    "row_index": row_idx,
                    "source": source,
                    "title": title,
                    "company": company,
                    "status": "Expired",
                    "is_expired": True,
                    "skipped": False,
                    "reason": f"HTTP {status_code}"
                }

            # 2. Redirected to generic root / search page without original job ID
            if "snagajob.com" in url and ("/jobs/" not in final_url or "404" in final_url):
                await page.close()
                return {
                    "row_index": row_idx,
                    "source": source,
                    "title": title,
                    "company": company,
                    "status": "Expired",
                    "is_expired": True,
                    "skipped": False,
                    "reason": "Snagajob redirected away from job posting"
                }

            # 3. Check for expired text phrases in body and title
            for phrase in EXPIRED_PHRASES:
                if phrase in body_text or phrase in page_title:
                    await page.close()
                    return {
                        "row_index": row_idx,
                        "source": source,
                        "title": title,
                        "company": company,
                        "status": "Expired",
                        "is_expired": True,
                        "skipped": False,
                        "reason": f"Detected expired phrase: '{phrase}'"
                    }

            # 4. Handle generic Indeed search URLs (e.g., /jobs?q=title...)
            if "indeed.com/jobs?" in url:
                # If neither the job title nor company appears in the search results
                has_title = title.lower() in body_text if title else False
                has_company = company.lower() in body_text if company else False
                if not has_title and not has_company:
                    await page.close()
                    return {
                        "row_index": row_idx,
                        "source": source,
                        "title": title,
                        "company": company,
                        "status": "Expired",
                        "is_expired": True,
                        "skipped": False,
                        "reason": "Listing not found on search results page"
                    }

            # If status code is valid (200, 3xx) and no expiration cues matched
            await page.close()
            return {
                "row_index": row_idx,
                "source": source,
                "title": title,
                "company": company,
                "status": "Active",
                "is_expired": False,
                "skipped": False,
                "reason": "Active listing confirmed"
            }

        except Exception as e:
            last_err = e
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if attempt < max_retries:
                await asyncio.sleep(1)
                continue

    # If all attempts failed (e.g. host unreachable, connection refused, DNS error)
    err_str = str(last_err)
    logger.warning(f"Row {row_idx} [{source}] error visiting {url}: {err_str}")
    # Connection failure / DNS dead link typically implies dead job link
    return {
        "row_index": row_idx,
        "source": source,
        "title": title,
        "company": company,
        "status": "Expired",
        "is_expired": True,
        "skipped": False,
        "reason": f"Connection error: {err_str[:60]}"
    }


async def review_expired_jobs_async(
    sheet_id: str = DEFAULT_SPREADSHEET_ID,
    tab_name: str = DEFAULT_TAB_NAME,
    concurrency: int = 3,
    update_sheet: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    row_limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Reviews all jobs in the Google Sheet and updates Column P.
    """
    from playwright.async_api import async_playwright

    logger.info(f"Connecting to Google Sheets (ID: {sheet_id})...")
    client = get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)

    # Locate worksheet by name or by target gid
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except Exception:
        # Fallback by gid
        matched = [ws for ws in spreadsheet.worksheets() if ws.id == TARGET_GID]
        if matched:
            worksheet = matched[0]
        else:
            worksheet = spreadsheet.sheet1
    logger.info(f"Target worksheet resolved: '{worksheet.title}' (id: {worksheet.id})")

    all_values = worksheet.get_all_values()
    if len(all_values) < 2:
        return {"status": "error", "message": "Worksheet does not have enough rows."}

    # Map column headers to indices (0-indexed)
    is_automated_posts = ("automated_posts" in worksheet.title.strip().lower())
    
    # Check if Row 1 has headers (e.g. Source, Job Title)
    row1_lower = [c.strip().lower() for c in all_values[0]]
    row1_has_headers = any(c in ["source", "job title", "title"] for c in row1_lower)
    
    header_row_idx = 0 if row1_has_headers else 1
    header_row = all_values[header_row_idx]
    data_start_idx = header_row_idx + 1  # 0-indexed: index 1 is row 2, index 2 is row 3

    col_map = {}
    for idx, col in enumerate(header_row):
        col_clean = col.strip().lower()
        if col_clean:
            col_map[col_clean] = idx

    source_col_idx = col_map.get("source", 0)
    title_col_idx = col_map.get("job title", 1)
    company_col_idx = col_map.get("company", 2)
    url_col_idx = col_map.get("job posting", col_map.get("job_url", 11))  # Default Column L (index 11)
    
    # Determine Status column index:
    if "status" in col_map:
        status_col_idx = col_map["status"]
    elif is_automated_posts:
        status_col_idx = len(header_row)  # Append Status column after all existing columns
    else:
        status_col_idx = 15  # Column P is 0-indexed index 15 (Column 16)

    # Collect jobs from data_start_idx onwards
    jobs_to_process: List[Dict[str, Any]] = []
    total_data_rows = 0

    for i in range(data_start_idx, len(all_values)):
        row = all_values[i]
        # Check if row has any meaningful content
        has_content = any(c.strip() for c in row[:14])
        if not has_content:
            continue

        total_data_rows += 1
        source = row[source_col_idx].strip() if len(row) > source_col_idx else ""
        title = row[title_col_idx].strip() if len(row) > title_col_idx else ""
        comp = row[company_col_idx].strip() if len(row) > company_col_idx else ""
        url = row[url_col_idx].strip() if len(row) > url_col_idx else ""
        existing_status = row[status_col_idx].strip() if len(row) > status_col_idx else ""

        # Stop if we hit rows that are just empty trailing cells with checkboxes
        if not source and not title and not url:
            continue

        jobs_to_process.append({
            "row_index": i + 1,  # 1-indexed spreadsheet row
            "row_arr_idx": i,
            "source": source,
            "title": title,
            "company": comp,
            "url": url,
            "existing_status": existing_status
        })

    if row_limit:
        jobs_to_process = jobs_to_process[:row_limit]

    total_jobs = len(jobs_to_process)
    company_jobs = [j for j in jobs_to_process if j["source"].lower() == "company"]
    reviewable_jobs = [j for j in jobs_to_process if j["source"].lower() != "company"]

    logger.info(
        f"Found {total_jobs} total job listings. "
        f"Skipping {len(company_jobs)} Company listings. "
        f"Reviewing {len(reviewable_jobs)} postings across Indeed, Snagajob, ZipRecruiter, etc."
    )

    results: Dict[int, Dict[str, Any]] = {}
    completed_count = 0
    expired_count = 0
    active_count = 0
    company_skipped_count = len(company_jobs)

    # Mark Company jobs as skipped immediately
    for c_job in company_jobs:
        results[c_job["row_index"]] = {
            "row_index": c_job["row_index"],
            "source": c_job["source"],
            "title": c_job["title"],
            "company": c_job["company"],
            "status": c_job["existing_status"],
            "is_expired": False,
            "skipped": True,
            "reason": "Skipped (Source: Company)"
        }

    # Start browser for reviewable jobs
    if reviewable_jobs:
        async with async_playwright() as p:
            logger.info("Launching browser engine with bot-detection bypass...")
            try:
                browser = await p.chromium.launch(
                    headless=False,
                    channel="chrome",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )
            except Exception:
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )
            context = await browser.new_context()

            # Warm Indeed session and solve Cloudflare Turnstile if any Indeed jobs exist
            has_indeed = any("indeed.com" in j.get("url", "").lower() for j in reviewable_jobs)
            if has_indeed:
                await warm_indeed_session(context)

            sem = asyncio.Semaphore(concurrency)

            async def worker(job):
                nonlocal completed_count, expired_count, active_count
                async with sem:
                    res = await check_job_url(context, job)
                    results[job["row_index"]] = res
                    completed_count += 1
                    if res.get("status") == "Expired":
                        expired_count += 1
                        logger.info(
                            f"  [EXPIRED] Row {job['row_index']} [{res.get('source')}]: "
                            f"{res.get('title')} ({res.get('reason')})"
                        )
                    elif res.get("status") == "Active":
                        active_count += 1

                    if progress_callback:
                        progress_callback({
                            "current": completed_count,
                            "total": len(reviewable_jobs),
                            "total_all": total_jobs,
                            "job": res,
                            "expired_count": expired_count,
                            "active_count": active_count,
                            "company_skipped_count": company_skipped_count
                        })

                    # Log periodically
                    if completed_count % 5 == 0 or completed_count == len(reviewable_jobs):
                        logger.info(
                            f"Progress: {completed_count}/{len(reviewable_jobs)} "
                            f"(Expired: {expired_count}, Active: {active_count})"
                        )
                    return res

            tasks = [worker(job) for job in reviewable_jobs]
            await asyncio.gather(*tasks)
            await browser.close()

    # Prepare Status column values for batch write
    last_row_index = jobs_to_process[-1]["row_index"] if jobs_to_process else (data_start_idx + 1)
    
    def _col_idx_to_letter(col_idx: int) -> str:
        res = ""
        c = col_idx + 1
        while c > 0:
            c, rem = divmod(c - 1, 26)
            res = chr(65 + rem) + res
        return res

    status_col_letter = _col_idx_to_letter(status_col_idx)
    header_row_num = header_row_idx + 1
    
    col_status_values = [["Status"]]
    for row_num in range(data_start_idx + 1, last_row_index + 1):
        if row_num in results:
            res = results[row_num]
            col_status_values.append([res.get("status", "")])
        else:
            col_status_values.append([""])

    if update_sheet and len(col_status_values) > 1:
        range_target = f"{status_col_letter}{header_row_num}:{status_col_letter}{last_row_index}"
        logger.info(f"Writing {len(col_status_values)} rows to Google Sheet range '{range_target}'...")
        worksheet.update(values=col_status_values, range_name=range_target)
        logger.info(f"[SUCCESS] Column {status_col_letter} batch update completed in Google Sheets.")

    summary = {
        "status": "success",
        "sheet_id": sheet_id,
        "worksheet": worksheet.title,
        "total_jobs": total_jobs,
        "company_skipped": company_skipped_count,
        "reviewed_jobs": len(reviewable_jobs),
        "expired_count": expired_count,
        "active_count": active_count,
        "last_row_updated": last_row_index,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logger.info(
        f"Review Complete: {total_jobs} total, {company_skipped_count} company skipped, "
        f"{len(reviewable_jobs)} reviewed -> {expired_count} Expired, {active_count} Active."
    )
    return summary


def run_review_expired_jobs(
    sheet_id: str = DEFAULT_SPREADSHEET_ID,
    tab_name: str = DEFAULT_TAB_NAME,
    concurrency: int = 3,
    update_sheet: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    row_limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper to execute the review async engine.
    """
    return asyncio.run(
        review_expired_jobs_async(
            sheet_id=sheet_id,
            tab_name=tab_name,
            concurrency=concurrency,
            update_sheet=update_sheet,
            progress_callback=progress_callback,
            row_limit=row_limit
        )
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Review active vs expired job postings in Google Sheet")
    parser.add_argument("--sheet-id", default=DEFAULT_SPREADSHEET_ID, help="Google Sheet ID")
    parser.add_argument("--tab", default=DEFAULT_TAB_NAME, help="Worksheet tab name")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent browser workers")
    parser.add_argument("--no-update", action="store_true", help="Dry run without writing to Sheet")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows to check")
    args = parser.parse_args()

    print("=== Starting Career Miner Job Expiry Review ===")
    res = run_review_expired_jobs(
        sheet_id=args.sheet_id,
        tab_name=args.tab,
        concurrency=args.concurrency,
        update_sheet=not args.no_update,
        row_limit=args.limit
    )
    print("\n=== Result Summary ===")
    for k, v in res.items():
        print(f"  {k}: {v}")
