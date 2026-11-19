TEC KPI Training Dashboard update

Extract this ZIP into the root of ~/TEC-KPI-app, preserving folder structure and replacing the existing dashboard files.

This update:
- Shows enrolment completion rate = completed / enrolled.
- Shows trained-to-completed rate = completed / trained.
- Displays enrolled, trained and completed comparisons by programme and unit.
- Includes all programmes and units returned by the API, including those with zero activities.
- Adds monthly activity counts and facilitator activity workload.
- Keeps date/programme/unit filters and filtered CSV export.

Restart the static server if needed and reload training-dashboard.html. The API and database are unchanged.
