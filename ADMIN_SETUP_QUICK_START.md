# Admin Setup - Schnellstart

## ✅ Gute Nachrichten!

**Development Mode ist bereits aktiv** - Sie brauchen nichts zu konfigurieren!

## Wie es funktioniert

Das Backend hat einen eingebauten Development Mode, der automatisch Admin-Berechtigungen vergibt:

```
🔧 Development Mode: ACTIVE
💡 Default User ID: 00000000-0000-0000-0000-000000000001
✅ Automatische Admin-Berechtigungen
```

## Was bedeutet das?

- ✅ **Keine Authentifizierung erforderlich** für lokale Entwicklung
- ✅ **Automatische Admin-Rechte** für alle Requests
- ✅ **Performance Dashboard funktioniert** ohne Login
- ✅ **Alle Admin-Endpunkte zugänglich**

## Testen Sie es jetzt!

### 1. Backend läuft bereits

```bash
# Backend ist bereits gestartet auf Port 8000
curl http://localhost:8000/health
# Sollte zurückgeben: {"status":"healthy",...}
```

### 2. Frontend starten

```bash
# In einem neuen Terminal
npm run dev
```

### 3. Dashboard öffnen

```
http://localhost:3000/admin/performance
```

Das Dashboard sollte jetzt funktionieren! 🎉

## Wenn Sie echte Benutzer verwenden möchten

### Option 1: Auth-Status überprüfen

```bash
cd backend
python3 scripts/check_auth_status.py
```

Das zeigt:
- Alle Benutzer in Supabase
- Alle Rollen
- Environment-Konfiguration
- Development Mode Status

### Option 2: Admin-Rolle zu echtem Benutzer hinzufügen

```bash
cd backend
python3 scripts/add_admin_user.py ihre-email@example.com
```

Das Skript:
1. Findet Ihren Benutzer in Supabase
2. Erstellt die Admin-Rolle (falls nicht vorhanden)
3. Weist die Admin-Rolle Ihrem Benutzer zu
4. Zeigt alle Ihre Rollen an

### Option 3: Mit User ID

```bash
python3 scripts/add_admin_user.py --user-id bf1b1732-2449-4987-9fdb-fefa2a93b816
```

## Vercel Auth deaktivieren

Wenn Sie Vercel Auth verwenden und zu Supabase Auth wechseln möchten:

### Vollständige Anleitung

Siehe **`AUTH_SETUP_GUIDE.md`** für:
- Frontend Auth-Integration
- Supabase Auth Provider Setup
- Login-Komponenten
- Environment Variables
- Datenbank-Schema

### Kurz-Version

1. **Supabase Auth Provider hinzufügen**
   ```typescript
   // app/providers/AuthProvider.tsx
   import { SessionContextProvider } from '@supabase/auth-helpers-react'
   ```

2. **Environment Variables setzen**
   ```bash
   # .env.local
   NEXT_PUBLIC_SUPABASE_URL=https://ihre-project-id.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=ihre-anon-key
   ```

3. **Login-Komponente erstellen**
   ```typescript
   const { data, error } = await supabase.auth.signInWithPassword({
     email, password
   })
   ```

## Aktueller Status

```
✅ Backend läuft auf Port 8000
✅ Development Mode aktiv
✅ Automatische Admin-Berechtigungen
✅ Keine Auth-Konfiguration erforderlich
```

## Nächste Schritte

### Für lokale Entwicklung (jetzt)

**Nichts zu tun!** Development Mode ist aktiv und funktioniert.

### Für Production (später)

1. Erstellen Sie Rollen in der Datenbank
2. Fügen Sie Admin-Benutzer hinzu
3. Implementieren Sie Frontend Auth
4. Deaktivieren Sie Development Mode

## Troubleshooting

### Dashboard zeigt immer noch Mock-Daten

**Überprüfen Sie:**

1. Backend läuft?
   ```bash
   curl http://localhost:8000/health
   ```

2. Frontend verbindet sich mit Backend?
   ```bash
   # In .env.local
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

3. Browser DevTools → Network Tab
   - Suchen Sie nach `/api/admin/performance/stats`
   - Response Header sollte sein: `X-Data-Source: backend-real`

### 403 Forbidden Fehler

**Das sollte nicht passieren im Development Mode!**

Wenn doch:
1. Überprüfen Sie `backend/auth/dependencies.py`
2. Stellen Sie sicher, dass Development-Fallback aktiv ist
3. Starten Sie Backend neu: `cd backend && ./start-dev.sh`

### "Cannot access admin API"

Das ist normal! Sie brauchen keinen Admin API Zugriff für Development Mode.

## Hilfreiche Befehle

```bash
# Auth-Status überprüfen
cd backend && python3 scripts/check_auth_status.py

# Admin-Rolle hinzufügen
cd backend && python3 scripts/add_admin_user.py email@example.com

# Backend neu starten
cd backend && ./start-dev.sh

# Backend-Logs anzeigen
# (In Kiro: Process Manager → Backend Process → View Output)

# Health Check
curl http://localhost:8000/health

# Performance Stats (sollte funktionieren ohne Auth)
curl http://localhost:8000/admin/performance/stats
```

## Zusammenfassung

| Feature | Status | Notizen |
|---------|--------|---------|
| Backend | ✅ Läuft | Port 8000 |
| Development Mode | ✅ Aktiv | Auto Admin-Rechte |
| Auth erforderlich | ❌ Nein | Für lokale Entwicklung |
| Dashboard | ✅ Sollte funktionieren | Ohne Login |
| Admin-Endpunkte | ✅ Zugänglich | Ohne Auth |

**Sie sind bereit! Das Dashboard sollte jetzt funktionieren.** 🚀

Wenn Sie Probleme haben:
1. Überprüfen Sie `AUTH_SETUP_GUIDE.md` für Details
2. Führen Sie `python3 scripts/check_auth_status.py` aus
3. Überprüfen Sie Backend-Logs in Kiro Process Manager
