# Performance Monitoring - Troubleshooting Guide

## Common Issues and Solutions

### Issue: 500 Internal Server Error

**Symptom:**
```
Stats API error: 500 Internal Server Error
```

**Causes and Solutions:**

#### 1. Backend Not Running
**Check:**
```bash
curl http://localhost:8000/health
```

**Solution:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

#### 2. Permission Error (FIXED)
**Problem:** Used `Permission.admin` which doesn't exist

**Solution:** Updated to use `Permission.admin_read` and `Permission.system_admin`

**Files Changed:**
- `backend/routers/admin_performance.py` - Now uses correct permissions

#### 3. Missing Middleware
**Check backend startup logs for:**
```
✅ Performance tracking middleware enabled
```

**If missing, verify:**
- `backend/main.py` includes the middleware import
- Middleware is added with `app.add_middleware(PerformanceMiddleware, tracker=performance_tracker)`

### Issue: Authentication Errors (401/403)

**Symptom:**
```
Unauthorized or Forbidden
```

**Solutions:**

1. **Check if logged in:**
   - Navigate to `/` and log in
   - Verify JWT token in browser cookies

2. **Check admin permissions:**
   - User must have `admin_read` permission
   - Default development user (ID: `00000000-0000-0000-0000-000000000001`) has admin permissions

3. **Check Authorization header:**
   - Frontend should send: `Authorization: Bearer <token>`
   - Check browser Network tab for the header

### Issue: No Data Showing

**Symptom:**
Dashboard shows 0 requests or empty statistics

**Solutions:**

1. **Generate some traffic:**
   ```bash
   # Make some API requests
   curl http://localhost:8000/projects
   curl http://localhost:8000/portfolios
   curl http://localhost:8000/health
   ```

2. **Check if middleware is tracking:**
   ```bash
   curl http://localhost:8000/admin/performance/stats
   ```
   Should show `total_requests > 0`

3. **Verify middleware is enabled:**
   - Check backend startup logs
   - Look for: `✅ Performance tracking middleware enabled`

### Issue: Frontend Can't Connect to Backend

**Symptom:**
```
Failed to fetch performance stats from backend
```

**Solutions:**

1. **Check BACKEND_URL:**
   ```bash
   # In .env.local
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

2. **Verify backend is accessible:**
   ```bash
   curl http://localhost:8000/admin/performance/stats
   ```

3. **Check CORS settings:**
   - Backend should allow `http://localhost:3000`
   - Check `backend/main.py` CORS configuration

### Issue: Metrics Reset After Server Restart

**Symptom:**
All statistics go back to 0 after restarting backend

**Explanation:**
This is expected behavior - metrics are stored in memory.

**Solutions:**

1. **For development:** This is fine - metrics reset on restart
2. **For production:** Consider implementing persistent storage:
   - Store metrics in database
   - Use Redis for distributed tracking
   - Export to monitoring tools (Prometheus, Grafana)

### Issue: Slow Query Threshold Too Sensitive

**Symptom:**
Too many queries marked as "slow"

**Solution:**
Adjust threshold in `backend/middleware/performance_tracker.py`:

```python
# Default: 1.0 second
performance_tracker = PerformanceTracker(slow_query_threshold=2.0)  # 2 seconds
```

### Issue: Memory Usage Growing

**Symptom:**
Backend memory usage increases over time

**Explanation:**
Tracker stores last 100 requests per endpoint and last 50 slow queries.

**Solutions:**

1. **Reset statistics periodically:**
   ```bash
   curl -X POST http://localhost:8000/admin/performance/reset \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Adjust limits in tracker:**
   ```python
   tracker.max_slow_queries = 25  # Reduce from 50
   # In record_request, reduce from 100 to 50
   ```

## Testing Checklist

Use this checklist to verify everything is working:

- [ ] Backend starts without errors
- [ ] See "✅ Performance tracking middleware enabled" in logs
- [ ] Can access `/admin/performance/stats` endpoint
- [ ] Frontend dashboard loads without errors
- [ ] Making API requests increases total_requests count
- [ ] Endpoint statistics show up in dashboard
- [ ] Health status displays correctly
- [ ] Slow queries are detected (if any)
- [ ] Dashboard auto-refreshes every 30 seconds

## Quick Test Commands

```bash
# 1. Check backend health
curl http://localhost:8000/health

# 2. Generate traffic
for i in {1..10}; do curl -s http://localhost:8000/projects > /dev/null; done

# 3. Check stats (without auth - will fail but generates traffic)
curl http://localhost:8000/admin/performance/stats

# 4. View in browser
open http://localhost:3000/admin/performance
```

## Debug Mode

To see detailed logs:

1. **Backend:**
   ```bash
   # Add to backend/main.py
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Frontend:**
   - Open browser DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for API calls

## Getting Help

If issues persist:

1. Check backend logs for errors
2. Check browser console for frontend errors
3. Verify all files were created correctly:
   - `backend/middleware/performance_tracker.py`
   - `backend/routers/admin_performance.py`
   - `app/api/admin/performance/stats/route.ts`
   - `app/api/admin/performance/health/route.ts`

4. Run tests:
   ```bash
   cd backend
   python -m pytest tests/test_performance_tracker.py -v
   ```

## Known Limitations

1. **In-Memory Only**: Metrics reset on server restart
2. **Single Instance**: No distributed tracking across multiple servers
3. **Limited History**: Keeps only recent data
4. **No Persistence**: No database storage of historical metrics

These are intentional design choices for simplicity. For production use, consider implementing persistent storage and distributed tracking.
