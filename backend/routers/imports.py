"""
Import Router for Actuals and Commitments

This router provides REST endpoints for importing financial actuals and commitments data.
Supports CSV and JSON file uploads with validation, anonymization, and audit logging.

Requirements: 2.1, 3.1, 5.1, 5.2, 5.3, 7.7, 10.4
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import Optional, List
import logging

from auth.dependencies import get_current_user
from auth.rbac import require_permission, Permission
from config.database import supabase
from models.imports import (
    ImportResult, ImportAuditLogResponse, ImportType
)
from services.actuals_commitments_import import ActualsCommitmentsImportService
from services.import_parser import ImportParser, ParseError, FileFormat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post("/actuals", response_model=ImportResult)
async def import_actuals(
    file: UploadFile = File(..., description="CSV or JSON file containing actuals data"),
    anonymize: bool = Query(default=True, description="Whether to anonymize sensitive data"),
    current_user = Depends(require_permission(Permission.data_import))
) -> ImportResult:
    """
    Import actuals from CSV/JSON file.
    
    This endpoint accepts a CSV (semicolon-delimited) or JSON file containing
    financial actuals data. The data is validated, optionally anonymized,
    checked for duplicates, and imported into the database.
    
    **Process:**
    1. Parse file (CSV or JSON)
    2. Validate each record
    3. Anonymize sensitive data (if requested)
    4. Check for duplicates by fi_doc_no
    5. Link to projects (create if needed)
    6. Insert valid records
    7. Log import operation
    
    **Required Fields:**
    - fi_doc_no: Financial Document Number
    - posting_date: Posting date (YYYY-MM-DD)
    - vendor: Vendor name
    - project_nr: Project number
    - amount: Transaction amount
    
    **Optional Fields:**
    - document_date, vendor_description, wbs_element, currency, item_text, document_type
    
    **Returns:**
    - ImportResult with statistics and error details
    
    **Requirements:** 2.1, 2.2, 5.1, 5.2, 5.3
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        # Parse file
        parser = ImportParser()
        try:
            records, file_format = parser.parse(
                file_content,
                file.filename,
                import_type='actuals'
            )
            logger.info(
                f"Parsed {len(records)} actuals records from {file_format.value} file"
            )
        except ParseError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse file: {str(e)}"
            )
        
        # Initialize import service
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID not found in authentication token"
            )
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable"
            )
        
        import_service = ActualsCommitmentsImportService(supabase, user_id)
        
        # Import records
        result = await import_service.import_actuals(records, anonymize=anonymize)
        
        logger.info(
            f"Actuals import {result.import_id} completed: "
            f"{result.success_count} success, {result.duplicate_count} duplicates, "
            f"{result.error_count} errors"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in actuals import: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import actuals: {str(e)}"
        )


@router.post("/commitments", response_model=ImportResult)
async def import_commitments(
    file: UploadFile = File(..., description="CSV or JSON file containing commitments data"),
    anonymize: bool = Query(default=True, description="Whether to anonymize sensitive data"),
    current_user = Depends(require_permission(Permission.data_import))
) -> ImportResult:
    """
    Import commitments from CSV/JSON file.
    
    This endpoint accepts a CSV (semicolon-delimited) or JSON file containing
    financial commitments data. The data is validated, optionally anonymized,
    checked for duplicates, and imported into the database.
    
    **Process:**
    1. Parse file (CSV or JSON)
    2. Validate each record
    3. Anonymize sensitive data (if requested)
    4. Check for duplicates by (po_number, po_line_nr)
    5. Link to projects (create if needed)
    6. Insert valid records
    7. Log import operation
    
    **Required Fields:**
    - po_number: Purchase Order Number
    - po_date: PO date (YYYY-MM-DD)
    - vendor: Vendor name
    - project_nr: Project number
    - po_net_amount: Net amount
    - total_amount: Total amount including taxes
    
    **Optional Fields:**
    - vendor_description, wbs_element, currency, po_status, po_line_nr, delivery_date
    
    **Returns:**
    - ImportResult with statistics and error details
    
    **Requirements:** 3.1, 3.2, 5.1, 5.2, 5.3
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        # Parse file
        parser = ImportParser()
        try:
            records, file_format = parser.parse(
                file_content,
                file.filename,
                import_type='commitments'
            )
            logger.info(
                f"Parsed {len(records)} commitments records from {file_format.value} file"
            )
        except ParseError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse file: {str(e)}"
            )
        
        # Initialize import service
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID not found in authentication token"
            )
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable"
            )
        
        import_service = ActualsCommitmentsImportService(supabase, user_id)
        
        # Import records
        result = await import_service.import_commitments(records, anonymize=anonymize)
        
        logger.info(
            f"Commitments import {result.import_id} completed: "
            f"{result.success_count} success, {result.duplicate_count} duplicates, "
            f"{result.error_count} errors"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in commitments import: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import commitments: {str(e)}"
        )


@router.get("/templates/{import_type}")
async def get_import_template(
    import_type: ImportType,
    current_user = Depends(get_current_user)
):
    """
    Get CSV template for import type.
    
    Returns a template with column headers and example data for the specified
    import type. Users can download this template, fill it with their data,
    and upload it for import.
    
    **Supported Import Types:**
    - actuals: Financial actuals template
    - commitments: Purchase order commitments template
    
    **Returns:**
    - Dictionary with headers and example row
    
    **Requirements:** 7.7
    """
    try:
        templates = {
            ImportType.actuals: {
                "headers": [
                    "fi_doc_no",
                    "posting_date",
                    "document_date",
                    "vendor",
                    "vendor_description",
                    "project_nr",
                    "wbs_element",
                    "amount",
                    "currency",
                    "item_text",
                    "document_type"
                ],
                "example": {
                    "fi_doc_no": "FI-2024-001234",
                    "posting_date": "2024-01-15",
                    "document_date": "2024-01-14",
                    "vendor": "Vendor A",
                    "vendor_description": "Vendor Description",
                    "project_nr": "P0001",
                    "wbs_element": "WBS-001",
                    "amount": "12345.67",
                    "currency": "EUR",
                    "item_text": "Item Description",
                    "document_type": "Invoice"
                },
                "description": "Template for importing financial actuals data",
                "required_fields": [
                    "fi_doc_no",
                    "posting_date",
                    "vendor",
                    "project_nr",
                    "amount"
                ]
            },
            ImportType.commitments: {
                "headers": [
                    "po_number",
                    "po_date",
                    "vendor",
                    "vendor_description",
                    "project_nr",
                    "wbs_element",
                    "po_net_amount",
                    "total_amount",
                    "currency",
                    "po_status",
                    "po_line_nr",
                    "delivery_date"
                ],
                "example": {
                    "po_number": "PO-2024-001234",
                    "po_date": "2024-01-15",
                    "vendor": "Vendor A",
                    "vendor_description": "Vendor Description",
                    "project_nr": "P0001",
                    "wbs_element": "WBS-001",
                    "po_net_amount": "10000.00",
                    "total_amount": "11900.00",
                    "currency": "EUR",
                    "po_status": "Open",
                    "po_line_nr": "1",
                    "delivery_date": "2024-02-15"
                },
                "description": "Template for importing purchase order commitments data",
                "required_fields": [
                    "po_number",
                    "po_date",
                    "vendor",
                    "project_nr",
                    "po_net_amount",
                    "total_amount"
                ]
            }
        }
        
        template = templates.get(import_type)
        if not template:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid import type: {import_type}. Must be 'actuals' or 'commitments'"
            )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import template: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get import template: {str(e)}"
        )


@router.get("/history", response_model=List[ImportAuditLogResponse])
async def get_import_history(
    import_type: Optional[ImportType] = Query(None, description="Filter by import type"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user = Depends(get_current_user)
) -> List[ImportAuditLogResponse]:
    """
    Get import history for the current user.
    
    Returns a paginated list of import audit log entries for the authenticated user.
    Can be filtered by import type (actuals or commitments).
    
    **Query Parameters:**
    - import_type: Optional filter by 'actuals' or 'commitments'
    - limit: Maximum number of records (1-100, default 50)
    - offset: Number of records to skip for pagination (default 0)
    
    **Returns:**
    - List of import audit log entries with statistics
    
    **Requirements:** 10.4
    """
    try:
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable"
            )
        
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID not found in authentication token"
            )
        
        # Build query
        query = supabase.table("import_audit_logs").select("*").eq("user_id", user_id)
        
        # Apply import type filter if provided
        if import_type:
            query = query.eq("import_type", import_type.value)
        
        # Apply pagination and ordering
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        # Convert to response models
        audit_logs = []
        for log in response.data:
            audit_logs.append(ImportAuditLogResponse(
                id=log["id"],
                import_id=log["import_id"],
                user_id=log["user_id"],
                import_type=log["import_type"],
                total_records=log["total_records"],
                success_count=log["success_count"],
                duplicate_count=log["duplicate_count"],
                error_count=log["error_count"],
                status=log["status"],
                errors=log.get("errors"),
                created_at=log["created_at"],
                completed_at=log.get("completed_at")
            ))
        
        logger.info(f"Retrieved {len(audit_logs)} import history entries for user {user_id}")
        
        return audit_logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get import history: {str(e)}"
        )
