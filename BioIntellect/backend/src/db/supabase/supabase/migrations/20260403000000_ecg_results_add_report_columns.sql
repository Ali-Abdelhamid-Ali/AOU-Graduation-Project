-- Add enriched_conditions and clinical_report columns to ecg_results
-- enriched_conditions: full per-code clinical data from reports_by_code.json + scp_compact_schema.json
-- clinical_report: formatted plain-text clinical report printable by the doctor

alter table "public"."ecg_results"
  add column if not exists "enriched_conditions" jsonb default '[]'::jsonb,
  add column if not exists "clinical_report" text;
