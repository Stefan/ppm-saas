# Requirements Document

## Introduction

This document specifies the requirements for the "Import Actuals and Commitments" feature in the PPM (Project Portfolio Management) SaaS application. The feature enables users to import financial actuals and commitments data from CSV/JSON files into the system, supporting project financial tracking and variance analysis. Data must be anonymized before import to remove sensitive vendor and personnel information.

## Glossary

- **Actuals**: Financial transactions that have already occurred, representing actual costs incurred on projects
- **Commitments**: Financial obligations that have been made but not yet paid, such as purchase orders
- **Import_Service**: The backend service responsible for processing and validating import data
- **Anonymizer**: The component that replaces sensitive data with generic placeholders
- **FI_Doc_No**: Financial Document Number, a unique identifier for actual transactions
- **Commitment_No**: Commitment Number, a unique identifier for commitment records (derived from PO Number + Line)
- **WBS_Element**: Work Breakdown Structure element, linking financial data to project structure
- **Project_Linker**: The component that creates or links projects based on imported Project Nr. values

## Requirements

### Requirement 1: Data Anonymization

**User Story:** As a data administrator, I want to anonymize sensitive information before import, so that vendor names, personnel data, and company-specific references are protected.

#### Acceptance Criteria

1. WHEN a CSV file contains vendor names, THE Anonymizer SHALL replace them with generic identifiers (Vendor A, Vendor B, Vendor C, etc.)
2. WHEN a CSV file contains vendor descriptions, THE Anonymizer SHALL replace them with generic text "Vendor Description"
3. WHEN a CSV file contains Project Nr. values, THE Anonymizer SHALL transform them to fictitious format (P0001, P0002, etc.) while maintaining referential integrity
4. WHEN a CSV file contains Personnel Numbers, THE Anonymizer SHALL replace them with anonymized identifiers (EMP001, EMP002, etc.)
5. WHEN a CSV file contains item text or descriptions, THE Anonymizer SHALL replace them with generic text "Item Description"
6. THE Anonymizer SHALL preserve the structure of dates, amounts, currency codes, and status fields unchanged
7. WHEN anonymizing data, THE Anonymizer SHALL maintain consistent mapping (same original vendor always maps to same anonymized vendor within an import session)

### Requirement 2: Actuals Import Backend

**User Story:** As a project manager, I want to import actuals data via API, so that I can track actual project costs in the system.

#### Acceptance Criteria

1. WHEN a user submits a POST request to `/api/imports/actuals` with valid CSV/JSON data, THE Import_Service SHALL parse and validate the data
2. WHEN actuals data passes validation, THE Import_Service SHALL insert records into the 'actuals' table in Supabase
3. THE Import_Service SHALL accept the following fields for actuals: fi_doc_no, posting_date, document_date, vendor, vendor_description, project_nr, wbs_element, amount, currency, item_text, document_type
4. WHEN a required field is missing, THE Import_Service SHALL return a validation error with field name and row number
5. WHEN an amount field contains non-numeric data, THE Import_Service SHALL return a validation error specifying the invalid value
6. WHEN a date field contains invalid date format, THE Import_Service SHALL return a validation error specifying the expected format (YYYY-MM-DD)
7. THE Import_Service SHALL support both CSV (semicolon-delimited) and JSON upload formats

### Requirement 3: Commitments Import Backend

**User Story:** As a project manager, I want to import commitments data via API, so that I can track committed project costs in the system.

#### Acceptance Criteria

1. WHEN a user submits a POST request to `/api/imports/commitments` with valid CSV/JSON data, THE Import_Service SHALL parse and validate the data
2. WHEN commitments data passes validation, THE Import_Service SHALL insert records into the 'commitments' table in Supabase
3. THE Import_Service SHALL accept the following fields for commitments: po_number, po_date, vendor, vendor_description, project_nr, wbs_element, po_net_amount, total_amount, currency, po_status, po_line_nr, delivery_date
4. WHEN a required field is missing, THE Import_Service SHALL return a validation error with field name and row number
5. WHEN an amount field contains non-numeric data, THE Import_Service SHALL return a validation error specifying the invalid value
6. WHEN a date field contains invalid date format, THE Import_Service SHALL return a validation error specifying the expected format (YYYY-MM-DD)
7. THE Import_Service SHALL support both CSV (semicolon-delimited) and JSON upload formats

### Requirement 4: Duplicate Detection

**User Story:** As a data administrator, I want the system to detect duplicate records, so that I can prevent data inconsistencies.

#### Acceptance Criteria

1. WHEN importing actuals, THE Import_Service SHALL check for existing records with the same fi_doc_no
2. WHEN importing commitments, THE Import_Service SHALL check for existing records with the same po_number and po_line_nr combination
3. WHEN a duplicate is detected, THE Import_Service SHALL skip the duplicate record and include it in the import summary
4. WHEN duplicates are detected, THE Import_Service SHALL continue processing remaining records (partial import)
5. THE Import_Service SHALL return a summary indicating total records, successful imports, duplicates skipped, and errors

### Requirement 5: Authentication and Authorization

**User Story:** As a system administrator, I want import endpoints to require authentication, so that only authorized users can import financial data.

#### Acceptance Criteria

1. WHEN a request to import endpoints lacks a valid JWT token, THE Import_Service SHALL return a 401 Unauthorized error
2. WHEN a request contains an expired JWT token, THE Import_Service SHALL return a 401 Unauthorized error
3. WHEN a user lacks the 'data_import' permission, THE Import_Service SHALL return a 403 Forbidden error
4. THE Import_Service SHALL log all import operations with user ID, timestamp, and record counts

### Requirement 6: Project Linking

**User Story:** As a project manager, I want imported financial data to be linked to projects, so that I can view actuals and commitments per project.

#### Acceptance Criteria

1. WHEN importing data with a Project Nr. that exists in the projects table, THE Project_Linker SHALL link the record to the existing project
2. WHEN importing data with a Project Nr. that does not exist, THE Project_Linker SHALL create a new project with the anonymized Project Nr. as the name
3. WHEN creating a new project, THE Project_Linker SHALL set default values for required project fields (status: 'active', health: 'green')
4. THE Project_Linker SHALL use the WBS Element to provide additional project context in the description field

### Requirement 7: Frontend Import Interface (IMPLEMENTED)

**User Story:** As a user, I want a drag-and-drop interface to upload import files, so that I can easily import actuals and commitments data.

**Status:** ✅ COMPLETE - Implemented in `CSVImportView` component

#### Acceptance Criteria

1. ✅ WHEN a user navigates to the Financials page and selects "CSV Import" tab, THE System SHALL display the import interface
2. ✅ WHEN a user selects Commitments or Actuals section, THE System SHALL provide separate upload areas for each type
3. ✅ WHEN a user drags a CSV file onto the dropzone, THE System SHALL accept the file and display the filename
4. ✅ WHEN a user clicks the Import button after selecting a file, THE System SHALL upload the file and display a progress indicator
5. ✅ WHEN the import completes successfully, THE System SHALL display a success message with import statistics (processed, imported, errors)
6. ✅ WHEN the import fails or has errors, THE System SHALL display error details with row numbers and field names
7. ✅ THE System SHALL allow users to download a sample CSV template for each import type (Commitments and Actuals)

### Requirement 8: Database Schema

**User Story:** As a developer, I want properly structured database tables, so that actuals and commitments data can be stored and queried efficiently.

#### Acceptance Criteria

1. THE System SHALL create an 'actuals' table with columns: id (UUID), fi_doc_no (VARCHAR), posting_date (DATE), document_date (DATE), vendor (VARCHAR), vendor_description (VARCHAR), project_id (UUID FK), project_nr (VARCHAR), wbs_element (VARCHAR), amount (DECIMAL), currency (VARCHAR), item_text (TEXT), document_type (VARCHAR), created_at (TIMESTAMP), updated_at (TIMESTAMP)
2. THE System SHALL create a 'commitments' table with columns: id (UUID), po_number (VARCHAR), po_date (DATE), vendor (VARCHAR), vendor_description (VARCHAR), project_id (UUID FK), project_nr (VARCHAR), wbs_element (VARCHAR), po_net_amount (DECIMAL), total_amount (DECIMAL), currency (VARCHAR), po_status (VARCHAR), po_line_nr (INTEGER), delivery_date (DATE), created_at (TIMESTAMP), updated_at (TIMESTAMP)
3. THE System SHALL create foreign key relationships from actuals.project_id and commitments.project_id to projects.id
4. THE System SHALL create indexes on fi_doc_no, po_number, project_id, and project_nr for query performance
5. THE System SHALL create an 'import_audit_logs' table to track all import operations with user_id, import_type, record_count, success_count, error_count, and timestamp

### Requirement 9: Error Handling

**User Story:** As a user, I want clear error messages when imports fail, so that I can correct issues and retry.

#### Acceptance Criteria

1. WHEN a file format is invalid (not CSV or JSON), THE System SHALL return an error message specifying accepted formats
2. WHEN CSV parsing fails due to malformed data, THE System SHALL return the line number and nature of the parsing error
3. WHEN validation fails for specific rows, THE System SHALL continue processing and return a summary of all errors
4. WHEN a database error occurs during import, THE System SHALL rollback the transaction and return an appropriate error message
5. IF partial import is enabled, THEN THE System SHALL commit successful records and report failed records separately

### Requirement 10: Import Audit Trail

**User Story:** As an administrator, I want to track all import operations, so that I can audit data changes and troubleshoot issues.

#### Acceptance Criteria

1. WHEN an import operation starts, THE System SHALL create an audit log entry with import_id, user_id, import_type, and start_timestamp
2. WHEN an import operation completes, THE System SHALL update the audit log with end_timestamp, total_records, success_count, error_count, and status
3. THE System SHALL store error details in the audit log for failed records
4. WHEN a user requests import history, THE System SHALL return paginated audit log entries filtered by user or import type

### Requirement 11: View Imported Commitments Data

**User Story:** As a project manager, I want to view all imported commitments data in a table, so that I can verify the imported records and analyze commitment details.

#### Acceptance Criteria

1. WHEN a user navigates to the Commitments & Actuals tab, THE System SHALL display a sub-tab for "Commitments"
2. WHEN the Commitments sub-tab is selected, THE System SHALL fetch and display all imported commitment records from the database
3. THE System SHALL display all imported commitment fields in a sortable, filterable table including: po_number, po_date, vendor, vendor_description, project_nr, wbs_element, po_net_amount, total_amount, currency, po_status, po_line_nr, delivery_date, and all additional imported columns
4. WHEN a user clicks a column header, THE System SHALL sort the table by that column (ascending/descending)
5. WHEN a user enters text in filter fields, THE System SHALL filter the table to show only matching records
6. THE System SHALL support pagination with configurable page size (25, 50, 100 records per page)
7. WHEN a user clicks the Export button, THE System SHALL download the filtered commitments data as CSV
8. THE System SHALL display the total count of commitments records and filtered count
9. WHEN no commitments data exists, THE System SHALL display a message prompting the user to import data

### Requirement 12: View Imported Actuals Data

**User Story:** As a project manager, I want to view all imported actuals data in a table, so that I can verify the imported records and analyze actual expenditure details.

#### Acceptance Criteria

1. WHEN a user navigates to the Commitments & Actuals tab, THE System SHALL display a sub-tab for "Actuals"
2. WHEN the Actuals sub-tab is selected, THE System SHALL fetch and display all imported actual records from the database
3. THE System SHALL display all imported actual fields in a sortable, filterable table including: fi_doc_no, posting_date, document_date, vendor, vendor_description, project_nr, wbs_element, amount, currency, item_text, document_type, and all additional imported columns
4. WHEN a user clicks a column header, THE System SHALL sort the table by that column (ascending/descending)
5. WHEN a user enters text in filter fields, THE System SHALL filter the table to show only matching records
6. THE System SHALL support pagination with configurable page size (25, 50, 100 records per page)
7. WHEN a user clicks the Export button, THE System SHALL download the filtered actuals data as CSV
8. THE System SHALL display the total count of actuals records and filtered count
9. WHEN no actuals data exists, THE System SHALL display a message prompting the user to import data

### Requirement 13: Integrated View with Variance Analysis

**User Story:** As a project manager, I want to switch between viewing raw imported data and variance analysis, so that I can analyze data from different perspectives.

#### Acceptance Criteria

1. WHEN a user is on the Commitments & Actuals tab, THE System SHALL display three sub-tabs: "Variance Analysis", "Commitments", and "Actuals"
2. WHEN a user switches between sub-tabs, THE System SHALL preserve filter and sort settings where applicable
3. THE System SHALL maintain the selected currency across all sub-tabs
4. WHEN a user clicks on a project_nr in the Commitments or Actuals table, THE System SHALL filter the Variance Analysis view to show only that project
5. THE System SHALL provide a "Refresh" button that reloads data for all sub-tabs
