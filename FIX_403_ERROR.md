# 403 Forbidden Error beheben - 2 Minuten Fix

## Problem

```
INFO: 127.0.0.1:59193 - "GET /admin/performance/stats HTTP/1.1" 403 Forbidden
```

Ihr Benutzer hat keine Admin-Berechtigung.

## Lösung (2 Schritte)

### Schritt 1: Supabase SQL Editor öffnen

1. Gehen Sie zu https://supabase.com/dashboard
2. Wählen Sie Ihr Projekt
3. Klicken Sie auf **"SQL Editor"** (linke Sidebar)
4. Klicken Sie auf **"New Query"**

### Schritt 2: Dieses SQL ausführen

Kopieren Sie dieses SQL und klicken Sie auf **"Run"**:

```sql
-- Admin-Rolle erstellen
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

-- Admin-Rolle zu Ihrem Benutzer hinzufügen
INSERT INTO user_roles (user_id, role_id)
VALUES (
  'bf1b1732-2449-4987-9fdb-fefa2a93b816',
  (SELECT id FROM roles WHERE name = 'admin')
)
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Überprüfen
SELECT 
  ur.user_id,
  au.email,
  r.name as role_name
FROM user_roles ur
JOIN auth.users au ON ur.user_id = au.id
JOIN roles r ON ur.role_id = r.id
WHERE ur.user_id = 'bf1b1732-2449-4987-9fdb-fefa2a93b816';
```

### Schritt 3: Dashboard neu laden

1. Öffnen Sie http://localhost:3000/admin/performance
2. Drücken Sie **Cmd+Shift+R** (Mac) oder **Ctrl+Shift+R** (Windows)
3. Oder verwenden Sie Inkognito-Modus

**Fertig!** Das Dashboard sollte jetzt echte Daten anzeigen. 🎉

## Wenn es nicht funktioniert

### Fehler: "table roles does not exist"

Die Tabellen müssen erstellt werden:

```sql
-- Rollen-Tabelle erstellen
CREATE TABLE IF NOT EXISTS roles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
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

Dann führen Sie das SQL aus Schritt 2 erneut aus.

### Fehler: "Row Level Security policy violation"

RLS-Policies erstellen:

```sql
-- Policies für roles Tabelle
CREATE POLICY "Allow service role to manage roles"
ON roles FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow authenticated users to read roles"
ON roles FOR SELECT
TO authenticated
USING (true);

-- Policies für user_roles Tabelle
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

Dann führen Sie das SQL aus Schritt 2 erneut aus.

### Immer noch 403 Fehler

1. **Backend neu starten** (Cache leeren):
   ```bash
   cd backend && ./start-dev.sh
   ```

2. **Überprüfen Sie die Zuweisung in Supabase:**
   ```sql
   SELECT * FROM user_roles WHERE user_id = 'bf1b1732-2449-4987-9fdb-fefa2a93b816';
   ```
   
   Sie sollten eine Zeile sehen mit Ihrer User ID und einer Role ID.

3. **Browser-Cache leeren:**
   - Cmd+Shift+R (Mac) oder Ctrl+Shift+R (Windows)
   - Oder Inkognito-Modus verwenden

## Alternative: Development Mode

Wenn Sie die Datenbank nicht ändern möchten, können Sie temporär Development Mode verwenden:

**Datei bearbeiten:** `backend/auth/rbac.py`

Finden Sie diese Zeile (ca. Zeile 280):
```python
if user_id == "00000000-0000-0000-0000-000000000001":
```

Ändern Sie zu:
```python
if user_id in ["00000000-0000-0000-0000-000000000001", "bf1b1732-2449-4987-9fdb-fefa2a93b816"]:
```

Backend neu starten:
```bash
cd backend && ./start-dev.sh
```

**Das ist ein Workaround für Entwicklung. Für Production verwenden Sie die SQL-Lösung!**

## Zusammenfassung

**Schnellste Lösung:**
1. Supabase SQL Editor öffnen
2. SQL aus Schritt 2 ausführen
3. Dashboard neu laden

**Fertig in 2 Minuten!** 🚀
