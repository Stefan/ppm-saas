# Admin-Rolle einrichten - Schritt für Schritt

## Problem

Das Backend läuft, aber Sie bekommen **403 Forbidden** Fehler, weil Ihr Benutzer keine Admin-Berechtigung hat.

```
INFO: 127.0.0.1:59193 - "GET /admin/performance/stats HTTP/1.1" 403 Forbidden
```

Ihr Benutzer: `bf1b1732-2449-4987-9fdb-fefa2a93b816`

## Lösung: Admin-Rolle in Supabase hinzufügen

### Option 1: SQL in Supabase ausführen (Empfohlen)

1. **Öffnen Sie Supabase Dashboard**
   - Gehen Sie zu https://supabase.com/dashboard
   - Wählen Sie Ihr Projekt

2. **Öffnen Sie SQL Editor**
   - Klicken Sie auf "SQL Editor" in der linken Sidebar
   - Klicken Sie auf "New Query"

3. **Führen Sie dieses SQL aus:**

```sql
-- 1. Admin-Rolle erstellen (falls nicht vorhanden)
-- WICHTIG: permissions ist JSONB, nicht TEXT[]
INSERT INTO roles (name, description, permissions)
VALUES (
  'admin',
  'Full system administrator with all permissions',
  '["portfolio_create", "portfolio_read", "portfolio_update", "portfolio_delete",
    "project_create", "project_read", "project_update", "project_delete",
    "resource_create", "resource_read", "resource_update", "resource_delete",
    "financial_read", "financial_create", "financial_update", "financial_delete",
    "user_manage", "role_manage", "admin_read", "admin_update", "system_admin",
    "pmr_create", "pmr_read", "pmr_update", "pmr_delete", "pmr_approve",
    "audit:read", "audit:export"]'::jsonb
)
ON CONFLICT (name) DO UPDATE
SET permissions = EXCLUDED.permissions;

-- 2. Admin-Rolle zu Ihrem Benutzer hinzufügen
INSERT INTO user_roles (user_id, role_id)
VALUES (
  'bf1b1732-2449-4987-9fdb-fefa2a93b816',  -- Ihre User ID
  (SELECT id FROM roles WHERE name = 'admin')
)
ON CONFLICT (user_id, role_id) DO NOTHING;

-- 3. Überprüfen
SELECT 
  ur.user_id,
  au.email,
  r.name as role_name
FROM user_roles ur
JOIN auth.users au ON ur.user_id = au.id
JOIN roles r ON ur.role_id = r.id
WHERE ur.user_id = 'bf1b1732-2449-4987-9fdb-fefa2a93b816';
```

4. **Klicken Sie auf "Run"**

5. **Überprüfen Sie das Ergebnis**
   - Sie sollten eine Zeile mit Ihrer E-Mail und "admin" als Rolle sehen

### Option 2: RLS-Policies anpassen

Wenn Sie einen "Row Level Security" Fehler bekommen:

```sql
-- RLS-Policies für roles und user_roles Tabellen erstellen
-- Führen Sie dies in Supabase SQL Editor aus

-- Policy für roles Tabelle
CREATE POLICY "Allow service role to manage roles"
ON roles FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow authenticated users to read roles"
ON roles FOR SELECT
TO authenticated
USING (true);

-- Policy für user_roles Tabelle
CREATE POLICY "Allow service role to manage user roles"
ON user_roles FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow users to read their own roles"
ON user_roles FOR SELECT
TO authenticated
USING (auth.uid() = user_id);
```

Dann führen Sie das SQL aus Option 1 erneut aus.

### Option 3: Development Mode verwenden (Temporär)

Wenn Sie die Datenbank nicht ändern möchten, können Sie temporär den Development Mode verwenden:

**Backend-Code ändern** (`backend/auth/dependencies.py`):

```python
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Extract user from JWT token with development mode fallback"""
    try:
        if not credentials:
            # Development mode: Use default user
            return {"user_id": "00000000-0000-0000-0000-000000000001", "email": "dev@example.com"}
        
        token = credentials.credentials
        payload = jwt.decode(token, options={"verify_signature": False})
        
        user_id = payload.get("sub")
        
        # TEMPORARY: Give admin permissions to your user
        if user_id == "bf1b1732-2449-4987-9fdb-fefa2a93b816":
            print(f"🔧 Development mode: Granting admin permissions to user {user_id}")
            return {"user_id": user_id, "email": payload.get("email", "dev@example.com")}
        
        # ... rest of the code
```

Dann Backend neu starten:
```bash
cd backend && ./start-dev.sh
```

## Nach der Einrichtung

### 1. Backend neu starten (optional)

```bash
cd backend
./start-dev.sh
```

### 2. Frontend neu laden

- Öffnen Sie http://localhost:3000/admin/performance
- Drücken Sie Cmd+Shift+R (Mac) oder Ctrl+Shift+R (Windows) für Hard Reload
- Oder verwenden Sie Inkognito-Modus

### 3. Überprüfen

Das Dashboard sollte jetzt echte Daten anzeigen!

Überprüfen Sie in Browser DevTools → Network Tab:
- Request zu `/api/admin/performance/stats`
- Response Header: `X-Data-Source: backend-real` ✅

## Troubleshooting

### Immer noch 403 Forbidden

1. **Überprüfen Sie die Rollenzuweisung in Supabase:**
   ```sql
   SELECT * FROM user_roles WHERE user_id = 'bf1b1732-2449-4987-9fdb-fefa2a93b816';
   ```

2. **Überprüfen Sie die Admin-Rolle:**
   ```sql
   SELECT * FROM roles WHERE name = 'admin';
   ```

3. **Löschen Sie den RBAC-Cache:**
   - Backend neu starten: `cd backend && ./start-dev.sh`
   - Der Cache wird automatisch geleert

### "Table roles does not exist"

Die Tabellen müssen erstellt werden:

```sql
-- Rollen-Tabelle erstellen
CREATE TABLE IF NOT EXISTS roles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  permissions TEXT[] NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Benutzer-Rollen-Tabelle erstellen
CREATE TABLE IF NOT EXISTS user_roles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, role_id)
);

-- Indizes erstellen
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
```

### "Row Level Security policy violation"

Führen Sie die RLS-Policies aus Option 2 aus.

## Zusammenfassung

**Schnellste Lösung:**

1. Öffnen Sie Supabase SQL Editor
2. Führen Sie das SQL aus Option 1 aus
3. Laden Sie das Dashboard neu

**Das sollte funktionieren!** 🚀

Wenn Sie Probleme haben:
- Siehe `AUTH_SETUP_GUIDE.md` für vollständige Details
- Oder verwenden Sie Option 3 (Development Mode) als Workaround
