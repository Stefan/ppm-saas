# 🚀 Vercel CLI Commands - PPM SaaS Monorepo

## 📋 Deployment Commands

### 🎯 Production Deployment

#### Aus Root-Verzeichnis:
```bash
# Automatisches Deployment via Git
git add .
git commit -m "Deploy: Production ready"
git push origin main

# Manuelles Deployment
vercel --prod
```

#### Aus Frontend-Verzeichnis:
```bash
cd frontend
vercel --prod
```

### 🔧 Development & Preview

#### Preview Deployment:
```bash
# Aus Root
vercel

# Aus Frontend
cd frontend
vercel
```

#### Development Server:
```bash
cd frontend
npm run dev
```

## 🔐 Environment Variables

### Environment Variables pullen:
```bash
# Alle Environments
vercel env pull

# Spezifisches Environment
vercel env pull .env.local --environment=production
vercel env pull .env.preview --environment=preview
vercel env pull .env.development --environment=development
```

### Environment Variables setzen:
```bash
# Interaktiv
vercel env add

# Direkt
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add NEXT_PUBLIC_API_URL production
```

### Environment Variables auflisten:
```bash
vercel env ls
```

## 🔍 Debugging & Logs

### Deployment Logs anzeigen:
```bash
vercel logs
vercel logs --follow
```

### Build Logs:
```bash
vercel logs [deployment-url]
```

### Projekt-Informationen:
```bash
vercel ls
vercel inspect
```

## 🏗️ Build & Test Commands

### Lokaler Build-Test:
```bash
cd frontend
npm install
npm run build
npm run start
```

### TypeScript Check:
```bash
cd frontend
npx tsc --noEmit
```

### Linting:
```bash
cd frontend
npm run lint
```

## 🔄 Re-Deploy Strategien

### 1. Git-basiertes Re-Deploy (Empfohlen):
```bash
# Änderungen machen
git add .
git commit -m "Fix: Update configuration"
git push origin main
# → Automatisches Deployment
```

### 2. Force Re-Deploy:
```bash
vercel --prod --force
```

### 3. Rollback zu vorheriger Version:
```bash
# Liste Deployments
vercel ls

# Promote spezifisches Deployment
vercel promote [deployment-url]
```

## 🎯 Monorepo-spezifische Commands

### Root Directory validieren:
```bash
# Zeigt aktuelle Konfiguration
vercel inspect

# Project Settings anzeigen
vercel project ls
```

### Build-Konfiguration testen:
```bash
# Simuliert Vercel Build
cd frontend
npm run build

# Mit Vercel CLI
vercel build
```

## 🚨 Troubleshooting Commands

### Bei "No Next.js version detected":
```bash
# 1. Root Directory prüfen
vercel inspect

# 2. Lokalen Build testen
cd frontend && npm run build

# 3. Force redeploy
vercel --prod --force
```

### Bei Environment Variable Problemen:
```bash
# Environment Variables prüfen
vercel env ls

# Lokale .env.local prüfen
cat frontend/.env.local

# Environment Variables neu pullen
vercel env pull .env.local
```

### Bei Build Failures:
```bash
# Detaillierte Logs
vercel logs --follow

# Lokalen Build debuggen
cd frontend
npm run build --verbose

# Dependencies prüfen
npm audit
npm update
```

## 📊 Monitoring Commands

### Performance Monitoring:
```bash
# Deployment Status
vercel ls

# Live Logs
vercel logs --follow

# Analytics (falls aktiviert)
vercel analytics
```

### Health Check:
```bash
# Deployment testen
curl -I https://deine-domain.vercel.app

# API Endpoint testen
curl https://deine-domain.vercel.app/api/health
```

## 🔧 Konfiguration Commands

### Projekt-Konfiguration:
```bash
# Vercel-Projekt verlinken
vercel link

# Konfiguration anzeigen
vercel inspect

# Domains verwalten
vercel domains ls
vercel domains add example.com
```

### Team & Collaboration:
```bash
# Team-Projekte auflisten
vercel teams ls

# Projekt zu Team hinzufügen
vercel teams add
```

---

## 🎯 Schnell-Referenz

### Häufigste Commands:
```bash
# Production Deploy
vercel --prod

# Environment Variables pullen
vercel env pull .env.local

# Logs anzeigen
vercel logs --follow

# Lokaler Build-Test
cd frontend && npm run build
```

### Bei Problemen:
```bash
# 1. Lokalen Build testen
cd frontend && npm run build

# 2. Environment Variables prüfen
vercel env ls

# 3. Force redeploy
vercel --prod --force

# 4. Logs checken
vercel logs
```