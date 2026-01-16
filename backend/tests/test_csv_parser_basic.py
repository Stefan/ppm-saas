"""
Basic unit tests for CSVParser

These tests verify the core functionality of the CSV parser including
CSV parsing, column validation, and row-to-project conversion.
"""

import pytest
from io import BytesIO
from uuid import uuid4

from services.csv_parser import CSVParser, CSVParseError


class TestCSVParser:
    """Test suite for CSVParser"""
    
    @pytest.fixture
    def csv_parser(self):
        """Create a CSVParser instance"""
        return CSVParser()
    
    @pytest.fixture
    def portfolio_id(self):
        """Create a test portfolio ID"""
        return uuid4()
    
    def test_parse_csv_success(self, csv_parser, portfolio_id):
        """Test successful CSV parsing"""
        # Arrange
        csv_content = b"""name,budget,status,description
Project Alpha,10000.50,planning,Test project 1
Project Beta,25000.75,active,Test project 2"""
        
        # Act
        projects = csv_parser.parse_csv(csv_content, portfolio_id)
        
        # Assert
        assert len(projects) == 2
        assert projects[0].name == "Project Alpha"
        assert projects[0].budget == 10000.50
        assert projects[0].status == "planning"
        assert projects[1].name == "Project Beta"
        assert projects[1].budget == 25000.75
    
    def test_parse_csv_with_semicolon_delimiter(self, csv_parser, portfolio_id):
        """Test CSV parsing with semicolon delimiter"""
        # Arrange
        csv_content = b"""name;budget;status;description
Project Alpha;10000.50;planning;Test project 1
Project Beta;25000.75;active;Test project 2"""
        
        # Act
        projects = csv_parser.parse_csv(csv_content, portfolio_id)
        
        # Assert
        assert len(projects) == 2
        assert projects[0].name == "Project Alpha"
        assert projects[1].name == "Project Beta"
    
    def test_parse_csv_with_quoted_fields(self, csv_parser, portfolio_id):
        """Test CSV parsing with quoted fields containing commas"""
        # Arrange
        csv_content = b"""name,budget,status,description
"Project Alpha, Phase 1",10000.50,planning,"Test project, with commas"
Project Beta,25000.75,active,Simple description"""
        
        # Act
        projects = csv_parser.parse_csv(csv_content, portfolio_id)
        
        # Assert
        assert len(projects) == 2
        assert projects[0].name == "Project Alpha, Phase 1"
        assert projects[0].description == "Test project, with commas"
    
    def test_parse_csv_with_dates(self, csv_parser, portfolio_id):
        """Test CSV parsing with date fields"""
        # Arrange
        csv_content = b"""name,budget,status,start_date,end_date
Project Alpha,10000.50,planning,2024-01-15,2024-12-31
Project Beta,25000.75,active,2024-02-01,2024-06-30"""
        
        # Act
        projects = csv_parser.parse_csv(csv_content, portfolio_id)
        
        # Assert
        assert len(projects) == 2
        assert projects[0].start_date is not None
        assert projects[0].end_date is not None
        assert str(projects[0].start_date) == "2024-01-15"
    
    def test_parse_csv_missing_required_columns(self, csv_parser, portfolio_id):
        """Test CSV parsing fails when required columns are missing"""
        # Arrange - missing 'budget' column
        csv_content = b"""name,status,description
Project Alpha,planning,Test project 1"""
        
        # Act & Assert
        with pytest.raises(CSVParseError) as exc_info:
            csv_parser.parse_csv(csv_content, portfolio_id)
        
        assert "Missing required columns" in str(exc_info.value)
        assert "budget" in str(exc_info.value)
    
    def test_parse_csv_empty_file(self, csv_parser, portfolio_id):
        """Test CSV parsing fails with empty file"""
        # Arrange
        csv_content = b""
        
        # Act & Assert
        with pytest.raises(CSVParseError) as exc_info:
            csv_parser.parse_csv(csv_content, portfolio_id)
        
        assert "empty" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()
    
    def test_parse_csv_invalid_date_format(self, csv_parser, portfolio_id):
        """Test CSV parsing fails with invalid date format"""
        # Arrange
        csv_content = b"""name,budget,status,start_date
Project Alpha,10000.50,planning,01/15/2024"""
        
        # Act & Assert
        with pytest.raises(CSVParseError) as exc_info:
            csv_parser.parse_csv(csv_content, portfolio_id)
        
        assert "date" in str(exc_info.value).lower()
    
    def test_parse_csv_case_insensitive_columns(self, csv_parser, portfolio_id):
        """Test CSV parsing handles case-insensitive column names"""
        # Arrange - mixed case column names
        csv_content = b"""Name,Budget,Status,Description
Project Alpha,10000.50,planning,Test project 1"""
        
        # Act
        projects = csv_parser.parse_csv(csv_content, portfolio_id)
        
        # Assert
        assert len(projects) == 1
        assert projects[0].name == "Project Alpha"
    
    def test_parse_csv_with_optional_fields(self, csv_parser, portfolio_id):
        """Test CSV parsing with only required fields"""
        # Arrange - only required fields
        csv_content = b"""name,budget,status
Project Alpha,10000.50,planning
Project Beta,25000.75,active"""
        
        # Act
        projects = csv_parser.parse_csv(csv_content, portfolio_id)
        
        # Assert
        assert len(projects) == 2
        assert projects[0].name == "Project Alpha"
        assert projects[0].description is None
        assert projects[0].start_date is None
    
    def test_parse_csv_with_empty_optional_fields(self, csv_parser, portfolio_id):
        """Test CSV parsing handles empty optional fields"""
        # Arrange
        csv_content = b"""name,budget,status,description,start_date
Project Alpha,10000.50,planning,,
Project Beta,25000.75,active,Test,2024-01-15"""
        
        # Act
        projects = csv_parser.parse_csv(csv_content, portfolio_id)
        
        # Assert
        assert len(projects) == 2
        assert projects[0].description is None
        assert projects[0].start_date is None
        assert projects[1].description == "Test"
        assert projects[1].start_date is not None
    
    def test_get_field_required_missing(self, csv_parser):
        """Test _get_field raises error for missing required field"""
        # Arrange
        row_dict = {"name": "Test", "budget": "10000"}
        
        # Act & Assert
        with pytest.raises(CSVParseError) as exc_info:
            csv_parser._get_field(row_dict, "status", required=True)
        
        assert "Required field" in str(exc_info.value)
        assert "status" in str(exc_info.value)
    
    def test_get_field_optional_missing(self, csv_parser):
        """Test _get_field returns None for missing optional field"""
        # Arrange
        row_dict = {"name": "Test", "budget": "10000"}
        
        # Act
        result = csv_parser._get_field(row_dict, "description", required=False)
        
        # Assert
        assert result is None
    
    def test_parse_date_valid(self, csv_parser):
        """Test _parse_date with valid ISO date"""
        # Act
        result = csv_parser._parse_date("2024-01-15")
        
        # Assert
        assert result is not None
        assert str(result) == "2024-01-15"
    
    def test_parse_date_invalid(self, csv_parser):
        """Test _parse_date with invalid date format"""
        # Act & Assert
        with pytest.raises(CSVParseError) as exc_info:
            csv_parser._parse_date("01/15/2024")
        
        assert "Invalid date format" in str(exc_info.value)
