# Implementation Plan: Import Actuals and Commitments

## Overview

This implementation plan breaks down the Import Actuals and Commitments feature into discrete coding tasks. The implementation follows the existing patterns in the codebase, using FastAPI for backend endpoints, Pydantic for validation, and React with react-dropzone for the frontend.

## Tasks

- [x] 1. Create database schema and migrations
  - [x] 1.1 Create SQL migration for 'actuals' table
    - Create table with all columns: id, fi_doc_no, posting_date, document_date, vendor, vendor_description, project_id, project_nr, wbs_element, amount, currency, item_text, document_type, created_at, updated_at
    - Add unique constraint on fi_doc_no
    - Add foreign key to projects table
    - Create indexes on fi_doc_no, project_id, project_nr, posting_date
    - _Requirements: 8.1, 8.3, 8.4_
  
  - [x] 1.2 Create SQL migration for 'commitments' table
    - Create table with all columns: id, po_number, po_date, vendor, vendor_description, project_id, project_nr, wbs_element, po_net_amount, total_amount, currency, po_status, po_line_nr, delivery_date, created_at, updated_at
    - Add unique constraint on (po_number, po_line_nr)
    - Add foreign key to projects table
    - Create indexes on po_number, project_id, project_nr, po_date
    - _Requirements: 8.2, 8.3, 8.4_
  
  - [x] 1.3 Create SQL migration for 'import_audit_logs' table
    - Create table with columns: id, import_id, user_id, import_type, total_records, success_count, duplicate_count, error_count, status, errors (JSONB), created_at, completed_at
    - Add check constraints for import_type and status
    - Create indexes on user_id, import_type, created_at
    - _Requirements: 8.5, 10.1, 10.2_

- [x] 2. Checkpoint - Verify database migrations
  - Ensure all migrations apply successfully, ask the user if questions arise.

- [x] 3. Implement Pydantic models
  - [x] 3.1 Create imports models file (`backend/models/imports.py`)
    - Define ActualCreate model with validators for amount and date parsing
    - Define CommitmentCreate model with validators
    - Define ImportResult model
    - Define ImportAuditLog model
    - Define ActualResponse and CommitmentResponse models
    - _Requirements: 2.3, 3.3_
  
  - [ ]* 3.2 Write unit tests for Pydantic models
    - Test amount parsing with various formats (comma, dot decimal separators)
    - Test date parsing with various formats
    - Test validation error messages
    - _Requirements: 2.4, 2.5, 2.6, 3.4, 3.5, 3.6_

- [x] 4. Implement Anonymizer Service
  - [x] 4.1 Create anonymizer service (`backend/services/anonymizer.py`)
    - Implement AnonymizerService class with vendor, project, and personnel maps
    - Implement anonymize_vendor method with letter-based naming (Vendor A, B, C...)
    - Implement anonymize_project_nr method with P0001 format
    - Implement anonymize_personnel method with EMP001 format
    - Implement anonymize_text method for descriptions
    - Implement anonymize_actual and anonymize_commitment methods
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  
  - [ ]* 4.2 Write property test for anonymization consistency
    - **Property 1: Anonymization Consistency**
    - **Validates: Requirements 1.7**
  
  - [ ]* 4.3 Write property test for field preservation
    - **Property 2: Anonymization Preserves Non-Sensitive Fields**
    - **Validates: Requirements 1.6**
  
  - [ ]* 4.4 Write property test for vendor anonymization format
    - **Property 3: Vendor Anonymization Format**
    - **Validates: Requirements 1.1**
  
  - [ ]* 4.5 Write property test for project number format
    - **Property 4: Project Number Anonymization Format**
    - **Validates: Requirements 1.3**

- [x] 5. Implement Project Linker Service
  - [x] 5.1 Create project linker service (`backend/services/project_linker.py`)
    - Implement ProjectLinker class with project cache
    - Implement get_or_create_project method
    - Implement _find_project_by_nr method to search existing projects
    - Implement _create_project method with default values (status='active', health='green')
    - Use WBS element for project description
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ]* 5.2 Write property test for project linking consistency
    - **Property 11: Project Linking Consistency**
    - **Validates: Requirements 6.1, 6.2**
  
  - [ ]* 5.3 Write property test for auto-created project defaults
    - **Property 12: Auto-Created Project Defaults**
    - **Validates: Requirements 6.3**

- [x] 6. Checkpoint - Verify services
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Import Service
  - [x] 7.1 Create import service (`backend/services/actuals_commitments_import.py`)
    - Implement ActualsCommitmentsImportService class
    - Implement import_actuals method with validation and duplicate detection
    - Implement import_commitments method with validation and duplicate detection
    - Implement check_duplicate_actual method (by fi_doc_no)
    - Implement check_duplicate_commitment method (by po_number + po_line_nr)
    - Implement log_import method for audit logging
    - Integrate AnonymizerService and ProjectLinker
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 4.5, 5.4_
  
  - [ ]* 7.2 Write property test for actuals round-trip
    - **Property 5: Import Round-Trip for Actuals**
    - **Validates: Requirements 2.2**
  
  - [ ]* 7.3 Write property test for commitments round-trip
    - **Property 6: Import Round-Trip for Commitments**
    - **Validates: Requirements 3.2**
  
  - [ ]* 7.4 Write property test for validation error completeness
    - **Property 7: Validation Error Completeness**
    - **Validates: Requirements 2.4, 2.5, 2.6, 3.4, 3.5, 3.6**
  
  - [ ]* 7.5 Write property test for duplicate detection idempotency
    - **Property 9: Duplicate Detection Idempotency**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  
  - [ ]* 7.6 Write property test for import summary accuracy
    - **Property 10: Import Summary Accuracy**
    - **Validates: Requirements 4.5**
  
  - [ ]* 7.7 Write property test for audit log completeness
    - **Property 13: Audit Log Completeness**
    - **Validates: Requirements 5.4, 10.1, 10.2, 10.3**

- [x] 8. Implement CSV/JSON Parser
  - [x] 8.1 Create parser utilities (`backend/services/import_parser.py`)
    - Implement parse_csv function for semicolon-delimited CSV
    - Implement parse_json function for JSON arrays
    - Implement detect_format function based on file extension
    - Handle encoding detection (UTF-8, Latin-1)
    - Map CSV column headers to model fields
    - _Requirements: 2.7, 3.7_
  
  - [ ]* 8.2 Write property test for format equivalence
    - **Property 8: Format Equivalence**
    - **Validates: Requirements 2.7, 3.7**
  
  - [ ]* 8.3 Write property test for invalid file format rejection
    - **Property 14: Invalid File Format Rejection**
    - **Validates: Requirements 9.1**
  
  - [ ]* 8.4 Write property test for partial import error collection
    - **Property 15: Partial Import Error Collection**
    - **Validates: Requirements 9.3, 9.5**

- [x] 9. Checkpoint - Verify import service and parser
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Import Router
  - [x] 10.1 Create import router (`backend/routers/imports.py`)
    - Implement POST /api/imports/actuals endpoint
    - Implement POST /api/imports/commitments endpoint
    - Implement GET /api/imports/templates/{import_type} endpoint
    - Implement GET /api/imports/history endpoint
    - Add JWT authentication dependency
    - Add data_import permission check
    - Handle file upload with UploadFile
    - Return standardized ImportResult responses
    - _Requirements: 2.1, 3.1, 5.1, 5.2, 5.3, 7.7, 10.4_
  
  - [x] 10.2 Register router in main.py
    - Import imports router
    - Add router to FastAPI app
    - _Requirements: 2.1, 3.1_
  
  - [ ]* 10.3 Write integration tests for import endpoints
    - Test successful actuals import
    - Test successful commitments import
    - Test authentication errors (401)
    - Test authorization errors (403)
    - Test validation errors (400)
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 11. Checkpoint - Verify backend API
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Frontend Import Interface (ALREADY IMPLEMENTED)
  - The CSVImportView component (`app/financials/components/views/CSVImportView.tsx`) already provides:
    - ✅ Drag-and-drop upload for Commitments and Actuals
    - ✅ Template download buttons
    - ✅ Upload progress indicator
    - ✅ Success/error result display with statistics
    - ✅ Import history table
    - ✅ Integration with backend API endpoints
  - This task is complete and accessible via the "CSV Import" tab on the Financials page
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 13. Final checkpoint - Full integration verification
  - Ensure all tests pass, ask the user if questions arise.
  - Verify end-to-end flow: Upload CSV → Parse → Validate → Anonymize → Import → Display results
  - ✅ Import functionality is complete and working

- [x] 14. Extend CommitmentsActualsView with Sub-Tabs
  - [x] 14.1 Add sub-tab navigation to CommitmentsActualsView
    - Create sub-tab component with three tabs: "Variance Analysis", "Commitments", "Actuals"
    - Implement tab state management
    - Style tabs to match existing TabNavigation component
    - _Requirements: 13.1, 13.2_
  
  - [x] 14.2 Refactor existing variance analysis into sub-tab
    - Move existing CommitmentsActualsView content into "Variance Analysis" sub-tab
    - Preserve all existing functionality (filters, sorting, charts, export)
    - _Requirements: 13.1_

- [x] 15. Implement Commitments Data Table View
  - [x] 15.1 Create CommitmentsTable component
    - Create table component in `app/financials/components/tables/CommitmentsTable.tsx`
    - Display all commitment columns: po_number, po_date, vendor, vendor_description, project_nr, wbs_element, po_net_amount, total_amount, currency, po_status, po_line_nr, delivery_date, and additional columns
    - Implement responsive table with horizontal scroll for many columns
    - Add loading and error states
    - _Requirements: 11.3_
  
  - [x] 15.2 Add sorting functionality
    - Implement column header click handlers for sorting
    - Support ascending/descending sort order
    - Add visual indicators for sort direction (arrows)
    - _Requirements: 11.4_
  
  - [x] 15.3 Add filtering functionality
    - Add filter input fields above table columns
    - Implement client-side filtering for text fields
    - Implement date range filtering for date fields
    - Implement numeric range filtering for amount fields
    - _Requirements: 11.5_
  
  - [x] 15.4 Add pagination
    - Implement pagination controls (Previous, Next, Page Numbers)
    - Add page size selector (25, 50, 100 records per page)
    - Display current page info (showing X-Y of Z records)
    - _Requirements: 11.6_
  
  - [x] 15.5 Add export functionality
    - Implement CSV export button
    - Export filtered and sorted data
    - Include all columns in export
    - _Requirements: 11.7_
  
  - [x] 15.6 Integrate with API endpoint
    - Fetch data from `/api/csv-import/commitments` endpoint
    - Handle pagination parameters (limit, offset)
    - Handle filtering parameters (project_nr)
    - Display total and filtered record counts
    - _Requirements: 11.2, 11.8_
  
  - [x] 15.7 Add empty state
    - Display message when no commitments data exists
    - Add link to CSV Import tab
    - _Requirements: 11.9_

- [x] 16. Implement Actuals Data Table View
  - [x] 16.1 Create ActualsTable component
    - Create table component in `app/financials/components/tables/ActualsTable.tsx`
    - Display all actual columns: fi_doc_no, posting_date, document_date, vendor, vendor_description, project_nr, wbs_element, amount, currency, item_text, document_type, and additional columns
    - Implement responsive table with horizontal scroll for many columns
    - Add loading and error states
    - _Requirements: 12.3_
  
  - [x] 16.2 Add sorting functionality
    - Implement column header click handlers for sorting
    - Support ascending/descending sort order
    - Add visual indicators for sort direction (arrows)
    - _Requirements: 12.4_
  
  - [x] 16.3 Add filtering functionality
    - Add filter input fields above table columns
    - Implement client-side filtering for text fields
    - Implement date range filtering for date fields
    - Implement numeric range filtering for amount fields
    - _Requirements: 12.5_
  
  - [x] 16.4 Add pagination
    - Implement pagination controls (Previous, Next, Page Numbers)
    - Add page size selector (25, 50, 100 records per page)
    - Display current page info (showing X-Y of Z records)
    - _Requirements: 12.6_
  
  - [x] 16.5 Add export functionality
    - Implement CSV export button
    - Export filtered and sorted data
    - Include all columns in export
    - _Requirements: 12.7_
  
  - [x] 16.6 Integrate with API endpoint
    - Fetch data from `/api/csv-import/actuals` endpoint
    - Handle pagination parameters (limit, offset)
    - Handle filtering parameters (project_nr)
    - Display total and filtered record counts
    - _Requirements: 12.2, 12.8_
  
  - [x] 16.7 Add empty state
    - Display message when no actuals data exists
    - Add link to CSV Import tab
    - _Requirements: 12.9_

- [x] 17. Integrate Sub-Tabs into CommitmentsActualsView
  - [x] 17.1 Wire up sub-tab content switching
    - Render CommitmentsTable when "Commitments" sub-tab is active
    - Render ActualsTable when "Actuals" sub-tab is active
    - Render existing variance analysis when "Variance Analysis" sub-tab is active
    - _Requirements: 13.1_
  
  - [x] 17.2 Implement cross-tab navigation
    - Add click handler on project_nr in Commitments/Actuals tables
    - Switch to Variance Analysis tab and filter by clicked project
    - _Requirements: 13.4_
  
  - [x] 17.3 Add unified refresh functionality
    - Create refresh button that reloads data for all sub-tabs
    - Show loading state during refresh
    - _Requirements: 13.5_
  
  - [x] 17.4 Preserve state across sub-tabs
    - Maintain selected currency across all sub-tabs
    - Preserve filter settings where applicable
    - _Requirements: 13.2, 13.3_

- [x] 18. Final checkpoint - Viewing functionality verification
  - Ensure all tests pass, ask the user if questions arise.
  - Verify end-to-end flow: Import CSV → View in Commitments/Actuals tables → Filter/Sort → Export → Switch to Variance Analysis

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using hypothesis library
- Unit tests validate specific examples and edge cases
- The implementation follows existing patterns in the codebase (see `backend/routers/csv_import.py` and `backend/routers/projects_import.py`)
- Tasks 14-18 extend the spec to add viewing functionality for imported data, reusing the existing financials page structure
