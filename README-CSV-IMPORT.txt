TEC KPI Training CSV Import Patch

Files in this patch:
- backend/routers/training.py
- backend/main.py
- index.html
- js/app.js
- js/config.js

What changed:
1. Adds POST /api/training/activities/import for CSV upload.
2. Resolves programme, skill, unit and facilitator names against existing database rows.
3. Supports multiple facilitator names separated by semicolons.
4. Validates dates and participant counts.
5. Skips duplicate activities (same programme, skill, unit, date range and course name).
6. Returns row-by-row imported/skipped/rejected results.
7. Connects the Training page to the API, with a login form, database-backed activity list and direct CSV upload.
8. Adds local-development CORS origins for a frontend served on localhost:5500.

Apply:
- Back up your current project files first.
- Extract this ZIP into the root of ~/TEC-KPI-app, preserving folder structure and allowing overwrite.
- Restart/reload the API:
  sudo docker compose -f compose.yaml -f compose.dev.yaml up -d --build
- Serve the frontend from the project directory:
  python3 -m http.server 5500
- Open http://localhost:5500 and use the Training page's Connect panel.
- Sign in with an Administrator account.

CSV columns:
programme,start_date,end_date,course,level,skill,unit,enrolled,trained,completed,facilitator_names,status,notes

Rules:
- Programme, skill, unit and facilitator names must already exist in the database.
- Separate multiple facilitator names with semicolons.
- Leave unit blank for institution-wide activities.
- Allowed statuses: draft, ongoing, completed, cancelled.
- A legacy CSV may use its level column as the programme name and a numeric facilitators column as a count only. Numeric legacy counts do not create named facilitator assignments.
- Legacy Submitted status is imported as draft because the database status enum has no Submitted value.

Important:
- CSV import endpoint is administrator-only.
- Maximum CSV size is 5 MB.
- Import is row-tolerant: valid rows are committed, duplicates skipped and invalid rows reported.
- The frontend currently connects to http://localhost:8000. Change API_BASE_URL in js/app.js when deploying the API elsewhere.
- CORS currently allows localhost:5500 and localhost:8000 only. Add your actual trusted frontend origin before hosting the frontend elsewhere.
- Do not overwrite .env or share credentials.
