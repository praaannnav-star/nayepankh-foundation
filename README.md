# NayePankh Flask CMS

Flask CMS migration scaffold for the NayePankh Foundation website. Public pages, contact details, certificates, media recognition records, gallery images, logo, favicon, and footer settings are stored in the database and editable through `/admin`.

## Setup

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python seed_data.py
python run.py
```

Open `http://127.0.0.1:5000`.

## Volunteer Management

- Public registration: `/volunteer/signup`
- Volunteer portal and editable profile: `/volunteer/dashboard`
- Admin approvals, hours, notes, and CSV reports: `/admin/volunteers`
- Authenticated volunteer JSON endpoint: `/api/volunteers/me`

## Admin Login

Set these before first seed in production:

```powershell
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="use-a-long-random-password"
$env:ADMIN_NAME="Site Admin"
python seed_data.py
```

For local development, the fallback login is `admin@nayepankh.local` / `ChangeMe123!`. Change it with environment variables before deployment.

## Migration Utilities

- `seed_data.py` creates tables and imports live content from `https://nayepankh.com`.
- `app/services/content_importer.py` exposes `import_homepage`, `import_about_page`, `import_contact_page`, `import_certificates`, `import_media_recognition`, and `import_gallery_assets`.
- `migrations/001_initial_schema.sql` mirrors the SQLAlchemy schema for explicit database setup.

Uploaded assets are stored under `static/uploads/` using the requested structure.

## Render + PostgreSQL Deployment

This app is ready for Render PostgreSQL through the `DATABASE_URL` environment variable. Render provides a Postgres connection string, and [config.py](C:/Users/Pranav/Documents/naypank/config.py) automatically normalizes it for SQLAlchemy/psycopg.

### Option A: Render Blueprint

Use [render.yaml](C:/Users/Pranav/Documents/naypank/render.yaml) from the repository root.

1. Push this repository to GitHub.
2. In Render, choose **Blueprint** and select this repo.
3. Render will create:
   - `nayepankh-backend` Python web service
   - `nayepankh-db` PostgreSQL database
4. Set these environment variables in the web service before first deploy:
   - `ADMIN_EMAIL`
   - `ADMIN_PASSWORD`
   - `ADMIN_NAME`
5. Deploy.
6. Deploy. The Blueprint runs this automatically before startup:

```bash
python scripts/render_release.py
```

The app starts with:

```bash
gunicorn run:app
```

### Option B: Manual Render Setup

Create a PostgreSQL database in Render, then create a Python web service.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn run:app
```

Required environment variables:

```text
DATABASE_URL=<Render internal PostgreSQL connection string>
SECRET_KEY=<long random secret>
ADMIN_EMAIL=<admin email>
ADMIN_PASSWORD=<long random password>
ADMIN_NAME=<admin display name>
SOURCE_SITE_URL=https://nayepankh.com
```

Initialize tables and curated CMS content. If you use the Blueprint this runs automatically as `preDeployCommand`; for manual setup, run it from the Render shell:

```bash
python scripts/render_release.py
```

Run the full live asset/content import only when you explicitly want to crawl the current public site:

```bash
python seed_data.py
```

Note: Render services have ephemeral local disks. Files uploaded through the admin panel can disappear on redeploy unless you add persistent storage or move uploads to object storage. The migrated static assets committed under `static/uploads/` are safe because they live in the repository.
