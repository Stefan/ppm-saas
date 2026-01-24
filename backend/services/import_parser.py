"""
Import Parser Service for Actuals and Commitments

This service parses CSV and JSON files for importing financial actuals and commitments data.
Handles semicolon-delimited CSV, JSON arrays, encoding detection, and column mapping.

Requirements: 2.7, 3.7
"""

import csv
import json
import chardet
from typing import List, Dict, Any, Tuple
from io import StringIO
from enum import Enum


class FileFormat(str, Enum):
    """Supported file formats for import."""
    CSV = "csv"
    JSON = "json"
    UNKNOWN = "unknown"


class ParseError(Exception):
    """Exception raised for parsing errors."""
    pass


class ImportParser:
    """
    Service for parsing CSV and JSON files for actuals and commitments import.
    
    Supports:
    - Semicolon-delimited CSV files
    - JSON array format
    - Automatic encoding detection (UTF-8, Latin-1, etc.)
    - Column header mapping to model fields
    - Quoted fields with embedded semicolons/newlines
    """
    
    # Column mappings for actuals
    ACTUALS_COLUMN_MAPPING = {
        "fi_doc_no": ["fi_doc_no", "fi doc no", "financial document number", "doc_no", "document_number"],
        "posting_date": ["posting_date", "posting date", "post_date", "date"],
        "document_date": ["document_date", "document date", "doc_date"],
        "vendor": ["vendor", "vendor_name", "supplier"],
        "vendor_description": ["vendor_description", "vendor description", "vendor_desc"],
        "project_nr": ["project_nr", "project nr", "project number", "project_number", "project"],
        "wbs_element": ["wbs_element", "wbs element", "wbs", "work breakdown structure"],
        "amount": ["amount", "value", "cost"],
        "currency": ["currency", "curr", "currency_code"],
        "item_text": ["item_text", "item text", "description", "item_description"],
        "document_type": ["document_type", "document type", "doc_type", "type"],
    }
    
    # Column mappings for commitments
    COMMITMENTS_COLUMN_MAPPING = {
        "po_number": ["po_number", "po number", "purchase order", "po", "order_number"],
        "po_date": ["po_date", "po date", "order_date", "date"],
        "vendor": ["vendor", "vendor_name", "supplier"],
        "vendor_description": ["vendor_description", "vendor description", "vendor_desc"],
        "project_nr": ["project_nr", "project nr", "project number", "project_number", "project"],
        "wbs_element": ["wbs_element", "wbs element", "wbs", "work breakdown structure"],
        "po_net_amount": ["po_net_amount", "po net amount", "net_amount", "net amount"],
        "total_amount": ["total_amount", "total amount", "total", "gross_amount"],
        "currency": ["currency", "curr", "currency_code"],
        "po_status": ["po_status", "po status", "status", "order_status"],
        "po_line_nr": ["po_line_nr", "po line nr", "line_number", "line number", "line"],
        "delivery_date": ["delivery_date", "delivery date", "expected_delivery", "delivery"],
    }
    
    def detect_format(self, filename: str) -> FileFormat:
        """
        Detect file format based on file extension.
        
        Args:
            filename: Name of the file including extension
            
        Returns:
            FileFormat enum value (CSV, JSON, or UNKNOWN)
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.csv'):
            return FileFormat.CSV
        elif filename_lower.endswith('.json'):
            return FileFormat.JSON
        else:
            return FileFormat.UNKNOWN
    
    def detect_encoding(self, file_content: bytes) -> str:
        """
        Detect the encoding of file content.
        
        Uses chardet library to detect encoding, with fallback to UTF-8.
        
        Args:
            file_content: Raw file bytes
            
        Returns:
            Detected encoding name (e.g., 'utf-8', 'latin-1')
        """
        # Try to detect encoding
        detection = chardet.detect(file_content)
        encoding = detection.get('encoding', 'utf-8')
        confidence = detection.get('confidence', 0)
        
        # If confidence is low, default to UTF-8
        if confidence < 0.7:
            encoding = 'utf-8'
        
        # Normalize encoding names
        if encoding and encoding.lower() in ['ascii', 'us-ascii']:
            encoding = 'utf-8'
        
        return encoding or 'utf-8'
    
    def parse_csv(
        self,
        file_content: bytes,
        import_type: str,
        encoding: str = None
    ) -> List[Dict[str, Any]]:
        """
        Parse semicolon-delimited CSV file into list of dictionaries.
        
        Process:
        1. Detect encoding if not provided
        2. Decode bytes to string
        3. Parse CSV with semicolon delimiter
        4. Map column headers to model fields
        5. Return list of records
        
        Args:
            file_content: Raw CSV file bytes
            import_type: Type of import ('actuals' or 'commitments')
            encoding: Optional encoding (auto-detected if not provided)
            
        Returns:
            List of dictionaries with mapped field names
            
        Raises:
            ParseError: If CSV cannot be parsed
        """
        # Detect encoding if not provided
        if encoding is None:
            encoding = self.detect_encoding(file_content)
        
        # Try to decode with detected encoding
        try:
            content_str = file_content.decode(encoding)
        except UnicodeDecodeError:
            # Fallback to UTF-8 with error handling
            try:
                content_str = file_content.decode('utf-8', errors='replace')
            except Exception as e:
                raise ParseError(f"Failed to decode file content: {str(e)}")
        
        # Parse CSV
        try:
            # Use StringIO to treat string as file
            csv_file = StringIO(content_str)
            
            # Try semicolon delimiter first (as specified in requirements)
            reader = csv.DictReader(csv_file, delimiter=';')
            rows = list(reader)
            
            # If we got no rows or only one column, try comma delimiter
            if not rows or (rows and len(rows[0]) == 1):
                csv_file.seek(0)
                reader = csv.DictReader(csv_file, delimiter=',')
                rows = list(reader)
            
            if not rows:
                raise ParseError("CSV file is empty or has no data rows")
            
        except csv.Error as e:
            raise ParseError(f"Failed to parse CSV: {str(e)}")
        except Exception as e:
            raise ParseError(f"Unexpected error parsing CSV: {str(e)}")
        
        # Map column headers to model fields
        column_mapping = (
            self.ACTUALS_COLUMN_MAPPING if import_type == 'actuals'
            else self.COMMITMENTS_COLUMN_MAPPING
        )
        
        mapped_rows = []
        for row_num, row in enumerate(rows, start=2):  # Start at 2 (1 is header)
            try:
                mapped_row = self._map_columns(row, column_mapping)
                mapped_rows.append(mapped_row)
            except Exception as e:
                raise ParseError(f"Error mapping columns in row {row_num}: {str(e)}")
        
        return mapped_rows
    
    def parse_json(
        self,
        file_content: bytes,
        import_type: str,
        encoding: str = None
    ) -> List[Dict[str, Any]]:
        """
        Parse JSON file into list of dictionaries.
        
        Expects JSON array format: [{"field": "value", ...}, ...]
        
        Args:
            file_content: Raw JSON file bytes
            import_type: Type of import ('actuals' or 'commitments')
            encoding: Optional encoding (auto-detected if not provided)
            
        Returns:
            List of dictionaries with mapped field names
            
        Raises:
            ParseError: If JSON cannot be parsed
        """
        # Detect encoding if not provided
        if encoding is None:
            encoding = self.detect_encoding(file_content)
        
        # Try to decode with detected encoding
        try:
            content_str = file_content.decode(encoding)
        except UnicodeDecodeError:
            # Fallback to UTF-8 with error handling
            try:
                content_str = file_content.decode('utf-8', errors='replace')
            except Exception as e:
                raise ParseError(f"Failed to decode file content: {str(e)}")
        
        # Parse JSON
        try:
            data = json.loads(content_str)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON format: {str(e)}")
        
        # Validate that data is a list
        if not isinstance(data, list):
            raise ParseError("JSON must be an array of objects")
        
        if not data:
            raise ParseError("JSON array is empty")
        
        # Map column headers to model fields
        column_mapping = (
            self.ACTUALS_COLUMN_MAPPING if import_type == 'actuals'
            else self.COMMITMENTS_COLUMN_MAPPING
        )
        
        mapped_rows = []
        for row_num, row in enumerate(data, start=1):
            if not isinstance(row, dict):
                raise ParseError(f"Row {row_num} is not a valid object")
            try:
                mapped_row = self._map_columns(row, column_mapping)
                mapped_rows.append(mapped_row)
            except Exception as e:
                raise ParseError(f"Error mapping columns in row {row_num}: {str(e)}")
        
        return mapped_rows
    
    def _map_columns(
        self,
        row: Dict[str, Any],
        column_mapping: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Map CSV/JSON column names to model field names.
        
        Performs case-insensitive matching and handles various column name formats.
        
        Args:
            row: Dictionary with original column names
            column_mapping: Mapping from model fields to possible column names
            
        Returns:
            Dictionary with standardized field names
        """
        mapped = {}
        
        # Normalize row keys to lowercase for case-insensitive matching
        row_lower = {k.lower().strip(): v for k, v in row.items()}
        
        # Map each field
        for model_field, possible_names in column_mapping.items():
            value = None
            
            # Try each possible column name
            for col_name in possible_names:
                if col_name.lower() in row_lower:
                    value = row_lower[col_name.lower()]
                    break
            
            # Store the value (even if None)
            if value is not None and value != '':
                # Strip whitespace from string values
                if isinstance(value, str):
                    value = value.strip()
                mapped[model_field] = value
        
        return mapped
    
    def parse(
        self,
        file_content: bytes,
        filename: str,
        import_type: str
    ) -> Tuple[List[Dict[str, Any]], FileFormat]:
        """
        Parse file content based on detected format.
        
        Convenience method that detects format and calls appropriate parser.
        
        Args:
            file_content: Raw file bytes
            filename: Name of the file (used for format detection)
            import_type: Type of import ('actuals' or 'commitments')
            
        Returns:
            Tuple of (parsed records, detected format)
            
        Raises:
            ParseError: If file format is unsupported or parsing fails
        """
        # Detect format
        file_format = self.detect_format(filename)
        
        if file_format == FileFormat.UNKNOWN:
            raise ParseError(
                f"Unsupported file format. Please upload a CSV or JSON file. "
                f"Accepted formats: .csv, .json"
            )
        
        # Parse based on format
        if file_format == FileFormat.CSV:
            records = self.parse_csv(file_content, import_type)
        elif file_format == FileFormat.JSON:
            records = self.parse_json(file_content, import_type)
        else:
            raise ParseError(f"Unsupported file format: {file_format}")
        
        return records, file_format
