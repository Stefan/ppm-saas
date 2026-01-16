# Design Document: Project Import MVP

## Overview

The Project Import MVP feature enables users to import multiple projects into ORKA-PPM through two primary methods: JSON array via REST API and CSV file upload. The system validates all imported data against business rules, enforces authentication and authorization, and maintains a comprehensive audit trail.

The architecture follows a layered approach with clear separation between API endpoints, business logic, validation, and data persistence. The frontend provides an intuitive modal interface for both import methods with real-time feedback and error reporting.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌────────────────┐         ┌──────────────────────────┐   │
│  │   Dashboard    │────────▶│  ProjectImportModal      │   │
│  │  (Quick Actions)│         │  - JSON Input            │   │
│  └────────────────┘         │  - CSV Upload            │   │
│                              │  - Error Display         │   │
│                              └──────────┬───────────────┘   │
└─────────────────────────────────────────┼───────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /api/projects/import                           │  │
│  │  POST /api/projects/import/csv                       │  │
│  │  - JWT Authentication                                │  │
│  │  - RBAC Permission Check (data_import)               │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ Import Service  │  │  Validation  │  │ Audit Logger  │ │
│  │ - Orchestration │─▶│   Engine     │  │ - Log Events  │ │
│  │ - Transaction   │  │ - Required   │  │ - User Track  │ │
│  │   Management    │  │   Fields     │  │ - Timestamps  │ │
│  │                 │  │ - Duplicates │  └───────────────┘ │
│  │                 │  │ - Data Types │                     │
│  └─────────────────┘  └──────────────┘                     │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                        │
│  │   CSV Parser    │                                        │
│  │ - Pandas-based  │                                        │
│  │ - Header Map    │                                        │
│  │ - Type Coercion │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Persistence Layer                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Supabase Database                       │  │
│  │  - projects table                                    │  │
│  │  - audit_logs table                                  │  │
│  │  - Transaction support                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Initiates Import**: User clicks import button in dashboard, opens modal
2. **Method Selection**: User chooses JSON input or CSV upload
3. **Data Submission**: Frontend sends data to appropriate API endpoint
4. **Authentication**: API validates JWT token and extracts user identity
5. **Authorization**: API checks user has `data_import` permission
6. **Parsing** (CSV only): CSV Parser converts file to project records
7. **Validation**: Validation Engine checks all records against business rules
8. **Audit Logging**: Audit Logger records import attempt with user and timestamp
9. **Database Transaction**: Import Service creates all projects in single transaction
10. **Response**: API returns success with count or detailed error messages
11. **User Feedback**: Frontend displays results in modal

## Components and Interfaces

### Backend Components

#### 1. Import Router (`backend/routers/projects_import.py`)

New router module for import endpoints.

```python
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
from backend.auth.dependencies import get_current_user
from backend.auth.rbac import require_permission, Permission
from backend.models.projects import ProjectCreate
from backend.services.import_service import ImportService
from backend.models.users import User

router = APIRouter(prefix="/api/projects", tags=["import"])

@router.post("/import")
async def import_projects_json(
    projects: List[ProjectCreate],
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.data_import))
):
    """
    Import multiple projects from JSON array.
    
    Args:
        projects: List of project data to import
        current_user: Authenticated user from JWT
        
    Returns:
        ImportResult with success status and count
        
    Raises:
        HTTPException: 400 for validation errors, 401/403 for auth errors
    """
    pass

@router.post("/import/csv")
async def import_projects_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.data_import))
):
    """
    Import multiple projects from CSV file.
    
    Args:
        file: CSV file upload
        current_user: Authenticated user from JWT
        
    Returns:
        ImportResult with success status and count
        
    Raises:
        HTTPException: 400 for parsing/validation errors, 401/403 for auth errors
    """
    pass
```

#### 2. Import Service (`backend/services/import_service.py`)

Core business logic for import operations.

```python
from typing import List, Dict, Any
from backend.models.projects import ProjectCreate
from backend.database import get_db
from backend.services.validation_service import ValidationService
from backend.services.audit_service import AuditService

class ImportResult:
    """Result of an import operation"""
    success: bool
    count: int
    errors: List[Dict[str, Any]]
    message: str

class ImportService:
    """
    Service for importing projects with validation and audit logging.
    """
    
    def __init__(self, db_session, user_id: str):
        self.db = db_session
        self.user_id = user_id
        self.validator = ValidationService(db_session)
        self.auditor = AuditService(db_session)
    
    async def import_projects(
        self, 
        projects: List[ProjectCreate],
        import_method: str
    ) -> ImportResult:
        """
        Import multiple projects with validation and audit logging.
        
        Process:
        1. Validate all projects
        2. Log audit event (start)
        3. Create all projects in transaction
        4. Log audit event (complete)
        5. Return result
        
        Args:
            projects: List of project data to import
            import_method: "json" or "csv"
            
        Returns:
            ImportResult with success status, count, and any errors
        """
        pass
    
    async def _validate_batch(
        self, 
        projects: List[ProjectCreate]
    ) -> List[Dict[str, Any]]:
        """
        Validate all projects in batch.
        Returns list of validation errors (empty if all valid).
        """
        pass
    
    async def _create_projects_transaction(
        self, 
        projects: List[ProjectCreate]
    ) -> int:
        """
        Create all projects in a single database transaction.
        Rolls back on any error.
        Returns count of created projects.
        """
        pass
```

#### 3. Validation Service (`backend/services/validation_service.py`)

Validates project data against business rules.

```python
from typing import Dict, Any, Optional
from backend.models.projects import ProjectCreate
from datetime import datetime

class ValidationService:
    """
    Service for validating project data against business rules.
    """
    
    REQUIRED_FIELDS = ["name", "budget", "status"]
    VALID_STATUSES = ["planning", "active", "on_hold", "completed", "cancelled"]
    
    def __init__(self, db_session):
        self.db = db_session
    
    def validate_project(
        self, 
        project: ProjectCreate, 
        index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a single project record.
        
        Validation rules:
        - Required fields must be present and non-empty
        - Budget must be numeric
        - Dates must be ISO 8601 format
        - Status must be in allowed values
        - Name must not duplicate existing project
        
        Args:
            project: Project data to validate
            index: Record index for error reporting
            
        Returns:
            Error dict if validation fails, None if valid
            Error format: {
                "index": int,
                "field": str,
                "value": Any,
                "error": str
            }
        """
        pass
    
    def _check_required_fields(
        self, 
        project: ProjectCreate
    ) -> Optional[str]:
        """Check all required fields are present and non-empty"""
        pass
    
    def _check_duplicate_name(
        self, 
        name: str
    ) -> bool:
        """Check if project name already exists in database"""
        pass
    
    def _validate_budget(
        self, 
        budget: Any
    ) -> bool:
        """Validate budget is numeric"""
        pass
    
    def _validate_date(
        self, 
        date_str: str
    ) -> bool:
        """Validate date is ISO 8601 format (YYYY-MM-DD)"""
        pass
    
    def _validate_status(
        self, 
        status: str
    ) -> bool:
        """Validate status is in allowed values"""
        pass
```

#### 4. CSV Parser Service (`backend/services/csv_parser.py`)

Parses CSV files into project records.

```python
import pandas as pd
from typing import List, Dict, Any
from io import BytesIO
from backend.models.projects import ProjectCreate

class CSVParseError(Exception):
    """Exception raised for CSV parsing errors"""
    pass

class CSVParser:
    """
    Service for parsing CSV files into project records.
    """
    
    COLUMN_MAPPING = {
        "name": "name",
        "budget": "budget",
        "status": "status",
        "start_date": "start_date",
        "end_date": "end_date",
        "description": "description"
    }
    
    REQUIRED_COLUMNS = ["name", "budget", "status"]
    
    def parse_csv(
        self, 
        file_content: bytes
    ) -> List[ProjectCreate]:
        """
        Parse CSV file into list of ProjectCreate objects.
        
        Process:
        1. Read CSV with pandas
        2. Validate header columns
        3. Map columns to project fields
        4. Convert each row to ProjectCreate
        5. Return list of projects
        
        Args:
            file_content: Raw CSV file bytes
            
        Returns:
            List of ProjectCreate objects
            
        Raises:
            CSVParseError: If CSV cannot be parsed or has invalid structure
        """
        pass
    
    def _validate_columns(
        self, 
        df: pd.DataFrame
    ) -> None:
        """
        Validate CSV has required columns.
        Raises CSVParseError if missing required columns.
        """
        pass
    
    def _row_to_project(
        self, 
        row: pd.Series, 
        index: int
    ) -> ProjectCreate:
        """
        Convert DataFrame row to ProjectCreate object.
        
        Args:
            row: Pandas Series representing one CSV row
            index: Row index for error reporting
            
        Returns:
            ProjectCreate object
            
        Raises:
            CSVParseError: If row cannot be converted
        """
        pass
```

#### 5. Audit Service (`backend/services/audit_service.py`)

Logs import operations for audit trail.

```python
from datetime import datetime
from typing import Optional

class AuditService:
    """
    Service for logging import operations to audit trail.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def log_import_start(
        self,
        user_id: str,
        import_method: str,
        record_count: int
    ) -> str:
        """
        Log the start of an import operation.
        
        Args:
            user_id: ID of user performing import
            import_method: "json" or "csv"
            record_count: Number of records in import batch
            
        Returns:
            Audit log ID for tracking this operation
        """
        pass
    
    async def log_import_complete(
        self,
        audit_id: str,
        success: bool,
        imported_count: int,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log the completion of an import operation.
        
        Args:
            audit_id: ID from log_import_start
            success: Whether import succeeded
            imported_count: Number of projects successfully imported
            error_message: Error description if failed
        """
        pass
```

### Frontend Components

#### 1. Import Button in Dashboard (`app/dashboards/page.tsx`)

Add import button to Quick Actions section (around line 756).

```typescript
// Add to Quick Actions section
<button
  onClick={() => setShowImportModal(true)}
  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
>
  <UploadIcon className="w-5 h-5" />
  Import Projects
</button>
```

#### 2. Project Import Modal (`components/projects/ProjectImportModal.tsx`)

Main modal component for import interface.

```typescript
import { useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface ImportError {
  index: number;
  field: string;
  value: any;
  error: string;
}

interface ImportResult {
  success: boolean;
  count: number;
  errors: ImportError[];
  message: string;
}

type ImportMethod = 'json' | 'csv';

export default function ProjectImportModal({ 
  isOpen, 
  onClose 
}: { 
  isOpen: boolean; 
  onClose: () => void;
}) {
  const [method, setMethod] = useState<ImportMethod>('json');
  const [jsonInput, setJsonInput] = useState('');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setCsvFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: false
  });

  const handleImport = async () => {
    // Implementation for calling import API
  };

  return (
    // Modal UI with method selection, input areas, and result display
  );
}
```

#### 3. Frontend API Route (`app/api/projects/import/route.ts`)

Next.js API route for proxying import requests.

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get('content-type');
    
    // Determine if JSON or CSV based on content type
    const isCSV = contentType?.includes('multipart/form-data');
    
    // Get auth token from cookies or headers
    const token = request.cookies.get('auth_token')?.value;
    
    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Proxy to backend API
    const backendUrl = isCSV 
      ? `${process.env.BACKEND_URL}/api/projects/import/csv`
      : `${process.env.BACKEND_URL}/api/projects/import`;
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        ...(isCSV ? {} : { 'Content-Type': 'application/json' })
      },
      body: isCSV ? await request.formData() : await request.text()
    });
    
    const data = await response.json();
    
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

## Data Models

### Project Import Request (JSON)

```json
[
  {
    "name": "Project Alpha",
    "budget": 150000.00,
    "status": "planning",
    "start_date": "2024-01-15",
    "end_date": "2024-12-31",
    "description": "Strategic initiative for Q1-Q4 2024"
  },
  {
    "name": "Project Beta",
    "budget": 75000.00,
    "status": "active",
    "start_date": "2024-02-01",
    "end_date": "2024-06-30",
    "description": "Infrastructure upgrade project"
  }
]
```

### CSV Format

```csv
name,budget,status,start_date,end_date,description
Project Alpha,150000.00,planning,2024-01-15,2024-12-31,Strategic initiative for Q1-Q4 2024
Project Beta,75000.00,active,2024-02-01,2024-06-30,Infrastructure upgrade project
```

### Import Result Response

```json
{
  "success": true,
  "count": 2,
  "errors": [],
  "message": "Successfully imported 2 projects"
}
```

### Validation Error Response

```json
{
  "success": false,
  "count": 0,
  "errors": [
    {
      "index": 0,
      "field": "name",
      "value": "",
      "error": "Required field 'name' is missing or empty"
    },
    {
      "index": 1,
      "field": "budget",
      "value": "invalid",
      "error": "Budget must be a numeric value"
    },
    {
      "index": 2,
      "field": "name",
      "value": "Existing Project",
      "error": "Project with name 'Existing Project' already exists"
    }
  ],
  "message": "Validation failed for 3 records"
}
```

### Audit Log Entry

```json
{
  "id": "audit_123456",
  "user_id": "user_789",
  "action": "project_import",
  "method": "csv",
  "timestamp": "2024-01-15T10:30:00Z",
  "record_count": 10,
  "success": true,
  "imported_count": 10,
  "error_message": null
}
```

## Error Handling

### Error Categories

1. **Authentication Errors (401)**
   - Missing JWT token
   - Invalid JWT token
   - Expired JWT token

2. **Authorization Errors (403)**
   - User lacks `data_import` permission
   - User account disabled

3. **Validation Errors (400)**
   - Missing required fields
   - Invalid data types
   - Duplicate project names
   - Invalid date formats
   - Invalid status values

4. **Parsing Errors (400)**
   - Invalid CSV structure
   - Missing required columns
   - Malformed JSON
   - File encoding issues

5. **Server Errors (500)**
   - Database connection failures
   - Transaction rollback failures
   - Audit logging failures

### Error Response Format

All errors follow consistent JSON structure:

```json
{
  "success": false,
  "count": 0,
  "errors": [
    {
      "index": 0,
      "field": "field_name",
      "value": "invalid_value",
      "error": "Human-readable error message"
    }
  ],
  "message": "Overall error summary"
}
```

### Error Handling Strategy

1. **Validation Errors**: Return all validation errors in single response (don't fail fast)
2. **Parsing Errors**: Return immediately with parsing error details
3. **Auth Errors**: Return immediately with appropriate status code
4. **Database Errors**: Roll back transaction, log error, return generic message
5. **Audit Failures**: Log warning but don't fail import operation

### Frontend Error Display

- Display validation errors in a scrollable list
- Highlight which record (index) and field failed
- Show the invalid value and reason
- Provide "Copy errors" button for sharing with support
- Allow user to fix data and retry without closing modal


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Valid imports create all projects

*For any* valid array of project data (JSON or CSV), when imported through the API, all projects should be created in the database and the response count should equal the number of projects in the input.

**Validates: Requirements 1.1, 1.2, 2.1, 2.3**

### Property 2: CSV header mapping preserves data

*For any* valid CSV file with a header row, regardless of column order, the CSV_Parser should correctly map all columns to their corresponding project fields and preserve all data values.

**Validates: Requirements 2.2, 10.1, 10.2**

### Property 3: Missing required fields are rejected

*For any* project record missing one or more required fields (name, budget, or status), the Validation_Engine should reject that record with an error identifying the missing field.

**Validates: Requirements 3.1, 8.4**

### Property 4: Duplicate names are rejected

*For any* project record with a name that already exists in the database, the Validation_Engine should reject that record with an error identifying the duplicate name.

**Validates: Requirements 3.2, 7.3**

### Property 5: Non-numeric budgets are rejected

*For any* project record with a budget value that cannot be parsed as a number, the Validation_Engine should reject that record with an error identifying the invalid budget.

**Validates: Requirements 3.3, 8.1**

### Property 6: Invalid date formats are rejected

*For any* project record with a date field that does not match ISO 8601 format (YYYY-MM-DD), the Validation_Engine should reject that record with an error identifying the invalid date.

**Validates: Requirements 3.4, 8.2**

### Property 7: Validation errors are comprehensive

*For any* import batch containing invalid records, the Import_Service should return error messages that identify every invalid record by index, the specific field that failed, the invalid value, and a human-readable error description.

**Validates: Requirements 3.5, 7.1**

### Property 8: Import atomicity (all-or-nothing)

*For any* import batch containing at least one invalid record, the Import_Service should reject the entire batch and ensure zero projects from that batch are created in the database.

**Validates: Requirements 3.6, 9.1, 9.5**

### Property 9: Invalid status values are rejected

*For any* project record with a status value not in the allowed set (planning, active, on_hold, completed, cancelled), the Validation_Engine should reject that record with an error identifying the invalid status.

**Validates: Requirements 8.3**

### Property 10: Minimal valid records are accepted

*For any* project record containing only required fields (name, budget, status) with valid values, the Validation_Engine should accept that record even when optional fields (start_date, end_date, description) are missing.

**Validates: Requirements 8.5**

### Property 11: Transaction atomicity for valid batches

*For any* import batch where all records pass validation, the Import_Service should create all projects in a single database transaction such that either all projects are created or none are created (if a database error occurs).

**Validates: Requirements 9.2**

### Property 12: Audit logging completeness

*For any* import operation (successful or failed), the Audit_Logger should create a database record containing the user identity, timestamp, import method, record count, success status, and (if failed) error message.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 13: Error response format consistency

*For any* error condition (validation, parsing, authentication, authorization, or server error), the Import_Service should return a JSON response with the structure: `{success: false, count: 0, errors: [...], message: "..."}`.

**Validates: Requirements 7.6**

### Property 14: CSV delimiter flexibility

*For any* valid CSV file using either comma or semicolon as the field delimiter, the CSV_Parser should successfully parse all rows into project records.

**Validates: Requirements 10.4**

### Property 15: Quoted field handling

*For any* CSV file containing quoted fields with embedded commas or newlines, the CSV_Parser should correctly parse the quoted content as single field values without splitting on the embedded delimiters.

**Validates: Requirements 10.5**

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, error conditions, and integration points
- **Property tests**: Verify universal properties across randomized inputs

Both approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide input space.

### Property-Based Testing Configuration

**Library Selection**: 
- Backend: Use `hypothesis` for Python property-based testing
- Frontend: Use `fast-check` for TypeScript property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: project-import-mvp, Property {number}: {property_text}`

**Property Test Implementation**:
- Each correctness property must be implemented by a single property-based test
- Property tests should be placed close to implementation tasks to catch errors early
- Each test must explicitly reference the property number from this design document

### Unit Testing Focus

Unit tests should focus on:
- Specific examples demonstrating correct behavior (e.g., importing a known valid project)
- Edge cases (e.g., empty CSV file, single-record import, maximum field lengths)
- Error conditions (e.g., malformed JSON, invalid JWT token, database connection failure)
- Integration points (e.g., API endpoint routing, authentication middleware, database transactions)

**Avoid writing too many unit tests** - property-based tests handle covering lots of inputs. Unit tests should be targeted and purposeful.

### Backend Testing

**Unit Tests**:
- Authentication failure scenarios (missing token, invalid token, expired token)
- Authorization failure scenarios (missing permission, disabled account)
- CSV parsing errors (malformed CSV, missing columns, encoding issues)
- Database transaction rollback on errors
- Audit logging failure graceful degradation
- API endpoint routing and HTTP method validation

**Property Tests** (one per correctness property):
1. Valid imports create all projects (Property 1)
2. CSV header mapping preserves data (Property 2)
3. Missing required fields are rejected (Property 3)
4. Duplicate names are rejected (Property 4)
5. Non-numeric budgets are rejected (Property 5)
6. Invalid date formats are rejected (Property 6)
7. Validation errors are comprehensive (Property 7)
8. Import atomicity for invalid batches (Property 8)
9. Invalid status values are rejected (Property 9)
10. Minimal valid records are accepted (Property 10)
11. Transaction atomicity for valid batches (Property 11)
12. Audit logging completeness (Property 12)
13. Error response format consistency (Property 13)
14. CSV delimiter flexibility (Property 14)
15. Quoted field handling (Property 15)

### Frontend Testing

**Unit Tests**:
- Import button renders in dashboard
- Modal opens and closes correctly
- Method selection switches UI
- File upload accepts CSV files only
- Loading indicator displays during API calls
- Success message displays with correct count
- Error messages display with record details
- JSON textarea validation

**Integration Tests**:
- End-to-end import flow with mock API
- Error handling with various API responses
- File upload with mock file objects

### Test Data Generators

For property-based tests, implement generators for:

**Valid Project Generator**:
```python
from hypothesis import strategies as st

@st.composite
def valid_project(draw):
    return {
        "name": draw(st.text(min_size=1, max_size=100)),
        "budget": draw(st.floats(min_value=0, max_value=1e9)),
        "status": draw(st.sampled_from(["planning", "active", "on_hold", "completed", "cancelled"])),
        "start_date": draw(st.dates().map(lambda d: d.isoformat())),
        "end_date": draw(st.dates().map(lambda d: d.isoformat())),
        "description": draw(st.text(max_size=500))
    }
```

**Invalid Project Generators**:
- Missing required fields
- Invalid budget values (strings, negative numbers)
- Invalid date formats
- Invalid status values
- Duplicate names

**CSV Generators**:
- Valid CSV with various column orders
- CSV with different delimiters
- CSV with quoted fields
- Malformed CSV structures

### Test Execution

**Backend**:
```bash
# Run all tests
pytest backend/tests/

# Run only property tests
pytest backend/tests/ -m property

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

**Frontend**:
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage
```

### Continuous Integration

- All tests must pass before merging
- Property tests run with 100 iterations in CI
- Code coverage target: 80% for new code
- Integration tests run against test database
