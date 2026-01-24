"""
Unit tests for ImportParser service.

Tests the parsing of CSV and JSON files for actuals and commitments import.
"""

import pytest
from services.import_parser import ImportParser, FileFormat, ParseError


class TestImportParser:
    """Test suite for ImportParser service."""
    
    @pytest.fixture
    def parser(self):
        """Create ImportParser instance."""
        return ImportParser()
    
    # Format Detection Tests
    
    def test_detect_format_csv(self, parser):
        """Test CSV format detection."""
        assert parser.detect_format("data.csv") == FileFormat.CSV
        assert parser.detect_format("DATA.CSV") == FileFormat.CSV
        assert parser.detect_format("file.CSV") == FileFormat.CSV
    
    def test_detect_format_json(self, parser):
        """Test JSON format detection."""
        assert parser.detect_format("data.json") == FileFormat.JSON
        assert parser.detect_format("DATA.JSON") == FileFormat.JSON
        assert parser.detect_format("file.JSON") == FileFormat.JSON
    
    def test_detect_format_unknown(self, parser):
        """Test unknown format detection."""
        assert parser.detect_format("data.txt") == FileFormat.UNKNOWN
        assert parser.detect_format("data.xlsx") == FileFormat.UNKNOWN
        assert parser.detect_format("data") == FileFormat.UNKNOWN
    
    # CSV Parsing Tests
    
    def test_parse_csv_actuals_semicolon_delimiter(self, parser):
        """Test parsing actuals CSV with semicolon delimiter."""
        csv_content = b"""fi_doc_no;posting_date;vendor;project_nr;amount;currency
FI-001;2024-01-15;ACME Corp;PRJ-001;1000.50;EUR
FI-002;2024-01-16;XYZ Ltd;PRJ-002;2500.75;USD"""
        
        records = parser.parse_csv(csv_content, 'actuals')
        
        assert len(records) == 2
        assert records[0]['fi_doc_no'] == 'FI-001'
        assert records[0]['vendor'] == 'ACME Corp'
        assert records[0]['amount'] == '1000.50'
        assert records[1]['fi_doc_no'] == 'FI-002'
    
    def test_parse_csv_commitments_semicolon_delimiter(self, parser):
        """Test parsing commitments CSV with semicolon delimiter."""
        csv_content = b"""po_number;po_date;vendor;project_nr;po_net_amount;total_amount;currency;po_line_nr
PO-001;2024-01-15;ACME Corp;PRJ-001;5000.00;5500.00;EUR;1
PO-001;2024-01-15;ACME Corp;PRJ-001;3000.00;3300.00;EUR;2"""
        
        records = parser.parse_csv(csv_content, 'commitments')
        
        assert len(records) == 2
        assert records[0]['po_number'] == 'PO-001'
        assert records[0]['po_line_nr'] == '1'
        assert records[1]['po_line_nr'] == '2'
    
    def test_parse_csv_comma_delimiter_fallback(self, parser):
        """Test CSV parsing falls back to comma delimiter."""
        csv_content = b"""fi_doc_no,posting_date,vendor,project_nr,amount,currency
FI-001,2024-01-15,ACME Corp,PRJ-001,1000.50,EUR"""
        
        records = parser.parse_csv(csv_content, 'actuals')
        
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
    
    def test_parse_csv_case_insensitive_headers(self, parser):
        """Test CSV parsing handles case-insensitive headers."""
        csv_content = b"""FI_DOC_NO;POSTING_DATE;VENDOR;PROJECT_NR;AMOUNT;CURRENCY
FI-001;2024-01-15;ACME Corp;PRJ-001;1000.50;EUR"""
        
        records = parser.parse_csv(csv_content, 'actuals')
        
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
    
    def test_parse_csv_alternative_column_names(self, parser):
        """Test CSV parsing maps alternative column names."""
        csv_content = b"""financial document number;posting date;supplier;project number;amount;curr
FI-001;2024-01-15;ACME Corp;PRJ-001;1000.50;EUR"""
        
        records = parser.parse_csv(csv_content, 'actuals')
        
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
        assert records[0]['vendor'] == 'ACME Corp'  # 'supplier' maps to 'vendor'
        assert records[0]['project_nr'] == 'PRJ-001'
    
    def test_parse_csv_empty_file(self, parser):
        """Test CSV parsing fails with empty file."""
        csv_content = b""
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse_csv(csv_content, 'actuals')
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_parse_csv_only_headers(self, parser):
        """Test CSV parsing fails with only headers."""
        csv_content = b"fi_doc_no;posting_date;vendor;project_nr;amount;currency"
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse_csv(csv_content, 'actuals')
        
        assert "empty" in str(exc_info.value).lower()
    
    # JSON Parsing Tests
    
    def test_parse_json_actuals(self, parser):
        """Test parsing actuals JSON."""
        json_content = b"""[
            {
                "fi_doc_no": "FI-001",
                "posting_date": "2024-01-15",
                "vendor": "ACME Corp",
                "project_nr": "PRJ-001",
                "amount": 1000.50,
                "currency": "EUR"
            },
            {
                "fi_doc_no": "FI-002",
                "posting_date": "2024-01-16",
                "vendor": "XYZ Ltd",
                "project_nr": "PRJ-002",
                "amount": 2500.75,
                "currency": "USD"
            }
        ]"""
        
        records = parser.parse_json(json_content, 'actuals')
        
        assert len(records) == 2
        assert records[0]['fi_doc_no'] == 'FI-001'
        assert records[0]['vendor'] == 'ACME Corp'
        assert records[1]['fi_doc_no'] == 'FI-002'
    
    def test_parse_json_commitments(self, parser):
        """Test parsing commitments JSON."""
        json_content = b"""[
            {
                "po_number": "PO-001",
                "po_date": "2024-01-15",
                "vendor": "ACME Corp",
                "project_nr": "PRJ-001",
                "po_net_amount": 5000.00,
                "total_amount": 5500.00,
                "currency": "EUR",
                "po_line_nr": 1
            }
        ]"""
        
        records = parser.parse_json(json_content, 'commitments')
        
        assert len(records) == 1
        assert records[0]['po_number'] == 'PO-001'
        assert records[0]['po_line_nr'] == 1
    
    def test_parse_json_invalid_format(self, parser):
        """Test JSON parsing fails with invalid JSON."""
        json_content = b"{invalid json"
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse_json(json_content, 'actuals')
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_parse_json_not_array(self, parser):
        """Test JSON parsing fails when not an array."""
        json_content = b'{"fi_doc_no": "FI-001"}'
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse_json(json_content, 'actuals')
        
        assert "array" in str(exc_info.value).lower()
    
    def test_parse_json_empty_array(self, parser):
        """Test JSON parsing fails with empty array."""
        json_content = b"[]"
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse_json(json_content, 'actuals')
        
        assert "empty" in str(exc_info.value).lower()
    
    # Encoding Detection Tests
    
    def test_detect_encoding_utf8(self, parser):
        """Test UTF-8 encoding detection."""
        content = "Test content".encode('utf-8')
        encoding = parser.detect_encoding(content)
        assert encoding in ['utf-8', 'ascii']
    
    def test_detect_encoding_latin1(self, parser):
        """Test Latin-1 encoding detection."""
        content = "Tëst cöntënt".encode('latin-1')
        encoding = parser.detect_encoding(content)
        # Should detect some encoding
        assert encoding is not None
    
    # Parse Method Tests
    
    def test_parse_detects_csv_format(self, parser):
        """Test parse method detects CSV format."""
        csv_content = b"fi_doc_no;posting_date;vendor;project_nr;amount;currency\nFI-001;2024-01-15;ACME;PRJ-001;1000;EUR"
        
        records, file_format = parser.parse(csv_content, "data.csv", "actuals")
        
        assert file_format == FileFormat.CSV
        assert len(records) == 1
    
    def test_parse_detects_json_format(self, parser):
        """Test parse method detects JSON format."""
        json_content = b'[{"fi_doc_no": "FI-001", "posting_date": "2024-01-15", "vendor": "ACME", "project_nr": "PRJ-001", "amount": 1000, "currency": "EUR"}]'
        
        records, file_format = parser.parse(json_content, "data.json", "actuals")
        
        assert file_format == FileFormat.JSON
        assert len(records) == 1
    
    def test_parse_rejects_unknown_format(self, parser):
        """Test parse method rejects unknown format."""
        content = b"some content"
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse(content, "data.txt", "actuals")
        
        assert "Unsupported file format" in str(exc_info.value)
        assert ".csv" in str(exc_info.value)
        assert ".json" in str(exc_info.value)
