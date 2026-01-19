"""
Content Indexing Service for RAG System
Automatically indexes content (projects, portfolios, resources, etc.) for vector search
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import Client
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from ai_agents import RAGReporterAgent

logger = logging.getLogger(__name__)

class ContentIndexingService:
    """Service for indexing content into the RAG embeddings system"""
    
    def __init__(self, supabase_client: Client, rag_agent: RAGReporterAgent):
        self.supabase = supabase_client
        self.rag_agent = rag_agent
        self.batch_size = 10  # Process in batches to avoid rate limits
        
    async def index_all_content(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Index all content types for an organization or globally"""
        
        logger.info(f"Starting full content indexing for organization: {organization_id or 'all'}")
        
        results = {
            "projects": await self.index_projects(organization_id),
            "portfolios": await self.index_portfolios(organization_id),
            "resources": await self.index_resources(organization_id),
            "risks": await self.index_risks(organization_id),
            "issues": await self.index_issues(organization_id)
        }
        
        total_indexed = sum(r["indexed_count"] for r in results.values())
        total_errors = sum(len(r["errors"]) for r in results.values())
        
        logger.info(f"Content indexing complete: {total_indexed} items indexed, {total_errors} errors")
        
        return {
            "total_indexed": total_indexed,
            "total_errors": total_errors,
            "details": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def index_projects(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Index all projects"""
        
        logger.info("Indexing projects...")
        indexed_count = 0
        errors = []
        
        try:
            # Query projects
            query = self.supabase.table("projects").select("*")
            if organization_id:
                query = query.eq("organization_id", organization_id)
            
            response = query.execute()
            projects = response.data or []
            
            logger.info(f"Found {len(projects)} projects to index")
            
            # Process in batches
            for i in range(0, len(projects), self.batch_size):
                batch = projects[i:i + self.batch_size]
                
                for project in batch:
                    try:
                        # Generate content text
                        content_text = self._generate_project_content_text(project)
                        
                        # Generate metadata
                        metadata = {
                            "name": project.get("name"),
                            "status": project.get("status"),
                            "priority": project.get("priority"),
                            "budget": project.get("budget"),
                            "start_date": project.get("start_date"),
                            "end_date": project.get("end_date")
                        }
                        
                        # Store embedding
                        await self.rag_agent.store_content_embedding(
                            content_type="project",
                            content_id=project["id"],
                            content_text=content_text,
                            metadata=metadata
                        )
                        
                        # Update with organization_id if available
                        if organization_id or project.get("organization_id"):
                            org_id = organization_id or project.get("organization_id")
                            self.supabase.table("embeddings").update({
                                "organization_id": org_id
                            }).eq("content_type", "project").eq("content_id", project["id"]).execute()
                        
                        indexed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Project {project.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                # Small delay between batches to avoid rate limits
                if i + self.batch_size < len(projects):
                    await asyncio.sleep(1)
            
            logger.info(f"Indexed {indexed_count} projects with {len(errors)} errors")
            
        except Exception as e:
            error_msg = f"Failed to index projects: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return {
            "content_type": "project",
            "indexed_count": indexed_count,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    async def index_portfolios(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Index all portfolios"""
        
        logger.info("Indexing portfolios...")
        indexed_count = 0
        errors = []
        
        try:
            query = self.supabase.table("portfolios").select("*")
            if organization_id:
                query = query.eq("organization_id", organization_id)
            
            response = query.execute()
            portfolios = response.data or []
            
            logger.info(f"Found {len(portfolios)} portfolios to index")
            
            for i in range(0, len(portfolios), self.batch_size):
                batch = portfolios[i:i + self.batch_size]
                
                for portfolio in batch:
                    try:
                        content_text = self._generate_portfolio_content_text(portfolio)
                        
                        metadata = {
                            "name": portfolio.get("name"),
                            "owner_id": portfolio.get("owner_id"),
                            "description": portfolio.get("description", "")[:200]
                        }
                        
                        await self.rag_agent.store_content_embedding(
                            content_type="portfolio",
                            content_id=portfolio["id"],
                            content_text=content_text,
                            metadata=metadata
                        )
                        
                        if organization_id or portfolio.get("organization_id"):
                            org_id = organization_id or portfolio.get("organization_id")
                            self.supabase.table("embeddings").update({
                                "organization_id": org_id
                            }).eq("content_type", "portfolio").eq("content_id", portfolio["id"]).execute()
                        
                        indexed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Portfolio {portfolio.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                if i + self.batch_size < len(portfolios):
                    await asyncio.sleep(1)
            
            logger.info(f"Indexed {indexed_count} portfolios with {len(errors)} errors")
            
        except Exception as e:
            error_msg = f"Failed to index portfolios: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return {
            "content_type": "portfolio",
            "indexed_count": indexed_count,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    async def index_resources(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Index all resources"""
        
        logger.info("Indexing resources...")
        indexed_count = 0
        errors = []
        
        try:
            query = self.supabase.table("resources").select("*")
            if organization_id:
                query = query.eq("organization_id", organization_id)
            
            response = query.execute()
            resources = response.data or []
            
            logger.info(f"Found {len(resources)} resources to index")
            
            for i in range(0, len(resources), self.batch_size):
                batch = resources[i:i + self.batch_size]
                
                for resource in batch:
                    try:
                        content_text = self._generate_resource_content_text(resource)
                        
                        metadata = {
                            "name": resource.get("name"),
                            "role": resource.get("role"),
                            "skills": resource.get("skills", []),
                            "location": resource.get("location"),
                            "availability": resource.get("availability")
                        }
                        
                        await self.rag_agent.store_content_embedding(
                            content_type="resource",
                            content_id=resource["id"],
                            content_text=content_text,
                            metadata=metadata
                        )
                        
                        if organization_id or resource.get("organization_id"):
                            org_id = organization_id or resource.get("organization_id")
                            self.supabase.table("embeddings").update({
                                "organization_id": org_id
                            }).eq("content_type", "resource").eq("content_id", resource["id"]).execute()
                        
                        indexed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Resource {resource.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                if i + self.batch_size < len(resources):
                    await asyncio.sleep(1)
            
            logger.info(f"Indexed {indexed_count} resources with {len(errors)} errors")
            
        except Exception as e:
            error_msg = f"Failed to index resources: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return {
            "content_type": "resource",
            "indexed_count": indexed_count,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    async def index_risks(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Index all risks"""
        
        logger.info("Indexing risks...")
        indexed_count = 0
        errors = []
        
        try:
            query = self.supabase.table("risks").select("*")
            if organization_id:
                query = query.eq("organization_id", organization_id)
            
            response = query.execute()
            risks = response.data or []
            
            logger.info(f"Found {len(risks)} risks to index")
            
            for i in range(0, len(risks), self.batch_size):
                batch = risks[i:i + self.batch_size]
                
                for risk in batch:
                    try:
                        content_text = self._generate_risk_content_text(risk)
                        
                        metadata = {
                            "title": risk.get("title"),
                            "category": risk.get("category"),
                            "probability": risk.get("probability"),
                            "impact": risk.get("impact"),
                            "status": risk.get("status")
                        }
                        
                        await self.rag_agent.store_content_embedding(
                            content_type="risk",
                            content_id=risk["id"],
                            content_text=content_text,
                            metadata=metadata
                        )
                        
                        if organization_id or risk.get("organization_id"):
                            org_id = organization_id or risk.get("organization_id")
                            self.supabase.table("embeddings").update({
                                "organization_id": org_id
                            }).eq("content_type", "risk").eq("content_id", risk["id"]).execute()
                        
                        indexed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Risk {risk.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                if i + self.batch_size < len(risks):
                    await asyncio.sleep(1)
            
            logger.info(f"Indexed {indexed_count} risks with {len(errors)} errors")
            
        except Exception as e:
            error_msg = f"Failed to index risks: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return {
            "content_type": "risk",
            "indexed_count": indexed_count,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    async def index_issues(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Index all issues"""
        
        logger.info("Indexing issues...")
        indexed_count = 0
        errors = []
        
        try:
            query = self.supabase.table("issues").select("*")
            if organization_id:
                query = query.eq("organization_id", organization_id)
            
            response = query.execute()
            issues = response.data or []
            
            logger.info(f"Found {len(issues)} issues to index")
            
            for i in range(0, len(issues), self.batch_size):
                batch = issues[i:i + self.batch_size]
                
                for issue in batch:
                    try:
                        content_text = self._generate_issue_content_text(issue)
                        
                        metadata = {
                            "title": issue.get("title"),
                            "severity": issue.get("severity"),
                            "status": issue.get("status"),
                            "assigned_to": issue.get("assigned_to")
                        }
                        
                        await self.rag_agent.store_content_embedding(
                            content_type="issue",
                            content_id=issue["id"],
                            content_text=content_text,
                            metadata=metadata
                        )
                        
                        if organization_id or issue.get("organization_id"):
                            org_id = organization_id or issue.get("organization_id")
                            self.supabase.table("embeddings").update({
                                "organization_id": org_id
                            }).eq("content_type", "issue").eq("content_id", issue["id"]).execute()
                        
                        indexed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Issue {issue.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                if i + self.batch_size < len(issues):
                    await asyncio.sleep(1)
            
            logger.info(f"Indexed {indexed_count} issues with {len(errors)} errors")
            
        except Exception as e:
            error_msg = f"Failed to index issues: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return {
            "content_type": "issue",
            "indexed_count": indexed_count,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    async def index_single_content(self, content_type: str, content_id: str, 
                                   content_data: Dict[str, Any]) -> bool:
        """Index a single piece of content (for real-time updates)"""
        
        try:
            # Generate content text based on type
            if content_type == "project":
                content_text = self._generate_project_content_text(content_data)
            elif content_type == "portfolio":
                content_text = self._generate_portfolio_content_text(content_data)
            elif content_type == "resource":
                content_text = self._generate_resource_content_text(content_data)
            elif content_type == "risk":
                content_text = self._generate_risk_content_text(content_data)
            elif content_type == "issue":
                content_text = self._generate_issue_content_text(content_data)
            else:
                logger.warning(f"Unknown content type: {content_type}")
                return False
            
            # Store embedding
            await self.rag_agent.update_content_embedding(
                content_type=content_type,
                content_id=content_id,
                updated_content=content_data
            )
            
            # Update organization_id if available
            if content_data.get("organization_id"):
                self.supabase.table("embeddings").update({
                    "organization_id": content_data["organization_id"]
                }).eq("content_type", content_type).eq("content_id", content_id).execute()
            
            logger.info(f"Indexed {content_type}:{content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index {content_type}:{content_id}: {str(e)}")
            return False
    
    async def delete_content_embedding(self, content_type: str, content_id: str) -> bool:
        """Delete embedding for deleted content"""
        
        try:
            result = self.supabase.rpc('delete_content_embedding', {
                'p_content_type': content_type,
                'p_content_id': content_id
            }).execute()
            
            logger.info(f"Deleted embedding for {content_type}:{content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embedding for {content_type}:{content_id}: {str(e)}")
            return False
    
    # Content text generation methods
    
    def _generate_project_content_text(self, project: Dict[str, Any]) -> str:
        """Generate searchable text for a project"""
        parts = [
            f"Project: {project.get('name', 'Unnamed')}",
            f"Description: {project.get('description', 'No description')}",
            f"Status: {project.get('status', 'Unknown')}",
            f"Priority: {project.get('priority', 'Normal')}",
        ]
        
        if project.get('budget'):
            parts.append(f"Budget: ${project['budget']}")
        
        if project.get('start_date'):
            parts.append(f"Start Date: {project['start_date']}")
        
        if project.get('end_date'):
            parts.append(f"End Date: {project['end_date']}")
        
        if project.get('owner_name'):
            parts.append(f"Owner: {project['owner_name']}")
        
        return ". ".join(parts) + "."
    
    def _generate_portfolio_content_text(self, portfolio: Dict[str, Any]) -> str:
        """Generate searchable text for a portfolio"""
        parts = [
            f"Portfolio: {portfolio.get('name', 'Unnamed')}",
            f"Description: {portfolio.get('description', 'No description')}",
        ]
        
        if portfolio.get('owner_name'):
            parts.append(f"Owner: {portfolio['owner_name']}")
        
        return ". ".join(parts) + "."
    
    def _generate_resource_content_text(self, resource: Dict[str, Any]) -> str:
        """Generate searchable text for a resource"""
        parts = [
            f"Resource: {resource.get('name', 'Unnamed')}",
            f"Role: {resource.get('role', 'Unknown')}",
        ]
        
        if resource.get('skills'):
            skills_text = ", ".join(resource['skills']) if isinstance(resource['skills'], list) else resource['skills']
            parts.append(f"Skills: {skills_text}")
        
        if resource.get('location'):
            parts.append(f"Location: {resource['location']}")
        
        if resource.get('availability'):
            parts.append(f"Availability: {resource['availability']}")
        
        return ". ".join(parts) + "."
    
    def _generate_risk_content_text(self, risk: Dict[str, Any]) -> str:
        """Generate searchable text for a risk"""
        parts = [
            f"Risk: {risk.get('title', 'Unnamed')}",
            f"Description: {risk.get('description', 'No description')}",
            f"Category: {risk.get('category', 'Unknown')}",
        ]
        
        if risk.get('probability'):
            parts.append(f"Probability: {risk['probability']}")
        
        if risk.get('impact'):
            parts.append(f"Impact: {risk['impact']}")
        
        if risk.get('mitigation'):
            parts.append(f"Mitigation: {risk['mitigation']}")
        
        if risk.get('status'):
            parts.append(f"Status: {risk['status']}")
        
        return ". ".join(parts) + "."
    
    def _generate_issue_content_text(self, issue: Dict[str, Any]) -> str:
        """Generate searchable text for an issue"""
        parts = [
            f"Issue: {issue.get('title', 'Unnamed')}",
            f"Description: {issue.get('description', 'No description')}",
            f"Severity: {issue.get('severity', 'Unknown')}",
        ]
        
        if issue.get('status'):
            parts.append(f"Status: {issue['status']}")
        
        if issue.get('resolution'):
            parts.append(f"Resolution: {issue['resolution']}")
        
        if issue.get('assigned_to_name'):
            parts.append(f"Assigned to: {issue['assigned_to_name']}")
        
        return ". ".join(parts) + "."


# Standalone function for background job
async def run_content_indexing(organization_id: Optional[str] = None):
    """Run content indexing as a background job"""
    
    from config.database import supabase
    
    # Initialize RAG agent
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY not set, cannot run content indexing")
        return
    
    rag_agent = RAGReporterAgent(
        supabase_client=supabase,
        openai_api_key=openai_api_key,
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    
    # Initialize indexing service
    indexing_service = ContentIndexingService(supabase, rag_agent)
    
    # Run indexing
    result = await indexing_service.index_all_content(organization_id)
    
    logger.info(f"Content indexing complete: {result}")
    return result


if __name__ == "__main__":
    # Run indexing when executed directly
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("Starting content indexing...")
    result = asyncio.run(run_content_indexing())
    print(f"Indexing complete: {result}")
