# Requirements Document: Project Import MVP

## Introduction

This feature enables users to import multiple projects into the ORKA-PPM application through REST API endpoints and CSV file uploads. The MVP focuses on JSON array imports and CSV file parsing with comprehensive validation, authentication, and audit trail logging. This provides a foundation for future integrations with MS Project, Jira, and ERP systems.

## Glossary

- **Import_Service**: The backend service responsible for processing project import requests
- **Validation_Engine**: The component that validates imported project data against business rules
- **Audit_Logger**: The component that records all import operations for compliance and tracking
- **Import_Modal**: The frontend UI component that provides the import interface
- **CSV_Parser**: The component that parses CSV files into project data structures
- **API_Endpoint**: The REST API endpoint that accepts import requests
- **Project_Record**: A single project entity with all required and optional fields
- **Import_Session**: A single import operation that may contain multiple projects

## Requirements

### Requirement 1: JSON Array Import via REST API

**User Story:** As a system administrator, I want to import multiple projects via a REST API endpoint accepting JSON arrays, so that I can integrate ORKA-PPM with external systems programmatically.

#### Acceptance Criteria

1. WHEN a valid JSON array of projects is posted to the API endpoint, THE Import_Service SHALL create all projects in the database
2. WHEN the JSON array contains valid project data, THE Import_Service SHALL return a success response with the count of imported projects
3. WHEN authentication credentials are missing or invalid, THE API_Endpoint SHALL reject the request with a 401 status code
4. WHEN the user lacks data import permissions, THE API_Endpoint SHALL reject the request with a 403 status code
5. THE API_Endpoint SHALL accept requests at the path `/api/projects/import` using the POST method

### Requirement 2: CSV File Upload and Parsing

**User Story:** As a project manager, I want to upload a CSV file containing project data, so that I can quickly import projects from spreadsheets and legacy systems.

#### Acceptance Criteria

1. WHEN a valid CSV file is uploaded, THE CSV_Parser SHALL parse all rows into project records
2. WHEN the CSV file contains a header row, THE CSV_Parser SHALL map column names to project fields
3. WHEN the CSV file is successfully parsed, THE Import_Service SHALL create all valid projects in the database
4. THE API_Endpoint SHALL accept CSV file uploads at the path `/api/projects/import/csv` using the POST method
5. WHEN the CSV file cannot be parsed, THE Import_Service SHALL return an error message describing the parsing failure

### Requirement 3: Data Validation

**User Story:** As a data administrator, I want all imported projects to be validated against business rules, so that invalid or incomplete data does not corrupt the database.

#### Acceptance Criteria

1. WHEN a project record is missing required fields (name, budget, status), THE Validation_Engine SHALL reject that record
2. WHEN a project name already exists in the database, THE Validation_Engine SHALL reject that record as a duplicate
3. WHEN a budget field contains non-numeric data, THE Validation_Engine SHALL reject that record
4. WHEN a date field is not in ISO format, THE Validation_Engine SHALL reject that record
5. WHEN validation fails for any record, THE Import_Service SHALL return detailed error messages identifying the invalid records and reasons
6. WHEN some records are valid and others invalid, THE Import_Service SHALL reject the entire import batch and maintain database consistency

### Requirement 4: Authentication and Authorization

**User Story:** As a security administrator, I want all import operations to require authentication and proper permissions, so that only authorized users can import project data.

#### Acceptance Criteria

1. WHEN an import request is received, THE API_Endpoint SHALL validate the JWT token
2. WHEN the JWT token is valid, THE API_Endpoint SHALL extract the user identity
3. WHEN the user identity is extracted, THE API_Endpoint SHALL verify the user has the `data_import` permission
4. WHEN the user lacks the `data_import` permission, THE API_Endpoint SHALL reject the request with a 403 status code
5. WHEN authentication or authorization fails, THE API_Endpoint SHALL not process any import data

### Requirement 5: Audit Trail Logging

**User Story:** As a compliance officer, I want all import operations to be logged with user identity and timestamp, so that I can track data changes for audit purposes.

#### Acceptance Criteria

1. WHEN an import operation begins, THE Audit_Logger SHALL record the user identity, timestamp, and import method
2. WHEN an import operation completes successfully, THE Audit_Logger SHALL record the number of projects imported
3. WHEN an import operation fails, THE Audit_Logger SHALL record the failure reason
4. THE Audit_Logger SHALL persist all audit records to the database
5. WHEN audit logging fails, THE Import_Service SHALL still complete the import operation but log the audit failure

### Requirement 6: Frontend Import Interface

**User Story:** As a project manager, I want a user-friendly interface to import projects, so that I can easily upload CSV files or paste JSON data without technical knowledge.

#### Acceptance Criteria

1. WHEN a user views the dashboard, THE Import_Modal SHALL be accessible via an import button in the Quick Actions section
2. WHEN the import button is clicked, THE Import_Modal SHALL display with two import method options: JSON input and CSV file upload
3. WHEN the JSON input method is selected, THE Import_Modal SHALL provide a textarea for pasting JSON data
4. WHEN the CSV upload method is selected, THE Import_Modal SHALL provide a drag-and-drop file upload area
5. WHEN the user submits the import, THE Import_Modal SHALL display a loading indicator during processing
6. WHEN the import succeeds, THE Import_Modal SHALL display a success message with the count of imported projects
7. WHEN the import fails, THE Import_Modal SHALL display validation errors in a clear, readable format
8. WHEN validation errors are displayed, THE Import_Modal SHALL identify which records failed and why

### Requirement 7: Error Handling and User Feedback

**User Story:** As a user, I want clear error messages when imports fail, so that I can correct the data and retry the import successfully.

#### Acceptance Criteria

1. WHEN validation fails, THE Import_Service SHALL return error messages that identify the specific record and field that failed
2. WHEN a CSV parsing error occurs, THE Import_Service SHALL return the line number and parsing error description
3. WHEN a duplicate project name is detected, THE Import_Service SHALL return the conflicting project name
4. WHEN authentication fails, THE API_Endpoint SHALL return a clear message indicating invalid credentials
5. WHEN authorization fails, THE API_Endpoint SHALL return a clear message indicating insufficient permissions
6. THE Import_Service SHALL return all error messages in a structured JSON format for frontend parsing

### Requirement 8: Data Type Validation

**User Story:** As a data administrator, I want imported data to match expected data types, so that the application functions correctly with imported projects.

#### Acceptance Criteria

1. WHEN a budget value is provided, THE Validation_Engine SHALL verify it can be parsed as a numeric value
2. WHEN a date value is provided, THE Validation_Engine SHALL verify it matches ISO 8601 format (YYYY-MM-DD)
3. WHEN a status value is provided, THE Validation_Engine SHALL verify it matches one of the allowed status values
4. WHEN a required field is empty or null, THE Validation_Engine SHALL reject the record
5. WHEN optional fields are missing, THE Validation_Engine SHALL accept the record and use default values

### Requirement 9: Batch Import Atomicity

**User Story:** As a data administrator, I want import operations to be atomic, so that either all valid projects are imported or none are imported if any validation fails.

#### Acceptance Criteria

1. WHEN any record in an import batch fails validation, THE Import_Service SHALL reject the entire batch
2. WHEN all records in an import batch pass validation, THE Import_Service SHALL import all records in a single database transaction
3. WHEN a database error occurs during import, THE Import_Service SHALL roll back all changes from that import session
4. WHEN an import is rolled back, THE Import_Service SHALL return an error message indicating the rollback occurred
5. THE Import_Service SHALL ensure no partial imports are committed to the database

### Requirement 10: CSV Format Requirements

**User Story:** As a user, I want to understand the expected CSV format, so that I can prepare my data correctly for import.

#### Acceptance Criteria

1. THE CSV_Parser SHALL accept CSV files with a header row containing column names
2. THE CSV_Parser SHALL map the following column names to project fields: name, budget, status, start_date, end_date, description
3. WHEN column names do not match expected names, THE CSV_Parser SHALL return an error listing the expected column names
4. THE CSV_Parser SHALL accept both comma and semicolon as field delimiters
5. THE CSV_Parser SHALL handle quoted fields containing commas or newlines
