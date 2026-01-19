# RAG Implementation Status

## Aktueller Stand (19. Januar 2026 - Update 2)

### ✅ Vollständig Implementiert

1. **RAG Agent Klasse** (`backend/ai_agents.py`)
   - `RAGReporterAgent` vollständig implementiert
   - Embedding-Generierung mit OpenAI ODER lokalen Modellen (sentence-transformers)
   - Vector-Similarity-Search
   - Conversation-Storage
   - Logging und Monitoring
   - **NEU**: Unterstützung für lokale Embeddings (all-MiniLM-L6-v2, 384 Dimensionen)

2. **API Endpoint** (`backend/routers/ai.py`)
   - POST `/ai/rag/query` mit Pydantic Request Body
   - Integration mit RAGReporterAgent
   - Fallback zu Mock-Response wenn kein API-Key vorhanden
   - Proper Error Handling

3. **Frontend Integration** (`app/reports/page.tsx`)
   - Chat-Interface für RAG-Queries
   - Error Recovery mit Retry-Logik
   - PMR-Mode für Report-spezifische Queries
   - Source-Anzeige und Confidence-Scores

4. **Content Indexing Service** (`backend/services/content_indexing_service.py`)
   - Vollständig implementiert
   - Batch-Processing mit Rate-Limiting
   - Indexierung von Projects, Portfolios, Resources, Risks, Issues
   - Error-Handling und Logging
   - Organization-Filtering

5. **Lokale Embeddings**
   - sentence-transformers installiert
   - all-MiniLM-L6-v2 Modell (384 Dimensionen)
   - USE_LOCAL_EMBEDDINGS=true in .env konfiguriert
   - Funktioniert ohne OpenAI API Key

### ⚠️ Teilweise Implementiert / Blockiert

1. **Vector Database**
   - ✅ Code verwendet pgvector für Similarity Search
   - ✅ Database Migration 026 erstellt für `embeddings` Tabelle (1536 Dimensionen)
   - ❌ **BLOCKIERT**: Migration 027 muss manuell angewendet werden (384 Dimensionen)
   - ✅ Fallback-Logik vorhanden für fehlende Vector-DB
   - **Problem**: Datenbank-Spalte ist auf 1536 Dimensionen konfiguriert, aber lokales Modell generiert 384 Dimensionen

2. **Content Indexing**
   - ✅ Code zum Speichern von Embeddings vorhanden
   - ✅ Indexing-Service vollständig implementiert
   - ❌ **BLOCKIERT**: Kann nicht ausgeführt werden wegen Dimensions-Mismatch
   - ❌ **FEHLT**: Automatisches Indexing von Projekten/Portfolios/Ressourcen (nach Migration)
   - ❌ **FEHLT**: Background-Job für regelmäßiges Re-Indexing

### ❌ Blockiert - Manuelle Aktion Erforderlich

1. **Database Dimension Update** ⚠️ **KRITISCH**
   ```sql
   -- MUSS in Supabase SQL Editor ausgeführt werden:
   -- Siehe: backend/migrations/027_update_embedding_dimension.sql
   
   -- Kurzversion:
   DROP INDEX IF EXISTS embeddings_vector_idx;
   ALTER TABLE embeddings ALTER COLUMN embedding TYPE vector(384);
   CREATE INDEX embeddings_vector_idx ON embeddings 
   USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
   ```
   
   **Warum**: Lokales Modell (all-MiniLM-L6-v2) generiert 384-dimensionale Vektoren,
   aber Datenbank erwartet 1536 Dimensionen (OpenAI ada-002).
   
   **Wo ausführen**:
   1. Supabase Dashboard → SQL Editor
   2. Oder: `psql $DATABASE_URL < backend/migrations/027_update_embedding_dimension.sql`

2. **Initial Content Indexing**
   ```bash
   # Nach Migration 027:
   cd orka-ppm
   python3 backend/services/content_indexing_service.py
   ```
   
   **Erwartet**: 5 Projekte werden indexiert (aktuell 0 wegen Dimensions-Fehler)
   ```sql
   -- Benötigt:
   CREATE EXTENSION IF NOT EXISTS vector;
   
   CREATE TABLE embeddings (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     content_type TEXT NOT NULL,
     content_id TEXT NOT NULL,
     content_text TEXT NOT NULL,
     embedding vector(1536), -- OpenAI ada-002 dimension
     metadata JSONB,
     created_at TIMESTAMPTZ DEFAULT NOW(),
     updated_at TIMESTAMPTZ DEFAULT NOW(),
     UNIQUE(content_type, content_id)
   );
   
   CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
   ```

2. **RPC Function für Vector Search**
   ```sql
   CREATE OR REPLACE FUNCTION vector_similarity_search(
     query_embedding vector(1536),
     content_types text[],
     similarity_limit int
   )
   RETURNS TABLE (
     content_type text,
     content_id text,
     content_text text,
     metadata jsonb,
     similarity_score float
   ) AS $$
   BEGIN
     RETURN QUERY
     SELECT 
       e.content_type,
       e.content_id,
       e.content_text,
       e.metadata,
       (1 - (e.embedding <=> query_embedding)) as similarity_score
     FROM embeddings e
     WHERE (content_types IS NULL OR e.content_type = ANY(content_types))
     ORDER BY e.embedding <=> query_embedding
     LIMIT similarity_limit;
   END;
   $$ LANGUAGE plpgsql;
   ```

3. **Content Indexing Service**
   - Background-Worker zum Indexieren neuer/geänderter Inhalte
   - Webhook/Trigger bei Projekt-/Portfolio-Änderungen
   - Batch-Indexing für bestehende Daten

4. **API Key Configuration**
   - OPENAI_API_KEY muss in `.env` gesetzt werden
   - Optional: OPENAI_BASE_URL für alternative Providers (Grok, etc.)
   - Optional: OPENAI_MODEL und OPENAI_EMBEDDING_MODEL

## Nächste Schritte

### Priorität 1: Database Setup
1. Migration erstellen für `embeddings` Tabelle
2. pgvector Extension aktivieren
3. RPC Function für Vector Search erstellen
4. Indexes für Performance optimieren

### Priorität 2: Content Indexing
1. Script zum initialen Indexing aller Projekte/Portfolios
2. Background-Job für automatisches Re-Indexing
3. Webhook-Integration für Echtzeit-Updates

### Priorität 3: API Key Setup
1. OPENAI_API_KEY in Production-Environment setzen
2. Dokumentation für API-Key-Setup erstellen
3. Health-Check für AI-Services implementieren

### Priorität 4: Testing & Monitoring
1. Integration-Tests für RAG-Queries
2. Performance-Monitoring für Embedding-Generierung
3. Quality-Metrics für RAG-Responses

## Verwendung (Aktuell)

### Mit API Key (Volle Funktionalität)
```bash
# Backend .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4  # optional
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002  # optional
```

### Ohne API Key (Mock-Modus)
- System gibt Mock-Responses zurück
- Warnung wird im Frontend angezeigt
- Keine echte KI-Analyse

## Architektur

```
Frontend (reports/page.tsx)
    ↓
API Router (routers/ai.py)
    ↓
RAGReporterAgent (ai_agents.py)
    ↓
┌─────────────┬──────────────┐
│   OpenAI    │   Supabase   │
│  Embeddings │   pgvector   │
└─────────────┴──────────────┘
```

## Bekannte Limitierungen

1. **Keine Vector-DB**: Similarity Search funktioniert nicht ohne pgvector
2. **Kein Content**: Embeddings-Tabelle ist leer, keine Daten zum Durchsuchen
3. **Mock-Responses**: Ohne API-Key nur Beispiel-Antworten
4. **Keine Indexierung**: Neue Projekte werden nicht automatisch indexiert
