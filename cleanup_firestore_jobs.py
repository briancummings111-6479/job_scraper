import sys
import argparse
from firestore_sync import get_firestore_client
from scrapper import is_rejected_job, is_expired_job_content, clean_job_title

def cleanup_jobs(dry_run=True):
    db = get_firestore_client()
    docs = list(db.collection('jobs').stream())
    
    print(f"Total documents found in 'jobs' collection: {len(docs)}")
    
    to_delete = []
    to_update_title = []
    retained = []

    for d in docs:
        data = d.to_dict()
        raw_title = data.get('title', '')
        company = data.get('company', '')
        desc = data.get('description', '')
        cleaned_title = clean_job_title(raw_title)

        is_exp = is_expired_job_content(desc) or is_expired_job_content(raw_title)
        is_rej, rej_reason = is_rejected_job(cleaned_title, company, desc)

        if is_exp or is_rej:
            reason = "Expired job listing" if is_exp else rej_reason
            to_delete.append((d.id, raw_title, company, reason))
        else:
            if raw_title != cleaned_title:
                to_update_title.append((d.id, raw_title, cleaned_title))
            retained.append((d.id, cleaned_title, company))

    print(f"\n--- Scan Results ---")
    print(f"Jobs to be DELETED (Expired or Non-Entry-Level): {len(to_delete)}")
    print(f"Jobs to have TITLE CLEANED (Strip '- job post'): {len(to_update_title)}")
    print(f"Jobs to be RETAINED: {len(retained)}")

    print("\nSample Jobs to Delete:")
    for item in to_delete[:10]:
        print(f"  - [{item[3]}] {item[1]} at {item[2]} (id: {item[0]})")

    if dry_run:
        print("\n[DRY RUN COMPLETE] No changes were written to Firestore.")
        print("To apply these changes, run with '--execute'.")
        return len(to_delete), len(to_update_title)

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

    # Perform title updates in batches
    print(f"[EXECUTING] Updating {len(to_update_title)} titles...")
    batch = db.batch()
    b_count = 0
    upd_total = 0

    for doc_id, old_t, new_t in to_update_title:
        doc_ref = db.collection('jobs').document(doc_id)
        batch.update(doc_ref, {'title': new_t})
        b_count += 1
        upd_total += 1
        if b_count >= 400:
            batch.commit()
            batch = db.batch()
            b_count = 0

    if b_count > 0:
        batch.commit()
    print(f"Successfully updated {upd_total} job titles.")
    print("Database cleanup finished.")
    return del_total, upd_total

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Purge invalid / expired jobs from Firestore")
    parser.add_argument('--execute', action='store_true', help='Execute deletions and updates')
    args = parser.parse_args()

    cleanup_jobs(dry_run=not args.execute)
