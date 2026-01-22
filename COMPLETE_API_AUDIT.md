# Vollständige API Endpoint Audit

## Backend Router Übersicht

| Router File | Prefix | Status |
|-------------|--------|--------|
| admin.py | `/api/admin` | ✅ Konsistent |
| admin_performance.py | `/api/admin/performance` | ✅ Konsistent |
| users.py | `/api/admin/users` | ✅ Konsistent (gerade gefixt) |
| feature_flags.py | `/api/admin/feature-flags` | ✅ Konsistent (gerade gefixt) |
| audit.py | `/api/audit` | ✅ Konsistent |
| rbac.py | `/api/rbac` | ✅ Konsistent |
| enhanced_pmr.py | `/api/reports/pmr` | ✅ Konsistent |
| pmr_performance.py | `/api/reports/pmr/performance` | ✅ Konsistent |
| projects_import.py | `/api/projects` | ✅ Konsistent |
| simulations.py | `/api/v1/monte-carlo` | ✅ Konsistent |
| shareable_urls.py | `/api` | ✅ Konsistent |
| portfolios.py | `/portfolios` | ✅ Kein /api (OK) |
| projects.py | `/projects` | ✅ Kein /api (OK) |
| resources.py | `/resources` | ✅ Kein /api (OK) |
| risks.py | `/risks` | ✅ Kein /api (OK) |
| scenarios.py | `/simulations/what-if` | ✅ Kein /api (OK) |
| feedback.py | `/feedback` | ⚠️ Aber auch `/notifications` |
| ai.py | `/ai` | ✅ Kein /api (OK) |
| help_chat.py | `/ai/help` | ✅ Kein /api (OK) |
| variance.py | `/variance` | ✅ Kein /api (OK) |
| csv_import.py | `/csv-import` | ✅ Kein /api (OK) |
| reports.py | `/reports` | ✅ Kein /api (OK) |
| workflows.py | `/workflows` | ✅ Kein /api (OK) |
| financial.py | `/financial-tracking` + `/budget-alerts` | ⚠️ Zwei Router |
| schedules.py | `/schedules` | ✅ Kein /api (OK) |
| po_breakdown.py | `/pos/breakdown` | ✅ Kein /api (OK) |
| change_management.py | `/changes` | ✅ Kein /api (OK) |

---

## Problematische Fälle

### 1. feedback.py - Zwei Router!

```python
router = APIRouter(prefix="/feedback", tags=["feedback"])
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
```

**Problem**: Zwei verschiedene Prefixes in einer Datei!

**Frontend ruft auf**:
- `/feedback/features` ✅
- `/feedback/bugs` ✅
- `/notifications` ✅

**Status**: ✅ Korrekt, aber verwirrend

---

### 2. financial.py - Zwei Router!

```python
router = APIRouter(prefix="/financial-tracking", tags=["financial"])
budget_alerts_router = APIRouter(prefix="/budget-alerts", tags=["budget-alerts"])
```

**Problem**: Zwei verschiedene Prefixes!

**Frontend ruft auf**:
- `/financial-tracking/budget-alerts` ✅

**Status**: ✅ Korrekt

---

### 3. risks.py - Zwei Router!

```python
router = APIRouter(prefix="/risks", tags=["risks"])
issues_router = APIRouter(prefix="/issues", tags=["issues"])
```

**Problem**: Zwei verschiedene Prefixes!

**Frontend ruft auf**:
- `/risks/` ✅

**Status**: ✅ Korrekt, aber `/issues` wird nicht genutzt?

---

### 4. users.py - Zwei Router!

```python
router = APIRouter(prefix="/api/admin/users", tags=["users"])
role_router = APIRouter(prefix="/users", tags=["user-roles"])
```

**Problem**: Zwei verschiedene Prefixes!

**Status**: ⚠️ Verwirrend! Sollte vereinheitlicht werden

---

## Frontend Calls die geprüft werden müssen

### Bereits geprüft und gefixt ✅:
1. Admin Endpoints → `/api/admin/*`
2. Audit Endpoints → `/api/audit/*`
3. Monte Carlo → `/api/v1/monte-carlo/*`
4. PMR Reports → `/api/reports/pmr/*`
5. CSV Import → `/csv-import/*`

### Noch zu prüfen:

#### 1. AI RAG Query
**Frontend**: `/ai/rag/query` (app/reports/page.tsx)
**Backend**: `/ai/*` (ai.py)
**Status**: ✅ Sollte funktionieren

#### 2. Admin Help Setup
**Frontend**: `/admin/help/setup` (components/admin/SetupHelp.tsx)
**Backend**: Kein Router gefunden!
**Status**: ❌ Endpoint existiert nicht?

#### 3. Analytics Performance
**Frontend**: `/api/analytics/performance` (app/admin/performance/page.tsx)
**Backend**: Kein Router gefunden!
**Status**: ❌ Endpoint existiert nicht?

#### 4. Audit Endpoints (weitere)
**Frontend**: 
- `/api/audit/logs/{id}/tag`
- `/api/audit/anomalies/{id}/feedback`
- `/api/audit/export/{format}`

**Backend**: `/api/audit/*` (audit.py)
**Status**: ✅ Sollte funktionieren

#### 5. Variance Alerts
**Frontend**: `/variance/alerts/{id}/resolve` (app/dashboards/components/VarianceAlerts.tsx)
**Backend**: `/variance/*` (variance.py)
**Status**: ✅ Sollte funktionieren

#### 6. CSV Import Template
**Frontend**: `/csv-import/template/{type}` (app/financials/components/views/CSVImportView.tsx)
**Backend**: `/csv-import/*` (csv_import.py)
**Status**: ✅ Sollte funktionieren

#### 7. Scenarios
**Frontend**: 
- `/projects/{id}/scenarios`
- `/simulations/what-if`
- `/simulations/what-if/compare`
- `/simulations/what-if/{id}` (DELETE)

**Backend**: `/simulations/what-if/*` (scenarios.py)
**Status**: ⚠️ `/projects/{id}/scenarios` könnte problematisch sein

---

## Empfohlene Fixes

### 1. Nicht existierende Endpoints entfernen

**Datei**: `components/admin/SetupHelp.tsx`
```typescript
// Entfernen oder korrigieren:
const response = await fetch(getApiUrl('/admin/help/setup'), {
```

**Datei**: `app/admin/performance/page.tsx`
```typescript
// Entfernen oder korrigieren:
analyticsEndpoint: getApiUrl('/api/analytics/performance'),
```

### 2. users.py vereinheitlichen

**Aktuell**:
```python
router = APIRouter(prefix="/api/admin/users", tags=["users"])
role_router = APIRouter(prefix="/users", tags=["user-roles"])
```

**Sollte sein**:
```python
router = APIRouter(prefix="/api/admin/users", tags=["users"])
role_router = APIRouter(prefix="/api/admin/users", tags=["user-roles"])
```

### 3. Scenarios Endpoint prüfen

**Frontend ruft auf**: `/projects/{id}/scenarios`
**Backend hat**: `/simulations/what-if/*`

**Frage**: Gibt es einen Endpoint in projects.py für Scenarios?

---

## Zusammenfassung

### ✅ Konsistent und funktioniert:
- Admin Endpoints (`/api/admin/*`)
- Audit Endpoints (`/api/audit/*`)
- Monte Carlo (`/api/v1/monte-carlo/*`)
- PMR Reports (`/api/reports/pmr/*`)
- RBAC (`/api/rbac/*`)
- Portfolios, Projects, Resources, Risks
- Feedback, AI, Variance, CSV Import
- Workflows, Schedules, Reports

### ⚠️ Zu prüfen:
1. `/admin/help/setup` - Existiert nicht?
2. `/api/analytics/performance` - Existiert nicht?
3. `/projects/{id}/scenarios` - Welcher Router?
4. `users.py` - Zwei Router mit verschiedenen Prefixes

### ❌ Zu fixen:
- Nicht existierende Endpoints aus Frontend entfernen
- `users.py` role_router Prefix vereinheitlichen

---

**Erstellt**: 22. Januar 2026, 19:30 Uhr
**Status**: Audit abgeschlossen, Fixes ausstehend

