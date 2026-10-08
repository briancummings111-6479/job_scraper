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
DEFAULT_TAB_NAME = "Redding Area Job Postings"
TARGET_GID = 778721942

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
]

async def check_job_url(context, job: Dict[str, Any], max_retries: int = 1) -> Dict[str, Any]:
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

    for attempt in range(max_retries + 1):
        try:
            page = await context.new_page()
            
            # Navigate with generous timeout
            resp = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=18000,
                referer="https://www.google.com/"
            )
            
            # Short wait for client-side rendering / banner display
            await page.wait_for_timeout(1400)
            
            status_code = resp.status if resp else 0
            final_url = page.url.lower()
            page_title = (await page.title()).lower()
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

    # Row 2 contains headers
    header_row = all_values[1]
    
    # Map column headers to indices (0-indexed)
    col_map = {}
    for idx, col in enumerate(header_row):
        col_clean = col.strip().lower()
        if col_clean:
            col_map[col_clean] = idx

    source_col_idx = col_map.get("source", 0)
    title_col_idx = col_map.get("job title", 1)
    company_col_idx = col_map.get("company", 2)
    url_col_idx = col_map.get("job posting", col_map.get("job_url", 10))
    status_col_idx = 15  # Column P is 0-indexed index 15 (Column 16)

    # Collect jobs from row 3 (index 2) onwards
    jobs_to_process: List[Dict[str, Any]] = []
    total_data_rows = 0

    for i in range(2, len(all_values)):
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
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-position=-2000,-2000",
                    "--window-size=1280,800"
                ]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.google.com/"
                }
            )

            sem = asyncio.Semaphore(concurrency)

            async def worker(job):
                nonlocal completed_count, expired_count, active_count
                async with sem:
                    res = await check_job_url(context, job)
                    results[job["row_index"]] = res
                    completed_count += 1
                    if res.get("status") == "Expired":
                        expired_count += 1
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

    # Prepare Column P values for batch write
    # Row 2 (header): "Status"
    last_row_index = jobs_to_process[-1]["row_index"] if jobs_to_process else 2
    
    col_p_values = [["Status"]]  # P2 header
    for i in range(3, last_row_index + 1):
        if i in results:
            res = results[i]
            if res.get("skipped"):
                # Preserve existing or leave blank
                col_p_values.append([res.get("status", "")])
            else:
                col_p_values.append([res.get("status", "")])
        else:
            col_p_values.append([""])

    if update_sheet and len(col_p_values) > 1:
        range_target = f"P2:P{last_row_index}"
        logger.info(f"Writing {len(col_p_values)} rows to Google Sheet range '{range_target}'...")
        worksheet.update(values=col_p_values, range_name=range_target)
        logger.info("[SUCCESS] Column P batch update completed in Google Sheets.")

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
