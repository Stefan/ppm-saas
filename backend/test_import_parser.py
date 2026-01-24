"""
Unit tests for Import Parser Service

Tests CSV and JSON parsing functionality for actuals and commitments import.
"""

import pytest
from services.import_parser import ImportParser, ParseError, FileFormat


class TestImportParser:
    """Test suite for ImportParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ImportParser()
    
    def test_detect_format_csv(self):
        """Test CSV format detection."""
        assert self.parser.detect_format("actuals.csv") == FileFormat.CSV
        assert self.parser.detect_format("ACTUALS.CSV") == FileFormat.CSV
        assert self.parser.detect_format("data.csv") == FileFormat.CSV
    
    def test_detect_format_json(self):
        """Test JSON format detection."""
        assert self.parser.detect_format("actuals.json") == FileFormat.JSON
        assert self.parser.detect_format("ACTUALS.JSON") == FileFormat.JSON
        assert self.parser.detect_format("data.json") == FileFormat.JSON
    
    def test_detect_format_unknown(self):
        """Test unknown format detection."""
        assert self.parser.detect_format("actuals.txt") == FileFormat.UNKNOWN
        assert self.parser.detect_format("actuals.xlsx") == FileFormat.UNKNOWN
        assert self.parser.detect_format("actuals") == FileFormat.UNKNOWN
    
    def test_detect_encoding_utf8(self):
        """Test UTF-8 encoding detection."""
        content = "Hello World".encode('utf-8')
        encoding = self.parser.detect_encoding(content)
        assert encoding in ['utf-8', 'ascii']
    
    def test_detect_encoding_latin1(self):
        """Test Latin-1 encoding detection."""
        content = "Café München".encode('latin-1')
        encoding = self.parser.detect_encoding(content)
        # Should detect some encoding (latin-1, iso-8859-1, or similar)
        assert encoding is not None
    
    def test_parse_csv_actuals_semicolon(self):
        """Test parsing semicolon-delimited CSV for actuals."""
        csv_content = """fi_doc_no;posting_date;vendor;project_nr;amount;currency
FI-001;2024-01-15;Vendor A;P0001;1234.56;EUR
FI-002;2024-01-16;Vendor B;P0002;2345.67;USD"""
        
        records = self.parser.parse_csv(
            csv_content.encode('utf-8'),
            'actuals'
        )
        
        assert len(records) == 2
        assert records[0]['fi_doc_no'] == 'FI-001'
        assert records[0]['posting_date'] == '2024-01-15'
        assert records[0]['vendor'] == 'Vendor A'
        assert records[0]['project_nr'] == 'P0001'
        assert records[0]['amount'] == '1234.56'
        assert records[0]['currency'] == 'EUR'
    
    def test_parse_csv_commitments_semicolon(self):
        """Test parsing semicolon-delimited CSV for commitments."""
        csv_content = """po_number;po_date;vendor;project_nr;po_net_amount;total_amount;currency;po_line_nr
PO-001;2024-01-15;Vendor A;P0001;10000.00;11900.00;EUR;1
PO-002;2024-01-16;Vendor B;P0002;20000.00;23800.00;USD;1"""
        
        records = self.parser.parse_csv(
            csv_content.encode('utf-8'),
            'commitments'
        )
        
        assert len(records) == 2
        assert records[0]['po_number'] == 'PO-001'
        assert records[0]['po_date'] == '2024-01-15'
        assert records[0]['vendor'] == 'Vendor A'
        assert records[0]['project_nr'] == 'P0001'
        assert records[0]['po_net_amount'] == '10000.00'
        assert records[0]['total_amount'] == '11900.00'
        assert records[0]['po_line_nr'] == '1'
    
    def test_parse_csv_comma_fallback(self):
        """Test parsing comma-delimited CSV (fallback)."""
        csv_content = """fi_doc_no,posting_date,vendor,project_nr,amount,currency
FI-001,2024-01-15,Vendor A,P0001,1234.56,EUR"""
        
        records = self.parser.parse_csv(
            csv_content.encode('utf-8'),
            'actuals'
        )
        
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
    
    def test_parse_csv_case_insensitive_headers(self):
        """Test case-insensitive column header matching."""
        csv_content = """FI_DOC_NO;POSTING_DATE;VENDOR;PROJECT_NR;AMOUNT;CURRENCY
FI-001;2024-01-15;Vendor A;P0001;1234.56;EUR"""
        
        records = self.parser.parse_csv(
            csv_content.encode('utf-8'),
            'actuals'
        )
        
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
    
    def test_parse_csv_alternative_column_names(self):
        """Test parsing with alternative column names."""
        csv_content = """document_number;posting date;vendor_name;project number;value;curr
FI-001;2024-01-15;Vendor A;P0001;1234.56;EUR"""
        
        records = self.parser.parse_csv(
            csv_content.encode('utf-8'),
            'actuals'
        )
        
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
        assert records[0]['posting_date'] == '2024-01-15'
        assert records[0]['vendor'] == 'Vendor A'
        assert records[0]['project_nr'] == 'P0001'
        assert records[0]['amount'] == '1234.56'
        assert records[0]['currency'] == 'EUR'
    
    def test_parse_csv_empty_file(self):
        """Test parsing empty CSV file."""
        csv_content = ""
        
        with pytest.raises(ParseError, match="empty"):
            self.parser.parse_csv(
                csv_content.encode('utf-8'),
                'actuals'
            )
    
    def test_parse_csv_header_only(self):
        """Test parsing CSV with header but no data."""
        csv_content = "fi_doc_no;posting_date;vendor;project_nr;amount;currency"
        
        with pytest.raises(ParseError, match="empty"):
            self.parser.parse_csv(
                csv_content.encode('utf-8'),
                'actuals'
            )
    
    def test_parse_json_actuals(self):
        """Test parsing JSON for actuals."""
        json_content = """[
            {
                "fi_doc_no": "FI-001",
                "posting_date": "2024-01-15",
                "vendor": "Vendor A",
                "project_nr": "P0001",
                "amount": "1234.56",
                "currency": "EUR"
            },
            {
                "fi_doc_no": "FI-002",
                "posting_date": "2024-01-16",
                "vendor": "Vendor B",
                "project_nr": "P0002",
                "amount": "2345.67",
                "currency": "USD"
            }
        ]"""
        
        records = self.parser.parse_json(
            json_content.encode('utf-8'),
            'actuals'
        )
        
        assert len(records) == 2
        assert records[0]['fi_doc_no'] == 'FI-001'
        assert records[0]['posting_date'] == '2024-01-15'
        assert records[0]['vendor'] == 'Vendor A'
    
    def test_parse_json_commitments(self):
        """Test parsing JSON for commitments."""
        json_content = """[
            {
                "po_number": "PO-001",
                "po_date": "2024-01-15",
                "vendor": "Vendor A",
                "project_nr": "P0001",
                "po_net_amount": "10000.00",
                "total_amount": "11900.00",
                "currency": "EUR",
                "po_line_nr": 1
            }
        ]"""
        
        records = self.parser.parse_json(
            json_content.encode('utf-8'),
            'commitments'
        )
        
        assert len(records) == 1
        assert records[0]['po_number'] == 'PO-001'
        assert records[0]['po_line_nr'] == 1
    
    def test_parse_json_invalid_format(self):
        """Test parsing invalid JSON."""
        json_content = "not valid json"
        
        with pytest.raises(ParseError, match="Invalid JSON"):
            self.parser.parse_json(
                json_content.encode('utf-8'),
                'actuals'
            )
    
    def test_parse_json_not_array(self):
        """Test parsing JSON that is not an array."""
        json_content = '{"fi_doc_no": "FI-001"}'
        
        with pytest.raises(ParseError, match="must be an array"):
            self.parser.parse_json(
                json_content.encode('utf-8'),
                'actuals'
            )
    
    def test_parse_json_empty_array(self):
        """Test parsing empty JSON array."""
        json_content = "[]"
        
        with pytest.raises(ParseError, match="empty"):
            self.parser.parse_json(
                json_content.encode('utf-8'),
                'actuals'
            )
    
    def test_parse_convenience_method_csv(self):
        """Test convenience parse method with CSV."""
        csv_content = """fi_doc_no;posting_date;vendor;project_nr;amount;currency
FI-001;2024-01-15;Vendor A;P0001;1234.56;EUR"""
        
        records, file_format = self.parser.parse(
            csv_content.encode('utf-8'),
            'actuals.csv',
            'actuals'
        )
        
        assert file_format == FileFormat.CSV
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
    
    def test_parse_convenience_method_json(self):
        """Test convenience parse method with JSON."""
        json_content = """[{"fi_doc_no": "FI-001", "posting_date": "2024-01-15", "vendor": "Vendor A", "project_nr": "P0001", "amount": "1234.56", "currency": "EUR"}]"""
        
        records, file_format = self.parser.parse(
            json_content.encode('utf-8'),
            'actuals.json',
            'actuals'
        )
        
        assert file_format == FileFormat.JSON
        assert len(records) == 1
        assert records[0]['fi_doc_no'] == 'FI-001'
    
    def test_parse_unsupported_format(self):
        """Test parsing unsupported file format."""
        content = b"some content"
        
        with pytest.raises(ParseError, match="Unsupported file format"):
            self.parser.parse(
                content,
                'actuals.txt',
                'actuals'
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
