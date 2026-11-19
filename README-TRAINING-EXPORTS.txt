TEC KPI Training Dashboard: Excel and PDF exports

1. Extract this ZIP into ~/TEC-KPI-app, replacing the existing dashboard files.
2. Refresh training-dashboard.html with Ctrl+Shift+R.
3. Connect to the API and apply any required filters before exporting.

CSV downloads the filtered records.
Excel downloads a genuine .xlsx workbook using SheetJS from jsDelivr CDN (internet access required).
PDF opens the browser print dialog; select "Save to PDF". The print layout hides controls and formats the dashboard and table for landscape pages.

All exports respect the selected date, programme and unit filters. No database or API changes are required.
