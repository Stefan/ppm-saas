# 📋 Vercel Deployment Checklist

## Vor dem Deployment

### ✅ Lokale Tests
- [ ] `cd frontend && npm run build` läuft erfolgreich
- [ ] `cd frontend && npm run dev` startet ohne Errors
- [ ] Alle TypeScript Errors behoben
- [ ] Environment Variables in `.env.local` gesetzt

### ✅ GitHub Repository
- [ ] Alle Änderungen committed und gepusht
- [ ] Repository ist öffentlich oder Vercel hat Zugriff
- [ ] Monorepo-Struktur korrekt (root/frontend/backend)

## Vercel Dashboard Setup

### 🎯 Projekt Settings
- [ ] **Root Directory**: `frontend` (KRITISCH!)
- [ ] **Framework Preset**: Next.js
- [ ] **Build Command**: `npm run build` (automatisch erkannt)
- [ ] **Output Directory**: `.next` (automatisch erkannt)

### 🔐 Environment Variables
Alle für **Production**, **Preview** UND **Development** setzen:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xceyrfvxooiplbmwavlb.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo
NEXT_PUBLIC_API_URL=https://backend-six-inky-90.vercel.app
```

## Deployment Ausführen

### Option 1: Auto-Deploy (Empfohlen)
```bash
git add .
git commit -m "Deploy: Production ready configuration"
git push origin main
```

### Option 2: Manual Deploy
```bash
vercel --prod
```

## Nach dem Deployment

### 🧪 Funktionalitäts-Tests
- [ ] **Homepage lädt**: Keine 404 oder 500 Errors
- [ ] **Authentication**: Login/Signup funktioniert
- [ ] **Dashboards**: Daten werden geladen und angezeigt
- [ ] **API Calls**: Backend-Verbindung funktioniert
- [ ] **Charts**: Recharts rendern korrekt

### 🔍 Debug Tools nutzen
- [ ] AuthDebugger auf Login-Seite testen
- [ ] "Run Diagnostics" - Environment Variables OK?
- [ ] "Test Direct API" - Supabase Verbindung OK?

### 🚨 Error Checking
- [ ] **Browser Console**: Keine JavaScript Errors
- [ ] **Network Tab**: Alle API Calls erfolgreich (200/201)
- [ ] **Vercel Logs**: Keine Build oder Runtime Errors

### 🎯 Performance Check
- [ ] **Lighthouse Score**: > 90 Performance
- [ ] **Load Time**: < 3 Sekunden
- [ ] **Images**: Optimiert geladen
- [ ] **Fonts**: Korrekt geladen

## Häufige Probleme & Lösungen

### ❌ "No Next.js version detected"
**Lösung**: Root Directory auf `frontend` setzen

### ❌ Environment Variables nicht verfügbar
**Lösung**: In Vercel Dashboard für alle Environments setzen

### ❌ API Calls fehlschlagen
**Lösung**: NEXT_PUBLIC_API_URL überprüfen, CORS Headers checken

### ❌ Authentication Errors
**Lösung**: AuthDebugger nutzen, Supabase Keys überprüfen

### ❌ Build Failures
**Lösung**: Lokal `npm run build` testen, TypeScript Errors fixen

## 🎉 Deployment Erfolgreich!

Wenn alle Checkboxen ✅ sind:
- [ ] **AuthDebugger entfernen** (Production cleanup)
- [ ] **Custom Domain** einrichten (optional)
- [ ] **Analytics** einrichten (optional)
- [ ] **Monitoring** einrichten (optional)

---

**Deployment Status**: 🚀 READY FOR PRODUCTION