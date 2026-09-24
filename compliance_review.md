# Compliance Standards Review

This document summarizes the current state of the WRTP-CMS codebase against the requirements outlined in the `Data Infrastructure and Compliance Policy and Procedures.docx` document.

## 1. Data Sovereignty (US-Based Multi-Region)
**Status**: ✅ **IN PLACE**
- The `firebase.json` configuration specifies `nam5` for the Firestore database location. `nam5` is a Google Cloud multi-region located in North America, satisfying the US-based geo-redundancy requirement.

## 2. PII Protection (FIPS 140-2 Encryption)
**Status**: ✅ **IN PLACE (By Default)**
- Google Cloud Platform (and Firebase) encrypts all data at rest and in transit using FIPS 140-2 validated cryptographic modules by default.

## 3. Audit Trail (Immutable Logs)
**Status**: ⚠️ **PARTIALLY IN PLACE**
- There is a Cloud Function (`auditClientChanges` in `functions/src/audit.ts`) that successfully captures `CREATE`, `UPDATE`, and `DELETE` events for Client records, saving them to an `auditLogs` collection with timestamps and User IDs.
- **Needs Implementation**: The audit logging must be expanded to cover all other critical entities (e.g., tasks, case notes, planning forms, and system configurations). 

## 4. Access Control (Role-Based RBAC)
**Status**: ❌ **NEEDS IMPLEMENTATION**
- While the front-end application implements RBAC (checking user roles defined in `AuthContext` and `staff.ts`), the database level is completely open. 
- `firestore.rules` currently states `allow read, write: if request.auth != null;`. This means any authenticated user can read or modify any document directly, bypassing the UI. Firestore Security Rules need to be written to strictly enforce role-based access control.

## 5. Soft-Delete Logic
**Status**: ❌ **NEEDS IMPLEMENTATION**
- The policy requires that records must be preserved for auditors using "soft-delete" flags (inactive status). 
- Currently, the codebase uses `deleteDoc` (hard deletion) extensively across multiple services (`clientService.ts`, `taskService.ts`, `planningService.ts`, `interactionService.ts`, etc.). This must be updated to modify a `status` field instead.

## 6. Data Backup Strategy (3-2-1 Protocol & Automated Exports)
**Status**: ❌ **NEEDS IMPLEMENTATION**
- There is a client-side JSON export function in `systemService.ts`, but this does not satisfy the automated, off-site, secondary vault requirements.
- **Needs Implementation**: Automated weekly scripts or GCP Workflows need to be set up to export Firestore collections to a secondary GCP project ("Cold Storage"). 

## 7. Digital Signature Validation
**Status**: ❌ **NEEDS IMPLEMENTATION**
- The policy requires electronic signature workflows to be verified for compliance with California Government Code § 16.5.
- Currently, signatures are tracked as simple boolean flags (e.g., `applicantSignature: boolean`) in the `Demographics` model. A compliant digital signature provider (like DocuSign or a cryptographic equivalent) needs to be integrated, or additional metadata (IP, precise timestamp, consent record) must be captured.

## 8. GCP-Level Requirements (Liens, PITR, Vault Projects)
**Status**: ⚠️ **UNKNOWN / REQUIRES MANUAL VERIFICATION**
- **Resource Manager Liens**: Cannot be verified in the codebase. Must be checked in the GCP Console to ensure a "do not delete" flag is placed on the primary project.
- **Point-in-Time Recovery (PITR)**: Cannot be verified in the codebase. Must be enabled via the GCP Console for the Firestore database.
- **Secondary Vault Project**: Requires creating a separate GCP project in the console and linking it to the automated exports.
