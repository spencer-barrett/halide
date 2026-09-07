# Halide

> *Artificial Intelligence may be used for generating documentation*

Self-hosted photo backup. Select photos from an iPhone camera roll, upload them to
object storage you control, verify they arrived intact, then delete the originals
from the device to free space.

Built as a web app installed to the home screen rather than a native app, and
designed around batches (~100 photos at a time) rather than continuous background
sync.

## Why it works this way

**The server never touches photo bytes.** It issues presigned URLs; the browser
uploads directly to R2. A 400MB batch never passes through the API.

**Storage keys are opaque.** Objects live at `assets/<uuid>` with no meaning
encoded in the path. All organization — albums, tags, dates — lives in Postgres.
Reorganizing is an `UPDATE`, never a byte move.

**Upload is a two-phase handshake.** `prepare` records intent and hands out
permission; `confirm` verifies the bytes actually landed at the expected size
before anything is marked safe. Since the workflow ends in deleting the only
other copy, verification is the point.

## Stack

| Layer | Choice |
|---|---|
| API | FastAPI + uvicorn |
| ORM | SQLAlchemy 2.0 + Alembic |
| Database | Neon Postgres (psycopg3) |
| Object storage | Cloudflare R2 (S3-compatible, via boto3) |
| Config | pydantic-settings |
| Packaging | uv + hatchling |

## Layout

```
halide/
├── api/
│   ├── migrations/           
│   ├── scripts/              # throwaway/dev scripts
│   ├── test-assets/
│   └── src/halide_api/
│       ├── config.py         # Settings only
│       ├── db.py             # engine, session, get_db
│       ├── main.py           # app assembly
│       ├── models/           # SQLAlchemy tables
│       ├── routers/          # FastAPI routes
│       ├── schemas/          # Pydantic request/response
│       └── services/         # R2, images, EXIF
└── web/                      # (not yet built)
```

`models/` and `schemas/` are deliberately separate: database rows and API payloads
describe different things at different boundaries.

## Setup

```bash
cd api
uv sync
```

Create `api/.env.local`:

```
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=...
ENDPOINT_URL=...
DATABASE_URL_POOLED=...
DATABASE_URL=...
```

Then:

```bash
uv run alembic upgrade head
uv run uvicorn halide_api.main:app --reload
```

Interactive docs at `localhost:8000/docs`.

## Upload flow

```
POST /api/upload/prepare
  ├─ dedup: one query against known sha256 hashes
  ├─ create batch row
  ├─ mint asset UUIDs, write pending rows (verified_at null)
  └─ return presigned PUT URLs

  [browser PUTs bytes directly to R2 — server not involved]

POST /api/upload/confirm
  ├─ head_object per asset: exists? size matches?
  ├─ stamp verified_at on what passed
  ├─ stamp batch.verified_at if nothing remains pending
  └─ return per-asset status + batch receipt
```

Confirm returns one of four per-asset statuses: `verified`, `missing` (never
uploaded), `size_mismatch` (truncated or corrupt), `unknown` (id not pending in
this batch). `batch_verified` is only true when every asset in the batch has
passed — that flag is the signal that it's safe to delete from the device.

## Schema

**assets** — `id` (uuid, pk), `sha256` (unique, indexed), `original_filename`,
`mime`, `size_bytes`, `width`, `height`, `taken_at`, `uploaded_at`,
`verified_at`, `deleted_at`, `batch_id` (fk)

**batches** — `id`, `created_at`, `label`, `verified_at`, `device_deleted_at`

All timestamps are `timestamptz`. `taken_at` is nullable because screenshots and
downloaded images carry no EXIF date. Deletes are soft.

## Roadmap

- [x] **M0** — spike iOS file input behavior (HEIC vs JPEG, EXIF survival)
- [x] **M1** — skeleton: settings, R2, migrations, live DB reads
- [x] **M2** — upload path: presign, direct PUT, dedup
- [x] **M3** — verification and batch receipts
- [ ] **M3.5** — auth, `GET /api/assets`, test suite
- [ ] **M4** — thumbnails and grid
- [ ] **M5** — albums, tags, date filtering
- [ ] **M6** — offsite backup and a *tested* restore
