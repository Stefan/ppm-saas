# Enhanced PMR API Router

## Overview

The Enhanced PMR (Project Monthly Report) API router provides endpoints for AI-powered, collaborative project monthly reports. This implementation fulfills task 4 of the Enhanced PMR feature specification.

## Implemented Endpoints

### Report Generation

#### POST `/api/reports/pmr/generate`
Generate an AI-enhanced Project Monthly Report with:
- AI-generated insights and predictions
- Monte Carlo variance analysis (optional)
- Real-time metrics integration
- Executive summary powered by RAG

**Request Body**: `EnhancedPMRGenerationRequest`
**Response**: `EnhancedPMRResponse` (201 Created)
**Rate Limit**: 5 requests/minute

#### GET `/api/reports/pmr/{report_id}`
Retrieve a complete Enhanced PMR report by ID, including:
- AI insights with confidence scores
- Monte Carlo analysis results
- Real-time metrics
- Collaboration session data

**Response**: `EnhancedPMRResponse`
**Rate Limit**: 30 requests/minute

#### GET `/api/reports/pmr/projects/{project_id}/reports`
List all Enhanced PMR reports for a project with filtering support:
- Filter by year and month
- Filter by report status
- Pagination support

**Query Parameters**:
- `year` (optional): Filter by report year
- `month` (optional): Filter by report month (1-12)
- `status` (optional): Filter by report status
- `limit` (default: 50, max: 100): Number of results
- `offset` (default: 0): Pagination offset

**Response**: `List[EnhancedPMRResponse]`
**Rate Limit**: 30 requests/minute

### Interactive Editing

#### POST `/api/reports/pmr/{report_id}/edit/chat`
Edit report using natural language chat interface. Supports commands like:
- "Add more detail about budget variance"
- "Update the executive summary to highlight risks"
- "Generate a new insight about resource allocation"

**Request Body**: `ChatEditRequest`
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "context": {} (optional)
}
```

**Response**: `ChatEditResponse`
**Rate Limit**: 20 requests/minute

#### POST `/api/reports/pmr/{report_id}/edit/section`
Update a specific section of the report with merge strategies:
- `replace`: Replace entire section content
- `merge`: Merge with existing content
- `append`: Append to existing content

**Request Body**: `SectionUpdateRequest`
```json
{
  "section_id": "string",
  "content": {},
  "merge_strategy": "replace|merge|append"
}
```

**Response**: `SectionUpdateResponse`
**Rate Limit**: 30 requests/minute

#### GET `/api/reports/pmr/{report_id}/edit/suggestions`
Get AI-powered suggestions for report improvement.

**Query Parameters**:
- `section` (optional): Specific section to get suggestions for
- `suggestion_type` (default: "content"): Type of suggestions
  - `content`: Content improvements and additions
  - `structure`: Structural organization suggestions
  - `metrics`: Recommended metrics to include
  - `visualizations`: Visualization suggestions

**Response**: `AISuggestionsResponse`
**Rate Limit**: 20 requests/minute

### Health Check

#### GET `/api/reports/pmr/health`
Check Enhanced PMR service health status.

**Response**:
```json
{
  "service_available": boolean,
  "database_connected": boolean,
  "openai_configured": boolean,
  "timestamp": "ISO 8601 datetime",
  "features": {
    "ai_insights": boolean,
    "monte_carlo_analysis": boolean,
    "chat_editing": boolean,
    "real_time_metrics": boolean,
    "collaboration": boolean
  }
}
```

**Rate Limit**: 60 requests/minute

## Authentication & Authorization

All endpoints (except health check) require authentication and appropriate permissions:
- Report generation/retrieval: `Permission.project_read`
- Report editing: `Permission.project_update`

## Error Responses

### 404 Not Found
- Report not found
- Project not found

### 503 Service Unavailable
- Enhanced PMR service not available
- Database service not available

### 500 Internal Server Error
- Unexpected errors during processing

## Dependencies

### Services
- `EnhancedPMRService`: Main orchestration service for report generation
- `AIInsightsEngine`: AI-powered insight generation
- `HelpRAGAgent`: RAG-powered executive summary generation

### Models
- `EnhancedPMRGenerationRequest`
- `EnhancedPMRResponse`
- `ChatEditRequest`
- `ChatEditResponse`
- `SectionUpdateRequest`
- `SectionUpdateResponse`
- `AISuggestionsRequest`
- `AISuggestionsResponse`

### Configuration
- `OPENAI_API_KEY`: Required for AI features
- Supabase client: Required for database operations

## Integration

The router is registered in `main.py`:

```python
from routers.enhanced_pmr import router as enhanced_pmr_router
app.include_router(enhanced_pmr_router)
```

## Testing

Run the simple router tests:

```bash
python test_enhanced_pmr_router_simple.py
```

Expected output:
```
============================================================
Testing Enhanced PMR Router
============================================================

✅ Router imported successfully
✅ Router prefix is correct: /api/reports/pmr
✅ Router tags are correct
✅ All expected endpoints are present
✅ Endpoint HTTP methods are correct

============================================================
Results: 5/5 tests passed
============================================================
```

## Requirements Fulfilled

This implementation fulfills the following requirements from task 4:

✅ Create `backend/routers/enhanced_pmr.py` with new API endpoints
✅ Implement POST `/api/reports/pmr/generate` for AI-enhanced report creation
✅ Add GET `/api/reports/pmr/{report_id}` for retrieving enhanced reports
✅ Create POST `/api/reports/pmr/{report_id}/edit/chat` for chat-based editing
✅ Additional endpoints for comprehensive report management

## Next Steps

To fully utilize these endpoints, ensure:
1. Database tables are created (task 8)
2. Frontend components are implemented (tasks 9-19)
3. Export pipeline is configured (task 7)
4. Real-time collaboration service is implemented (task 5)

## Notes

- Rate limiting is implemented using the `limiter` from `performance_optimization`
- All endpoints include proper error handling and logging
- The router follows existing patterns from other routers in the codebase
- Mock responses are provided for some endpoints pending full service implementation
