import sys
import argparse
from firestore_sync import get_firestore_client
from scrapper import is_rejected_job, is_expired_job_content, clean_job_title, determine_industry, extract_key_requirements, generate_key_description, clean_location_str, is_shasta_county_location, extract_pay

def cleanup_jobs(dry_run=True):
    db = get_firestore_client()
    docs = list(db.collection('jobs').stream())
    
    print(f"Total documents found in 'jobs' collection: {len(docs)}")
    
    to_delete = []
    to_update = []
    retained = []

    for d in docs:
        data = d.to_dict()
        raw_title = data.get('title', '')
        company = data.get('company', '')
        desc = data.get('description', '')
        raw_loc = data.get('location', 'Redding, CA')
        cleaned_loc = clean_location_str(raw_loc)
        cleaned_title = clean_job_title(raw_title)

        is_shasta, loc_reason = is_shasta_county_location(cleaned_loc)
        if not is_shasta:
            to_delete.append((d.id, raw_title, company, loc_reason))
            continue

        raw_pay = data.get('pay', '')
        desc_pay = extract_pay(desc)
        
        # Prioritize description pay; purge estimated algorithmic guesses
        if desc_pay:
            final_pay = desc_pay
        elif data.get('source') == 'Snagajob' and raw_pay in ['$15 per hour', '$17.90', '$20.25', '$14 per hour', '$15', '$14', '$18 per hour', '$26 per hour']:
            final_pay = 'N/A'
        else:
            final_pay = raw_pay or 'N/A'

        is_exp = is_expired_job_content(desc) or is_expired_job_content(raw_title)
        is_rej, rej_reason = is_rejected_job(cleaned_title, company, desc, pay=final_pay, location=cleaned_loc)

        if is_exp or is_rej:
            reason = "Expired job listing" if is_exp else rej_reason
            to_delete.append((d.id, raw_title, company, reason))
        else:
            fields_to_update = {}
            if raw_title != cleaned_title:
                fields_to_update['title'] = cleaned_title

            if raw_loc != cleaned_loc:
                fields_to_update['location'] = cleaned_loc

            if raw_pay != final_pay:
                fields_to_update['pay'] = final_pay

            current_sector = data.get('sector')
            new_sector = determine_industry(cleaned_title, company, desc)
            if current_sector != new_sector or not data.get('category'):
                fields_to_update['sector'] = new_sector
                fields_to_update['category'] = new_sector

            current_exp = data.get('experience')
            current_desc = str(data.get('description') or '')

            is_boilerplate = bool("industry sector:" in current_desc.lower() or "key requirements:" in current_desc.lower() or "position with" in current_desc.lower())
            true_desc = "" if is_boilerplate else current_desc

            # Calculate rich, non-contradictory key requirements (Column I)
            new_exp = extract_key_requirements(
                text=true_desc,
                existing_exp="",
                job_dict={"title": cleaned_title, "company": company, "sector": new_sector, "location": cleaned_loc}
            )

            if not current_exp or current_exp != new_exp:
                fields_to_update['experience'] = new_exp
                fields_to_update['requirements'] = new_exp

            # Calculate accurate job description (Column J)
            new_desc = generate_key_description(
                title=cleaned_title,
                company=company,
                location=cleaned_loc,
                sector=new_sector,
                job_type=data.get('jobType', 'N/A'),
                schedule=data.get('schedule') or data.get('shift', 'N/A'),
                pay=final_pay,
                requirements=new_exp
            )

            if not current_desc or current_desc != new_desc:
                fields_to_update['description'] = new_desc

            if fields_to_update:
                to_update.append((d.id, fields_to_update, cleaned_title, current_sector, new_sector))

            retained.append((d.id, cleaned_title, company, new_sector))

    print(f"\n--- Scan Results ---")
    print(f"Jobs to be DELETED (Expired or Non-Entry-Level): {len(to_delete)}")
    print(f"Jobs to be UPDATED (Clean Title / Update Sector): {len(to_update)}")
    print(f"Jobs to be RETAINED: {len(retained)}")

    print("\nSample Jobs to Delete:")
    for item in to_delete[:10]:
        print(f"  - [{item[3]}] {item[1]} at {item[2]} (id: {item[0]})")

    print("\nSample Jobs to Update (Sector/Title):")
    for item in to_update[:10]:
        print(f"  - {item[2]}: {item[3]} -> {item[4]} (fields: {list(item[1].keys())})")

    if dry_run:
        print("\n[DRY RUN COMPLETE] No changes were written to Firestore.")
        print("To apply these changes, run with '--execute'.")
        return len(to_delete), len(to_update)

    # Perform deletion in batches
    print(f"\n[EXECUTING] Deleting {len(to_delete)} rejected/expired documents...")
    batch = db.batch()
    b_count = 0
    del_total = 0

    for item in to_delete:
        doc_ref = db.collection('jobs').document(item[0])
        batch.delete(doc_ref)
        b_count += 1
        del_total += 1
        if b_count >= 400:
            batch.commit()
            batch = db.batch()
            b_count = 0

    if b_count > 0:
        batch.commit()
    print(f"Successfully deleted {del_total} documents.")

    # Perform updates in batches
    print(f"[EXECUTING] Updating {len(to_update)} documents (titles, sectors)...")
    batch = db.batch()
    b_count = 0
    upd_total = 0

    for doc_id, fields, title, _, _ in to_update:
        doc_ref = db.collection('jobs').document(doc_id)
        batch.update(doc_ref, fields)
        b_count += 1
        upd_total += 1
        if b_count >= 400:
            batch.commit()
            batch = db.batch()
            b_count = 0

    if b_count > 0:
        batch.commit()
    print(f"Successfully updated {upd_total} jobs in Firestore.")
    print("Database cleanup finished.")
    return del_total, upd_total

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Purge invalid / expired jobs from Firestore")
    parser.add_argument('--execute', action='store_true', help='Execute deletions and updates')
    args = parser.parse_args()

    cleanup_jobs(dry_run=not args.execute)
