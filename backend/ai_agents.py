"""
AI Agents Implementation for PPM Platform
Implements the four core AI agents: RAG Reporter, Resource Optimizer, Risk Forecaster, and Hallucination Validator
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from openai import OpenAI
from supabase import Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAgentBase:
    """Base class for all AI agents with common functionality"""
    
    def __init__(self, supabase_client: Client, openai_api_key: str):
        self.supabase = supabase_client
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.agent_type = self.__class__.__name__.lower()
    
    async def log_metrics(self, operation: str, user_id: str, input_tokens: int = 0, 
                         output_tokens: int = 0, response_time_ms: int = 0, 
                         success: bool = True, error_message: str = None, 
                         confidence_score: float = None):
        """Log agent performance metrics"""
        try:
            self.supabase.table("ai_agent_metrics").insert({
                "agent_type": self.agent_type,
                "operation": operation,
                "user_id": user_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "response_time_ms": response_time_ms,
                "success": success,
                "error_message": error_message,
                "confidence_score": confidence_score
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

class RAGReporterAgent(AIAgentBase):
    """Natural Language Reporting Agent using RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self, supabase_client: Client, openai_api_key: str):
        super().__init__(supabase_client, openai_api_key)
        self.embedding_model = "text-embedding-ada-002"
        self.chat_model = "gpt-4"
        self.max_context_length = 8000
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def store_content_embedding(self, content_type: str, content_id: str, 
                                    content_text: str, metadata: Dict = None):
        """Store content embedding in vector database"""
        try:
            embedding = await self.generate_embedding(content_text)
            
            self.supabase.table("embeddings").upsert({
                "content_type": content_type,
                "content_id": content_id,
                "content_text": content_text,
                "embedding": embedding,
                "metadata": metadata or {}
            }, on_conflict="content_type,content_id").execute()
            
            logger.info(f"Stored embedding for {content_type}:{content_id}")
        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            raise
    
    async def search_similar_content(self, query: str, content_types: List[str] = None, 
                                   limit: int = 5) -> List[Dict]:
        """Search for similar content using vector similarity"""
        try:
            query_embedding = await self.generate_embedding(query)
            
            # Build the query
            query_builder = self.supabase.table("embeddings").select(
                "content_type, content_id, content_text, metadata"
            )
            
            if content_types:
                query_builder = query_builder.in_("content_type", content_types)
            
            # Note: This is a simplified version. In production, you'd use pgvector
            # for proper vector similarity search
            response = query_builder.limit(limit * 3).execute()  # Get more to filter
            
            if not response.data:
                return []
            
            # Calculate similarity scores (simplified cosine similarity)
            results = []
            for item in response.data:
                if item.get('embedding'):
                    # This would be done in the database with pgvector in production
                    similarity = self._calculate_similarity(query_embedding, item['embedding'])
                    results.append({
                        **item,
                        'similarity_score': similarity
                    })
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Content search failed: {e}")
            return []
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0
    
    async def get_context_data(self, user_id: str) -> Dict[str, Any]:
        """Gather contextual data for RAG queries"""
        try:
            context = {}
            
            # Get user's projects
            projects_response = self.supabase.table("projects").select("*").execute()
            context['projects'] = projects_response.data or []
            
            # Get portfolios
            portfolios_response = self.supabase.table("portfolios").select("*").execute()
            context['portfolios'] = portfolios_response.data or []
            
            # Get resources
            resources_response = self.supabase.table("resources").select("*").execute()
            context['resources'] = resources_response.data or []
            
            # Get recent metrics
            context['summary'] = {
                'total_projects': len(context['projects']),
                'total_portfolios': len(context['portfolios']),
                'total_resources': len(context['resources']),
                'timestamp': datetime.now().isoformat()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context data: {e}")
            return {}
    
    async def process_rag_query(self, query: str, user_id: str, 
                              conversation_id: str = None) -> Dict[str, Any]:
        """Process a natural language query using RAG"""
        start_time = datetime.now()
        
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"conv_{int(datetime.now().timestamp())}"
            
            # Search for relevant content
            similar_content = await self.search_similar_content(
                query, 
                content_types=['project', 'portfolio', 'resource'],
                limit=5
            )
            
            # Get additional context
            context_data = await self.get_context_data(user_id)
            
            # Build the prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(query, similar_content, context_data)
            
            # Call OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # Calculate metrics
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            # Extract sources and confidence
            sources = [
                {
                    "type": item["content_type"],
                    "id": item["content_id"],
                    "similarity": item["similarity_score"]
                }
                for item in similar_content
            ]
            
            confidence_score = self._calculate_confidence(similar_content, ai_response)
            
            # Store conversation
            await self._store_conversation(
                user_id, conversation_id, query, ai_response, 
                sources, confidence_score
            )
            
            # Log metrics
            await self.log_metrics(
                "rag_query", user_id, input_tokens, output_tokens,
                response_time, True, None, confidence_score
            )
            
            return {
                "response": ai_response,
                "sources": sources,
                "confidence_score": confidence_score,
                "conversation_id": conversation_id,
                "response_time_ms": response_time
            }
            
        except Exception as e:
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.log_metrics(
                "rag_query", user_id, 0, 0, response_time, False, str(e)
            )
            logger.error(f"RAG query failed: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for RAG queries"""
        return """You are an AI assistant for a Project Portfolio Management (PPM) platform. 
        You help users analyze their projects, portfolios, and resources by providing insights based on their data.
        
        Guidelines:
        - Provide accurate, data-driven responses based on the provided context
        - Include specific numbers and metrics when available
        - Suggest actionable insights and recommendations
        - If data is insufficient, clearly state limitations
        - Format responses clearly with bullet points or sections when appropriate
        - Focus on project management, resource allocation, and portfolio optimization
        
        Always base your responses on the provided context data and similar content."""
    
    def _build_user_prompt(self, query: str, similar_content: List[Dict], 
                          context_data: Dict) -> str:
        """Build the user prompt with context"""
        prompt = f"User Query: {query}\n\n"
        
        # Add similar content
        if similar_content:
            prompt += "Relevant Content:\n"
            for i, content in enumerate(similar_content[:3], 1):
                prompt += f"{i}. {content['content_type']}: {content['content_text'][:200]}...\n"
            prompt += "\n"
        
        # Add context summary
        if context_data.get('summary'):
            summary = context_data['summary']
            prompt += f"Current Portfolio Summary:\n"
            prompt += f"- Total Projects: {summary['total_projects']}\n"
            prompt += f"- Total Portfolios: {summary['total_portfolios']}\n"
            prompt += f"- Total Resources: {summary['total_resources']}\n\n"
        
        prompt += "Please provide a comprehensive response based on this data."
        
        return prompt
    
    def _calculate_confidence(self, similar_content: List[Dict], response: str) -> float:
        """Calculate confidence score for the response"""
        if not similar_content:
            return 0.3  # Low confidence without relevant content
        
        # Base confidence on similarity scores
        avg_similarity = sum(item['similarity_score'] for item in similar_content) / len(similar_content)
        
        # Adjust based on response length and content
        response_length_factor = min(len(response) / 500, 1.0)  # Normalize to 0-1
        
        confidence = (avg_similarity * 0.7) + (response_length_factor * 0.3)
        return min(max(confidence, 0.0), 1.0)
    
    async def _store_conversation(self, user_id: str, conversation_id: str, 
                                query: str, response: str, sources: List[Dict], 
                                confidence_score: float):
        """Store conversation in database"""
        try:
            self.supabase.table("rag_contexts").insert({
                "user_id": user_id,
                "conversation_id": conversation_id,
                "query": query,
                "response": response,
                "sources": sources,
                "confidence_score": confidence_score
            }).execute()
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")

class ResourceOptimizerAgent(AIAgentBase):
    """AI agent for optimizing resource allocation and utilization"""
    
    def __init__(self, supabase_client: Client, openai_api_key: str):
        super().__init__(supabase_client, openai_api_key)
    
    async def analyze_resource_allocation(self, user_id: str, project_id: str = None) -> Dict[str, Any]:
        """Analyze current resource allocation and suggest optimizations"""
        start_time = datetime.now()
        
        try:
            # Get resources with skills
            resources_data = await self._get_resources_with_skills()
            
            # Get project requirements
            requirements_data = await self._get_project_requirements(project_id)
            
            # Get availability data
            availability_data = await self._get_resource_availability()
            
            # Perform optimization analysis
            optimization_results = await self._optimize_allocation(
                resources_data, requirements_data, availability_data
            )
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log metrics
            await self.log_metrics(
                "resource_optimization", user_id, 0, 0, response_time, True
            )
            
            return optimization_results
            
        except Exception as e:
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.log_metrics(
                "resource_optimization", user_id, 0, 0, response_time, False, str(e)
            )
            logger.error(f"Resource optimization failed: {e}")
            raise
    
    async def _get_resources_with_skills(self) -> List[Dict]:
        """Get all resources with their skills"""
        try:
            # Get resources
            resources_response = self.supabase.table("resources").select("*").execute()
            resources = resources_response.data or []
            
            # Get skills for each resource
            for resource in resources:
                skills_response = self.supabase.table("resource_skills").select("*").eq(
                    "resource_id", resource["id"]
                ).execute()
                resource["skills"] = skills_response.data or []
            
            return resources
        except Exception as e:
            logger.error(f"Failed to get resources with skills: {e}")
            return []
    
    async def _get_project_requirements(self, project_id: str = None) -> List[Dict]:
        """Get project requirements"""
        try:
            query = self.supabase.table("project_requirements").select("*")
            if project_id:
                query = query.eq("project_id", project_id)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get project requirements: {e}")
            return []
    
    async def _get_resource_availability(self) -> List[Dict]:
        """Get resource availability for the next 30 days"""
        try:
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=30)
            
            response = self.supabase.table("resource_availability").select("*").gte(
                "date", start_date.isoformat()
            ).lte("date", end_date.isoformat()).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get resource availability: {e}")
            return []
    
    async def _optimize_allocation(self, resources: List[Dict], requirements: List[Dict], 
                                 availability: List[Dict]) -> Dict[str, Any]:
        """Perform resource allocation optimization"""
        try:
            suggestions = []
            utilization_analysis = {}
            
            # Calculate current utilization
            for resource in resources:
                resource_id = resource["id"]
                resource_availability = [a for a in availability if a["resource_id"] == resource_id]
                
                total_available = sum(a["available_hours"] for a in resource_availability)
                total_allocated = sum(a["allocated_hours"] for a in resource_availability)
                
                utilization = (total_allocated / total_available * 100) if total_available > 0 else 0
                
                utilization_analysis[resource_id] = {
                    "resource_name": resource["name"],
                    "utilization_percent": round(utilization, 1),
                    "available_hours": total_available - total_allocated,
                    "skills": [s["skill_name"] for s in resource.get("skills", [])]
                }
                
                # Generate suggestions based on utilization
                if utilization < 60:  # Under-utilized
                    suggestions.append({
                        "type": "underutilized",
                        "resource_id": resource_id,
                        "resource_name": resource["name"],
                        "current_utilization": round(utilization, 1),
                        "available_hours": total_available - total_allocated,
                        "recommendation": f"Consider allocating more work to {resource['name']} who has {total_available - total_allocated:.1f} available hours",
                        "priority": "medium"
                    })
                elif utilization > 90:  # Over-utilized
                    suggestions.append({
                        "type": "overutilized",
                        "resource_id": resource_id,
                        "resource_name": resource["name"],
                        "current_utilization": round(utilization, 1),
                        "recommendation": f"{resource['name']} is over-allocated. Consider redistributing {total_allocated - total_available:.1f} hours",
                        "priority": "high"
                    })
            
            # Skill matching suggestions
            for requirement in requirements:
                matching_resources = []
                for resource in resources:
                    resource_skills = [s["skill_name"] for s in resource.get("skills", [])]
                    if requirement["skill_name"] in resource_skills:
                        skill_data = next((s for s in resource.get("skills", []) if s["skill_name"] == requirement["skill_name"]), None)
                        if skill_data and skill_data["proficiency_level"] >= requirement["required_level"]:
                            matching_resources.append({
                                "resource_id": resource["id"],
                                "resource_name": resource["name"],
                                "proficiency": skill_data["proficiency_level"],
                                "utilization": utilization_analysis.get(resource["id"], {}).get("utilization_percent", 0)
                            })
                
                if matching_resources:
                    # Sort by proficiency and availability
                    matching_resources.sort(key=lambda x: (x["proficiency"], -x["utilization"]), reverse=True)
                    best_match = matching_resources[0]
                    
                    suggestions.append({
                        "type": "skill_match",
                        "requirement": requirement["skill_name"],
                        "project_id": requirement["project_id"],
                        "recommended_resource": best_match["resource_name"],
                        "resource_id": best_match["resource_id"],
                        "match_score": best_match["proficiency"] / 5.0,
                        "recommendation": f"Assign {best_match['resource_name']} to {requirement['skill_name']} tasks (proficiency: {best_match['proficiency']}/5)",
                        "priority": "high" if requirement["priority"] == "critical" else "medium"
                    })
            
            return {
                "suggestions": suggestions,
                "utilization_analysis": utilization_analysis,
                "summary": {
                    "total_suggestions": len(suggestions),
                    "high_priority": len([s for s in suggestions if s["priority"] == "high"]),
                    "avg_utilization": round(sum(u["utilization_percent"] for u in utilization_analysis.values()) / len(utilization_analysis), 1) if utilization_analysis else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Optimization analysis failed: {e}")
            return {"suggestions": [], "utilization_analysis": {}, "summary": {}}

class RiskForecasterAgent(AIAgentBase):
    """AI agent for predicting and forecasting project risks"""
    
    def __init__(self, supabase_client: Client, openai_api_key: str):
        super().__init__(supabase_client, openai_api_key)
    
    async def forecast_project_risks(self, user_id: str, project_id: str = None) -> Dict[str, Any]:
        """Forecast potential risks for projects"""
        start_time = datetime.now()
        
        try:
            # Get project data
            projects_data = await self._get_projects_data(project_id)
            
            # Analyze risk patterns
            risk_predictions = []
            for project in projects_data:
                project_risks = await self._analyze_project_risks(project)
                risk_predictions.extend(project_risks)
            
            # Store predictions
            for prediction in risk_predictions:
                await self._store_risk_prediction(prediction)
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log metrics
            await self.log_metrics(
                "risk_forecast", user_id, 0, 0, response_time, True
            )
            
            return {
                "predictions": risk_predictions,
                "summary": {
                    "total_risks": len(risk_predictions),
                    "high_probability": len([r for r in risk_predictions if r["probability"] > 0.7]),
                    "critical_impact": len([r for r in risk_predictions if r["impact_score"] >= 4])
                }
            }
            
        except Exception as e:
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.log_metrics(
                "risk_forecast", user_id, 0, 0, response_time, False, str(e)
            )
            logger.error(f"Risk forecasting failed: {e}")
            raise
    
    async def _get_projects_data(self, project_id: str = None) -> List[Dict]:
        """Get project data for risk analysis"""
        try:
            query = self.supabase.table("projects").select("*")
            if project_id:
                query = query.eq("id", project_id)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get projects data: {e}")
            return []
    
    async def _analyze_project_risks(self, project: Dict) -> List[Dict]:
        """Analyze risks for a specific project"""
        risks = []
        
        try:
            # Budget risk analysis
            if project.get("budget") and project.get("spent"):
                budget_utilization = project["spent"] / project["budget"]
                if budget_utilization > 0.8:
                    risks.append({
                        "project_id": project["id"],
                        "risk_type": "budget_overrun",
                        "description": f"Project is at {budget_utilization*100:.1f}% of budget",
                        "probability": min(budget_utilization, 0.95),
                        "impact_score": 4,
                        "confidence_score": 0.8,
                        "mitigation_suggestions": [
                            "Review remaining tasks and budget allocation",
                            "Consider scope reduction or additional funding",
                            "Implement stricter budget controls"
                        ]
                    })
            
            # Timeline risk analysis
            if project.get("start_date") and project.get("end_date"):
                start_date = datetime.fromisoformat(project["start_date"].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(project["end_date"].replace('Z', '+00:00'))
                now = datetime.now(start_date.tzinfo)
                
                total_duration = (end_date - start_date).days
                elapsed_duration = (now - start_date).days
                
                if total_duration > 0:
                    timeline_progress = elapsed_duration / total_duration
                    
                    # Assume 50% completion for demo (in real scenario, get from project status)
                    work_progress = 0.5
                    
                    if timeline_progress > work_progress + 0.2:  # Behind schedule
                        risks.append({
                            "project_id": project["id"],
                            "risk_type": "schedule_delay",
                            "description": f"Project appears behind schedule ({timeline_progress*100:.1f}% time elapsed, ~{work_progress*100:.1f}% complete)",
                            "probability": 0.7,
                            "impact_score": 3,
                            "confidence_score": 0.6,
                            "mitigation_suggestions": [
                                "Reassess project timeline and milestones",
                                "Consider additional resources",
                                "Identify and remove blockers"
                            ]
                        })
            
            # Resource availability risk
            # This would analyze resource allocation vs availability
            risks.append({
                "project_id": project["id"],
                "risk_type": "resource_constraint",
                "description": "Potential resource availability issues identified",
                "probability": 0.4,
                "impact_score": 3,
                "confidence_score": 0.5,
                "mitigation_suggestions": [
                    "Review resource allocation plan",
                    "Identify backup resources",
                    "Consider timeline adjustments"
                ]
            })
            
        except Exception as e:
            logger.error(f"Risk analysis failed for project {project.get('id')}: {e}")
        
        return risks
    
    async def _store_risk_prediction(self, prediction: Dict):
        """Store risk prediction in database"""
        try:
            self.supabase.table("risk_predictions").upsert(prediction).execute()
        except Exception as e:
            logger.error(f"Failed to store risk prediction: {e}")

class HallucinationValidator(AIAgentBase):
    """AI agent for validating AI-generated content and detecting hallucinations"""
    
    def __init__(self, supabase_client: Client, openai_api_key: str):
        super().__init__(supabase_client, openai_api_key)
    
    async def validate_response(self, response: str, sources: List[Dict], 
                              context_data: Dict = None) -> Dict[str, Any]:
        """Validate AI response against source data"""
        try:
            validation_results = {
                "is_valid": True,
                "confidence_score": 1.0,
                "issues": [],
                "source_coverage": 0.0
            }
            
            # Check if response is grounded in sources
            if not sources:
                validation_results["issues"].append("No sources provided for validation")
                validation_results["confidence_score"] *= 0.5
            
            # Check for specific claims that can be verified
            claims = self._extract_claims(response)
            verified_claims = 0
            
            for claim in claims:
                if self._verify_claim_against_sources(claim, sources):
                    verified_claims += 1
                else:
                    validation_results["issues"].append(f"Unverified claim: {claim}")
            
            if claims:
                validation_results["source_coverage"] = verified_claims / len(claims)
                validation_results["confidence_score"] *= validation_results["source_coverage"]
            
            # Flag potential hallucinations
            if validation_results["confidence_score"] < 0.6:
                validation_results["is_valid"] = False
                validation_results["issues"].append("Low confidence score indicates potential hallucination")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return {
                "is_valid": False,
                "confidence_score": 0.0,
                "issues": [f"Validation error: {str(e)}"],
                "source_coverage": 0.0
            }
    
    def _extract_claims(self, response: str) -> List[str]:
        """Extract factual claims from response"""
        # Simplified claim extraction - in production, use NLP techniques
        sentences = response.split('.')
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and any(keyword in sentence.lower() for keyword in 
                              ['total', 'number', 'percent', 'budget', 'deadline', 'resource']):
                claims.append(sentence)
        
        return claims
    
    def _verify_claim_against_sources(self, claim: str, sources: List[Dict]) -> bool:
        """Verify a claim against source data"""
        # Simplified verification - in production, use semantic similarity
        claim_lower = claim.lower()
        
        for source in sources:
            source_text = source.get('content_text', '').lower()
            if any(word in source_text for word in claim_lower.split() if len(word) > 3):
                return True
        
        return False

# Factory function to create AI agents
def create_ai_agents(supabase_client: Client, openai_api_key: str) -> Dict[str, AIAgentBase]:
    """Create all AI agents"""
    return {
        "rag_reporter": RAGReporterAgent(supabase_client, openai_api_key),
        "resource_optimizer": ResourceOptimizerAgent(supabase_client, openai_api_key),
        "risk_forecaster": RiskForecasterAgent(supabase_client, openai_api_key),
        "hallucination_validator": HallucinationValidator(supabase_client, openai_api_key)
    }