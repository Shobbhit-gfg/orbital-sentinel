# ORBITAL SENTINEL

A deterministic Space Situational Awareness (SSA) MVP for screening conjunctions from public orbital element data.

## Architecture

```text
CelesTrak GP / OMM / TLE
          |
          v
 FastAPI ingestion service -----> Supabase/PostgreSQL
          |
          v
   Python SGP4 propagator
          |
          +--> TEME state
          |
          +--> TEME -> ECEF -> WGS84 geodetic
          |
          v
  Coarse 60 s screening
          |
          v
 Refined 1 s TCA search
          |
          v
 Screening Risk (distance thresholds only)
          |
          +----------------------+
          |                      |
          v                      v
      Next.js API           Grounded LLM
          |                 event explanation only
          v
   CesiumJS + Recharts
```

## Safety / engineering boundary

This prototype deliberately does **not** calculate operational probability of collision (Pc). A conjunction event contains deterministic TCA, miss distance, relative speed, data-source timestamp, and a prototype `screening_risk` tier derived from configurable distance thresholds.

The LLM receives only those structured facts and is instructed not to invent orbital quantities, risk probabilities, or observations.

## Current versions used in the scaffold

- Next.js 16.x + TypeScript + Tailwind CSS 4
- CesiumJS 1.145
- Python FastAPI
- `sgp4` 2.27
- NumPy / SciPy
- Supabase PostgreSQL

The versions are pinned to a known-good current baseline for the generated project; update them deliberately rather than relying on floating major-version changes.

## 1. Create Supabase project

Create a Supabase project, then run `supabase/migrations/001_init.sql` in the SQL editor.

The backend uses the Supabase service-role key server-side. Do not expose that key to Next.js/browser code. CelesTrak requests should be throttled in a production deployment; their documentation notes that GP data updates on a schedule and excessive polling can be rejected. citeturn830351search0

## 2. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
uvicorn app.main:app --reload --port 8000
```

Run a first ingest + screen:

```bash
curl -X POST http://localhost:8000/api/screen \
  -H "Content-Type: application/json" \
  -d '{"window_hours": 3, "coarse_step_seconds": 60, "refine_step_seconds": 1, "max_objects": 80}'
```

## 3. Frontend

```bash
cd frontend
npm install
copy .env.local.example .env.local   # Windows
# cp .env.local.example .env.local   # macOS/Linux
npm run dev
```

Open `http://localhost:3000`.

## 4. API

- `GET /api/health`
- `GET /api/objects?window_hours=3&step_seconds=120&limit=80`
- `GET /api/events?limit=25`
- `GET /api/events/{id}`
- `POST /api/screen`
- `POST /api/events/{id}/explain`

## Data source

Default source URLs can be configured through `CELESTRAK_URLS` and point to CelesTrak GP JSON endpoints, with debris-specific feeds enabled by default. The ingestion parser also accepts CelesTrak TLE/3LE text and creates `Satrec` objects through `Satrec.twoline2rv()`. Each ingestion run stores the source URL, retrieval timestamp, record count, and SHA-256 checksum so the UI can show data freshness and provenance. CelesTrak currently supports catalog numbers beyond 99,999 in the newer OMM-based formats, so this project persists the catalog ID as text and ingests OMM JSON rather than depending on the legacy 5-digit TLE field layout. citeturn830351search5

## Coordinate handling

SGP4 returns TEME states. The backend never sends raw TEME coordinates to the browser. It rotates position into an Earth-fixed frame using a deterministic Greenwich sidereal-time conversion and also computes WGS84 geodetic latitude/longitude/height for diagnostics. Polar motion is intentionally omitted in this MVP and called out in the UI/API metadata; operational astrodynamics should use a full EOP-aware TEME conversion.

## Prototype screening behavior

1. Propagate every object at a coarse 60-second grid.
2. Use `scipy.spatial.cKDTree.query_pairs()` at a configurable broad-phase distance to find candidate pairs without O(N²) pair materialization for every sample.
3. For each candidate, find the coarse minimum and refine around it with 1-second propagation.
4. Store the refined TCA, miss distance, and relative speed.
5. Map miss distance to a `LOW`, `MEDIUM`, or `HIGH` **Screening Risk** using configurable thresholds.

This is a screening prototype, not an operational conjunction assessment service.

## LLM explanation boundary

When `OPENAI_API_KEY` is configured, `/api/events/{id}/explain` sends only the deterministic event facts to the configured model using the Responses API. The model is prohibited from adding unsupported orbital facts. Without a key, the endpoint falls back to a deterministic summary so the UI remains functional.
