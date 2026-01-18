# Design Document: Admin Performance Optimization

## Overview

This design addresses critical performance issues in the admin performance monitoring page identified through Lighthouse audits. The page currently suffers from excessive Total Blocking Time (350ms), high Cumulative Layout Shift (0.639), and bloated JavaScript bundles (3,326 KiB total, 2,955 KiB unused). These issues stem from:

1. **Synchronous loading of heavy dependencies** - Recharts library (~500KB) loads synchronously, blocking initial render
2. **Inefficient component structure** - All components render immediately without code splitting
3. **Missing layout reservations** - Charts and dynamic content cause layout shifts during load
4. **Suboptimal bundle configuration** - Unused code from libraries not being tree-shaken
5. **Non-composited animations** - CSS animations triggering layout recalculations
6. **Missing performance monitoring** - No visibility into real-world performance metrics

The solution implements a multi-layered optimization strategy:
- **Progressive loading** with React.lazy() and dynamic imports
- **Layout stability** through explicit dimensions and skeleton loaders
- **Bundle optimization** via selective imports and code splitting
- **Animation optimization** using GPU-accelerated transforms
- **Performance monitoring** with Web Vitals tracking

This design maintains full functionality while achieving target metrics: TBT < 200ms, CLS < 0.1, and bundle size < 1,500 KiB.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Admin Performance Page                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Progressive Loading Layer                   │  │
│  │  - Initial Shell (Critical CSS + Minimal JS)         │  │
│  │  - Lazy-loaded Components (Charts, Tables)           │  │
│  │  - Deferred Non-critical Features                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Layout Stability Layer                      │  │
│  │  - Skeleton Loaders with Fixed Dimensions            │  │
│  │  - Reserved Space for Dynamic Content                │  │
│  │  - Aspect Ratio Containers                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Optimized Component Layer                   │  │
│  │  - Memoized Components (React.memo)                  │  │
│  │  - Memoized Computations (useMemo)                   │  │
│  │  - Optimized Re-renders                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Performance Monitoring Layer                │  │
│  │  - Web Vitals Tracking (LCP, FID, CLS, INP)         │  │
│  │  - Long Task Detection                               │  │
│  │  - Bundle Size Monitoring                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
PerformanceDashboard (Main Container)
├── CriticalMetrics (Immediate Load)
│   ├── HealthStatusCard
│   ├── MetricCard (Total Requests)
│   ├── MetricCard (Total Errors)
│   ├── MetricCard (Slow Queries)
│   └── MetricCard (Cache Hit Rate)
│
├── LazyChartSection (Lazy Loaded)
│   ├── Suspense (with ChartSkeleton)
│   ├── EndpointPerformanceChart
│   └── RequestVolumeChart
│
├── LazySlowQueriesTable (Lazy Loaded)
│   ├── Suspense (with TableSkeleton)
│   └── SlowQueriesTable
│
└── LazyCacheStatistics (Lazy Loaded)
    ├── Suspense (with StatsSkeleton)
    └── CacheStatsCard
```

### Loading Strategy

**Phase 1: Initial Shell (0-500ms)**
- Load minimal HTML structure
- Inline critical CSS for above-the-fold content
- Load core React runtime and page shell
- Display skeleton loaders with fixed dimensions

**Phase 2: Critical Data (500-1000ms)**
- Fetch health status and key metrics
- Render metric cards with actual data
- Maintain skeleton loaders for charts

**Phase 3: Secondary Content (1000-2000ms)**
- Lazy load Recharts library
- Render charts with fetched data
- Load slow queries table

**Phase 4: Tertiary Content (2000ms+)**
- Load cache statistics
- Enable auto-refresh functionality
- Initialize performance monitoring

## Components and Interfaces

### Core Components

#### 1. PerformanceDashboard (Main Container)

**Purpose**: Orchestrates progressive loading and manages global state

**Props**: None (uses hooks for auth and translations)

**State**:
```typescript
interface DashboardState {
  stats: PerformanceStats | null
  health: HealthStatus | null
  cacheStats: CacheStats | null
  loading: boolean
  error: string | null
  successMessage: string | null
  refreshing: boolean
}
```

**Key Optimizations**:
- Uses React.lazy() for chart components
- Implements Suspense boundaries with skeleton loaders
- Memoizes expensive data transformations
- Batches state updates to minimize re-renders

#### 2. CriticalMetrics (Immediate Load)

**Purpose**: Displays key performance indicators without blocking

**Props**:
```typescript
interface CriticalMetricsProps {
  health: HealthStatus | null
  stats: PerformanceStats | null
  cacheStats: CacheStats | null
  loading: boolean
}
```

**Optimizations**:
- Wrapped in React.memo() to prevent unnecessary re-renders
- Uses fixed dimensions to prevent CLS
- Minimal dependencies (no heavy libraries)

#### 3. LazyChartSection (Lazy Loaded)

**Purpose**: Renders performance charts without blocking initial load

**Implementation**:
```typescript
const LazyChartSection = React.lazy(() => 
  import('./components/ChartSection').then(module => ({
    default: module.ChartSection
  }))
)
```

**Props**:
```typescript
interface ChartSectionProps {
  endpointData: ChartDataPoint[]
  slowQueriesData: SlowQueryDataPoint[]
}
```

**Optimizations**:
- Dynamically imports Recharts only when needed
- Uses selective imports for Recharts components
- Memoizes chart data transformations
- Defines explicit chart dimensions (width: 100%, height: 300px)

#### 4. ChartSkeleton (Loading State)

**Purpose**: Maintains layout stability while charts load

**Implementation**:
```typescript
function ChartSkeleton() {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="h-6 w-48 bg-gray-200 rounded animate-pulse mb-4" />
      <div className="w-full h-[300px] bg-gray-100 rounded animate-pulse" />
    </div>
  )
}
```

**Key Features**:
- Fixed height (300px) matches actual chart height
- Prevents CLS by reserving exact space
- Lightweight (no dependencies)

### Data Interfaces

#### PerformanceStats
```typescript
interface PerformanceStats {
  endpoint_stats: Record<string, EndpointStat>
  total_requests: number
  total_errors: number
  slow_queries_count: number
  recent_slow_queries: SlowQuery[]
}

interface EndpointStat {
  total_requests: number
  avg_duration: number
  min_duration: number
  max_duration: number
  error_rate: number
  requests_per_minute: number
}

interface SlowQuery {
  endpoint: string
  duration: number
  timestamp: string
}
```

#### HealthStatus
```typescript
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  metrics: {
    total_requests: number
    error_rate: number
    slow_queries: number
    uptime: string
  }
  cache_status: string
}
```

#### CacheStats
```typescript
interface CacheStats {
  type: 'redis' | 'memory'
  entries?: number
  timestamps?: number
  connected_clients?: number
  used_memory?: string
  keyspace_hits?: number
  keyspace_misses?: number
  hit_rate?: number
  error?: string
}
```

### Utility Functions

#### 1. Data Transformation (Memoized)

```typescript
const prepareEndpointData = useMemo(() => {
  if (!stats?.endpoint_stats) return []
  
  return Object.entries(stats.endpoint_stats)
    .map(([endpoint, data]) => ({
      endpoint: endpoint.length > 30 
        ? endpoint.substring(0, 30) + '...' 
        : endpoint,
      fullEndpoint: endpoint,
      avg_duration: Math.round(data.avg_duration * 1000),
      requests: data.total_requests,
      error_rate: data.error_rate,
      rpm: data.requests_per_minute
    }))
    .slice(0, 10)
}, [stats?.endpoint_stats])
```

**Optimization**: Memoization prevents recalculation on every render

#### 2. Batch API Calls

```typescript
async function fetchPerformanceData() {
  const [statsResponse, healthResponse, cacheResponse] = 
    await Promise.all([
      fetch(getApiUrl('/admin/performance/stats'), { headers }),
      fetch(getApiUrl('/admin/performance/health'), { headers }),
      fetch(getApiUrl('/admin/cache/stats'), { headers })
    ])
  
  // Process responses in parallel
  const [statsData, healthData, cacheData] = await Promise.all([
    statsResponse.ok ? statsResponse.json() : null,
    healthResponse.ok ? healthResponse.json() : null,
    cacheResponse.ok ? cacheResponse.json() : null
  ])
  
  // Batch state updates
  React.startTransition(() => {
    setStats(statsData)
    setHealth(healthData)
    setCacheStats(cacheData)
    setLoading(false)
  })
}
```

**Optimization**: Parallel fetching + batched state updates reduce render cycles

## Data Models

### Chart Data Models

#### ChartDataPoint
```typescript
interface ChartDataPoint {
  endpoint: string          // Truncated for display
  fullEndpoint: string      // Full endpoint for tooltips
  avg_duration: number      // In milliseconds
  requests: number          // Total request count
  error_rate: number        // Percentage (0-100)
  rpm: number              // Requests per minute
}
```

#### SlowQueryDataPoint
```typescript
interface SlowQueryDataPoint {
  endpoint: string
  duration: number          // In milliseconds
  time: string             // Formatted time string
}
```

### Performance Metrics Model

```typescript
interface WebVitalsMetrics {
  lcp: number              // Largest Contentful Paint (ms)
  fid: number              // First Input Delay (ms)
  cls: number              // Cumulative Layout Shift (score)
  ttfb: number             // Time to First Byte (ms)
  inp: number              // Interaction to Next Paint (ms)
  fcp: number              // First Contentful Paint (ms)
}
```

### Bundle Analysis Model

```typescript
interface BundleStats {
  totalSize: number
  gzippedSize: number
  chunks: ChunkInfo[]
}

interface ChunkInfo {
  name: string
  size: number
  modules: ModuleInfo[]
}

interface ModuleInfo {
  name: string
  size: number
  reasons: string[]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Total Blocking Time Under Threshold

*For any* page load of the admin performance page, the Total Blocking Time (sum of all blocking tasks) should be less than 200ms.

**Validates: Requirements 1.1**

**Testing Approach**: Use PerformanceObserver to measure all long tasks during page load, sum their blocking time (time over 50ms), and verify the total is under 200ms.

### Property 2: No Long Tasks Exceed Threshold

*For any* JavaScript task executed on the main thread during page operation, the task duration should not exceed 50ms.

**Validates: Requirements 1.2, 9.4**

**Testing Approach**: Use PerformanceObserver with entryType 'longtask' to monitor all tasks and verify none exceed 50ms duration.

### Property 3: Critical Content Renders Before Non-Critical Scripts

*For any* page load, critical content (health status and metric cards) should be rendered in the DOM before non-critical JavaScript (charts, tables) begins loading.

**Validates: Requirements 1.3**

**Testing Approach**: Monitor DOM mutations and script loading events to verify critical content appears before dynamic imports execute.

### Property 4: Third-Party Libraries Use Dynamic Imports

*For any* third-party library imported in the page, the import should use dynamic import() syntax rather than static import statements.

**Validates: Requirements 1.5, 3.4**

**Testing Approach**: Analyze the source code and webpack bundle to verify Recharts and other heavy libraries use React.lazy() or dynamic import().

### Property 5: Cumulative Layout Shift Below Threshold

*For any* page load and subsequent interactions, the Cumulative Layout Shift score should remain below 0.1.

**Validates: Requirements 2.1, 2.2, 2.3, 2.5, 2.6**

**Testing Approach**: Use Web Vitals library to measure CLS during page load and verify it stays below 0.1. This property subsumes individual layout stability checks.

### Property 6: Skeleton Dimensions Match Final Content

*For any* loading skeleton displayed, its dimensions (width and height) should match the dimensions of the final content that replaces it.

**Validates: Requirements 2.1, 7.3**

**Testing Approach**: Measure skeleton dimensions before content loads and final content dimensions after loading, verify they match within 5px tolerance.

### Property 7: Total JavaScript Bundle Under Size Limit

*For any* production build, the total JavaScript payload delivered to the browser should be less than 1,500 KiB.

**Validates: Requirements 3.6**

**Testing Approach**: Analyze webpack bundle output and sum all JavaScript chunk sizes, verify total is under 1,500 KiB.

### Property 8: Unused JavaScript Under Size Limit

*For any* production build, the amount of unused JavaScript (code not executed during page load) should be less than 500 KiB.

**Validates: Requirements 4.5**

**Testing Approach**: Use Chrome DevTools Coverage tool to measure unused JavaScript and verify it's under 500 KiB.

### Property 9: Animations Use Only Compositable Properties

*For any* CSS animation or transition defined in the page, it should only animate transform and opacity properties.

**Validates: Requirements 5.1, 5.3, 5.5**

**Testing Approach**: Parse all CSS animations and transitions, verify they only use transform and opacity. Use Performance API to verify no layout recalculations during animations.

### Property 10: Will-Change Only on Active Animations

*For any* element with will-change CSS property, the property should only be present while the element is actively animating.

**Validates: Requirements 5.4**

**Testing Approach**: Monitor DOM for will-change property and verify it's added before animation starts and removed after animation ends.

### Property 11: No Console Errors on Page Load

*For any* page load, no errors should be logged to the browser console.

**Validates: Requirements 6.1**

**Testing Approach**: Monitor console.error calls during page load and verify count is zero.

### Property 12: Critical Content Renders Within Time Budget

*For any* page load, the page shell and critical metrics should be rendered and visible within 1 second.

**Validates: Requirements 7.1**

**Testing Approach**: Use Performance API to measure time from navigation start to when critical content is visible in the DOM, verify it's under 1000ms.

### Property 13: Charts Load After Initial Render

*For any* page load, the Recharts library should begin loading only after the initial page shell has rendered.

**Validates: Requirements 7.2**

**Testing Approach**: Monitor network requests and DOM render timing to verify Recharts request starts after initial render completes.

### Property 14: Critical API Calls Start Before Non-Critical

*For any* page load, API calls for health status and key metrics should start before API calls for detailed statistics.

**Validates: Requirements 7.4**

**Testing Approach**: Monitor network request timing and verify health/metrics requests start before stats/cache requests.

### Property 15: Pending Requests Cancelled on Refresh

*For any* auto-refresh trigger, any pending API requests from the previous refresh should be cancelled before new requests start.

**Validates: Requirements 8.3**

**Testing Approach**: Monitor AbortController usage and verify pending requests are aborted when new requests begin.

### Property 16: State Updates Are Batched

*For any* data fetch completion, related state updates (stats, health, cache) should be batched into a single render cycle.

**Validates: Requirements 8.4**

**Testing Approach**: Use React DevTools Profiler to count render cycles and verify multiple state updates result in single render.

### Property 17: Web Vitals Measured and Reported

*For any* page load, Core Web Vitals (LCP, FID, CLS, TTFB, INP) should be measured and sent to the analytics endpoint.

**Validates: Requirements 9.1, 9.2**

**Testing Approach**: Monitor network requests to verify Web Vitals data is sent to analytics endpoint with all required metrics.

### Property 18: Component Render Times Tracked

*For any* component render, the render time should be tracked and available for performance profiling.

**Validates: Requirements 9.3**

**Testing Approach**: Verify React Profiler or custom timing code tracks render times for all major components.

### Property 19: CSS Does Not Block First Contentful Paint

*For any* page load, CSS loading should not delay First Contentful Paint beyond 1.5 seconds.

**Validates: Requirements 10.5**

**Testing Approach**: Use Performance API to measure FCP and verify it occurs within 1.5s, indicating CSS is not blocking.

## Error Handling

### API Error Handling

**Strategy**: Graceful degradation with user-friendly messages

**Implementation**:
```typescript
async function fetchPerformanceData() {
  try {
    const responses = await Promise.all([
      fetch(getApiUrl('/admin/performance/stats'), { headers }),
      fetch(getApiUrl('/admin/performance/health'), { headers }),
      fetch(getApiUrl('/admin/cache/stats'), { headers })
    ])
    
    // Handle individual response failures gracefully
    const [statsData, healthData, cacheData] = await Promise.all(
      responses.map(async (response, index) => {
        if (!response.ok) {
          console.error(`API error for endpoint ${index}: ${response.status}`)
          return null
        }
        return response.json()
      })
    )
    
    // Update state with whatever data we got
    setStats(statsData)
    setHealth(healthData)
    setCacheStats(cacheData)
    
  } catch (error) {
    console.error('Failed to fetch performance data:', error)
    setError('Unable to load performance data. Please try again.')
  } finally {
    setLoading(false)
  }
}
```

**Error States**:
- **Network Failure**: Display "Unable to connect to server" message
- **Partial Data**: Show available data, hide unavailable sections
- **Timeout**: Cancel request after 10s, show timeout message
- **Invalid Data**: Log warning, use fallback empty state

### Component Error Boundaries

**Strategy**: Isolate failures to prevent full page crashes

**Implementation**:
```typescript
class ChartErrorBoundary extends React.Component {
  state = { hasError: false }
  
  static getDerivedStateFromError(error) {
    return { hasError: true }
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Chart rendering error:', error, errorInfo)
    // Send to error tracking service
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-red-50 rounded-lg">
          <p>Unable to display chart. Please refresh the page.</p>
        </div>
      )
    }
    return this.props.children
  }
}
```

**Boundaries**:
- Wrap each lazy-loaded section in error boundary
- Prevent chart errors from crashing entire page
- Log errors for debugging while showing fallback UI

### Loading State Management

**Strategy**: Progressive enhancement with skeleton loaders

**States**:
1. **Initial Loading**: Show skeleton loaders for all sections
2. **Partial Loading**: Show data as it arrives, maintain skeletons for pending
3. **Complete**: All data loaded, no skeletons
4. **Error**: Show error message, allow retry
5. **Refreshing**: Show spinner on refresh button, maintain existing data

### Console Error Prevention

**Common Issues and Solutions**:

1. **Undefined Data Access**:
```typescript
// Bad: Can cause "Cannot read property of undefined"
const value = stats.endpoint_stats.someEndpoint.avg_duration

// Good: Safe navigation with optional chaining
const value = stats?.endpoint_stats?.someEndpoint?.avg_duration ?? 0
```

2. **Missing Dependencies**:
```typescript
// Bad: Missing dependency causes stale closures
useEffect(() => {
  fetchData()
}, []) // Missing session dependency

// Good: Include all dependencies
useEffect(() => {
  if (session) fetchData()
}, [session])
```

3. **Memory Leaks**:
```typescript
// Bad: Doesn't cleanup interval
useEffect(() => {
  const interval = setInterval(fetchData, 30000)
}, [])

// Good: Cleanup on unmount
useEffect(() => {
  const interval = setInterval(fetchData, 30000)
  return () => clearInterval(interval)
}, [])
```

## Testing Strategy

### Dual Testing Approach

This specification requires both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Together they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness

### Property-Based Testing

**Library**: fast-check (already in package.json)

**Configuration**: Each property test runs minimum 100 iterations

**Test Structure**:
```typescript
import fc from 'fast-check'

describe('Admin Performance Optimization', () => {
  it('Property 1: Total Blocking Time Under Threshold', async () => {
    // Feature: admin-performance-optimization, Property 1: TBT < 200ms
    
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          // Generate random page load scenarios
          networkSpeed: fc.constantFrom('fast', 'slow', '3g'),
          cacheState: fc.constantFrom('empty', 'partial', 'full'),
          dataSize: fc.integer({ min: 100, max: 10000 })
        }),
        async (scenario) => {
          const metrics = await measurePageLoad(scenario)
          expect(metrics.totalBlockingTime).toBeLessThan(200)
        }
      ),
      { numRuns: 100 }
    )
  })
  
  it('Property 2: No Long Tasks Exceed Threshold', async () => {
    // Feature: admin-performance-optimization, Property 2: No task > 50ms
    
    await fc.assert(
      fc.asyncProperty(
        fc.array(fc.integer({ min: 1, max: 100 })), // Random task counts
        async (taskCount) => {
          const tasks = await monitorTasks(taskCount)
          tasks.forEach(task => {
            expect(task.duration).toBeLessThanOrEqual(50)
          })
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

### Unit Testing

**Focus Areas**:
1. **Component Rendering**: Verify components render without errors
2. **Data Transformation**: Test edge cases in data processing
3. **Error Handling**: Simulate API failures and verify graceful handling
4. **User Interactions**: Test button clicks, refresh, cache clear

**Example Tests**:
```typescript
describe('PerformanceDashboard', () => {
  it('renders loading state initially', () => {
    render(<PerformanceDashboard />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })
  
  it('displays error message on API failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    render(<PerformanceDashboard />)
    await waitFor(() => {
      expect(screen.getByText(/unable to load/i)).toBeInTheDocument()
    })
  })
  
  it('handles empty data gracefully', async () => {
    mockFetch.mockResolvedValueOnce({ json: async () => ({}) })
    render(<PerformanceDashboard />)
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })
  })
})
```

### Performance Testing

**Lighthouse CI**: Automated performance testing in CI/CD

**Configuration** (lighthouserc.js):
```javascript
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/admin/performance'],
      numberOfRuns: 3
    },
    assert: {
      assertions: {
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'interactive': ['error', { maxNumericValue: 3500 }],
        'first-contentful-paint': ['error', { maxNumericValue: 1500 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }]
      }
    }
  }
}
```

**Bundle Analysis**: Automated bundle size monitoring

**Script** (package.json):
```json
{
  "scripts": {
    "analyze": "ANALYZE=true npm run build",
    "test:bundle": "node scripts/check-bundle-size.js"
  }
}
```

**Bundle Size Test**:
```javascript
// scripts/check-bundle-size.js
const fs = require('fs')
const path = require('path')

const MAX_BUNDLE_SIZE = 1500 * 1024 // 1500 KiB
const MAX_UNUSED_JS = 500 * 1024    // 500 KiB

function checkBundleSize() {
  const buildDir = path.join(__dirname, '../.next/static/chunks')
  let totalSize = 0
  
  fs.readdirSync(buildDir).forEach(file => {
    if (file.endsWith('.js')) {
      const stats = fs.statSync(path.join(buildDir, file))
      totalSize += stats.size
    }
  })
  
  if (totalSize > MAX_BUNDLE_SIZE) {
    throw new Error(`Bundle size ${totalSize} exceeds limit ${MAX_BUNDLE_SIZE}`)
  }
  
  console.log(`✓ Bundle size: ${totalSize} bytes (limit: ${MAX_BUNDLE_SIZE})`)
}

checkBundleSize()
```

### Integration Testing

**Playwright Tests**: End-to-end performance validation

```typescript
import { test, expect } from '@playwright/test'

test('admin performance page loads within budget', async ({ page }) => {
  await page.goto('/admin/performance')
  
  // Measure Web Vitals
  const metrics = await page.evaluate(() => {
    return new Promise(resolve => {
      new PerformanceObserver(list => {
        const entries = list.getEntries()
        resolve({
          lcp: entries.find(e => e.entryType === 'largest-contentful-paint')?.renderTime,
          cls: entries.find(e => e.entryType === 'layout-shift')?.value,
          fcp: entries.find(e => e.name === 'first-contentful-paint')?.startTime
        })
      }).observe({ entryTypes: ['largest-contentful-paint', 'layout-shift', 'paint'] })
    })
  })
  
  expect(metrics.lcp).toBeLessThan(2500)
  expect(metrics.cls).toBeLessThan(0.1)
  expect(metrics.fcp).toBeLessThan(1500)
})

test('no layout shifts during chart loading', async ({ page }) => {
  await page.goto('/admin/performance')
  
  // Monitor layout shifts
  const shifts = await page.evaluate(() => {
    const shifts = []
    new PerformanceObserver(list => {
      shifts.push(...list.getEntries())
    }).observe({ entryTypes: ['layout-shift'] })
    
    return new Promise(resolve => {
      setTimeout(() => resolve(shifts), 5000)
    })
  })
  
  const totalCLS = shifts.reduce((sum, shift) => sum + shift.value, 0)
  expect(totalCLS).toBeLessThan(0.1)
})
```

### Test Coverage Goals

- **Unit Test Coverage**: > 80% for all components
- **Property Test Coverage**: All 19 correctness properties
- **Integration Test Coverage**: Critical user flows
- **Performance Test Coverage**: All performance budgets

### Continuous Monitoring

**Production Monitoring**:
- Real User Monitoring (RUM) for Web Vitals
- Error tracking with Sentry or similar
- Bundle size tracking in CI/CD
- Performance regression detection

**Alerts**:
- TBT > 200ms for 3 consecutive measurements
- CLS > 0.1 for 5% of users
- Bundle size increase > 10%
- Error rate > 1%
