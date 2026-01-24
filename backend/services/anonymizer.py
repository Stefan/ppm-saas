"""
Anonymizer Service for Import Actuals and Commitments

This service anonymizes sensitive information in financial data imports,
replacing vendor names, project numbers, personnel numbers, and descriptive
text with generic placeholders while maintaining referential integrity.
"""

from typing import Dict, Any


class AnonymizerService:
    """
    Service for anonymizing sensitive data in actuals and commitments imports.
    
    Maintains consistent mapping within an import session:
    - Same vendor always maps to same anonymized vendor
    - Same project number always maps to same anonymized project number
    - Same personnel number always maps to same anonymized personnel number
    
    Preserves non-sensitive fields:
    - Dates (posting_date, document_date, po_date, delivery_date)
    - Amounts (amount, po_net_amount, total_amount)
    - Currency codes
    - Status fields
    - Document types
    """
    
    def __init__(self):
        """Initialize anonymizer with empty mapping dictionaries."""
        self.vendor_map: Dict[str, str] = {}
        self.project_map: Dict[str, str] = {}
        self.personnel_map: Dict[str, str] = {}
        self.vendor_counter = 0
        self.project_counter = 0
        self.personnel_counter = 0
        
        # Generic descriptions for anonymization
        self.generic_descriptions = {
            'project': [
                'Infrastructure Development Project',
                'Software Implementation Initiative',
                'Business Process Optimization',
                'Technology Upgrade Program',
                'Quality Improvement Project',
                'Facility Modernization',
                'Digital Transformation Initiative',
                'Operational Excellence Program',
                'Strategic Planning Project',
                'Innovation Development Program'
            ],
            'wbs': [
                'Planning and Design Phase',
                'Implementation Phase',
                'Testing and Validation',
                'Deployment and Rollout',
                'Training and Documentation',
                'Maintenance and Support',
                'Quality Assurance',
                'Project Management',
                'Technical Infrastructure',
                'User Acceptance Testing'
            ],
            'cost_center': [
                'Operations Department',
                'IT Services',
                'Finance and Administration',
                'Human Resources',
                'Facilities Management',
                'Quality Assurance',
                'Research and Development',
                'Customer Service',
                'Supply Chain Management',
                'Business Development'
            ],
            'po_line': [
                'Professional Services',
                'Software Licenses',
                'Hardware Equipment',
                'Consulting Services',
                'Maintenance Contract',
                'Training Services',
                'Technical Support',
                'Cloud Services',
                'Network Equipment',
                'Office Supplies'
            ],
            'po_title': [
                'Annual Service Agreement',
                'Software License Renewal',
                'Equipment Procurement',
                'Consulting Engagement',
                'Maintenance Services',
                'Professional Services Contract',
                'Technology Infrastructure',
                'Support Services Agreement',
                'Implementation Services',
                'Training and Development'
            ]
        }
        self.description_counters = {key: 0 for key in self.generic_descriptions.keys()}
    
    def anonymize_vendor(self, vendor: str) -> str:
        """
        Replace vendor name with generic identifier.
        
        Uses letter-based naming: Vendor A, Vendor B, Vendor C, etc.
        Maintains consistent mapping within import session.
        
        Args:
            vendor: Original vendor name
            
        Returns:
            Anonymized vendor name (e.g., "Vendor A", "Vendor B")
            
        Example:
            >>> anonymizer = AnonymizerService()
            >>> anonymizer.anonymize_vendor("ACME Corp")
            "Vendor A"
            >>> anonymizer.anonymize_vendor("ACME Corp")
            "Vendor A"
            >>> anonymizer.anonymize_vendor("XYZ Ltd")
            "Vendor B"
        """
        if not vendor:
            return vendor
            
        if vendor not in self.vendor_map:
            self.vendor_counter += 1
            # Convert counter to letter (1=A, 2=B, etc.)
            self.vendor_map[vendor] = f"Vendor {chr(64 + self.vendor_counter)}"
        
        return self.vendor_map[vendor]
    
    def anonymize_project_nr(self, project_nr: str) -> str:
        """
        Replace project number with fictitious format.
        
        Uses format P0001, P0002, P0003, etc.
        Maintains consistent mapping within import session.
        
        Args:
            project_nr: Original project number
            
        Returns:
            Anonymized project number (e.g., "P0001", "P0002")
            
        Example:
            >>> anonymizer = AnonymizerService()
            >>> anonymizer.anonymize_project_nr("PRJ-2024-001")
            "P0001"
            >>> anonymizer.anonymize_project_nr("PRJ-2024-001")
            "P0001"
            >>> anonymizer.anonymize_project_nr("PRJ-2024-002")
            "P0002"
        """
        if not project_nr:
            return project_nr
            
        if project_nr not in self.project_map:
            self.project_counter += 1
            self.project_map[project_nr] = f"P{self.project_counter:04d}"
        
        return self.project_map[project_nr]
    
    def anonymize_personnel(self, personnel_nr: str) -> str:
        """
        Replace personnel number with anonymized identifier.
        
        Uses format EMP001, EMP002, EMP003, etc.
        Maintains consistent mapping within import session.
        
        Args:
            personnel_nr: Original personnel number
            
        Returns:
            Anonymized personnel number (e.g., "EMP001", "EMP002")
            
        Example:
            >>> anonymizer = AnonymizerService()
            >>> anonymizer.anonymize_personnel("12345")
            "EMP001"
            >>> anonymizer.anonymize_personnel("12345")
            "EMP001"
            >>> anonymizer.anonymize_personnel("67890")
            "EMP002"
        """
        if not personnel_nr:
            return personnel_nr
            
        if personnel_nr not in self.personnel_map:
            self.personnel_counter += 1
            self.personnel_map[personnel_nr] = f"EMP{self.personnel_counter:03d}"
        
        return self.personnel_map[personnel_nr]
    
    def anonymize_text(self, text: str) -> str:
        """
        Replace descriptive text with generic placeholder.
        
        Args:
            text: Original descriptive text
            
        Returns:
            Generic placeholder text "Item Description"
            
        Example:
            >>> anonymizer = AnonymizerService()
            >>> anonymizer.anonymize_text("Consulting services for Q1")
            "Item Description"
        """
        if not text:
            return text
        
        return "Item Description"
    
    def get_generic_description(self, category: str, original: str = None) -> str:
        """
        Get a generic description from predefined list.
        
        Cycles through available descriptions to provide variety while
        maintaining anonymization.
        
        Args:
            category: Category of description (project, wbs, cost_center, etc.)
            original: Original text (not used, for future enhancement)
            
        Returns:
            Generic description from the category
        """
        if category not in self.generic_descriptions:
            return "Generic Description"
        
        descriptions = self.generic_descriptions[category]
        counter = self.description_counters[category]
        
        # Cycle through descriptions
        description = descriptions[counter % len(descriptions)]
        self.description_counters[category] += 1
        
        return description
    
    def anonymize_actual(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize a single actual record.
        
        Anonymizes:
        - vendor: Replaced with "Vendor A", "Vendor B", etc. (if present)
        - vendor_description: Replaced with "Vendor Description" (if present)
        - project_nr: Replaced with "P0001", "P0002", etc.
        - item_text: Replaced with "Item Description" (if present)
        
        Preserves:
        - fi_doc_no: Financial document number (unique identifier)
        - posting_date: Date of posting
        - document_date: Date of document
        - wbs_element: Work breakdown structure element
        - amount: Transaction amount
        - currency: Currency code
        - document_type: Type of document
        
        Args:
            record: Dictionary containing actual record fields
            
        Returns:
            Dictionary with anonymized fields
        """
        anonymized = record.copy()
        
        # Anonymize vendor name (if present and not empty)
        if "vendor" in anonymized and anonymized["vendor"]:
            anonymized["vendor"] = self.anonymize_vendor(anonymized["vendor"])
        
        # Anonymize vendor description (if present and not empty)
        if "vendor_description" in anonymized and anonymized["vendor_description"]:
            anonymized["vendor_description"] = "Vendor Description"
        
        # Anonymize project number
        if "project_nr" in anonymized and anonymized["project_nr"]:
            anonymized["project_nr"] = self.anonymize_project_nr(anonymized["project_nr"])
        
        # Anonymize item text (if present and not empty)
        if "item_text" in anonymized and anonymized["item_text"]:
            anonymized["item_text"] = self.anonymize_text(anonymized["item_text"])
        
        return anonymized
    
    def anonymize_commitment(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize a single commitment record.
        
        Anonymizes:
        - vendor: Replaced with "Vendor A", "Vendor B", etc.
        - vendor_description: Replaced with "Vendor Description"
        - project_nr: Replaced with "P0001", "P0002", etc.
        - project_description: Replaced with generic project description
        - wbs_description: Replaced with generic WBS description
        - cost_center_description: Replaced with generic cost center description
        - po_line_text: Replaced with generic item description
        - po_title: Replaced with generic PO title
        - requester: Replaced with anonymized personnel number
        - po_created_by: Replaced with anonymized personnel number
        
        Preserves:
        - po_number: Purchase order number (unique identifier)
        - po_date: Date of purchase order
        - wbs_element: Work breakdown structure element
        - cost_center: Cost center code
        - po_net_amount: Net amount of purchase order
        - total_amount: Total amount including taxes
        - currency: Currency code
        - po_status: Status of purchase order
        - po_line_nr: Line number within purchase order
        - delivery_date: Expected delivery date
        - All other technical/financial fields
        
        Args:
            record: Dictionary containing commitment record fields
            
        Returns:
            Dictionary with anonymized fields
        """
        anonymized = record.copy()
        
        # Anonymize vendor name
        if "vendor" in anonymized and anonymized["vendor"]:
            anonymized["vendor"] = self.anonymize_vendor(anonymized["vendor"])
        
        # Anonymize vendor description
        if "vendor_description" in anonymized and anonymized["vendor_description"]:
            anonymized["vendor_description"] = "Vendor Description"
        
        # Anonymize project number
        if "project_nr" in anonymized and anonymized["project_nr"]:
            anonymized["project_nr"] = self.anonymize_project_nr(anonymized["project_nr"])
        
        # Anonymize project description
        if "project_description" in anonymized and anonymized["project_description"]:
            anonymized["project_description"] = self.get_generic_description('project', anonymized["project_description"])
        
        # Anonymize WBS description
        if "wbs_description" in anonymized and anonymized["wbs_description"]:
            anonymized["wbs_description"] = self.get_generic_description('wbs', anonymized["wbs_description"])
        
        # Anonymize cost center description
        if "cost_center_description" in anonymized and anonymized["cost_center_description"]:
            anonymized["cost_center_description"] = self.get_generic_description('cost_center', anonymized["cost_center_description"])
        
        # Anonymize PO line text
        if "po_line_text" in anonymized and anonymized["po_line_text"]:
            anonymized["po_line_text"] = self.get_generic_description('po_line', anonymized["po_line_text"])
        
        # Anonymize PO title
        if "po_title" in anonymized and anonymized["po_title"]:
            anonymized["po_title"] = self.get_generic_description('po_title', anonymized["po_title"])
        
        # Anonymize requester
        if "requester" in anonymized and anonymized["requester"]:
            anonymized["requester"] = self.anonymize_personnel(anonymized["requester"])
        
        # Anonymize PO created by
        if "po_created_by" in anonymized and anonymized["po_created_by"]:
            anonymized["po_created_by"] = self.anonymize_personnel(anonymized["po_created_by"])
        
        return anonymized
