# Dashboard Real-Data Audit (Plan #1)

Date: 2026-04-03
Scope: admin, super-admin, doctor, patient dashboards

## Summary

- Data wiring is mostly real-data driven through API endpoints.
- Fallback text is used in several places when backend fields are missing. This is acceptable for resilience but is marked below.
- A real-data gap was fixed in this pass: shell notifications for admin and super-admin were static and are now loaded from backend overview data.

## Endpoint Mapping

- Admin overview data: `/dashboard/admin/overview`
- Doctor overview data: `/dashboard/doctor/overview`
- Patient stats/appointments: `/analytics/dashboard`, `/analytics/appointments`
- Patient results: clinical results endpoints via `medicalService`

## DONE / NOT DONE Matrix

### Admin Dashboard

- DONE: Overview charts and metrics are sourced from backend overview payload.
- DONE: Users table sourced from users APIs (`patients`, `doctors`, `administrators`).
- DONE: Patients table sourced from patients API.
- DONE: Alerts and system health sourced from backend overview.
- DONE (fixed now): Shell notification badge/items now sourced from backend overview alerts/activity.
- NOT DONE: Some labels still fall back to placeholders when backend fields are null (for example: profile/contact text). This is UI fallback, not fake data.

### Super Admin Dashboard

- DONE: Uses same route pages powered by real admin overview/users/patients APIs.
- DONE (fixed now): Shell notification badge/items now sourced from backend overview alerts/activity.
- NOT DONE: No separate super-admin-specific aggregate endpoint yet; currently reuses admin overview contract.

### Doctor Dashboard

- DONE: Overview/patients/results are sourced from doctor overview API.
- DONE: Clinical tool navigation is route-backed (no dead navigation).
- NOT DONE: Fallback text remains for missing clinical fields (MRN/case number/radiology summary). This is resilience behavior.

### Patient Dashboard

- DONE: Stats/appointments/results are sourced from analytics and clinical APIs.
- DONE: Partial-failure handling is explicit with availability flags.
- NOT DONE: Multiple fallback labels appear when APIs return null/unavailable values (for example: `Unavailable`, `No results yet`).

## Changes Implemented In This Audit Pass

- `src/pages/dashboards/admin/AdminLayout.jsx`
  - Replaced static notification values with live notifications loaded from `dashboardAPI.getAdminOverview()`.
- `src/pages/dashboards/super-admin/SuperAdminLayout.jsx`
  - Replaced static notification values with live notifications loaded from `dashboardAPI.getAdminOverview()`.

## Remaining Work For Plan #1

- Optional hardening: reduce UI fallback placeholders by improving backend completeness for nullable fields.
- Optional product enhancement: create a dedicated super-admin overview endpoint with truly global aggregates.
- Evidence closure step: capture QA screenshots/API traces per dashboard page for sign-off.
