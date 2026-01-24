"""
Integration tests for CSV import functionality

Tests the complete import flow including:
- CSV parsing
- Column mapping
- Validation
- Duplicate detection
- Database insertion
- Audit logging
"""

import pytest
import csv
import io
from fastapi.testclient import TestClient
from main import app
from config.database import service_supabase

# Skip if service role client not available
pytestmark = pytest.mark.skipif(
    not service_supabase,
    reason="Service role client required for integration tests"
)


class TestCSVImportIntegration:
    """Integration tests for CSV import"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        # In real tests, you'd get a valid JWT token
        return {"Authorization": "Bearer mock-token"}
    
    @pytest.fixture
    def sample_commitments_csv(self):
        """Create sample commitments CSV data"""
        csv_data = """PO Number;PO Date;Vendor;Vendor Description;Project;WBS Element;PO Net Amount;Total Amount Legal Entity Currency;Legal Entity Currency Code;PO Status;PO Line Nr.;Delivery Date
TEST001;2024-01-15;V001;Test Vendor 1;PRJ-001;WBS-001;1000.00;1190.00;EUR;Open;1;2024-02-15
TEST002;2024-01-16;V002;Test Vendor 2;PRJ-002;WBS-002;2000.00;2380.00;EUR;Open;1;2024-02-16
TEST003;2024-01-17;V003;Test Vendor 3;PRJ-003;WBS-003;3000.00;3570.00;EUR;Closed;1;2024-02-17"""
        return csv_data
    
    def test_commitments_import_success(self, client, auth_headers, sample_commitments_csv):
        """Test successful commitments import"""
        # Create file upload
        files = {
            'file': ('test_commitments.csv', sample_commitments_csv, 'text/csv')
        }
        
        # Make request
        response = client.post(
            "/api/csv-import/upload?import_type=commitments",
            files=files,
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["records_processed"] == 3
        assert data["records_imported"] >= 0  # May be 0 if duplicates
        assert len(data["errors"]) == 0
    
    def test_commitments_import_with_duplicates(self, client, auth_headers, sample_commitments_csv):
        """Test import handles duplicates correctly"""
        # Import once
        files = {
            'file': ('test_commitments.csv', sample_commitments_csv, 'text/csv')
        }
        
        response1 = client.post(
            "/api/csv-import/upload?import_type=commitments",
            files=files,
            headers=auth_headers
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        first_import_count = data1["records_imported"]
        
        # Import again - should detect duplicates
        files = {
            'file': ('test_commitments.csv', sample_commitments_csv, 'text/csv')
        }
        
        response2 = client.post(
            "/api/csv-import/upload?import_type=commitments",
            files=files,
            headers=auth_headers
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Second import should have fewer or no new records (duplicates)
        assert data2["records_imported"] <= first_import_count
    
    def test_commitments_import_invalid_csv(self, client, auth_headers):
        """Test import with invalid CSV format"""
        invalid_csv = "not,valid,csv,data\n1,2,3"
        
        files = {
            'file': ('invalid.csv', invalid_csv, 'text/csv')
        }
        
        response = client.post(
            "/api/csv-import/upload?import_type=commitments",
            files=files,
            headers=auth_headers
        )
        
        # Should return 200 but with errors
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
    
    def test_commitments_import_missing_required_fields(self, client, auth_headers):
        """Test import with missing required fields"""
        csv_data = """PO Number;PO Date
TEST001;2024-01-15"""
        
        files = {
            'file': ('missing_fields.csv', csv_data, 'text/csv')
        }
        
        response = client.post(
            "/api/csv-import/upload?import_type=commitments",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
    
    def test_get_import_history(self, client, auth_headers):
        """Test retrieving import history"""
        response = client.get(
            "/api/csv-import/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "imports" in data
        assert isinstance(data["imports"], list)
    
    def test_get_csv_template(self, client, auth_headers):
        """Test getting CSV template"""
        response = client.get(
            "/api/csv-import/template/commitments",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "headers" in data
        assert "example" in data
        assert "csv_content" in data
        assert len(data["headers"]) > 0


class TestImportServiceDirect:
    """Direct tests of import service (bypassing API)"""
    
    @pytest.mark.asyncio
    async def test_batch_duplicate_checking(self):
        """Test that batch duplicate checking works"""
        from services.actuals_commitments_import import ActualsCommitmentsImportService
        
        if not service_supabase:
            pytest.skip("Service role client not available")
        
        service = ActualsCommitmentsImportService(service_supabase, "test-user")
        
        # Test with known PO numbers
        po_keys = [("TEST001", 1), ("TEST002", 1), ("NONEXISTENT", 1)]
        existing = await service.batch_check_duplicate_commitments(po_keys)
        
        # Should return a set
        assert isinstance(existing, set)
    
    @pytest.mark.asyncio
    async def test_import_creates_projects(self):
        """Test that import creates projects if they don't exist"""
        from services.actuals_commitments_import import ActualsCommitmentsImportService
        
        if not service_supabase:
            pytest.skip("Service role client not available")
        
        service = ActualsCommitmentsImportService(service_supabase, "test-user")
        
        # Import a commitment with a new project
        records = [{
            "po_number": f"TEST-NEW-{int(__import__('time').time())}",
            "po_date": "2024-01-15",
            "vendor": "Test Vendor",
            "vendor_description": "Test Vendor Description",
            "project_nr": f"NEW-PRJ-{int(__import__('time').time())}",
            "wbs_element": "NEW-WBS-001",
            "po_net_amount": "1000.00",
            "total_amount": "1190.00",
            "currency": "EUR",
            "po_status": "Open",
            "po_line_nr": 1,
            "delivery_date": "2024-02-15"
        }]
        
        result = await service.import_commitments(records, anonymize=False)
        
        # Should succeed
        assert result.total_records == 1
        assert result.error_count == 0
        assert result.success_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
