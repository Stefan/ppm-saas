# Backend Starten - Schnellanleitung

## ✅ GELÖST: Backend läuft jetzt!

Das Backend wurde erfolgreich gestartet und läuft auf Port 8000.

**Aktuelles Problem**: Dashboard zeigt Mock-Daten wegen fehlender Admin-Berechtigungen (403 Forbidden).
Siehe `RESTART_DEV_SERVER.md` für Details zur Berechtigungskonfiguration.

---

## Original-Problem
Das Performance Dashboard zeigte keine Daten oder 500 Errors, weil das Backend nicht lief.

## Lösung: Backend Starten

### Option 1: Schnellstart (Empfohlen)

```bash
# Terminal 1: Backend starten
cd backend
python -m uvicorn main:app --reload --port 8000
```

```bash
# Terminal 2: Frontend starten (separates Terminal)
npm run dev
```

### Option 2: Mit Virtual Environment

```bash
# Terminal 1: Backend mit venv
cd backend
source .venv/bin/activate  # macOS/Linux
# ODER
.venv\Scripts\activate     # Windows

python -m uvicorn main:app --reload --port 8000
```

```bash
# Terminal 2: Frontend
npm run dev
```

### Option 3: Background Process

```bash
# Backend im Hintergrund starten
cd backend
nohup python -m uvicorn main:app --port 8000 > backend.log 2>&1 &

# Frontend normal starten
npm run dev
```

## Überprüfen ob Backend läuft

```bash
# Test 1: Health Check
curl http://localhost:8000/health

# Sollte zurückgeben:
# {"status":"healthy","timestamp":"..."}

# Test 2: Performance Stats (ohne Auth)
curl http://localhost:8000/admin/performance/stats

# Sollte 401 Unauthorized zurückgeben (das ist OK - bedeutet Backend läuft)
```

## Was Sie sehen sollten

### Backend Terminal:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
✅ Performance tracking middleware enabled
```

### Frontend Terminal:
```
▲ Next.js 16.1.1
- Local:        http://localhost:3000
- Network:      http://192.168.1.x:3000

✓ Ready in 2.3s
```

## Troubleshooting

### "Port 8000 already in use"

```bash
# Finden Sie den Prozess
lsof -i :8000

# Beenden Sie ihn
kill -9 <PID>

# Oder verwenden Sie einen anderen Port
python -m uvicorn main:app --reload --port 8001
# Dann in .env.local: NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
```

### "Module not found"

```bash
cd backend
pip install -r requirements.txt
```

### "Database connection failed"

Das ist OK für lokale Entwicklung. Das Backend läuft trotzdem und gibt Mock-Daten zurück.

### Performance Dashboard zeigt immer noch keine Daten

1. **Überprüfen Sie, ob Backend läuft:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Überprüfen Sie die Browser Console:**
   - Öffnen Sie DevTools (F12)
   - Gehen Sie zum Console Tab
   - Suchen Sie nach Fehlern

3. **Überprüfen Sie die Network Tab:**
   - Öffnen Sie DevTools (F12)
   - Gehen Sie zum Network Tab
   - Laden Sie die Seite neu
   - Suchen Sie nach `/api/admin/performance/stats`
   - Prüfen Sie den Response Header `X-Data-Source`
     - `backend-real` = Backend läuft ✅
     - `fallback-mock` = Backend läuft nicht ⚠️

4. **Generieren Sie Traffic:**
   ```bash
   # Machen Sie ein paar API Requests
   curl http://localhost:8000/projects
   curl http://localhost:8000/portfolios
   curl http://localhost:8000/health
   
   # Dann laden Sie das Dashboard neu
   ```

## Fallback-Modus

Wenn das Backend nicht läuft, zeigt das Dashboard jetzt **Fallback-Daten** an:
- Total Requests: 0
- Total Errors: 0
- Slow Queries: 0
- Health Status: Healthy

**Das ist OK für Entwicklung**, aber für echte Daten müssen Sie das Backend starten.

## Automatisches Starten

### Mit npm script (package.json):

```json
{
  "scripts": {
    "dev": "next dev",
    "dev:backend": "cd backend && python -m uvicorn main:app --reload --port 8000",
    "dev:all": "concurrently \"npm run dev:backend\" \"npm run dev\""
  }
}
```

Dann:
```bash
npm run dev:all
```

### Mit Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    command: uvicorn main:app --host 0.0.0.0 --port 8000
  
  frontend:
    build: .
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_BACKEND_URL=http://backend:8000
```

Dann:
```bash
docker-compose up
```

## Zusammenfassung

**Minimale Schritte:**

1. Terminal 1: `cd backend && python -m uvicorn main:app --reload --port 8000`
2. Terminal 2: `npm run dev`
3. Browser: `http://localhost:3000/admin/performance`
4. Generieren Sie Traffic: Machen Sie ein paar API Requests
5. Laden Sie das Dashboard neu

**Das Dashboard sollte jetzt echte Daten anzeigen!** 🎉
