# 🚀 Vercel Monorepo Deployment - Vollständige Anleitung

## ❌ Aktueller Fehler: "No Next.js version detected"

**Ursache**: Vercel scannt das Root-Verzeichnis statt des `frontend/` Subfolders

## ✅ LÖSUNG: Root Directory konfigurieren

### 🎯 KRITISCHER SCHRITT 1: Vercel Dashboard

1. **Gehe zu Vercel Dashboard** → Dein Projekt
2. **Settings** → **General** (NICHT Team Settings!)
3. **Root Directory** → Setze auf: `frontend`
4. **Save** klicken

⚠️ **WICHTIG**: Ohne diesen Schritt wird das Deployment fehlschlagen!

### 🔐 SCHRITT 2: Environment Variables

**Settings** → **Environment Variables** → Für **Production**, **Preview** UND **Development**:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xceyrfvxooiplbmwavlb.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo
NEXT_PUBLIC_API_URL=https://backend-six-inky-90.vercel.app
```

## 🔧 Optimierte Konfigurationsdateien

### ✅ vercel.json (Root-Verzeichnis)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next@latest",
      "config": { "distDir": ".next" }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://backend-six-inky-90.vercel.app/$1",
      "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
      }
    },
    { "src": "/(.*)", "dest": "frontend/$1" }
  ]
}
```

### ✅ frontend/next.config.ts
- `output: 'standalone'` für Vercel-Optimierung
- Korrekte `outputFileTracingRoot` für Monorepo
- API Rewrites zum Backend
- Optimierte Image-Konfiguration

### ✅ frontend/tsconfig.json
- `strict: true` aktiviert
- `strictNullChecks: true` für Type Safety
- Alle TypeScript-Errors behoben

## 🚀 Deployment Commands

### Option A: Automatisches Deployment (Empfohlen)
```bash
# Push zu GitHub (löst automatisches Deployment aus)
git add .
git commit -m "Deploy: Optimized Vercel monorepo configuration"
git push origin main
```

### Option B: Manuelles Deployment
```bash
# Aus dem Root-Verzeichnis
vercel --prod

# Oder aus dem Frontend-Verzeichnis
cd frontend
vercel --prod
```

### Environment Variables pullen
```bash
vercel env pull .env.local
```

## 🔍 Build-Validierung

### Lokaler Test (MUSS erfolgreich sein):
```bash
cd frontend
npm install
npm run build
```

**Erwartete Ausgabe**:
```
✓ Compiled successfully
✓ Finished TypeScript
✓ Collecting page data
✓ Generating static pages
```

## 📊 Post-Deployment Checklist

### ✅ Funktionalitäts-Tests
- [ ] **Homepage lädt** (keine 404/500 Errors)
- [ ] **Authentication** funktioniert (Login/Signup)
- [ ] **Dashboards** laden Daten korrekt
- [ ] **API Calls** zum Backend erfolgreich
- [ ] **Charts** (Recharts) rendern korrekt

### ✅ Performance-Tests
- [ ] **Lighthouse Score** > 90
- [ ] **Load Time** < 3 Sekunden
- [ ] **Images** optimiert geladen
- [ ] **No Console Errors**

### ✅ Authentication-Tests
- [ ] **Supabase Integration** funktioniert
- [ ] **JWT Tokens** werden korrekt verwaltet
- [ ] **Session Persistence** funktioniert
- [ ] **Logout** funktioniert

## 🛠️ Troubleshooting

### ❌ "No Next.js version detected"
**Lösung**: Root Directory auf `frontend` setzen (Schritt 1)

### ❌ Environment Variables nicht verfügbar
**Lösung**: In Vercel Dashboard für alle Environments setzen

### ❌ Build Failures
**Lösung**: 
1. Lokal `npm run build` testen
2. TypeScript Errors beheben
3. Dependencies aktualisieren

### ❌ API Calls fehlschlagen
**Lösung**:
1. CORS Headers prüfen
2. Backend URL validieren
3. Network Tab in Browser prüfen

### ❌ Authentication Errors
**Lösung**:
1. AuthDebugger auf Login-Seite nutzen
2. Supabase Keys überprüfen
3. Environment Variables validieren

## 🎯 Monorepo-spezifische Konfiguration

### Warum Root Directory setzen?
- Vercel scannt standardmäßig das Root-Verzeichnis nach `package.json`
- In Monorepos liegt die Next.js App im Subfolder
- Root Directory teilt Vercel mit, wo die App liegt

### Warum vercel.json im Root?
- Definiert Build-Konfiguration für das gesamte Projekt
- Routet API-Calls zum Backend
- Konfiguriert CORS und Security Headers

### Backend Integration
- Backend läuft separat auf: `https://backend-six-inky-90.vercel.app`
- API-Calls werden über `/api/*` geroutet
- CORS ist korrekt konfiguriert

## 🎉 Erfolgreiche Deployment-Indikatoren

### ✅ Vercel Dashboard
- Build Status: "Ready"
- Deployment Zeit: < 2 Minuten
- Keine Error Logs

### ✅ Live Application
- Alle Seiten laden korrekt
- Authentication funktioniert
- Dashboards zeigen Daten
- Keine JavaScript Errors

### ✅ Performance
- Lighthouse Score > 90
- Fast loading times
- Optimized images
- No console errors

---

## 🚀 DEPLOYMENT BEREIT!

**Nach dem Setzen der Root Directory auf `frontend` sollte das Deployment erfolgreich sein!**

Nächste Schritte:
1. Root Directory setzen
2. Environment Variables hinzufügen  
3. Deployment auslösen
4. Funktionalität testen