create extension if not exists "btree_gin" with schema "extensions";

create extension if not exists "pg_repack" with schema "extensions";

create extension if not exists "postgis" with schema "extensions";

create extension if not exists "postgis_raster" with schema "extensions";

drop extension if exists "pg_net";

drop extension if exists "pg_stat_statements";

drop extension if exists "uuid-ossp";

create schema if not exists "pgmq";

create extension if not exists "pgmq" with schema "pgmq";

create type "public"."access_level_type" as enum ('read_only', 'full');

create type "public"."access_request_status" as enum ('pending', 'approved', 'rejected', 'revoked', 'expired');

create type "public"."analysis_status" as enum ('pending', 'processing', 'completed', 'failed', 'cancelled');

create type "public"."app_role" as enum ('super_admin', 'admin', 'doctor', 'nurse', 'patient');

create type "public"."blood_type" as enum ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown');

create type "public"."case_priority" as enum ('low', 'normal', 'high', 'urgent', 'critical');

create type "public"."case_status" as enum ('open', 'in_progress', 'pending_review', 'completed', 'archived', 'cancelled');

create type "public"."conversation_type" as enum ('patient_llm', 'doctor_llm', 'doctor_patient_llm');

create type "public"."gender_type" as enum ('male', 'female');

create type "public"."medical_file_type" as enum ('ecg', 'mri', 'ct_scan', 'xray', 'lab_report', 'prescription', 'clinical_note', 'other');

create type "public"."message_type" as enum ('text', 'medical_query', 'diagnosis_suggestion', 'summary', 'alert', 'recommendation');

create type "public"."notification_type" as enum ('chat_access_request', 'chat_access_approved', 'chat_access_rejected', 'new_case', 'case_update', 'new_result', 'system_alert');

create type "public"."sender_type" as enum ('patient', 'doctor', 'llm', 'system');

create type "public"."specialty_category" as enum ('medical', 'surgical', 'diagnostic', 'therapeutic', 'research');

create sequence "public"."case_number_seq";

create sequence "public"."patient_mrn_seq_global";


  create table "public"."administrators" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "hospital_id" uuid,
    "employee_id" character varying(50),
    "first_name" character varying(100) not null,
    "last_name" character varying(100) not null,
    "email" character varying(255) not null,
    "phone" character varying(20),
    "department" character varying(100),
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "role" character varying(50),
    "country_id" uuid,
    "region_id" uuid,
    "city" text,
    "address" text
      );


alter table "public"."administrators" enable row level security;


  create table "public"."audit_logs" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid,
    "user_role" public.app_role,
    "action" character varying(50) not null,
    "resource_type" character varying(50) not null,
    "resource_id" uuid,
    "hospital_id" uuid,
    "patient_id" uuid,
    "description" text,
    "old_values" jsonb,
    "new_values" jsonb,
    "changes" jsonb,
    "ip_address" inet,
    "user_agent" text,
    "request_id" uuid,
    "is_sensitive" boolean default false,
    "is_flagged" boolean default false,
    "flag_reason" text,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."audit_logs" enable row level security;


  create table "public"."chat_access_permissions" (
    "id" uuid not null default gen_random_uuid(),
    "patient_id" uuid not null,
    "conversation_id" uuid not null,
    "granted_by_doctor_id" uuid not null,
    "request_id" uuid,
    "access_level" public.access_level_type default 'read_only'::public.access_level_type,
    "valid_from" timestamp with time zone default now(),
    "valid_until" timestamp with time zone not null,
    "is_active" boolean default true,
    "revoked_at" timestamp with time zone,
    "revoked_by" uuid,
    "revoke_reason" text,
    "last_accessed_at" timestamp with time zone,
    "access_count" integer default 0,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."chat_access_permissions" enable row level security;


  create table "public"."chat_access_requests" (
    "id" uuid not null default gen_random_uuid(),
    "patient_id" uuid not null,
    "conversation_id" uuid not null,
    "doctor_id" uuid not null,
    "request_reason" text,
    "request_status" public.access_request_status default 'pending'::public.access_request_status,
    "responded_at" timestamp with time zone,
    "response_notes" text,
    "requested_duration_hours" integer default 24,
    "granted_duration_hours" integer,
    "expires_at" timestamp with time zone,
    "requested_at" timestamp with time zone default now(),
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."chat_access_requests" enable row level security;


  create table "public"."countries" (
    "id" uuid not null default gen_random_uuid(),
    "country_code" character varying(3) not null,
    "country_name_en" character varying(100) not null,
    "country_name_ar" character varying(100),
    "phone_code" character varying(10),
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."countries" enable row level security;


  create table "public"."data_access_logs" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "user_role" public.app_role not null,
    "accessed_table" character varying(100) not null,
    "accessed_record_id" uuid not null,
    "patient_id" uuid,
    "access_type" character varying(20) not null,
    "access_reason" text,
    "has_treatment_relationship" boolean default false,
    "relationship_type" character varying(50),
    "hospital_id" uuid,
    "case_id" uuid,
    "conversation_id" uuid,
    "ip_address" inet,
    "user_agent" text,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."data_access_logs" enable row level security;


  create table "public"."doctor_specialties" (
    "id" uuid not null default gen_random_uuid(),
    "doctor_id" uuid not null,
    "specialty_id" uuid not null,
    "is_primary" boolean default false,
    "certification_number" character varying(100),
    "certification_date" date,
    "expiry_date" date,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."doctor_specialties" enable row level security;


  create table "public"."doctors" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "hospital_id" uuid not null,
    "employee_id" character varying(50),
    "first_name" character varying(100) not null,
    "last_name" character varying(100) not null,
    "first_name_ar" character varying(100),
    "last_name_ar" character varying(100),
    "email" character varying(255) not null,
    "phone" character varying(20),
    "gender" public.gender_type,
    "date_of_birth" date,
    "license_number" character varying(50) not null,
    "license_expiry" date,
    "qualification" text,
    "years_of_experience" integer default 0,
    "bio" text,
    "avatar_url" text,
    "is_active" boolean default true,
    "is_verified" boolean default false,
    "verified_at" timestamp with time zone,
    "verified_by" uuid,
    "settings" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "country_id" uuid,
    "region_id" uuid,
    "city" text,
    "address" text,
    "specialty" character varying(100)
      );


alter table "public"."doctors" enable row level security;


  create table "public"."ecg_results" (
    "id" uuid not null default gen_random_uuid(),
    "signal_id" uuid not null,
    "patient_id" uuid not null,
    "case_id" uuid,
    "analyzed_by_model" character varying(100) not null,
    "model_version" character varying(50),
    "analysis_status" public.analysis_status default 'pending'::public.analysis_status,
    "heart_rate" integer,
    "heart_rate_variability" numeric(10,4),
    "rhythm_classification" character varying(100),
    "rhythm_confidence" numeric(5,4),
    "detected_conditions" jsonb default '[]'::jsonb,
    "pr_interval" integer,
    "qrs_duration" integer,
    "qt_interval" integer,
    "qtc_interval" integer,
    "ai_interpretation" text,
    "ai_recommendations" text[],
    "risk_score" numeric(5,2),
    "is_reviewed" boolean default false,
    "reviewed_by_doctor_id" uuid,
    "reviewed_at" timestamp with time zone,
    "doctor_notes" text,
    "doctor_agrees_with_ai" boolean,
    "processing_time_ms" integer,
    "raw_output" jsonb,
    "error_message" text,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."ecg_results" enable row level security;


  create table "public"."ecg_signals" (
    "id" uuid not null default gen_random_uuid(),
    "file_id" uuid not null,
    "patient_id" uuid not null,
    "case_id" uuid,
    "signal_data" jsonb,
    "sampling_rate" integer,
    "duration_seconds" numeric(10,2),
    "lead_count" integer default 12,
    "leads_available" text[],
    "recording_date" timestamp with time zone,
    "device_info" jsonb,
    "quality_score" numeric(5,2),
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."ecg_signals" enable row level security;


  create table "public"."generated_reports" (
    "id" uuid not null default gen_random_uuid(),
    "report_number" character varying(30) not null,
    "patient_id" uuid not null,
    "case_id" uuid,
    "doctor_id" uuid,
    "report_type" character varying(50) not null,
    "ecg_result_id" uuid,
    "mri_result_id" uuid,
    "title" character varying(255) not null,
    "summary" text,
    "content" jsonb not null,
    "generated_by_model" character varying(100),
    "model_version" character varying(50),
    "template_used" character varying(100),
    "status" character varying(20) default 'draft'::character varying,
    "approved_by_doctor_id" uuid,
    "approved_at" timestamp with time zone,
    "approval_notes" text,
    "digital_signature" text,
    "signature_timestamp" timestamp with time zone,
    "signed_by_doctor_id" uuid,
    "pdf_path" text,
    "pdf_generated_at" timestamp with time zone,
    "is_final" boolean default false,
    "version" integer default 1,
    "previous_version_id" uuid,
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."generated_reports" enable row level security;


  create table "public"."hospitals" (
    "id" uuid not null default gen_random_uuid(),
    "region_id" uuid not null,
    "hospital_code" character varying(10) not null,
    "hospital_name_en" character varying(200) not null,
    "hospital_name_ar" character varying(200),
    "address" text,
    "phone" character varying(20),
    "email" character varying(100),
    "license_number" character varying(50),
    "is_active" boolean default true,
    "settings" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."hospitals" enable row level security;


  create table "public"."llm_context_configs" (
    "id" uuid not null default gen_random_uuid(),
    "config_name" character varying(100) not null,
    "context_type" character varying(50) not null,
    "include_patient_info" boolean default true,
    "include_medical_history" boolean default true,
    "include_allergies" boolean default true,
    "include_medications" boolean default true,
    "include_recent_cases" integer default 5,
    "include_ecg_results" integer default 3,
    "include_mri_results" integer default 3,
    "include_doctor_info" boolean default true,
    "data_sources" jsonb default '[]'::jsonb,
    "excluded_fields" text[],
    "max_history_days" integer default 365,
    "access_rules" jsonb default '{}'::jsonb,
    "system_prompt_template" text,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."llm_context_configs" enable row level security;


  create table "public"."llm_conversations" (
    "id" uuid not null default gen_random_uuid(),
    "conversation_type" public.conversation_type not null,
    "patient_id" uuid not null,
    "doctor_id" uuid,
    "case_id" uuid,
    "hospital_id" uuid not null,
    "title" character varying(255),
    "system_prompt" text,
    "llm_model" character varying(100) default 'gpt-4'::character varying,
    "temperature" numeric(3,2) default 0.7,
    "max_tokens" integer default 4096,
    "is_active" boolean default true,
    "is_archived" boolean default false,
    "archived_at" timestamp with time zone,
    "message_count" integer default 0,
    "total_tokens_used" integer default 0,
    "last_message_at" timestamp with time zone,
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."llm_conversations" enable row level security;


  create table "public"."llm_messages" (
    "id" uuid not null default gen_random_uuid(),
    "conversation_id" uuid not null,
    "sender_type" public.sender_type not null,
    "sender_id" uuid,
    "message_content" text not null,
    "message_type" public.message_type default 'text'::public.message_type,
    "llm_model_used" character varying(100),
    "tokens_used" integer,
    "prompt_tokens" integer,
    "completion_tokens" integer,
    "llm_context_snapshot" jsonb,
    "attachments" jsonb default '[]'::jsonb,
    "is_edited" boolean default false,
    "edited_at" timestamp with time zone,
    "is_deleted" boolean default false,
    "deleted_at" timestamp with time zone,
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."llm_messages" enable row level security;


  create table "public"."medical_cases" (
    "id" uuid not null default gen_random_uuid(),
    "case_number" character varying(30) not null,
    "patient_id" uuid not null,
    "hospital_id" uuid not null,
    "assigned_doctor_id" uuid,
    "created_by_doctor_id" uuid,
    "status" public.case_status default 'open'::public.case_status,
    "priority" public.case_priority default 'normal'::public.case_priority,
    "chief_complaint" text,
    "diagnosis" text,
    "diagnosis_icd10" character varying(20),
    "treatment_plan" text,
    "notes" text,
    "admission_date" timestamp with time zone,
    "discharge_date" timestamp with time zone,
    "follow_up_date" date,
    "tags" text[],
    "metadata" jsonb default '{}'::jsonb,
    "is_archived" boolean default false,
    "archived_at" timestamp with time zone,
    "archived_by" uuid,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."medical_cases" enable row level security;


  create table "public"."medical_files" (
    "id" uuid not null default gen_random_uuid(),
    "case_id" uuid not null,
    "patient_id" uuid not null,
    "uploaded_by" uuid not null,
    "file_type" public.medical_file_type not null,
    "file_name" character varying(255) not null,
    "file_path" text not null,
    "file_size" bigint,
    "mime_type" character varying(100),
    "storage_bucket" character varying(100) default 'medical-files'::character varying,
    "description" text,
    "metadata" jsonb default '{}'::jsonb,
    "is_analyzed" boolean default false,
    "analyzed_at" timestamp with time zone,
    "is_deleted" boolean default false,
    "deleted_at" timestamp with time zone,
    "deleted_by" uuid,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."medical_files" enable row level security;


  create table "public"."model_versions" (
    "id" uuid not null default gen_random_uuid(),
    "model_name" character varying(100) not null,
    "model_version" character varying(50) not null,
    "model_type" character varying(50) not null,
    "description" text,
    "provider" character varying(100),
    "accuracy" numeric(5,4),
    "precision_score" numeric(5,4),
    "recall" numeric(5,4),
    "f1_score" numeric(5,4),
    "validation_dataset" text,
    "default_config" jsonb default '{}'::jsonb,
    "is_active" boolean default false,
    "is_production" boolean default false,
    "deployed_at" timestamp with time zone,
    "deprecated_at" timestamp with time zone,
    "created_by" uuid,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."model_versions" enable row level security;


  create table "public"."mri_scans" (
    "id" uuid not null default gen_random_uuid(),
    "file_id" uuid not null,
    "patient_id" uuid not null,
    "case_id" uuid,
    "scan_type" character varying(50),
    "sequence_type" character varying(50),
    "body_part" character varying(100),
    "slice_count" integer,
    "slice_thickness_mm" numeric(5,2),
    "field_strength" numeric(4,2),
    "scan_date" timestamp with time zone,
    "device_info" jsonb,
    "dicom_metadata" jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."mri_scans" enable row level security;


  create table "public"."mri_segmentation_results" (
    "id" uuid not null default gen_random_uuid(),
    "scan_id" uuid not null,
    "patient_id" uuid not null,
    "case_id" uuid,
    "analyzed_by_model" character varying(100) not null,
    "model_version" character varying(50),
    "analysis_status" public.analysis_status default 'pending'::public.analysis_status,
    "segmentation_mask_path" text,
    "segmented_regions" jsonb default '[]'::jsonb,
    "detected_abnormalities" jsonb default '[]'::jsonb,
    "measurements" jsonb default '{}'::jsonb,
    "ai_interpretation" text,
    "ai_recommendations" text[],
    "severity_score" numeric(5,2),
    "is_reviewed" boolean default false,
    "reviewed_by_doctor_id" uuid,
    "reviewed_at" timestamp with time zone,
    "doctor_notes" text,
    "doctor_agrees_with_ai" boolean,
    "processing_time_ms" integer,
    "raw_output" jsonb,
    "error_message" text,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."mri_segmentation_results" enable row level security;


  create table "public"."notifications" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "notification_type" public.notification_type not null,
    "title" character varying(255) not null,
    "message" text not null,
    "resource_type" character varying(50),
    "resource_id" uuid,
    "action_url" text,
    "hospital_id" uuid,
    "patient_id" uuid,
    "is_read" boolean default false,
    "read_at" timestamp with time zone,
    "is_archived" boolean default false,
    "archived_at" timestamp with time zone,
    "priority" character varying(20) default 'normal'::character varying,
    "expires_at" timestamp with time zone,
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."notifications" enable row level security;


  create table "public"."nurses" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "hospital_id" uuid not null,
    "employee_id" character varying(50),
    "first_name" character varying(100) not null,
    "last_name" character varying(100) not null,
    "email" character varying(255) not null,
    "phone" character varying(20),
    "license_number" character varying(50),
    "department" character varying(100),
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "country_id" uuid,
    "region_id" uuid,
    "city" text,
    "address" text
      );


alter table "public"."nurses" enable row level security;


  create table "public"."patients" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid,
    "hospital_id" uuid not null,
    "mrn" character varying(20) not null,
    "first_name" character varying(100) not null,
    "last_name" character varying(100) not null,
    "first_name_ar" character varying(100),
    "last_name_ar" character varying(100),
    "email" character varying(255),
    "phone" character varying(20),
    "gender" public.gender_type,
    "date_of_birth" date,
    "blood_type" public.blood_type default 'unknown'::public.blood_type,
    "national_id" character varying(50),
    "passport_number" character varying(50),
    "address" text,
    "city" character varying(100),
    "region_id" uuid,
    "country_id" uuid,
    "emergency_contact_name" character varying(200),
    "emergency_contact_phone" character varying(20),
    "emergency_contact_relation" character varying(50),
    "allergies" text[],
    "chronic_conditions" text[],
    "current_medications" jsonb default '[]'::jsonb,
    "insurance_provider" character varying(100),
    "insurance_number" character varying(50),
    "primary_doctor_id" uuid,
    "is_active" boolean default true,
    "notes" text,
    "settings" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."patients" enable row level security;


  create table "public"."regions" (
    "id" uuid not null default gen_random_uuid(),
    "country_id" uuid not null,
    "region_code" character varying(10) not null,
    "region_name_en" character varying(100) not null,
    "region_name_ar" character varying(100),
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."regions" enable row level security;


  create table "public"."specialty_types" (
    "id" uuid not null default gen_random_uuid(),
    "specialty_code" character varying(20) not null,
    "specialty_name_en" character varying(100) not null,
    "specialty_name_ar" character varying(100),
    "specialty_category" public.specialty_category not null default 'medical'::public.specialty_category,
    "parent_specialty_id" uuid,
    "description" text,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."specialty_types" enable row level security;


  create table "public"."system_settings" (
    "id" uuid not null default gen_random_uuid(),
    "scope" character varying(50) not null,
    "scope_id" uuid,
    "setting_key" character varying(100) not null,
    "setting_value" jsonb not null,
    "setting_type" character varying(50),
    "description" text,
    "is_sensitive" boolean default false,
    "created_by" uuid,
    "updated_by" uuid,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."system_settings" enable row level security;


  create table "public"."user_roles" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "role" public.app_role not null,
    "hospital_id" uuid,
    "granted_by" uuid,
    "granted_at" timestamp with time zone default now(),
    "expires_at" timestamp with time zone,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."user_roles" enable row level security;

CREATE UNIQUE INDEX administrators_pkey ON public.administrators USING btree (id);

CREATE UNIQUE INDEX administrators_user_id_key ON public.administrators USING btree (user_id);

CREATE UNIQUE INDEX audit_logs_pkey ON public.audit_logs USING btree (id);

CREATE UNIQUE INDEX chat_access_permissions_patient_id_conversation_id_valid_fr_key ON public.chat_access_permissions USING btree (patient_id, conversation_id, valid_from);

CREATE UNIQUE INDEX chat_access_permissions_pkey ON public.chat_access_permissions USING btree (id);

CREATE UNIQUE INDEX chat_access_requests_pkey ON public.chat_access_requests USING btree (id);

CREATE UNIQUE INDEX countries_country_code_key ON public.countries USING btree (country_code);

CREATE UNIQUE INDEX countries_pkey ON public.countries USING btree (id);

CREATE UNIQUE INDEX data_access_logs_pkey ON public.data_access_logs USING btree (id);

CREATE UNIQUE INDEX doctor_specialties_doctor_id_specialty_id_key ON public.doctor_specialties USING btree (doctor_id, specialty_id);

CREATE UNIQUE INDEX doctor_specialties_pkey ON public.doctor_specialties USING btree (id);

CREATE UNIQUE INDEX doctors_pkey ON public.doctors USING btree (id);

CREATE UNIQUE INDEX doctors_user_id_key ON public.doctors USING btree (user_id);

CREATE UNIQUE INDEX ecg_results_pkey ON public.ecg_results USING btree (id);

CREATE UNIQUE INDEX ecg_signals_pkey ON public.ecg_signals USING btree (id);

CREATE UNIQUE INDEX generated_reports_pkey ON public.generated_reports USING btree (id);

CREATE UNIQUE INDEX generated_reports_report_number_key ON public.generated_reports USING btree (report_number);

CREATE UNIQUE INDEX hospitals_hospital_code_key ON public.hospitals USING btree (hospital_code);

CREATE UNIQUE INDEX hospitals_pkey ON public.hospitals USING btree (id);

CREATE INDEX idx_administrators_country_id ON public.administrators USING btree (country_id);

CREATE INDEX idx_administrators_hospital ON public.administrators USING btree (hospital_id);

CREATE INDEX idx_administrators_region_id ON public.administrators USING btree (region_id);

CREATE INDEX idx_administrators_user ON public.administrators USING btree (user_id);

CREATE INDEX idx_audit_logs_action ON public.audit_logs USING btree (action);

CREATE INDEX idx_audit_logs_created_at ON public.audit_logs USING btree (created_at DESC);

CREATE INDEX idx_audit_logs_hospital ON public.audit_logs USING btree (hospital_id);

CREATE INDEX idx_audit_logs_hospital_action_created ON public.audit_logs USING btree (hospital_id, action, created_at DESC);

CREATE INDEX idx_audit_logs_hospital_action_date ON public.audit_logs USING btree (hospital_id, action, created_at DESC);

CREATE INDEX idx_audit_logs_patient ON public.audit_logs USING btree (patient_id);

CREATE INDEX idx_audit_logs_resource ON public.audit_logs USING btree (resource_type, resource_id);

CREATE INDEX idx_audit_logs_resource_type ON public.audit_logs USING btree (resource_type) WHERE (resource_type IS NOT NULL);

CREATE INDEX idx_audit_logs_user ON public.audit_logs USING btree (user_id);

CREATE INDEX idx_audit_logs_user_id ON public.audit_logs USING btree (user_id) WHERE (user_id IS NOT NULL);

CREATE INDEX idx_chat_access_permissions_request_id ON public.chat_access_permissions USING btree (request_id);

CREATE INDEX idx_chat_access_permissions_revoked_by ON public.chat_access_permissions USING btree (revoked_by);

CREATE INDEX idx_chat_access_requests_conversation ON public.chat_access_requests USING btree (conversation_id);

CREATE INDEX idx_chat_access_requests_doctor ON public.chat_access_requests USING btree (doctor_id);

CREATE INDEX idx_chat_access_requests_patient ON public.chat_access_requests USING btree (patient_id);

CREATE INDEX idx_chat_access_requests_status ON public.chat_access_requests USING btree (request_status);

CREATE INDEX idx_chat_permissions_conversation ON public.chat_access_permissions USING btree (conversation_id);

CREATE INDEX idx_chat_permissions_doctor ON public.chat_access_permissions USING btree (granted_by_doctor_id);

CREATE INDEX idx_chat_permissions_patient ON public.chat_access_permissions USING btree (patient_id);

CREATE INDEX idx_countries_active ON public.countries USING btree (is_active) WHERE (is_active = true);

CREATE INDEX idx_countries_code ON public.countries USING btree (country_code);

CREATE INDEX idx_data_access_logs_case_id ON public.data_access_logs USING btree (case_id);

CREATE INDEX idx_data_access_logs_conversation_id ON public.data_access_logs USING btree (conversation_id);

CREATE INDEX idx_data_access_logs_hospital_id ON public.data_access_logs USING btree (hospital_id);

CREATE INDEX idx_data_access_logs_user_patient_created ON public.data_access_logs USING btree (user_id, patient_id, created_at DESC);

CREATE INDEX idx_data_access_patient ON public.data_access_logs USING btree (patient_id);

CREATE INDEX idx_data_access_table ON public.data_access_logs USING btree (accessed_table);

CREATE INDEX idx_data_access_user ON public.data_access_logs USING btree (user_id);

CREATE INDEX idx_data_access_user_patient ON public.data_access_logs USING btree (user_id, patient_id);

CREATE INDEX idx_data_access_user_patient_date ON public.data_access_logs USING btree (user_id, patient_id, created_at DESC);

CREATE INDEX idx_doctor_specialties_doctor ON public.doctor_specialties USING btree (doctor_id);

CREATE INDEX idx_doctor_specialties_specialty ON public.doctor_specialties USING btree (specialty_id);

CREATE INDEX idx_doctors_country_id ON public.doctors USING btree (country_id);

CREATE INDEX idx_doctors_hospital ON public.doctors USING btree (hospital_id);

CREATE INDEX idx_doctors_hospital_active ON public.doctors USING btree (hospital_id, is_active) WHERE (is_active = true);

CREATE INDEX idx_doctors_region_id ON public.doctors USING btree (region_id);

CREATE INDEX idx_doctors_user ON public.doctors USING btree (user_id);

CREATE INDEX idx_doctors_verified_by ON public.doctors USING btree (verified_by);

CREATE INDEX idx_ecg_results_case ON public.ecg_results USING btree (case_id);

CREATE INDEX idx_ecg_results_patient ON public.ecg_results USING btree (patient_id);

CREATE INDEX idx_ecg_results_patient_status_created ON public.ecg_results USING btree (patient_id, analysis_status, created_at DESC);

CREATE INDEX idx_ecg_results_patient_status_date ON public.ecg_results USING btree (patient_id, analysis_status, created_at DESC);

CREATE INDEX idx_ecg_results_reviewed_by_doctor_id ON public.ecg_results USING btree (reviewed_by_doctor_id);

CREATE INDEX idx_ecg_results_signal ON public.ecg_results USING btree (signal_id);

CREATE INDEX idx_ecg_results_status ON public.ecg_results USING btree (analysis_status);

CREATE INDEX idx_ecg_signals_case ON public.ecg_signals USING btree (case_id);

CREATE INDEX idx_ecg_signals_file ON public.ecg_signals USING btree (file_id);

CREATE INDEX idx_ecg_signals_patient ON public.ecg_signals USING btree (patient_id);

CREATE INDEX idx_generated_reports_approved_by_doctor_id ON public.generated_reports USING btree (approved_by_doctor_id);

CREATE INDEX idx_generated_reports_ecg_result_id ON public.generated_reports USING btree (ecg_result_id);

CREATE INDEX idx_generated_reports_mri_result_id ON public.generated_reports USING btree (mri_result_id);

CREATE INDEX idx_generated_reports_previous_version_id ON public.generated_reports USING btree (previous_version_id);

CREATE INDEX idx_generated_reports_signed_by_doctor_id ON public.generated_reports USING btree (signed_by_doctor_id);

CREATE INDEX idx_hospitals_code ON public.hospitals USING btree (hospital_code);

CREATE INDEX idx_hospitals_region ON public.hospitals USING btree (region_id);

CREATE INDEX idx_llm_conversations_case ON public.llm_conversations USING btree (case_id);

CREATE INDEX idx_llm_conversations_doctor ON public.llm_conversations USING btree (doctor_id);

CREATE INDEX idx_llm_conversations_hospital ON public.llm_conversations USING btree (hospital_id);

CREATE INDEX idx_llm_conversations_last_message ON public.llm_conversations USING btree (last_message_at DESC);

CREATE INDEX idx_llm_conversations_patient ON public.llm_conversations USING btree (patient_id);

CREATE INDEX idx_llm_conversations_patient_active_date ON public.llm_conversations USING btree (patient_id, is_active, last_message_at DESC);

CREATE INDEX idx_llm_conversations_patient_active_updated ON public.llm_conversations USING btree (patient_id, is_active, last_message_at DESC);

CREATE INDEX idx_llm_messages_conv_created ON public.llm_messages USING btree (conversation_id, created_at);

CREATE INDEX idx_llm_messages_conversation ON public.llm_messages USING btree (conversation_id);

CREATE INDEX idx_llm_messages_conversation_created ON public.llm_messages USING btree (conversation_id, created_at DESC) WHERE (is_deleted = false);

CREATE INDEX idx_llm_messages_conversation_date ON public.llm_messages USING btree (conversation_id, created_at DESC) WHERE (is_deleted = false);

CREATE INDEX idx_llm_messages_created ON public.llm_messages USING btree (created_at);

CREATE INDEX idx_medical_cases_archived_by ON public.medical_cases USING btree (archived_by);

CREATE INDEX idx_medical_cases_created_by_doctor_id ON public.medical_cases USING btree (created_by_doctor_id);

CREATE INDEX idx_medical_cases_doctor ON public.medical_cases USING btree (assigned_doctor_id);

CREATE INDEX idx_medical_cases_doctor_status_created ON public.medical_cases USING btree (assigned_doctor_id, status, created_at DESC);

CREATE INDEX idx_medical_cases_doctor_status_date ON public.medical_cases USING btree (assigned_doctor_id, status, created_at DESC) WHERE (is_archived = false);

CREATE INDEX idx_medical_cases_hospital ON public.medical_cases USING btree (hospital_id);

CREATE INDEX idx_medical_cases_hospital_priority ON public.medical_cases USING btree (hospital_id, priority, status) WHERE (is_archived = false);

CREATE INDEX idx_medical_cases_hospital_priority_status ON public.medical_cases USING btree (hospital_id, priority, status) WHERE (is_archived = false);

CREATE INDEX idx_medical_cases_number ON public.medical_cases USING btree (case_number);

CREATE INDEX idx_medical_cases_patient ON public.medical_cases USING btree (patient_id);

CREATE INDEX idx_medical_cases_patient_status ON public.medical_cases USING btree (patient_id, status);

CREATE INDEX idx_medical_cases_patient_status_created ON public.medical_cases USING btree (patient_id, status, created_at DESC);

CREATE INDEX idx_medical_cases_patient_status_date ON public.medical_cases USING btree (patient_id, status, created_at DESC) WHERE (is_archived = false);

CREATE INDEX idx_medical_cases_priority ON public.medical_cases USING btree (priority);

CREATE INDEX idx_medical_cases_status ON public.medical_cases USING btree (status);

CREATE INDEX idx_medical_files_case ON public.medical_files USING btree (case_id);

CREATE INDEX idx_medical_files_deleted_by ON public.medical_files USING btree (deleted_by);

CREATE INDEX idx_medical_files_patient ON public.medical_files USING btree (patient_id);

CREATE INDEX idx_medical_files_patient_type_created ON public.medical_files USING btree (patient_id, file_type, created_at DESC) WHERE (is_deleted = false);

CREATE INDEX idx_medical_files_patient_type_date ON public.medical_files USING btree (patient_id, file_type, created_at DESC) WHERE (is_deleted = false);

CREATE INDEX idx_medical_files_uploaded_by ON public.medical_files USING btree (uploaded_by);

CREATE INDEX idx_model_versions_created_by ON public.model_versions USING btree (created_by);

CREATE INDEX idx_mri_results_case ON public.mri_segmentation_results USING btree (case_id);

CREATE INDEX idx_mri_results_patient ON public.mri_segmentation_results USING btree (patient_id);

CREATE INDEX idx_mri_results_patient_status_created ON public.mri_segmentation_results USING btree (patient_id, analysis_status, created_at DESC);

CREATE INDEX idx_mri_results_patient_status_date ON public.mri_segmentation_results USING btree (patient_id, analysis_status, created_at DESC);

CREATE INDEX idx_mri_results_reviewed_by_doctor_id ON public.mri_segmentation_results USING btree (reviewed_by_doctor_id);

CREATE INDEX idx_mri_results_scan ON public.mri_segmentation_results USING btree (scan_id);

CREATE INDEX idx_mri_results_status ON public.mri_segmentation_results USING btree (analysis_status);

CREATE INDEX idx_mri_scans_case ON public.mri_scans USING btree (case_id);

CREATE INDEX idx_mri_scans_file ON public.mri_scans USING btree (file_id);

CREATE INDEX idx_mri_scans_patient ON public.mri_scans USING btree (patient_id);

CREATE INDEX idx_notifications_hospital_id ON public.notifications USING btree (hospital_id);

CREATE INDEX idx_notifications_patient_id ON public.notifications USING btree (patient_id);

CREATE INDEX idx_notifications_user ON public.notifications USING btree (user_id);

CREATE INDEX idx_notifications_user_unread_created ON public.notifications USING btree (user_id, is_read, created_at DESC) WHERE (is_archived = false);

CREATE INDEX idx_notifications_user_unread_date ON public.notifications USING btree (user_id, is_read, created_at DESC) WHERE (is_archived = false);

CREATE INDEX idx_nurses_country_id ON public.nurses USING btree (country_id);

CREATE INDEX idx_nurses_hospital ON public.nurses USING btree (hospital_id);

CREATE INDEX idx_nurses_region_id ON public.nurses USING btree (region_id);

CREATE INDEX idx_nurses_user ON public.nurses USING btree (user_id);

CREATE INDEX idx_patients_country_id ON public.patients USING btree (country_id);

CREATE INDEX idx_patients_hospital ON public.patients USING btree (hospital_id);

CREATE INDEX idx_patients_hospital_active ON public.patients USING btree (hospital_id, is_active) WHERE (is_active = true);

CREATE INDEX idx_patients_hospital_mrn ON public.patients USING btree (hospital_id, mrn);

CREATE INDEX idx_patients_mrn ON public.patients USING btree (mrn);

CREATE INDEX idx_patients_name ON public.patients USING btree (first_name, last_name);

CREATE INDEX idx_patients_national_id ON public.patients USING btree (national_id) WHERE (national_id IS NOT NULL);

CREATE INDEX idx_patients_primary_doctor ON public.patients USING btree (primary_doctor_id) WHERE (primary_doctor_id IS NOT NULL);

CREATE INDEX idx_patients_region_id ON public.patients USING btree (region_id);

CREATE INDEX idx_patients_user ON public.patients USING btree (user_id) WHERE (user_id IS NOT NULL);

CREATE INDEX idx_regions_country ON public.regions USING btree (country_id);

CREATE INDEX idx_reports_case ON public.generated_reports USING btree (case_id);

CREATE INDEX idx_reports_created ON public.generated_reports USING btree (created_at DESC);

CREATE INDEX idx_reports_doctor ON public.generated_reports USING btree (doctor_id);

CREATE INDEX idx_reports_number ON public.generated_reports USING btree (report_number);

CREATE INDEX idx_reports_patient ON public.generated_reports USING btree (patient_id);

CREATE INDEX idx_reports_status ON public.generated_reports USING btree (status);

CREATE INDEX idx_reports_type ON public.generated_reports USING btree (report_type);

CREATE INDEX idx_specialty_types_parent_specialty_id ON public.specialty_types USING btree (parent_specialty_id) WHERE (parent_specialty_id IS NOT NULL);

CREATE INDEX idx_system_settings_created_by ON public.system_settings USING btree (created_by);

CREATE INDEX idx_system_settings_updated_by ON public.system_settings USING btree (updated_by);

CREATE INDEX idx_user_roles_granted_by ON public.user_roles USING btree (granted_by);

CREATE INDEX idx_user_roles_hospital ON public.user_roles USING btree (hospital_id);

CREATE INDEX idx_user_roles_role ON public.user_roles USING btree (role);

CREATE INDEX idx_user_roles_user ON public.user_roles USING btree (user_id);

CREATE INDEX idx_user_roles_user_active ON public.user_roles USING btree (user_id, is_active) WHERE (is_active = true);

CREATE UNIQUE INDEX llm_context_configs_config_name_key ON public.llm_context_configs USING btree (config_name);

CREATE UNIQUE INDEX llm_context_configs_pkey ON public.llm_context_configs USING btree (id);

CREATE UNIQUE INDEX llm_conversations_pkey ON public.llm_conversations USING btree (id);

CREATE UNIQUE INDEX llm_messages_pkey ON public.llm_messages USING btree (id);

CREATE UNIQUE INDEX medical_cases_case_number_key ON public.medical_cases USING btree (case_number);

CREATE UNIQUE INDEX medical_cases_pkey ON public.medical_cases USING btree (id);

CREATE UNIQUE INDEX medical_files_pkey ON public.medical_files USING btree (id);

CREATE UNIQUE INDEX model_versions_model_name_model_version_key ON public.model_versions USING btree (model_name, model_version);

CREATE UNIQUE INDEX model_versions_pkey ON public.model_versions USING btree (id);

CREATE UNIQUE INDEX mri_scans_pkey ON public.mri_scans USING btree (id);

CREATE UNIQUE INDEX mri_segmentation_results_pkey ON public.mri_segmentation_results USING btree (id);

CREATE UNIQUE INDEX notifications_pkey ON public.notifications USING btree (id);

CREATE UNIQUE INDEX nurses_pkey ON public.nurses USING btree (id);

CREATE UNIQUE INDEX nurses_user_id_key ON public.nurses USING btree (user_id);

CREATE UNIQUE INDEX patients_hospital_id_mrn_key ON public.patients USING btree (hospital_id, mrn);

CREATE UNIQUE INDEX patients_pkey ON public.patients USING btree (id);

CREATE UNIQUE INDEX patients_user_id_key ON public.patients USING btree (user_id);

CREATE UNIQUE INDEX regions_country_id_region_code_key ON public.regions USING btree (country_id, region_code);

CREATE UNIQUE INDEX regions_pkey ON public.regions USING btree (id);

CREATE UNIQUE INDEX specialty_types_pkey ON public.specialty_types USING btree (id);

CREATE UNIQUE INDEX specialty_types_specialty_code_key ON public.specialty_types USING btree (specialty_code);

CREATE UNIQUE INDEX system_settings_pkey ON public.system_settings USING btree (id);

CREATE UNIQUE INDEX system_settings_scope_scope_id_setting_key_key ON public.system_settings USING btree (scope, scope_id, setting_key);

CREATE UNIQUE INDEX user_roles_pkey ON public.user_roles USING btree (id);

CREATE UNIQUE INDEX user_roles_user_id_role_hospital_id_key ON public.user_roles USING btree (user_id, role, hospital_id);

alter table "public"."administrators" add constraint "administrators_pkey" PRIMARY KEY using index "administrators_pkey";

alter table "public"."audit_logs" add constraint "audit_logs_pkey" PRIMARY KEY using index "audit_logs_pkey";

alter table "public"."chat_access_permissions" add constraint "chat_access_permissions_pkey" PRIMARY KEY using index "chat_access_permissions_pkey";

alter table "public"."chat_access_requests" add constraint "chat_access_requests_pkey" PRIMARY KEY using index "chat_access_requests_pkey";

alter table "public"."countries" add constraint "countries_pkey" PRIMARY KEY using index "countries_pkey";

alter table "public"."data_access_logs" add constraint "data_access_logs_pkey" PRIMARY KEY using index "data_access_logs_pkey";

alter table "public"."doctor_specialties" add constraint "doctor_specialties_pkey" PRIMARY KEY using index "doctor_specialties_pkey";

alter table "public"."doctors" add constraint "doctors_pkey" PRIMARY KEY using index "doctors_pkey";

alter table "public"."ecg_results" add constraint "ecg_results_pkey" PRIMARY KEY using index "ecg_results_pkey";

alter table "public"."ecg_signals" add constraint "ecg_signals_pkey" PRIMARY KEY using index "ecg_signals_pkey";

alter table "public"."generated_reports" add constraint "generated_reports_pkey" PRIMARY KEY using index "generated_reports_pkey";

alter table "public"."hospitals" add constraint "hospitals_pkey" PRIMARY KEY using index "hospitals_pkey";

alter table "public"."llm_context_configs" add constraint "llm_context_configs_pkey" PRIMARY KEY using index "llm_context_configs_pkey";

alter table "public"."llm_conversations" add constraint "llm_conversations_pkey" PRIMARY KEY using index "llm_conversations_pkey";

alter table "public"."llm_messages" add constraint "llm_messages_pkey" PRIMARY KEY using index "llm_messages_pkey";

alter table "public"."medical_cases" add constraint "medical_cases_pkey" PRIMARY KEY using index "medical_cases_pkey";

alter table "public"."medical_files" add constraint "medical_files_pkey" PRIMARY KEY using index "medical_files_pkey";

alter table "public"."model_versions" add constraint "model_versions_pkey" PRIMARY KEY using index "model_versions_pkey";

alter table "public"."mri_scans" add constraint "mri_scans_pkey" PRIMARY KEY using index "mri_scans_pkey";

alter table "public"."mri_segmentation_results" add constraint "mri_segmentation_results_pkey" PRIMARY KEY using index "mri_segmentation_results_pkey";

alter table "public"."notifications" add constraint "notifications_pkey" PRIMARY KEY using index "notifications_pkey";

alter table "public"."nurses" add constraint "nurses_pkey" PRIMARY KEY using index "nurses_pkey";

alter table "public"."patients" add constraint "patients_pkey" PRIMARY KEY using index "patients_pkey";

alter table "public"."regions" add constraint "regions_pkey" PRIMARY KEY using index "regions_pkey";

alter table "public"."specialty_types" add constraint "specialty_types_pkey" PRIMARY KEY using index "specialty_types_pkey";

alter table "public"."system_settings" add constraint "system_settings_pkey" PRIMARY KEY using index "system_settings_pkey";

alter table "public"."user_roles" add constraint "user_roles_pkey" PRIMARY KEY using index "user_roles_pkey";

alter table "public"."administrators" add constraint "administrators_country_id_fkey" FOREIGN KEY (country_id) REFERENCES public.countries(id) not valid;

alter table "public"."administrators" validate constraint "administrators_country_id_fkey";

alter table "public"."administrators" add constraint "administrators_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE SET NULL not valid;

alter table "public"."administrators" validate constraint "administrators_hospital_id_fkey";

alter table "public"."administrators" add constraint "administrators_region_id_fkey" FOREIGN KEY (region_id) REFERENCES public.regions(id) not valid;

alter table "public"."administrators" validate constraint "administrators_region_id_fkey";

alter table "public"."administrators" add constraint "administrators_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."administrators" validate constraint "administrators_user_id_fkey";

alter table "public"."administrators" add constraint "administrators_user_id_key" UNIQUE using index "administrators_user_id_key";

alter table "public"."audit_logs" add constraint "audit_logs_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE SET NULL not valid;

alter table "public"."audit_logs" validate constraint "audit_logs_hospital_id_fkey";

alter table "public"."audit_logs" add constraint "audit_logs_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE SET NULL not valid;

alter table "public"."audit_logs" validate constraint "audit_logs_patient_id_fkey";

alter table "public"."audit_logs" add constraint "audit_logs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL not valid;

alter table "public"."audit_logs" validate constraint "audit_logs_user_id_fkey";

alter table "public"."chat_access_permissions" add constraint "chat_access_permissions_conversation_id_fkey" FOREIGN KEY (conversation_id) REFERENCES public.llm_conversations(id) ON DELETE CASCADE not valid;

alter table "public"."chat_access_permissions" validate constraint "chat_access_permissions_conversation_id_fkey";

alter table "public"."chat_access_permissions" add constraint "chat_access_permissions_granted_by_doctor_id_fkey" FOREIGN KEY (granted_by_doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE not valid;

alter table "public"."chat_access_permissions" validate constraint "chat_access_permissions_granted_by_doctor_id_fkey";

alter table "public"."chat_access_permissions" add constraint "chat_access_permissions_patient_id_conversation_id_valid_fr_key" UNIQUE using index "chat_access_permissions_patient_id_conversation_id_valid_fr_key";

alter table "public"."chat_access_permissions" add constraint "chat_access_permissions_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."chat_access_permissions" validate constraint "chat_access_permissions_patient_id_fkey";

alter table "public"."chat_access_permissions" add constraint "chat_access_permissions_request_id_fkey" FOREIGN KEY (request_id) REFERENCES public.chat_access_requests(id) ON DELETE SET NULL not valid;

alter table "public"."chat_access_permissions" validate constraint "chat_access_permissions_request_id_fkey";

alter table "public"."chat_access_permissions" add constraint "chat_access_permissions_revoked_by_fkey" FOREIGN KEY (revoked_by) REFERENCES auth.users(id) not valid;

alter table "public"."chat_access_permissions" validate constraint "chat_access_permissions_revoked_by_fkey";

alter table "public"."chat_access_requests" add constraint "chat_access_requests_conversation_id_fkey" FOREIGN KEY (conversation_id) REFERENCES public.llm_conversations(id) ON DELETE CASCADE not valid;

alter table "public"."chat_access_requests" validate constraint "chat_access_requests_conversation_id_fkey";

alter table "public"."chat_access_requests" add constraint "chat_access_requests_doctor_id_fkey" FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE not valid;

alter table "public"."chat_access_requests" validate constraint "chat_access_requests_doctor_id_fkey";

alter table "public"."chat_access_requests" add constraint "chat_access_requests_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."chat_access_requests" validate constraint "chat_access_requests_patient_id_fkey";

alter table "public"."countries" add constraint "countries_country_code_key" UNIQUE using index "countries_country_code_key";

alter table "public"."data_access_logs" add constraint "data_access_logs_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) not valid;

alter table "public"."data_access_logs" validate constraint "data_access_logs_case_id_fkey";

alter table "public"."data_access_logs" add constraint "data_access_logs_conversation_id_fkey" FOREIGN KEY (conversation_id) REFERENCES public.llm_conversations(id) not valid;

alter table "public"."data_access_logs" validate constraint "data_access_logs_conversation_id_fkey";

alter table "public"."data_access_logs" add constraint "data_access_logs_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) not valid;

alter table "public"."data_access_logs" validate constraint "data_access_logs_hospital_id_fkey";

alter table "public"."data_access_logs" add constraint "data_access_logs_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE SET NULL not valid;

alter table "public"."data_access_logs" validate constraint "data_access_logs_patient_id_fkey";

alter table "public"."data_access_logs" add constraint "data_access_logs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."data_access_logs" validate constraint "data_access_logs_user_id_fkey";

alter table "public"."doctor_specialties" add constraint "doctor_specialties_doctor_id_fkey" FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE not valid;

alter table "public"."doctor_specialties" validate constraint "doctor_specialties_doctor_id_fkey";

alter table "public"."doctor_specialties" add constraint "doctor_specialties_doctor_id_specialty_id_key" UNIQUE using index "doctor_specialties_doctor_id_specialty_id_key";

alter table "public"."doctor_specialties" add constraint "doctor_specialties_specialty_id_fkey" FOREIGN KEY (specialty_id) REFERENCES public.specialty_types(id) ON DELETE CASCADE not valid;

alter table "public"."doctor_specialties" validate constraint "doctor_specialties_specialty_id_fkey";

alter table "public"."doctors" add constraint "doctors_country_id_fkey" FOREIGN KEY (country_id) REFERENCES public.countries(id) not valid;

alter table "public"."doctors" validate constraint "doctors_country_id_fkey";

alter table "public"."doctors" add constraint "doctors_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE RESTRICT not valid;

alter table "public"."doctors" validate constraint "doctors_hospital_id_fkey";

alter table "public"."doctors" add constraint "doctors_region_id_fkey" FOREIGN KEY (region_id) REFERENCES public.regions(id) not valid;

alter table "public"."doctors" validate constraint "doctors_region_id_fkey";

alter table "public"."doctors" add constraint "doctors_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."doctors" validate constraint "doctors_user_id_fkey";

alter table "public"."doctors" add constraint "doctors_user_id_key" UNIQUE using index "doctors_user_id_key";

alter table "public"."doctors" add constraint "doctors_verified_by_fkey" FOREIGN KEY (verified_by) REFERENCES auth.users(id) not valid;

alter table "public"."doctors" validate constraint "doctors_verified_by_fkey";

alter table "public"."ecg_results" add constraint "ecg_results_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) ON DELETE SET NULL not valid;

alter table "public"."ecg_results" validate constraint "ecg_results_case_id_fkey";

alter table "public"."ecg_results" add constraint "ecg_results_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."ecg_results" validate constraint "ecg_results_patient_id_fkey";

alter table "public"."ecg_results" add constraint "ecg_results_reviewed_by_doctor_id_fkey" FOREIGN KEY (reviewed_by_doctor_id) REFERENCES public.doctors(id) not valid;

alter table "public"."ecg_results" validate constraint "ecg_results_reviewed_by_doctor_id_fkey";

alter table "public"."ecg_results" add constraint "ecg_results_signal_id_fkey" FOREIGN KEY (signal_id) REFERENCES public.ecg_signals(id) ON DELETE CASCADE not valid;

alter table "public"."ecg_results" validate constraint "ecg_results_signal_id_fkey";

alter table "public"."ecg_signals" add constraint "ecg_signals_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) ON DELETE SET NULL not valid;

alter table "public"."ecg_signals" validate constraint "ecg_signals_case_id_fkey";

alter table "public"."ecg_signals" add constraint "ecg_signals_file_id_fkey" FOREIGN KEY (file_id) REFERENCES public.medical_files(id) ON DELETE CASCADE not valid;

alter table "public"."ecg_signals" validate constraint "ecg_signals_file_id_fkey";

alter table "public"."ecg_signals" add constraint "ecg_signals_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."ecg_signals" validate constraint "ecg_signals_patient_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_approved_by_doctor_id_fkey" FOREIGN KEY (approved_by_doctor_id) REFERENCES public.doctors(id) not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_approved_by_doctor_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) ON DELETE SET NULL not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_case_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_doctor_id_fkey" FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_doctor_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_ecg_result_id_fkey" FOREIGN KEY (ecg_result_id) REFERENCES public.ecg_results(id) not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_ecg_result_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_mri_result_id_fkey" FOREIGN KEY (mri_result_id) REFERENCES public.mri_segmentation_results(id) not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_mri_result_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_patient_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_previous_version_id_fkey" FOREIGN KEY (previous_version_id) REFERENCES public.generated_reports(id) not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_previous_version_id_fkey";

alter table "public"."generated_reports" add constraint "generated_reports_report_number_key" UNIQUE using index "generated_reports_report_number_key";

alter table "public"."generated_reports" add constraint "generated_reports_signed_by_doctor_id_fkey" FOREIGN KEY (signed_by_doctor_id) REFERENCES public.doctors(id) not valid;

alter table "public"."generated_reports" validate constraint "generated_reports_signed_by_doctor_id_fkey";

alter table "public"."hospitals" add constraint "hospitals_hospital_code_key" UNIQUE using index "hospitals_hospital_code_key";

alter table "public"."hospitals" add constraint "hospitals_region_id_fkey" FOREIGN KEY (region_id) REFERENCES public.regions(id) ON DELETE CASCADE not valid;

alter table "public"."hospitals" validate constraint "hospitals_region_id_fkey";

alter table "public"."llm_context_configs" add constraint "llm_context_configs_config_name_key" UNIQUE using index "llm_context_configs_config_name_key";

alter table "public"."llm_conversations" add constraint "llm_conversations_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) ON DELETE SET NULL not valid;

alter table "public"."llm_conversations" validate constraint "llm_conversations_case_id_fkey";

alter table "public"."llm_conversations" add constraint "llm_conversations_doctor_id_fkey" FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE SET NULL not valid;

alter table "public"."llm_conversations" validate constraint "llm_conversations_doctor_id_fkey";

alter table "public"."llm_conversations" add constraint "llm_conversations_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE CASCADE not valid;

alter table "public"."llm_conversations" validate constraint "llm_conversations_hospital_id_fkey";

alter table "public"."llm_conversations" add constraint "llm_conversations_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."llm_conversations" validate constraint "llm_conversations_patient_id_fkey";

alter table "public"."llm_messages" add constraint "llm_messages_conversation_id_fkey" FOREIGN KEY (conversation_id) REFERENCES public.llm_conversations(id) ON DELETE CASCADE not valid;

alter table "public"."llm_messages" validate constraint "llm_messages_conversation_id_fkey";

alter table "public"."medical_cases" add constraint "medical_cases_archived_by_fkey" FOREIGN KEY (archived_by) REFERENCES auth.users(id) not valid;

alter table "public"."medical_cases" validate constraint "medical_cases_archived_by_fkey";

alter table "public"."medical_cases" add constraint "medical_cases_assigned_doctor_id_fkey" FOREIGN KEY (assigned_doctor_id) REFERENCES public.doctors(id) ON DELETE SET NULL not valid;

alter table "public"."medical_cases" validate constraint "medical_cases_assigned_doctor_id_fkey";

alter table "public"."medical_cases" add constraint "medical_cases_case_number_key" UNIQUE using index "medical_cases_case_number_key";

alter table "public"."medical_cases" add constraint "medical_cases_created_by_doctor_id_fkey" FOREIGN KEY (created_by_doctor_id) REFERENCES public.doctors(id) not valid;

alter table "public"."medical_cases" validate constraint "medical_cases_created_by_doctor_id_fkey";

alter table "public"."medical_cases" add constraint "medical_cases_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE RESTRICT not valid;

alter table "public"."medical_cases" validate constraint "medical_cases_hospital_id_fkey";

alter table "public"."medical_cases" add constraint "medical_cases_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE RESTRICT not valid;

alter table "public"."medical_cases" validate constraint "medical_cases_patient_id_fkey";

alter table "public"."medical_files" add constraint "medical_files_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) ON DELETE CASCADE not valid;

alter table "public"."medical_files" validate constraint "medical_files_case_id_fkey";

alter table "public"."medical_files" add constraint "medical_files_deleted_by_fkey" FOREIGN KEY (deleted_by) REFERENCES auth.users(id) not valid;

alter table "public"."medical_files" validate constraint "medical_files_deleted_by_fkey";

alter table "public"."medical_files" add constraint "medical_files_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."medical_files" validate constraint "medical_files_patient_id_fkey";

alter table "public"."medical_files" add constraint "medical_files_uploaded_by_fkey" FOREIGN KEY (uploaded_by) REFERENCES auth.users(id) not valid;

alter table "public"."medical_files" validate constraint "medical_files_uploaded_by_fkey";

alter table "public"."model_versions" add constraint "model_versions_created_by_fkey" FOREIGN KEY (created_by) REFERENCES auth.users(id) not valid;

alter table "public"."model_versions" validate constraint "model_versions_created_by_fkey";

alter table "public"."model_versions" add constraint "model_versions_model_name_model_version_key" UNIQUE using index "model_versions_model_name_model_version_key";

alter table "public"."mri_scans" add constraint "mri_scans_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) ON DELETE SET NULL not valid;

alter table "public"."mri_scans" validate constraint "mri_scans_case_id_fkey";

alter table "public"."mri_scans" add constraint "mri_scans_file_id_fkey" FOREIGN KEY (file_id) REFERENCES public.medical_files(id) ON DELETE CASCADE not valid;

alter table "public"."mri_scans" validate constraint "mri_scans_file_id_fkey";

alter table "public"."mri_scans" add constraint "mri_scans_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."mri_scans" validate constraint "mri_scans_patient_id_fkey";

alter table "public"."mri_segmentation_results" add constraint "mri_segmentation_results_case_id_fkey" FOREIGN KEY (case_id) REFERENCES public.medical_cases(id) ON DELETE SET NULL not valid;

alter table "public"."mri_segmentation_results" validate constraint "mri_segmentation_results_case_id_fkey";

alter table "public"."mri_segmentation_results" add constraint "mri_segmentation_results_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE not valid;

alter table "public"."mri_segmentation_results" validate constraint "mri_segmentation_results_patient_id_fkey";

alter table "public"."mri_segmentation_results" add constraint "mri_segmentation_results_reviewed_by_doctor_id_fkey" FOREIGN KEY (reviewed_by_doctor_id) REFERENCES public.doctors(id) not valid;

alter table "public"."mri_segmentation_results" validate constraint "mri_segmentation_results_reviewed_by_doctor_id_fkey";

alter table "public"."mri_segmentation_results" add constraint "mri_segmentation_results_scan_id_fkey" FOREIGN KEY (scan_id) REFERENCES public.mri_scans(id) ON DELETE CASCADE not valid;

alter table "public"."mri_segmentation_results" validate constraint "mri_segmentation_results_scan_id_fkey";

alter table "public"."notifications" add constraint "notifications_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) not valid;

alter table "public"."notifications" validate constraint "notifications_hospital_id_fkey";

alter table "public"."notifications" add constraint "notifications_patient_id_fkey" FOREIGN KEY (patient_id) REFERENCES public.patients(id) not valid;

alter table "public"."notifications" validate constraint "notifications_patient_id_fkey";

alter table "public"."notifications" add constraint "notifications_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."notifications" validate constraint "notifications_user_id_fkey";

alter table "public"."nurses" add constraint "nurses_country_id_fkey" FOREIGN KEY (country_id) REFERENCES public.countries(id) not valid;

alter table "public"."nurses" validate constraint "nurses_country_id_fkey";

alter table "public"."nurses" add constraint "nurses_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE RESTRICT not valid;

alter table "public"."nurses" validate constraint "nurses_hospital_id_fkey";

alter table "public"."nurses" add constraint "nurses_region_id_fkey" FOREIGN KEY (region_id) REFERENCES public.regions(id) not valid;

alter table "public"."nurses" validate constraint "nurses_region_id_fkey";

alter table "public"."nurses" add constraint "nurses_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."nurses" validate constraint "nurses_user_id_fkey";

alter table "public"."nurses" add constraint "nurses_user_id_key" UNIQUE using index "nurses_user_id_key";

alter table "public"."patients" add constraint "patients_country_id_fkey" FOREIGN KEY (country_id) REFERENCES public.countries(id) not valid;

alter table "public"."patients" validate constraint "patients_country_id_fkey";

alter table "public"."patients" add constraint "patients_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE RESTRICT not valid;

alter table "public"."patients" validate constraint "patients_hospital_id_fkey";

alter table "public"."patients" add constraint "patients_hospital_id_mrn_key" UNIQUE using index "patients_hospital_id_mrn_key";

alter table "public"."patients" add constraint "patients_primary_doctor_id_fkey" FOREIGN KEY (primary_doctor_id) REFERENCES public.doctors(id) not valid;

alter table "public"."patients" validate constraint "patients_primary_doctor_id_fkey";

alter table "public"."patients" add constraint "patients_region_id_fkey" FOREIGN KEY (region_id) REFERENCES public.regions(id) not valid;

alter table "public"."patients" validate constraint "patients_region_id_fkey";

alter table "public"."patients" add constraint "patients_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL not valid;

alter table "public"."patients" validate constraint "patients_user_id_fkey";

alter table "public"."patients" add constraint "patients_user_id_key" UNIQUE using index "patients_user_id_key";

alter table "public"."regions" add constraint "regions_country_id_fkey" FOREIGN KEY (country_id) REFERENCES public.countries(id) ON DELETE CASCADE not valid;

alter table "public"."regions" validate constraint "regions_country_id_fkey";

alter table "public"."regions" add constraint "regions_country_id_region_code_key" UNIQUE using index "regions_country_id_region_code_key";

alter table "public"."specialty_types" add constraint "specialty_types_parent_specialty_id_fkey" FOREIGN KEY (parent_specialty_id) REFERENCES public.specialty_types(id) not valid;

alter table "public"."specialty_types" validate constraint "specialty_types_parent_specialty_id_fkey";

alter table "public"."specialty_types" add constraint "specialty_types_specialty_code_key" UNIQUE using index "specialty_types_specialty_code_key";

alter table "public"."system_settings" add constraint "system_settings_created_by_fkey" FOREIGN KEY (created_by) REFERENCES auth.users(id) not valid;

alter table "public"."system_settings" validate constraint "system_settings_created_by_fkey";

alter table "public"."system_settings" add constraint "system_settings_scope_scope_id_setting_key_key" UNIQUE using index "system_settings_scope_scope_id_setting_key_key";

alter table "public"."system_settings" add constraint "system_settings_updated_by_fkey" FOREIGN KEY (updated_by) REFERENCES auth.users(id) not valid;

alter table "public"."system_settings" validate constraint "system_settings_updated_by_fkey";

alter table "public"."user_roles" add constraint "user_roles_granted_by_fkey" FOREIGN KEY (granted_by) REFERENCES auth.users(id) not valid;

alter table "public"."user_roles" validate constraint "user_roles_granted_by_fkey";

alter table "public"."user_roles" add constraint "user_roles_hospital_id_fkey" FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE SET NULL not valid;

alter table "public"."user_roles" validate constraint "user_roles_hospital_id_fkey";

alter table "public"."user_roles" add constraint "user_roles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_roles" validate constraint "user_roles_user_id_fkey";

alter table "public"."user_roles" add constraint "user_roles_user_id_role_hospital_id_key" UNIQUE using index "user_roles_user_id_role_hospital_id_key";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.approve_chat_access(_request_id uuid, _granted_duration_hours integer DEFAULT NULL::integer, _response_notes text DEFAULT NULL::text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _doctor_id UUID;
  _request_doctor_id UUID;
  _requested_duration INTEGER;
BEGIN
  -- Get doctor_id
  SELECT id INTO _doctor_id
  FROM public.doctors
  WHERE user_id = auth.uid();

  IF _doctor_id IS NULL THEN
    RAISE EXCEPTION 'Only doctors can approve access requests';
  END IF;

  -- Verify request belongs to this doctor
  SELECT doctor_id, requested_duration_hours 
  INTO _request_doctor_id, _requested_duration
  FROM public.chat_access_requests
  WHERE id = _request_id AND request_status = 'pending';

  IF _request_doctor_id IS NULL THEN
    RAISE EXCEPTION 'Request not found or already processed';
  END IF;

  IF _request_doctor_id != _doctor_id THEN
    RAISE EXCEPTION 'This request is not for your conversations';
  END IF;

  -- Update request
  UPDATE public.chat_access_requests
  SET 
    request_status = 'approved',
    responded_at = NOW(),
    response_notes = _response_notes,
    granted_duration_hours = COALESCE(_granted_duration_hours, _requested_duration),
    expires_at = NOW() + (COALESCE(_granted_duration_hours, _requested_duration) || ' hours')::INTERVAL
  WHERE id = _request_id;

  RETURN TRUE;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.check_user_existence_batch(user_types text[])
 RETURNS json
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE
    result JSON;
    user_type TEXT;
    count INT;
BEGIN
    result := '{}'::json;
    
    -- Check each user type
    FOREACH user_type IN ARRAY user_types LOOP
        -- Handle administrators with specific roles
        IF user_type = 'administrator' THEN
            SELECT COUNT(*) INTO count FROM administrators WHERE role = 'administrator';
            result := jsonb_set(result::jsonb, '{administrator}', to_jsonb(count > 0))::json;
            
        ELSIF user_type = 'super_admin' THEN
            SELECT COUNT(*) INTO count FROM administrators WHERE role = 'super_admin';
            result := jsonb_set(result::jsonb, '{super_admin}', to_jsonb(count > 0))::json;
            
        -- Handle other user types
        ELSIF user_type = 'doctor' THEN
            SELECT COUNT(*) INTO count FROM doctors;
            result := jsonb_set(result::jsonb, '{doctor}', to_jsonb(count > 0))::json;
            
        ELSIF user_type = 'patient' THEN
            SELECT COUNT(*) INTO count FROM patients;
            result := jsonb_set(result::jsonb, '{patient}', to_jsonb(count > 0))::json;
        END IF;
    END LOOP;
    
    RETURN result;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.create_doctor_conversation(_patient_id uuid, _case_id uuid DEFAULT NULL::uuid, _title character varying DEFAULT NULL::character varying)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _doctor_id UUID;
  _hospital_id UUID;
  _conversation_id UUID;
  _patient_name TEXT;
BEGIN
  -- Get doctor info
  SELECT id, hospital_id INTO _doctor_id, _hospital_id
  FROM public.doctors
  WHERE user_id = auth.uid();

  IF _doctor_id IS NULL THEN
    RAISE EXCEPTION 'Doctor not found for current user';
  END IF;

  -- Verify patient exists in same hospital
  SELECT first_name || ' ' || last_name INTO _patient_name
  FROM public.patients
  WHERE id = _patient_id AND hospital_id = _hospital_id;

  IF _patient_name IS NULL THEN
    RAISE EXCEPTION 'Patient not found or not in your hospital';
  END IF;

  -- Create conversation
  INSERT INTO public.llm_conversations (
    conversation_type,
    patient_id,
    doctor_id,
    case_id,
    hospital_id,
    title
  ) VALUES (
    'doctor_llm',
    _patient_id,
    _doctor_id,
    _case_id,
    _hospital_id,
    COALESCE(_title, 'Consultation: ' || _patient_name)
  )
  RETURNING id INTO _conversation_id;

  RETURN _conversation_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.create_medical_case(_patient_id uuid, _chief_complaint text, _priority public.case_priority DEFAULT 'normal'::public.case_priority, _notes text DEFAULT NULL::text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _doctor_id UUID;
  _hospital_id UUID;
  _hospital_code VARCHAR;
  _case_id UUID;
  _case_number VARCHAR;
BEGIN
  -- Get doctor info
  SELECT d.id, d.hospital_id, h.hospital_code 
  INTO _doctor_id, _hospital_id, _hospital_code
  FROM public.doctors d
  JOIN public.hospitals h ON d.hospital_id = h.id
  WHERE d.user_id = auth.uid();

  IF _doctor_id IS NULL THEN
    RAISE EXCEPTION 'Only doctors can create medical cases';
  END IF;

  -- Verify patient is in same hospital
  IF NOT EXISTS (
    SELECT 1 FROM public.patients
    WHERE id = _patient_id AND hospital_id = _hospital_id
  ) THEN
    RAISE EXCEPTION 'Patient not found in your hospital';
  END IF;

  -- Generate case number
  _case_number := public.generate_case_number(_hospital_code);

  -- Create case
  INSERT INTO public.medical_cases (
    case_number,
    patient_id,
    hospital_id,
    assigned_doctor_id,
    created_by_doctor_id,
    priority,
    chief_complaint,
    notes
  ) VALUES (
    _case_number,
    _patient_id,
    _hospital_id,
    _doctor_id,
    _doctor_id,
    _priority,
    _chief_complaint,
    _notes
  )
  RETURNING id INTO _case_id;

  RETURN _case_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.create_patient_conversation(_title character varying DEFAULT NULL::character varying)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _patient_id UUID;
  _hospital_id UUID;
  _conversation_id UUID;
BEGIN
  -- Get patient info
  SELECT id, hospital_id INTO _patient_id, _hospital_id
  FROM public.patients
  WHERE user_id = auth.uid();

  IF _patient_id IS NULL THEN
    RAISE EXCEPTION 'Patient not found for current user';
  END IF;

  -- Create conversation
  INSERT INTO public.llm_conversations (
    conversation_type,
    patient_id,
    hospital_id,
    title
  ) VALUES (
    'patient_llm',
    _patient_id,
    _hospital_id,
    COALESCE(_title, 'New Conversation')
  )
  RETURNING id INTO _conversation_id;

  RETURN _conversation_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.delete_old_audit_logs()
 RETURNS TABLE(deleted_count bigint)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    rows_deleted BIGINT;
BEGIN
    DELETE FROM public.audit_logs 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    
    RETURN QUERY SELECT rows_deleted;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.expire_chat_permissions()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _expired_count INTEGER;
BEGIN
  UPDATE public.chat_access_permissions
  SET is_active = false
  WHERE is_active = true
    AND valid_until < NOW();
  
  GET DIAGNOSTICS _expired_count = ROW_COUNT;
  
  -- Also update the corresponding requests
  UPDATE public.chat_access_requests
  SET request_status = 'expired'
  WHERE request_status = 'approved'
    AND expires_at < NOW();
    
  RETURN _expired_count;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.generate_case_number(_hospital_code character varying)
 RETURNS character varying
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE
  _date_part VARCHAR(8);
  _sequence INTEGER;
  _case_number VARCHAR(30);
BEGIN
  _date_part := TO_CHAR(NOW(), 'YYYYMMDD');
  
  SELECT COALESCE(MAX(
    CAST(SUBSTRING(case_number FROM LENGTH(_hospital_code) + 10) AS INTEGER)
  ), 0) + 1
  INTO _sequence
  FROM public.medical_cases
  WHERE case_number LIKE _hospital_code || '-' || _date_part || '%';
  
  _case_number := _hospital_code || '-' || _date_part || '-' || LPAD(_sequence::TEXT, 4, '0');
  
  RETURN _case_number;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.generate_mrn(_hospital_code character varying)
 RETURNS character varying
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE
  _year VARCHAR(2);
  _sequence INTEGER;
  _mrn VARCHAR(20);
BEGIN
  _year := TO_CHAR(NOW(), 'YY');
  
  -- Get next sequence for this hospital this year
  SELECT COALESCE(MAX(
    CAST(SUBSTRING(mrn FROM LENGTH(_hospital_code) + 3) AS INTEGER)
  ), 0) + 1
  INTO _sequence
  FROM public.patients
  WHERE mrn LIKE _hospital_code || _year || '%';
  
  _mrn := _hospital_code || _year || LPAD(_sequence::TEXT, 6, '0');
  
  RETURN _mrn;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.generate_report_number(_report_type character varying)
 RETURNS character varying
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE
  _prefix VARCHAR(3);
  _date_part VARCHAR(8);
  _sequence INTEGER;
BEGIN
  _prefix := UPPER(LEFT(_report_type, 3));
  _date_part := TO_CHAR(NOW(), 'YYYYMMDD');
  
  SELECT COALESCE(MAX(
    CAST(SUBSTRING(report_number FROM 13) AS INTEGER)
  ), 0) + 1
  INTO _sequence
  FROM public.generated_reports
  WHERE report_number LIKE _prefix || '-' || _date_part || '%';
  
  RETURN _prefix || '-' || _date_part || '-' || LPAD(_sequence::TEXT, 5, '0');
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_doctor_id_by_user(_user_id uuid)
 RETURNS uuid
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT id FROM public.doctors WHERE user_id = _user_id LIMIT 1
$function$
;

CREATE OR REPLACE FUNCTION public.get_doctor_public_info(_doctor_id uuid)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT jsonb_build_object(
    'name', d.first_name || ' ' || d.last_name,
    'hospital', h.hospital_name_en,
    'specialties', (
      SELECT COALESCE(jsonb_agg(
        jsonb_build_object(
          'name', st.specialty_name_en,
          'is_primary', ds.is_primary
        )
      ), '[]'::jsonb)
      FROM public.doctor_specialties ds
      JOIN public.specialty_types st ON ds.specialty_id = st.id
      WHERE ds.doctor_id = d.id
    ),
    'years_of_experience', d.years_of_experience
  )
  FROM public.doctors d
  JOIN public.hospitals h ON d.hospital_id = h.id
  WHERE d.id = _doctor_id
$function$
;

CREATE OR REPLACE FUNCTION public.get_patient_id_by_user(_user_id uuid)
 RETURNS uuid
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT id FROM public.patients WHERE user_id = _user_id LIMIT 1
$function$
;

CREATE OR REPLACE FUNCTION public.get_patient_llm_context(_patient_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _context JSONB;
  _patient_info JSONB;
  _medical_history JSONB;
  _recent_ecg JSONB;
  _recent_mri JSONB;
  _doctor_info JSONB;
BEGIN
  -- Get patient basic info (safe data only)
  SELECT jsonb_build_object(
    'first_name', first_name,
    'last_name', last_name,
    'age', EXTRACT(YEAR FROM AGE(date_of_birth)),
    'gender', gender,
    'blood_type', blood_type,
    'allergies', allergies,
    'chronic_conditions', chronic_conditions,
    'current_medications', current_medications
  ) INTO _patient_info
  FROM public.patients
  WHERE id = _patient_id;

  -- Get medical history (last 5 cases)
  SELECT COALESCE(jsonb_agg(
    jsonb_build_object(
      'case_number', case_number,
      'status', status,
      'diagnosis', diagnosis,
      'chief_complaint', chief_complaint,
      'created_at', created_at
    ) ORDER BY created_at DESC
  ), '[]'::jsonb) INTO _medical_history
  FROM (
    SELECT * FROM public.medical_cases
    WHERE patient_id = _patient_id
    ORDER BY created_at DESC
    LIMIT 5
  ) recent_cases;

  -- Get recent ECG results (last 3)
  SELECT COALESCE(jsonb_agg(
    jsonb_build_object(
      'heart_rate', heart_rate,
      'rhythm_classification', rhythm_classification,
      'detected_conditions', detected_conditions,
      'ai_interpretation', ai_interpretation,
      'created_at', created_at
    ) ORDER BY created_at DESC
  ), '[]'::jsonb) INTO _recent_ecg
  FROM (
    SELECT * FROM public.ecg_results
    WHERE patient_id = _patient_id AND analysis_status = 'completed'
    ORDER BY created_at DESC
    LIMIT 3
  ) recent_ecg;

  -- Get recent MRI results (last 3)
  SELECT COALESCE(jsonb_agg(
    jsonb_build_object(
      'scan_type', s.scan_type,
      'detected_abnormalities', r.detected_abnormalities,
      'ai_interpretation', r.ai_interpretation,
      'created_at', r.created_at
    ) ORDER BY r.created_at DESC
  ), '[]'::jsonb) INTO _recent_mri
  FROM (
    SELECT * FROM public.mri_segmentation_results
    WHERE patient_id = _patient_id AND analysis_status = 'completed'
    ORDER BY created_at DESC
    LIMIT 3
  ) r
  JOIN public.mri_scans s ON r.scan_id = s.id;

  -- Get primary doctor info (PUBLIC info only - name and specialty)
  SELECT jsonb_build_object(
    'name', d.first_name || ' ' || d.last_name,
    'specialties', (
      SELECT jsonb_agg(st.specialty_name_en)
      FROM public.doctor_specialties ds
      JOIN public.specialty_types st ON ds.specialty_id = st.id
      WHERE ds.doctor_id = d.id
    )
  ) INTO _doctor_info
  FROM public.patients p
  JOIN public.doctors d ON p.primary_doctor_id = d.id
  WHERE p.id = _patient_id;

  -- Build final context
  _context := jsonb_build_object(
    'patient_info', _patient_info,
    'medical_history', _medical_history,
    'recent_ecg_results', _recent_ecg,
    'recent_mri_results', _recent_mri,
    'primary_doctor', COALESCE(_doctor_info, '{}'::jsonb),
    'context_generated_at', NOW()
  );

  RETURN _context;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_user_hospital_id(_user_id uuid)
 RETURNS uuid
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT COALESCE(
    (SELECT hospital_id FROM public.doctors WHERE user_id = _user_id LIMIT 1),
    (SELECT hospital_id FROM public.nurses WHERE user_id = _user_id LIMIT 1),
    (SELECT hospital_id FROM public.administrators WHERE user_id = _user_id LIMIT 1),
    (SELECT hospital_id FROM public.patients WHERE user_id = _user_id LIMIT 1)
  )
$function$
;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _role public.app_role := 'patient'; 
  _role_str TEXT;
  _hospital_id UUID :=NULL;
  _hospital_code TEXT := 'GEN';
BEGIN

  -- ===== SAFE ROLE EXTRACTION =====
  BEGIN
    _role_str := COALESCE(
      NEW.app_metadata->>'role',
      NEW.raw_user_meta_data->>'role',
      'patient'
    );
    
    -- Only cast if not null
    IF _role_str IS NOT NULL THEN
      _role := _role_str::public.app_role;
    END IF;
  EXCEPTION WHEN OTHERS THEN
    _role := 'patient';
    RAISE LOG 'Role casting failed for user %, using patient. Error: %', NEW.email, SQLERRM;
  END;

  -- ===== SAFE HOSPITAL_ID EXTRACTION =====
  BEGIN
    _hospital_id := (
      COALESCE(
        NEW.app_metadata->>'hospital_id',
        NEW.raw_user_meta_data->>'hospital_id'
      )
    )::UUID;
  EXCEPTION WHEN OTHERS THEN
    _hospital_id := NULL;
    RAISE LOG 'Hospital ID extraction failed for user %', NEW.email;
  END;

  -- ===== GET HOSPITAL CODE =====
  IF _hospital_id IS NOT NULL THEN
    BEGIN
      SELECT hospital_code INTO _hospital_code
      FROM public.hospitals
      WHERE id = _hospital_id;
      
      IF _hospital_code IS NULL THEN
        _hospital_code := 'GEN';
      END IF;
    EXCEPTION WHEN OTHERS THEN
      _hospital_code := 'GEN';
    END;
  END IF;

  -- ===== INSERT user_roles =====
  BEGIN
    INSERT INTO public.user_roles (user_id, role, hospital_id)
    VALUES (NEW.id, _role, _hospital_id);
  EXCEPTION 
    WHEN unique_violation THEN
      RAISE LOG 'user_roles already exists for %', NEW.email;
    WHEN OTHERS THEN
      RAISE LOG 'Failed to insert user_roles for %: %', NEW.email, SQLERRM;
  END;

  -- ===== ROLE-SPECIFIC INSERTS =====
  
  IF _role = 'super_admin' THEN
    BEGIN
      INSERT INTO public.administrators (user_id, hospital_id, first_name, last_name, email)
      VALUES (
        NEW.id,
        NULL,
        COALESCE(NEW.app_metadata->>'first_name', NEW.raw_user_meta_data->>'first_name', 'Admin'),
        COALESCE(NEW.app_metadata->>'last_name', NEW.raw_user_meta_data->>'last_name', 'User'),
        NEW.email
      );
    EXCEPTION WHEN OTHERS THEN
      RAISE LOG 'Failed to create super_admin for %: %', NEW.email, SQLERRM;
    END;

  ELSIF _role = 'admin' THEN
    BEGIN
      INSERT INTO public.administrators (user_id, hospital_id, first_name, last_name, email)
      VALUES (
        NEW.id,
        _hospital_id,
        COALESCE(NEW.app_metadata->>'first_name', NEW.raw_user_meta_data->>'first_name', 'Admin'),
        COALESCE(NEW.app_metadata->>'last_name', NEW.raw_user_meta_data->>'last_name', 'User'),
        NEW.email
      );
    EXCEPTION WHEN OTHERS THEN
      RAISE LOG 'Failed to create admin for %: %', NEW.email, SQLERRM;
    END;

  ELSIF _role = 'doctor' THEN
    BEGIN
      INSERT INTO public.doctors (user_id, hospital_id, first_name, last_name, email, license_number)
      VALUES (
        NEW.id,
        _hospital_id,
        COALESCE(NEW.app_metadata->>'first_name', NEW.raw_user_meta_data->>'first_name', 'Doctor'),
        COALESCE(NEW.app_metadata->>'last_name', NEW.raw_user_meta_data->>'last_name', 'User'),
        NEW.email,
        COALESCE(NEW.app_metadata->>'license_number', NEW.raw_user_meta_data->>'license_number', 'PENDING')
      );
    EXCEPTION WHEN OTHERS THEN
      RAISE LOG 'Failed to create doctor for %: %', NEW.email, SQLERRM;
    END;

  ELSIF _role = 'nurse' THEN
    BEGIN
      INSERT INTO public.nurses (user_id, hospital_id, first_name, last_name, email)
      VALUES (
        NEW.id,
        _hospital_id,
        COALESCE(NEW.app_metadata->>'first_name', NEW.raw_user_meta_data->>'first_name', 'Nurse'),
        COALESCE(NEW.app_metadata->>'last_name', NEW.raw_user_meta_data->>'last_name', 'User'),
        NEW.email
      );
    EXCEPTION WHEN OTHERS THEN
      RAISE LOG 'Failed to create nurse for %: %', NEW.email, SQLERRM;
    END;

  ELSE -- patient (default)
    BEGIN
      INSERT INTO public.patients (user_id, hospital_id, mrn, first_name, last_name, email)
      VALUES (
        NEW.id,
        _hospital_id,
        public.generate_mrn(_hospital_code),
        COALESCE(NEW.app_metadata->>'first_name', NEW.raw_user_meta_data->>'first_name', 'Patient'),
        COALESCE(NEW.app_metadata->>'last_name', NEW.raw_user_meta_data->>'last_name', 'User'),
        NEW.email
      );
    EXCEPTION WHEN OTHERS THEN
      RAISE LOG 'Failed to create patient for %: %', NEW.email, SQLERRM;
    END;

  END IF;

  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.has_any_role(_user_id uuid, _roles public.app_role[])
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id
      AND role = ANY(_roles)
      AND is_active = true
      AND (expires_at IS NULL OR expires_at > now())
  )
$function$
;

CREATE OR REPLACE FUNCTION public.has_chat_access(_user_id uuid, _conversation_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  -- Check if user is the patient who owns the conversation
  SELECT EXISTS (
    SELECT 1 FROM public.llm_conversations c
    JOIN public.patients p ON c.patient_id = p.id
    WHERE c.id = _conversation_id 
      AND p.user_id = _user_id
      AND c.conversation_type = 'patient_llm'
  )
  -- Or check if user is the doctor who owns the conversation
  OR EXISTS (
    SELECT 1 FROM public.llm_conversations c
    JOIN public.doctors d ON c.doctor_id = d.id
    WHERE c.id = _conversation_id 
      AND d.user_id = _user_id
  )
  -- Or check if patient has valid access permission
  OR EXISTS (
    SELECT 1 FROM public.chat_access_permissions cap
    JOIN public.patients p ON cap.patient_id = p.id
    WHERE cap.conversation_id = _conversation_id
      AND p.user_id = _user_id
      AND cap.is_active = true
      AND cap.valid_from <= NOW()
      AND cap.valid_until > NOW()
  )
$function$
;

CREATE OR REPLACE FUNCTION public.has_role(_user_id uuid, _role public.app_role)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id
      AND role = _role
      AND is_active = true
      AND (expires_at IS NULL OR expires_at > now())
  )
$function$
;

CREATE OR REPLACE FUNCTION public.is_patient_doctor(_doctor_user_id uuid, _patient_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT EXISTS (
    SELECT 1 FROM public.patients p
    JOIN public.doctors d ON p.primary_doctor_id = d.id
    WHERE p.id = _patient_id AND d.user_id = _doctor_user_id
  )
  OR EXISTS (
    SELECT 1 FROM public.medical_cases mc
    JOIN public.doctors d ON mc.assigned_doctor_id = d.id
    WHERE mc.patient_id = _patient_id AND d.user_id = _doctor_user_id
  )
$function$
;

CREATE OR REPLACE FUNCTION public.log_audit_event()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _action VARCHAR(50);
  _old_values JSONB;
  _new_values JSONB;
  _patient_id UUID;
BEGIN
  -- Determine action
  IF TG_OP = 'INSERT' THEN
    _action := 'create';
    _new_values := to_jsonb(NEW);
    _old_values := NULL;
  ELSIF TG_OP = 'UPDATE' THEN
    _action := 'update';
    _old_values := to_jsonb(OLD);
    _new_values := to_jsonb(NEW);
  ELSIF TG_OP = 'DELETE' THEN
    _action := 'delete';
    _old_values := to_jsonb(OLD);
    _new_values := NULL;
  END IF;

  -- Try to get patient_id if exists
  IF TG_OP = 'DELETE' THEN
    _patient_id := OLD.patient_id;
  ELSE
    _patient_id := NEW.patient_id;
  END IF;

  -- Insert audit log
  INSERT INTO public.audit_logs (
    user_id,
    action,
    resource_type,
    resource_id,
    patient_id,
    old_values,
    new_values,
    is_sensitive
  ) VALUES (
    auth.uid(),
    _action,
    TG_TABLE_NAME,
    CASE 
      WHEN TG_OP = 'DELETE' THEN OLD.id 
      ELSE NEW.id 
    END,
    _patient_id,
    _old_values,
    _new_values,
    TRUE -- Medical data is always sensitive
  );

  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  ELSE
    RETURN NEW;
  END IF;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.notify_chat_access_request()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _doctor_user_id UUID;
  _patient_name TEXT;
BEGIN
  -- Get doctor's user_id
  SELECT user_id INTO _doctor_user_id
  FROM public.doctors WHERE id = NEW.doctor_id;

  -- Get patient name
  SELECT first_name || ' ' || last_name INTO _patient_name
  FROM public.patients WHERE id = NEW.patient_id;

  -- Create notification for doctor
  INSERT INTO public.notifications (
    user_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id,
    priority
  ) VALUES (
    _doctor_user_id,
    'chat_access_request',
    'New Chat Access Request',
    _patient_name || ' has requested access to view a conversation.',
    'chat_access_request',
    NEW.id,
    'high'
  );

  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.notify_chat_access_response()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _patient_user_id UUID;
  _notification_type public.notification_type;
  _title TEXT;
  _message TEXT;
BEGIN
  -- Only trigger on status change
  IF OLD.request_status = NEW.request_status THEN
    RETURN NEW;
  END IF;

  -- Get patient's user_id
  SELECT user_id INTO _patient_user_id
  FROM public.patients WHERE id = NEW.patient_id;

  IF NEW.request_status = 'approved' THEN
    _notification_type := 'chat_access_approved';
    _title := 'Access Request Approved';
    _message := 'Your request to view the conversation has been approved.';
    
    -- Create permission record
    INSERT INTO public.chat_access_permissions (
      patient_id,
      conversation_id,
      granted_by_doctor_id,
      request_id,
      access_level,
      valid_until
    ) VALUES (
      NEW.patient_id,
      NEW.conversation_id,
      NEW.doctor_id,
      NEW.id,
      'read_only',
      COALESCE(NEW.expires_at, NOW() + INTERVAL '24 hours')
    );
    
  ELSIF NEW.request_status = 'rejected' THEN
    _notification_type := 'chat_access_rejected';
    _title := 'Access Request Rejected';
    _message := 'Your request to view the conversation has been rejected.';
    IF NEW.response_notes IS NOT NULL THEN
      _message := _message || ' Reason: ' || NEW.response_notes;
    END IF;
  ELSE
    RETURN NEW;
  END IF;

  -- Create notification for patient
  INSERT INTO public.notifications (
    user_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id,
    priority
  ) VALUES (
    _patient_user_id,
    _notification_type,
    _title,
    _message,
    'chat_access_request',
    NEW.id,
    'normal'
  );

  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.reject_chat_access(_request_id uuid, _response_notes text DEFAULT NULL::text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _doctor_id UUID;
  _request_doctor_id UUID;
BEGIN
  -- Get doctor_id
  SELECT id INTO _doctor_id
  FROM public.doctors
  WHERE user_id = auth.uid();

  IF _doctor_id IS NULL THEN
    RAISE EXCEPTION 'Only doctors can reject access requests';
  END IF;

  -- Verify request belongs to this doctor
  SELECT doctor_id INTO _request_doctor_id
  FROM public.chat_access_requests
  WHERE id = _request_id AND request_status = 'pending';

  IF _request_doctor_id IS NULL THEN
    RAISE EXCEPTION 'Request not found or already processed';
  END IF;

  IF _request_doctor_id != _doctor_id THEN
    RAISE EXCEPTION 'This request is not for your conversations';
  END IF;

  -- Update request
  UPDATE public.chat_access_requests
  SET 
    request_status = 'rejected',
    responded_at = NOW(),
    response_notes = _response_notes
  WHERE id = _request_id;

  RETURN TRUE;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.request_chat_access(_conversation_id uuid, _request_reason text DEFAULT NULL::text, _requested_duration_hours integer DEFAULT 24)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _patient_id UUID;
  _doctor_id UUID;
  _conv_patient_id UUID;
  _request_id UUID;
BEGIN
  -- Get patient_id
  SELECT id INTO _patient_id
  FROM public.patients
  WHERE user_id = auth.uid();

  IF _patient_id IS NULL THEN
    RAISE EXCEPTION 'Only patients can request chat access';
  END IF;

  -- Get conversation details
  SELECT c.patient_id, c.doctor_id INTO _conv_patient_id, _doctor_id
  FROM public.llm_conversations c
  WHERE c.id = _conversation_id
    AND c.conversation_type IN ('doctor_llm', 'doctor_patient_llm');

  IF _doctor_id IS NULL THEN
    RAISE EXCEPTION 'Conversation not found or not a doctor conversation';
  END IF;

  -- Verify patient is the subject of the conversation
  IF _conv_patient_id != _patient_id THEN
    RAISE EXCEPTION 'You can only request access to conversations about yourself';
  END IF;

  -- Check for existing pending request
  IF EXISTS (
    SELECT 1 FROM public.chat_access_requests
    WHERE patient_id = _patient_id
      AND conversation_id = _conversation_id
      AND request_status = 'pending'
  ) THEN
    RAISE EXCEPTION 'You already have a pending request for this conversation';
  END IF;

  -- Create request
  INSERT INTO public.chat_access_requests (
    patient_id,
    conversation_id,
    doctor_id,
    request_reason,
    requested_duration_hours
  ) VALUES (
    _patient_id,
    _conversation_id,
    _doctor_id,
    _request_reason,
    _requested_duration_hours
  )
  RETURNING id INTO _request_id;

  RETURN _request_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.revoke_chat_access(_permission_id uuid, _revoke_reason text DEFAULT NULL::text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _doctor_id UUID;
  _permission_doctor_id UUID;
BEGIN
  -- Get doctor_id
  SELECT id INTO _doctor_id
  FROM public.doctors
  WHERE user_id = auth.uid();

  IF _doctor_id IS NULL THEN
    RAISE EXCEPTION 'Only doctors can revoke access';
  END IF;

  -- Verify permission was granted by this doctor
  SELECT granted_by_doctor_id INTO _permission_doctor_id
  FROM public.chat_access_permissions
  WHERE id = _permission_id AND is_active = true;

  IF _permission_doctor_id IS NULL THEN
    RAISE EXCEPTION 'Permission not found or already revoked';
  END IF;

  IF _permission_doctor_id != _doctor_id THEN
    RAISE EXCEPTION 'You can only revoke permissions you granted';
  END IF;

  -- Revoke permission
  UPDATE public.chat_access_permissions
  SET 
    is_active = false,
    revoked_at = NOW(),
    revoked_by = auth.uid(),
    revoke_reason = _revoke_reason
  WHERE id = _permission_id;

  -- Update the original request
  UPDATE public.chat_access_requests
  SET request_status = 'revoked'
  WHERE id = (
    SELECT request_id FROM public.chat_access_permissions WHERE id = _permission_id
  );

  RETURN TRUE;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.send_llm_message(_conversation_id uuid, _message_content text, _message_type public.message_type DEFAULT 'text'::public.message_type, _attachments jsonb DEFAULT '[]'::jsonb)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  _sender_type public.sender_type;
  _sender_id UUID;
  _patient_id UUID;
  _message_id UUID;
  _context JSONB;
BEGIN
  -- Verify access
  IF NOT public.has_chat_access(auth.uid(), _conversation_id) THEN
    RAISE EXCEPTION 'Access denied to this conversation';
  END IF;

  -- Determine sender type
  SELECT id INTO _sender_id FROM public.doctors WHERE user_id = auth.uid();
  IF _sender_id IS NOT NULL THEN
    _sender_type := 'doctor';
  ELSE
    SELECT id INTO _sender_id FROM public.patients WHERE user_id = auth.uid();
    IF _sender_id IS NOT NULL THEN
      _sender_type := 'patient';
    ELSE
      RAISE EXCEPTION 'User role not found';
    END IF;
  END IF;

  -- Get patient_id for context
  SELECT patient_id INTO _patient_id
  FROM public.llm_conversations
  WHERE id = _conversation_id;

  -- Get context snapshot for LLM
  _context := public.get_patient_llm_context(_patient_id);

  -- Insert message
  INSERT INTO public.llm_messages (
    conversation_id,
    sender_type,
    sender_id,
    message_content,
    message_type,
    attachments,
    llm_context_snapshot
  ) VALUES (
    _conversation_id,
    _sender_type,
    _sender_id,
    _message_content,
    _message_type,
    _attachments,
    _context
  )
  RETURNING id INTO _message_id;

  RETURN _message_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_conversation_stats()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.llm_conversations
    SET 
      message_count = message_count + 1,
      total_tokens_used = total_tokens_used + COALESCE(NEW.tokens_used, 0),
      last_message_at = NEW.created_at,
      updated_at = NOW()
    WHERE id = NEW.conversation_id;
  END IF;
  
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

grant delete on table "public"."administrators" to "anon";

grant insert on table "public"."administrators" to "anon";

grant references on table "public"."administrators" to "anon";

grant select on table "public"."administrators" to "anon";

grant trigger on table "public"."administrators" to "anon";

grant truncate on table "public"."administrators" to "anon";

grant update on table "public"."administrators" to "anon";

grant delete on table "public"."administrators" to "authenticated";

grant insert on table "public"."administrators" to "authenticated";

grant references on table "public"."administrators" to "authenticated";

grant select on table "public"."administrators" to "authenticated";

grant trigger on table "public"."administrators" to "authenticated";

grant truncate on table "public"."administrators" to "authenticated";

grant update on table "public"."administrators" to "authenticated";

grant delete on table "public"."administrators" to "service_role";

grant insert on table "public"."administrators" to "service_role";

grant references on table "public"."administrators" to "service_role";

grant select on table "public"."administrators" to "service_role";

grant trigger on table "public"."administrators" to "service_role";

grant truncate on table "public"."administrators" to "service_role";

grant update on table "public"."administrators" to "service_role";

grant delete on table "public"."audit_logs" to "anon";

grant insert on table "public"."audit_logs" to "anon";

grant references on table "public"."audit_logs" to "anon";

grant select on table "public"."audit_logs" to "anon";

grant trigger on table "public"."audit_logs" to "anon";

grant truncate on table "public"."audit_logs" to "anon";

grant update on table "public"."audit_logs" to "anon";

grant delete on table "public"."audit_logs" to "authenticated";

grant insert on table "public"."audit_logs" to "authenticated";

grant references on table "public"."audit_logs" to "authenticated";

grant select on table "public"."audit_logs" to "authenticated";

grant trigger on table "public"."audit_logs" to "authenticated";

grant truncate on table "public"."audit_logs" to "authenticated";

grant update on table "public"."audit_logs" to "authenticated";

grant delete on table "public"."audit_logs" to "service_role";

grant insert on table "public"."audit_logs" to "service_role";

grant references on table "public"."audit_logs" to "service_role";

grant select on table "public"."audit_logs" to "service_role";

grant trigger on table "public"."audit_logs" to "service_role";

grant truncate on table "public"."audit_logs" to "service_role";

grant update on table "public"."audit_logs" to "service_role";

grant delete on table "public"."chat_access_permissions" to "anon";

grant insert on table "public"."chat_access_permissions" to "anon";

grant references on table "public"."chat_access_permissions" to "anon";

grant select on table "public"."chat_access_permissions" to "anon";

grant trigger on table "public"."chat_access_permissions" to "anon";

grant truncate on table "public"."chat_access_permissions" to "anon";

grant update on table "public"."chat_access_permissions" to "anon";

grant delete on table "public"."chat_access_permissions" to "authenticated";

grant insert on table "public"."chat_access_permissions" to "authenticated";

grant references on table "public"."chat_access_permissions" to "authenticated";

grant select on table "public"."chat_access_permissions" to "authenticated";

grant trigger on table "public"."chat_access_permissions" to "authenticated";

grant truncate on table "public"."chat_access_permissions" to "authenticated";

grant update on table "public"."chat_access_permissions" to "authenticated";

grant delete on table "public"."chat_access_permissions" to "service_role";

grant insert on table "public"."chat_access_permissions" to "service_role";

grant references on table "public"."chat_access_permissions" to "service_role";

grant select on table "public"."chat_access_permissions" to "service_role";

grant trigger on table "public"."chat_access_permissions" to "service_role";

grant truncate on table "public"."chat_access_permissions" to "service_role";

grant update on table "public"."chat_access_permissions" to "service_role";

grant delete on table "public"."chat_access_requests" to "anon";

grant insert on table "public"."chat_access_requests" to "anon";

grant references on table "public"."chat_access_requests" to "anon";

grant select on table "public"."chat_access_requests" to "anon";

grant trigger on table "public"."chat_access_requests" to "anon";

grant truncate on table "public"."chat_access_requests" to "anon";

grant update on table "public"."chat_access_requests" to "anon";

grant delete on table "public"."chat_access_requests" to "authenticated";

grant insert on table "public"."chat_access_requests" to "authenticated";

grant references on table "public"."chat_access_requests" to "authenticated";

grant select on table "public"."chat_access_requests" to "authenticated";

grant trigger on table "public"."chat_access_requests" to "authenticated";

grant truncate on table "public"."chat_access_requests" to "authenticated";

grant update on table "public"."chat_access_requests" to "authenticated";

grant delete on table "public"."chat_access_requests" to "service_role";

grant insert on table "public"."chat_access_requests" to "service_role";

grant references on table "public"."chat_access_requests" to "service_role";

grant select on table "public"."chat_access_requests" to "service_role";

grant trigger on table "public"."chat_access_requests" to "service_role";

grant truncate on table "public"."chat_access_requests" to "service_role";

grant update on table "public"."chat_access_requests" to "service_role";

grant delete on table "public"."countries" to "anon";

grant insert on table "public"."countries" to "anon";

grant references on table "public"."countries" to "anon";

grant select on table "public"."countries" to "anon";

grant trigger on table "public"."countries" to "anon";

grant truncate on table "public"."countries" to "anon";

grant update on table "public"."countries" to "anon";

grant delete on table "public"."countries" to "authenticated";

grant insert on table "public"."countries" to "authenticated";

grant references on table "public"."countries" to "authenticated";

grant select on table "public"."countries" to "authenticated";

grant trigger on table "public"."countries" to "authenticated";

grant truncate on table "public"."countries" to "authenticated";

grant update on table "public"."countries" to "authenticated";

grant delete on table "public"."countries" to "service_role";

grant insert on table "public"."countries" to "service_role";

grant references on table "public"."countries" to "service_role";

grant select on table "public"."countries" to "service_role";

grant trigger on table "public"."countries" to "service_role";

grant truncate on table "public"."countries" to "service_role";

grant update on table "public"."countries" to "service_role";

grant delete on table "public"."data_access_logs" to "anon";

grant insert on table "public"."data_access_logs" to "anon";

grant references on table "public"."data_access_logs" to "anon";

grant select on table "public"."data_access_logs" to "anon";

grant trigger on table "public"."data_access_logs" to "anon";

grant truncate on table "public"."data_access_logs" to "anon";

grant update on table "public"."data_access_logs" to "anon";

grant delete on table "public"."data_access_logs" to "authenticated";

grant insert on table "public"."data_access_logs" to "authenticated";

grant references on table "public"."data_access_logs" to "authenticated";

grant select on table "public"."data_access_logs" to "authenticated";

grant trigger on table "public"."data_access_logs" to "authenticated";

grant truncate on table "public"."data_access_logs" to "authenticated";

grant update on table "public"."data_access_logs" to "authenticated";

grant delete on table "public"."data_access_logs" to "service_role";

grant insert on table "public"."data_access_logs" to "service_role";

grant references on table "public"."data_access_logs" to "service_role";

grant select on table "public"."data_access_logs" to "service_role";

grant trigger on table "public"."data_access_logs" to "service_role";

grant truncate on table "public"."data_access_logs" to "service_role";

grant update on table "public"."data_access_logs" to "service_role";

grant delete on table "public"."doctor_specialties" to "anon";

grant insert on table "public"."doctor_specialties" to "anon";

grant references on table "public"."doctor_specialties" to "anon";

grant select on table "public"."doctor_specialties" to "anon";

grant trigger on table "public"."doctor_specialties" to "anon";

grant truncate on table "public"."doctor_specialties" to "anon";

grant update on table "public"."doctor_specialties" to "anon";

grant delete on table "public"."doctor_specialties" to "authenticated";

grant insert on table "public"."doctor_specialties" to "authenticated";

grant references on table "public"."doctor_specialties" to "authenticated";

grant select on table "public"."doctor_specialties" to "authenticated";

grant trigger on table "public"."doctor_specialties" to "authenticated";

grant truncate on table "public"."doctor_specialties" to "authenticated";

grant update on table "public"."doctor_specialties" to "authenticated";

grant delete on table "public"."doctor_specialties" to "service_role";

grant insert on table "public"."doctor_specialties" to "service_role";

grant references on table "public"."doctor_specialties" to "service_role";

grant select on table "public"."doctor_specialties" to "service_role";

grant trigger on table "public"."doctor_specialties" to "service_role";

grant truncate on table "public"."doctor_specialties" to "service_role";

grant update on table "public"."doctor_specialties" to "service_role";

grant delete on table "public"."doctors" to "anon";

grant insert on table "public"."doctors" to "anon";

grant references on table "public"."doctors" to "anon";

grant select on table "public"."doctors" to "anon";

grant trigger on table "public"."doctors" to "anon";

grant truncate on table "public"."doctors" to "anon";

grant update on table "public"."doctors" to "anon";

grant delete on table "public"."doctors" to "authenticated";

grant insert on table "public"."doctors" to "authenticated";

grant references on table "public"."doctors" to "authenticated";

grant select on table "public"."doctors" to "authenticated";

grant trigger on table "public"."doctors" to "authenticated";

grant truncate on table "public"."doctors" to "authenticated";

grant update on table "public"."doctors" to "authenticated";

grant delete on table "public"."doctors" to "service_role";

grant insert on table "public"."doctors" to "service_role";

grant references on table "public"."doctors" to "service_role";

grant select on table "public"."doctors" to "service_role";

grant trigger on table "public"."doctors" to "service_role";

grant truncate on table "public"."doctors" to "service_role";

grant update on table "public"."doctors" to "service_role";

grant delete on table "public"."ecg_results" to "anon";

grant insert on table "public"."ecg_results" to "anon";

grant references on table "public"."ecg_results" to "anon";

grant select on table "public"."ecg_results" to "anon";

grant trigger on table "public"."ecg_results" to "anon";

grant truncate on table "public"."ecg_results" to "anon";

grant update on table "public"."ecg_results" to "anon";

grant delete on table "public"."ecg_results" to "authenticated";

grant insert on table "public"."ecg_results" to "authenticated";

grant references on table "public"."ecg_results" to "authenticated";

grant select on table "public"."ecg_results" to "authenticated";

grant trigger on table "public"."ecg_results" to "authenticated";

grant truncate on table "public"."ecg_results" to "authenticated";

grant update on table "public"."ecg_results" to "authenticated";

grant delete on table "public"."ecg_results" to "service_role";

grant insert on table "public"."ecg_results" to "service_role";

grant references on table "public"."ecg_results" to "service_role";

grant select on table "public"."ecg_results" to "service_role";

grant trigger on table "public"."ecg_results" to "service_role";

grant truncate on table "public"."ecg_results" to "service_role";

grant update on table "public"."ecg_results" to "service_role";

grant delete on table "public"."ecg_signals" to "anon";

grant insert on table "public"."ecg_signals" to "anon";

grant references on table "public"."ecg_signals" to "anon";

grant select on table "public"."ecg_signals" to "anon";

grant trigger on table "public"."ecg_signals" to "anon";

grant truncate on table "public"."ecg_signals" to "anon";

grant update on table "public"."ecg_signals" to "anon";

grant delete on table "public"."ecg_signals" to "authenticated";

grant insert on table "public"."ecg_signals" to "authenticated";

grant references on table "public"."ecg_signals" to "authenticated";

grant select on table "public"."ecg_signals" to "authenticated";

grant trigger on table "public"."ecg_signals" to "authenticated";

grant truncate on table "public"."ecg_signals" to "authenticated";

grant update on table "public"."ecg_signals" to "authenticated";

grant delete on table "public"."ecg_signals" to "service_role";

grant insert on table "public"."ecg_signals" to "service_role";

grant references on table "public"."ecg_signals" to "service_role";

grant select on table "public"."ecg_signals" to "service_role";

grant trigger on table "public"."ecg_signals" to "service_role";

grant truncate on table "public"."ecg_signals" to "service_role";

grant update on table "public"."ecg_signals" to "service_role";

grant delete on table "public"."generated_reports" to "anon";

grant insert on table "public"."generated_reports" to "anon";

grant references on table "public"."generated_reports" to "anon";

grant select on table "public"."generated_reports" to "anon";

grant trigger on table "public"."generated_reports" to "anon";

grant truncate on table "public"."generated_reports" to "anon";

grant update on table "public"."generated_reports" to "anon";

grant delete on table "public"."generated_reports" to "authenticated";

grant insert on table "public"."generated_reports" to "authenticated";

grant references on table "public"."generated_reports" to "authenticated";

grant select on table "public"."generated_reports" to "authenticated";

grant trigger on table "public"."generated_reports" to "authenticated";

grant truncate on table "public"."generated_reports" to "authenticated";

grant update on table "public"."generated_reports" to "authenticated";

grant delete on table "public"."generated_reports" to "service_role";

grant insert on table "public"."generated_reports" to "service_role";

grant references on table "public"."generated_reports" to "service_role";

grant select on table "public"."generated_reports" to "service_role";

grant trigger on table "public"."generated_reports" to "service_role";

grant truncate on table "public"."generated_reports" to "service_role";

grant update on table "public"."generated_reports" to "service_role";

grant delete on table "public"."hospitals" to "anon";

grant insert on table "public"."hospitals" to "anon";

grant references on table "public"."hospitals" to "anon";

grant select on table "public"."hospitals" to "anon";

grant trigger on table "public"."hospitals" to "anon";

grant truncate on table "public"."hospitals" to "anon";

grant update on table "public"."hospitals" to "anon";

grant delete on table "public"."hospitals" to "authenticated";

grant insert on table "public"."hospitals" to "authenticated";

grant references on table "public"."hospitals" to "authenticated";

grant select on table "public"."hospitals" to "authenticated";

grant trigger on table "public"."hospitals" to "authenticated";

grant truncate on table "public"."hospitals" to "authenticated";

grant update on table "public"."hospitals" to "authenticated";

grant delete on table "public"."hospitals" to "service_role";

grant insert on table "public"."hospitals" to "service_role";

grant references on table "public"."hospitals" to "service_role";

grant select on table "public"."hospitals" to "service_role";

grant trigger on table "public"."hospitals" to "service_role";

grant truncate on table "public"."hospitals" to "service_role";

grant update on table "public"."hospitals" to "service_role";

grant delete on table "public"."llm_context_configs" to "anon";

grant insert on table "public"."llm_context_configs" to "anon";

grant references on table "public"."llm_context_configs" to "anon";

grant select on table "public"."llm_context_configs" to "anon";

grant trigger on table "public"."llm_context_configs" to "anon";

grant truncate on table "public"."llm_context_configs" to "anon";

grant update on table "public"."llm_context_configs" to "anon";

grant delete on table "public"."llm_context_configs" to "authenticated";

grant insert on table "public"."llm_context_configs" to "authenticated";

grant references on table "public"."llm_context_configs" to "authenticated";

grant select on table "public"."llm_context_configs" to "authenticated";

grant trigger on table "public"."llm_context_configs" to "authenticated";

grant truncate on table "public"."llm_context_configs" to "authenticated";

grant update on table "public"."llm_context_configs" to "authenticated";

grant delete on table "public"."llm_context_configs" to "service_role";

grant insert on table "public"."llm_context_configs" to "service_role";

grant references on table "public"."llm_context_configs" to "service_role";

grant select on table "public"."llm_context_configs" to "service_role";

grant trigger on table "public"."llm_context_configs" to "service_role";

grant truncate on table "public"."llm_context_configs" to "service_role";

grant update on table "public"."llm_context_configs" to "service_role";

grant delete on table "public"."llm_conversations" to "anon";

grant insert on table "public"."llm_conversations" to "anon";

grant references on table "public"."llm_conversations" to "anon";

grant select on table "public"."llm_conversations" to "anon";

grant trigger on table "public"."llm_conversations" to "anon";

grant truncate on table "public"."llm_conversations" to "anon";

grant update on table "public"."llm_conversations" to "anon";

grant delete on table "public"."llm_conversations" to "authenticated";

grant insert on table "public"."llm_conversations" to "authenticated";

grant references on table "public"."llm_conversations" to "authenticated";

grant select on table "public"."llm_conversations" to "authenticated";

grant trigger on table "public"."llm_conversations" to "authenticated";

grant truncate on table "public"."llm_conversations" to "authenticated";

grant update on table "public"."llm_conversations" to "authenticated";

grant delete on table "public"."llm_conversations" to "service_role";

grant insert on table "public"."llm_conversations" to "service_role";

grant references on table "public"."llm_conversations" to "service_role";

grant select on table "public"."llm_conversations" to "service_role";

grant trigger on table "public"."llm_conversations" to "service_role";

grant truncate on table "public"."llm_conversations" to "service_role";

grant update on table "public"."llm_conversations" to "service_role";

grant delete on table "public"."llm_messages" to "anon";

grant insert on table "public"."llm_messages" to "anon";

grant references on table "public"."llm_messages" to "anon";

grant select on table "public"."llm_messages" to "anon";

grant trigger on table "public"."llm_messages" to "anon";

grant truncate on table "public"."llm_messages" to "anon";

grant update on table "public"."llm_messages" to "anon";

grant delete on table "public"."llm_messages" to "authenticated";

grant insert on table "public"."llm_messages" to "authenticated";

grant references on table "public"."llm_messages" to "authenticated";

grant select on table "public"."llm_messages" to "authenticated";

grant trigger on table "public"."llm_messages" to "authenticated";

grant truncate on table "public"."llm_messages" to "authenticated";

grant update on table "public"."llm_messages" to "authenticated";

grant delete on table "public"."llm_messages" to "service_role";

grant insert on table "public"."llm_messages" to "service_role";

grant references on table "public"."llm_messages" to "service_role";

grant select on table "public"."llm_messages" to "service_role";

grant trigger on table "public"."llm_messages" to "service_role";

grant truncate on table "public"."llm_messages" to "service_role";

grant update on table "public"."llm_messages" to "service_role";

grant delete on table "public"."medical_cases" to "anon";

grant insert on table "public"."medical_cases" to "anon";

grant references on table "public"."medical_cases" to "anon";

grant select on table "public"."medical_cases" to "anon";

grant trigger on table "public"."medical_cases" to "anon";

grant truncate on table "public"."medical_cases" to "anon";

grant update on table "public"."medical_cases" to "anon";

grant delete on table "public"."medical_cases" to "authenticated";

grant insert on table "public"."medical_cases" to "authenticated";

grant references on table "public"."medical_cases" to "authenticated";

grant select on table "public"."medical_cases" to "authenticated";

grant trigger on table "public"."medical_cases" to "authenticated";

grant truncate on table "public"."medical_cases" to "authenticated";

grant update on table "public"."medical_cases" to "authenticated";

grant delete on table "public"."medical_cases" to "service_role";

grant insert on table "public"."medical_cases" to "service_role";

grant references on table "public"."medical_cases" to "service_role";

grant select on table "public"."medical_cases" to "service_role";

grant trigger on table "public"."medical_cases" to "service_role";

grant truncate on table "public"."medical_cases" to "service_role";

grant update on table "public"."medical_cases" to "service_role";

grant delete on table "public"."medical_files" to "anon";

grant insert on table "public"."medical_files" to "anon";

grant references on table "public"."medical_files" to "anon";

grant select on table "public"."medical_files" to "anon";

grant trigger on table "public"."medical_files" to "anon";

grant truncate on table "public"."medical_files" to "anon";

grant update on table "public"."medical_files" to "anon";

grant delete on table "public"."medical_files" to "authenticated";

grant insert on table "public"."medical_files" to "authenticated";

grant references on table "public"."medical_files" to "authenticated";

grant select on table "public"."medical_files" to "authenticated";

grant trigger on table "public"."medical_files" to "authenticated";

grant truncate on table "public"."medical_files" to "authenticated";

grant update on table "public"."medical_files" to "authenticated";

grant delete on table "public"."medical_files" to "service_role";

grant insert on table "public"."medical_files" to "service_role";

grant references on table "public"."medical_files" to "service_role";

grant select on table "public"."medical_files" to "service_role";

grant trigger on table "public"."medical_files" to "service_role";

grant truncate on table "public"."medical_files" to "service_role";

grant update on table "public"."medical_files" to "service_role";

grant delete on table "public"."model_versions" to "anon";

grant insert on table "public"."model_versions" to "anon";

grant references on table "public"."model_versions" to "anon";

grant select on table "public"."model_versions" to "anon";

grant trigger on table "public"."model_versions" to "anon";

grant truncate on table "public"."model_versions" to "anon";

grant update on table "public"."model_versions" to "anon";

grant delete on table "public"."model_versions" to "authenticated";

grant insert on table "public"."model_versions" to "authenticated";

grant references on table "public"."model_versions" to "authenticated";

grant select on table "public"."model_versions" to "authenticated";

grant trigger on table "public"."model_versions" to "authenticated";

grant truncate on table "public"."model_versions" to "authenticated";

grant update on table "public"."model_versions" to "authenticated";

grant delete on table "public"."model_versions" to "service_role";

grant insert on table "public"."model_versions" to "service_role";

grant references on table "public"."model_versions" to "service_role";

grant select on table "public"."model_versions" to "service_role";

grant trigger on table "public"."model_versions" to "service_role";

grant truncate on table "public"."model_versions" to "service_role";

grant update on table "public"."model_versions" to "service_role";

grant delete on table "public"."mri_scans" to "anon";

grant insert on table "public"."mri_scans" to "anon";

grant references on table "public"."mri_scans" to "anon";

grant select on table "public"."mri_scans" to "anon";

grant trigger on table "public"."mri_scans" to "anon";

grant truncate on table "public"."mri_scans" to "anon";

grant update on table "public"."mri_scans" to "anon";

grant delete on table "public"."mri_scans" to "authenticated";

grant insert on table "public"."mri_scans" to "authenticated";

grant references on table "public"."mri_scans" to "authenticated";

grant select on table "public"."mri_scans" to "authenticated";

grant trigger on table "public"."mri_scans" to "authenticated";

grant truncate on table "public"."mri_scans" to "authenticated";

grant update on table "public"."mri_scans" to "authenticated";

grant delete on table "public"."mri_scans" to "service_role";

grant insert on table "public"."mri_scans" to "service_role";

grant references on table "public"."mri_scans" to "service_role";

grant select on table "public"."mri_scans" to "service_role";

grant trigger on table "public"."mri_scans" to "service_role";

grant truncate on table "public"."mri_scans" to "service_role";

grant update on table "public"."mri_scans" to "service_role";

grant delete on table "public"."mri_segmentation_results" to "anon";

grant insert on table "public"."mri_segmentation_results" to "anon";

grant references on table "public"."mri_segmentation_results" to "anon";

grant select on table "public"."mri_segmentation_results" to "anon";

grant trigger on table "public"."mri_segmentation_results" to "anon";

grant truncate on table "public"."mri_segmentation_results" to "anon";

grant update on table "public"."mri_segmentation_results" to "anon";

grant delete on table "public"."mri_segmentation_results" to "authenticated";

grant insert on table "public"."mri_segmentation_results" to "authenticated";

grant references on table "public"."mri_segmentation_results" to "authenticated";

grant select on table "public"."mri_segmentation_results" to "authenticated";

grant trigger on table "public"."mri_segmentation_results" to "authenticated";

grant truncate on table "public"."mri_segmentation_results" to "authenticated";

grant update on table "public"."mri_segmentation_results" to "authenticated";

grant delete on table "public"."mri_segmentation_results" to "service_role";

grant insert on table "public"."mri_segmentation_results" to "service_role";

grant references on table "public"."mri_segmentation_results" to "service_role";

grant select on table "public"."mri_segmentation_results" to "service_role";

grant trigger on table "public"."mri_segmentation_results" to "service_role";

grant truncate on table "public"."mri_segmentation_results" to "service_role";

grant update on table "public"."mri_segmentation_results" to "service_role";

grant delete on table "public"."notifications" to "anon";

grant insert on table "public"."notifications" to "anon";

grant references on table "public"."notifications" to "anon";

grant select on table "public"."notifications" to "anon";

grant trigger on table "public"."notifications" to "anon";

grant truncate on table "public"."notifications" to "anon";

grant update on table "public"."notifications" to "anon";

grant delete on table "public"."notifications" to "authenticated";

grant insert on table "public"."notifications" to "authenticated";

grant references on table "public"."notifications" to "authenticated";

grant select on table "public"."notifications" to "authenticated";

grant trigger on table "public"."notifications" to "authenticated";

grant truncate on table "public"."notifications" to "authenticated";

grant update on table "public"."notifications" to "authenticated";

grant delete on table "public"."notifications" to "service_role";

grant insert on table "public"."notifications" to "service_role";

grant references on table "public"."notifications" to "service_role";

grant select on table "public"."notifications" to "service_role";

grant trigger on table "public"."notifications" to "service_role";

grant truncate on table "public"."notifications" to "service_role";

grant update on table "public"."notifications" to "service_role";

grant delete on table "public"."nurses" to "anon";

grant insert on table "public"."nurses" to "anon";

grant references on table "public"."nurses" to "anon";

grant select on table "public"."nurses" to "anon";

grant trigger on table "public"."nurses" to "anon";

grant truncate on table "public"."nurses" to "anon";

grant update on table "public"."nurses" to "anon";

grant delete on table "public"."nurses" to "authenticated";

grant insert on table "public"."nurses" to "authenticated";

grant references on table "public"."nurses" to "authenticated";

grant select on table "public"."nurses" to "authenticated";

grant trigger on table "public"."nurses" to "authenticated";

grant truncate on table "public"."nurses" to "authenticated";

grant update on table "public"."nurses" to "authenticated";

grant delete on table "public"."nurses" to "service_role";

grant insert on table "public"."nurses" to "service_role";

grant references on table "public"."nurses" to "service_role";

grant select on table "public"."nurses" to "service_role";

grant trigger on table "public"."nurses" to "service_role";

grant truncate on table "public"."nurses" to "service_role";

grant update on table "public"."nurses" to "service_role";

grant delete on table "public"."patients" to "anon";

grant insert on table "public"."patients" to "anon";

grant references on table "public"."patients" to "anon";

grant select on table "public"."patients" to "anon";

grant trigger on table "public"."patients" to "anon";

grant truncate on table "public"."patients" to "anon";

grant update on table "public"."patients" to "anon";

grant delete on table "public"."patients" to "authenticated";

grant insert on table "public"."patients" to "authenticated";

grant references on table "public"."patients" to "authenticated";

grant select on table "public"."patients" to "authenticated";

grant trigger on table "public"."patients" to "authenticated";

grant truncate on table "public"."patients" to "authenticated";

grant update on table "public"."patients" to "authenticated";

grant delete on table "public"."patients" to "service_role";

grant insert on table "public"."patients" to "service_role";

grant references on table "public"."patients" to "service_role";

grant select on table "public"."patients" to "service_role";

grant trigger on table "public"."patients" to "service_role";

grant truncate on table "public"."patients" to "service_role";

grant update on table "public"."patients" to "service_role";

grant delete on table "public"."regions" to "anon";

grant insert on table "public"."regions" to "anon";

grant references on table "public"."regions" to "anon";

grant select on table "public"."regions" to "anon";

grant trigger on table "public"."regions" to "anon";

grant truncate on table "public"."regions" to "anon";

grant update on table "public"."regions" to "anon";

grant delete on table "public"."regions" to "authenticated";

grant insert on table "public"."regions" to "authenticated";

grant references on table "public"."regions" to "authenticated";

grant select on table "public"."regions" to "authenticated";

grant trigger on table "public"."regions" to "authenticated";

grant truncate on table "public"."regions" to "authenticated";

grant update on table "public"."regions" to "authenticated";

grant delete on table "public"."regions" to "service_role";

grant insert on table "public"."regions" to "service_role";

grant references on table "public"."regions" to "service_role";

grant select on table "public"."regions" to "service_role";

grant trigger on table "public"."regions" to "service_role";

grant truncate on table "public"."regions" to "service_role";

grant update on table "public"."regions" to "service_role";

grant delete on table "public"."specialty_types" to "anon";

grant insert on table "public"."specialty_types" to "anon";

grant references on table "public"."specialty_types" to "anon";

grant select on table "public"."specialty_types" to "anon";

grant trigger on table "public"."specialty_types" to "anon";

grant truncate on table "public"."specialty_types" to "anon";

grant update on table "public"."specialty_types" to "anon";

grant delete on table "public"."specialty_types" to "authenticated";

grant insert on table "public"."specialty_types" to "authenticated";

grant references on table "public"."specialty_types" to "authenticated";

grant select on table "public"."specialty_types" to "authenticated";

grant trigger on table "public"."specialty_types" to "authenticated";

grant truncate on table "public"."specialty_types" to "authenticated";

grant update on table "public"."specialty_types" to "authenticated";

grant delete on table "public"."specialty_types" to "service_role";

grant insert on table "public"."specialty_types" to "service_role";

grant references on table "public"."specialty_types" to "service_role";

grant select on table "public"."specialty_types" to "service_role";

grant trigger on table "public"."specialty_types" to "service_role";

grant truncate on table "public"."specialty_types" to "service_role";

grant update on table "public"."specialty_types" to "service_role";

grant delete on table "public"."system_settings" to "anon";

grant insert on table "public"."system_settings" to "anon";

grant references on table "public"."system_settings" to "anon";

grant select on table "public"."system_settings" to "anon";

grant trigger on table "public"."system_settings" to "anon";

grant truncate on table "public"."system_settings" to "anon";

grant update on table "public"."system_settings" to "anon";

grant delete on table "public"."system_settings" to "authenticated";

grant insert on table "public"."system_settings" to "authenticated";

grant references on table "public"."system_settings" to "authenticated";

grant select on table "public"."system_settings" to "authenticated";

grant trigger on table "public"."system_settings" to "authenticated";

grant truncate on table "public"."system_settings" to "authenticated";

grant update on table "public"."system_settings" to "authenticated";

grant delete on table "public"."system_settings" to "service_role";

grant insert on table "public"."system_settings" to "service_role";

grant references on table "public"."system_settings" to "service_role";

grant select on table "public"."system_settings" to "service_role";

grant trigger on table "public"."system_settings" to "service_role";

grant truncate on table "public"."system_settings" to "service_role";

grant update on table "public"."system_settings" to "service_role";

grant delete on table "public"."user_roles" to "anon";

grant insert on table "public"."user_roles" to "anon";

grant references on table "public"."user_roles" to "anon";

grant select on table "public"."user_roles" to "anon";

grant trigger on table "public"."user_roles" to "anon";

grant truncate on table "public"."user_roles" to "anon";

grant update on table "public"."user_roles" to "anon";

grant delete on table "public"."user_roles" to "authenticated";

grant insert on table "public"."user_roles" to "authenticated";

grant references on table "public"."user_roles" to "authenticated";

grant select on table "public"."user_roles" to "authenticated";

grant trigger on table "public"."user_roles" to "authenticated";

grant truncate on table "public"."user_roles" to "authenticated";

grant update on table "public"."user_roles" to "authenticated";

grant delete on table "public"."user_roles" to "service_role";

grant insert on table "public"."user_roles" to "service_role";

grant references on table "public"."user_roles" to "service_role";

grant select on table "public"."user_roles" to "service_role";

grant trigger on table "public"."user_roles" to "service_role";

grant truncate on table "public"."user_roles" to "service_role";

grant update on table "public"."user_roles" to "service_role";


  create policy "admins_update_own_profile"
  on "public"."administrators"
  as permissive
  for update
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "admins_view_own_profile"
  on "public"."administrators"
  as permissive
  for select
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "service_role_administrators"
  on "public"."administrators"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "super_admins_manage_all_admins"
  on "public"."administrators"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'super_admin'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "Admins can view audit logs for their hospital"
  on "public"."audit_logs"
  as permissive
  for select
  to public
using ((hospital_id IN ( SELECT administrators.hospital_id
   FROM public.administrators
  WHERE (administrators.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Admins view all logs"
  on "public"."audit_logs"
  as permissive
  for select
  to authenticated
using ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = 'super_admin'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "Service role full access"
  on "public"."audit_logs"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "Users view own logs"
  on "public"."audit_logs"
  as permissive
  for select
  to authenticated
using ((user_id = auth.uid()));



  create policy "Doctors can manage permissions they granted"
  on "public"."chat_access_permissions"
  as permissive
  for all
  to public
using ((granted_by_doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Patients can view their permissions"
  on "public"."chat_access_permissions"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Doctors can update requests (approve/reject)"
  on "public"."chat_access_requests"
  as permissive
  for update
  to public
using ((doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Doctors can view requests for their conversations"
  on "public"."chat_access_requests"
  as permissive
  for select
  to public
using ((doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Patients can create access requests"
  on "public"."chat_access_requests"
  as permissive
  for insert
  to public
with check ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Patients can view their own requests"
  on "public"."chat_access_requests"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Anyone can view countries"
  on "public"."countries"
  as permissive
  for select
  to authenticated
using ((is_active = true));



  create policy "Admins can view all access logs in their hospital"
  on "public"."data_access_logs"
  as permissive
  for select
  to authenticated
using ((public.has_role(auth.uid(), 'admin'::public.app_role) AND (hospital_id = public.get_user_hospital_id(auth.uid()))));



  create policy "Users can view their own access logs"
  on "public"."data_access_logs"
  as permissive
  for select
  to authenticated
using ((user_id = auth.uid()));



  create policy "Anyone can view doctor specialties"
  on "public"."doctor_specialties"
  as permissive
  for select
  to public
using (true);



  create policy "Doctors can manage their own specialties"
  on "public"."doctor_specialties"
  as permissive
  for all
  to public
using ((doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Admins can manage doctors in their hospital"
  on "public"."doctors"
  as permissive
  for all
  to public
using ((hospital_id IN ( SELECT administrators.hospital_id
   FROM public.administrators
  WHERE (administrators.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Doctors can update their own profile"
  on "public"."doctors"
  as permissive
  for update
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "Doctors can view their own profile"
  on "public"."doctors"
  as permissive
  for select
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "Patients can view their assigned doctor"
  on "public"."doctors"
  as permissive
  for select
  to public
using ((id IN ( SELECT patients.primary_doctor_id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Users can view doctors in their hospital"
  on "public"."doctors"
  as permissive
  for select
  to public
using ((hospital_id IN ( SELECT doctors_1.hospital_id
   FROM public.doctors doctors_1
  WHERE (doctors_1.user_id = ( SELECT auth.uid() AS uid))
UNION
 SELECT nurses.hospital_id
   FROM public.nurses
  WHERE (nurses.user_id = ( SELECT auth.uid() AS uid))
UNION
 SELECT administrators.hospital_id
   FROM public.administrators
  WHERE (administrators.user_id = ( SELECT auth.uid() AS uid))
UNION
 SELECT patients.hospital_id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Doctors can update ECG results (review)"
  on "public"."ecg_results"
  as permissive
  for update
  to public
using ((EXISTS ( SELECT 1
   FROM (public.patients p
     JOIN public.doctors d ON ((d.hospital_id = p.hospital_id)))
  WHERE ((p.id = ecg_results.patient_id) AND (d.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "Doctors can view ECG results for their hospital"
  on "public"."ecg_results"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM (public.patients p
     JOIN public.doctors d ON ((d.hospital_id = p.hospital_id)))
  WHERE ((p.id = ecg_results.patient_id) AND (d.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "Patients can view their own ECG results"
  on "public"."ecg_results"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "doctors_view_hospital_ecg_signals"
  on "public"."ecg_signals"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM (public.patients p
     JOIN public.doctors d ON ((d.hospital_id = p.hospital_id)))
  WHERE ((p.id = ecg_signals.patient_id) AND (d.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "patients_view_own_ecg_signals"
  on "public"."ecg_signals"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "service_role_ecg_signals"
  on "public"."ecg_signals"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "Doctors can create and update reports"
  on "public"."generated_reports"
  as permissive
  for all
  to public
using ((doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Doctors can view reports for their hospital"
  on "public"."generated_reports"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM (public.patients p
     JOIN public.doctors d ON ((d.hospital_id = p.hospital_id)))
  WHERE ((p.id = generated_reports.patient_id) AND (d.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "Patients can view their own reports"
  on "public"."generated_reports"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Anyone can view hospitals"
  on "public"."hospitals"
  as permissive
  for select
  to authenticated
using ((is_active = true));



  create policy "service_role_llm_context_configs"
  on "public"."llm_context_configs"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "super_admins_manage_llm_configs"
  on "public"."llm_context_configs"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'super_admin'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "Doctors can create conversations"
  on "public"."llm_conversations"
  as permissive
  for insert
  to public
with check (((conversation_type = ANY (ARRAY['doctor_llm'::public.conversation_type, 'doctor_patient_llm'::public.conversation_type])) AND (doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "Doctors can view conversations about their patients"
  on "public"."llm_conversations"
  as permissive
  for select
  to public
using ((doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Patients can create their own conversations"
  on "public"."llm_conversations"
  as permissive
  for insert
  to public
with check (((conversation_type = 'patient_llm'::public.conversation_type) AND (patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "Patients can view permitted doctor conversations"
  on "public"."llm_conversations"
  as permissive
  for select
  to public
using (((conversation_type = 'doctor_patient_llm'::public.conversation_type) AND public.has_chat_access(( SELECT auth.uid() AS uid), id)));



  create policy "Patients can view their own conversations"
  on "public"."llm_conversations"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Users can create messages in their conversations"
  on "public"."llm_messages"
  as permissive
  for insert
  to public
with check (public.has_chat_access(( SELECT auth.uid() AS uid), conversation_id));



  create policy "Users can view messages in accessible conversations"
  on "public"."llm_messages"
  as permissive
  for select
  to public
using (public.has_chat_access(( SELECT auth.uid() AS uid), conversation_id));



  create policy "Doctors can create cases"
  on "public"."medical_cases"
  as permissive
  for insert
  to public
with check ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "Doctors can update their assigned cases"
  on "public"."medical_cases"
  as permissive
  for update
  to public
using (((assigned_doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))) OR (created_by_doctor_id IN ( SELECT doctors.id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "Doctors can view cases in their hospital"
  on "public"."medical_cases"
  as permissive
  for select
  to public
using ((hospital_id IN ( SELECT doctors.hospital_id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Patients can view their own cases"
  on "public"."medical_cases"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Doctors can upload files"
  on "public"."medical_files"
  as permissive
  for insert
  to public
with check ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "Doctors can view files for their hospital"
  on "public"."medical_files"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM (public.patients p
     JOIN public.doctors d ON ((d.hospital_id = p.hospital_id)))
  WHERE ((p.id = medical_files.patient_id) AND (d.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "Patients can view their own files"
  on "public"."medical_files"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "service_role_model_versions"
  on "public"."model_versions"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "super_admins_manage_model_versions"
  on "public"."model_versions"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'super_admin'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "doctors_view_hospital_mri_scans"
  on "public"."mri_scans"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM (public.patients p
     JOIN public.doctors d ON ((d.hospital_id = p.hospital_id)))
  WHERE ((p.id = mri_scans.patient_id) AND (d.user_id = ( SELECT auth.uid() AS uid))))));



  create policy "patients_view_own_mri_scans"
  on "public"."mri_scans"
  as permissive
  for select
  to public
using ((patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "service_role_mri_scans"
  on "public"."mri_scans"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "Doctors can view MRI results for their hospital"
  on "public"."mri_segmentation_results"
  as permissive
  for select
  to authenticated
using ((public.has_role(auth.uid(), 'doctor'::public.app_role) AND (patient_id IN ( SELECT patients.id
   FROM public.patients
  WHERE (patients.hospital_id = public.get_user_hospital_id(auth.uid()))))));



  create policy "Patients can view their own MRI results"
  on "public"."mri_segmentation_results"
  as permissive
  for select
  to authenticated
using ((patient_id = public.get_patient_id_by_user(auth.uid())));



  create policy "Users can update their own notifications"
  on "public"."notifications"
  as permissive
  for update
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "Users can view their own notifications"
  on "public"."notifications"
  as permissive
  for select
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "admins_manage_hospital_nurses"
  on "public"."nurses"
  as permissive
  for all
  to public
using ((hospital_id IN ( SELECT administrators.hospital_id
   FROM public.administrators
  WHERE (administrators.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "nurses_update_own_profile"
  on "public"."nurses"
  as permissive
  for update
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "nurses_view_own_profile"
  on "public"."nurses"
  as permissive
  for select
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "service_role_nurses"
  on "public"."nurses"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "Admins can manage patients in their hospital"
  on "public"."patients"
  as permissive
  for all
  to public
using ((hospital_id IN ( SELECT administrators.hospital_id
   FROM public.administrators
  WHERE (administrators.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Doctors can create patients"
  on "public"."patients"
  as permissive
  for insert
  to public
with check ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "Doctors can view their patients"
  on "public"."patients"
  as permissive
  for select
  to public
using ((hospital_id IN ( SELECT doctors.hospital_id
   FROM public.doctors
  WHERE (doctors.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Patients can update their own record"
  on "public"."patients"
  as permissive
  for update
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "Patients can view their own record"
  on "public"."patients"
  as permissive
  for select
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "Anyone can view regions"
  on "public"."regions"
  as permissive
  for select
  to authenticated
using ((is_active = true));



  create policy "Anyone can view specialties"
  on "public"."specialty_types"
  as permissive
  for select
  to public
using (true);



  create policy "Super admins can manage specialties"
  on "public"."specialty_types"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'super_admin'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "service_role_system_settings"
  on "public"."system_settings"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "super_admins_manage_system_settings"
  on "public"."system_settings"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles.role = 'super_admin'::public.app_role) AND (user_roles.is_active = true)))));



  create policy "Admins can view roles in their hospital"
  on "public"."user_roles"
  as permissive
  for select
  to public
using ((hospital_id IN ( SELECT administrators.hospital_id
   FROM public.administrators
  WHERE (administrators.user_id = ( SELECT auth.uid() AS uid)))));



  create policy "Super admins can manage all roles"
  on "public"."user_roles"
  as permissive
  for all
  to public
using ((EXISTS ( SELECT 1
   FROM public.user_roles user_roles_1
  WHERE ((user_roles_1.user_id = ( SELECT auth.uid() AS uid)) AND (user_roles_1.role = 'super_admin'::public.app_role) AND (user_roles_1.is_active = true)))));



  create policy "Users can view their own roles"
  on "public"."user_roles"
  as permissive
  for select
  to public
using ((user_id = ( SELECT auth.uid() AS uid)));



  create policy "service_role_user_roles"
  on "public"."user_roles"
  as permissive
  for all
  to service_role
using (true)
with check (true);


CREATE TRIGGER update_administrators_updated_at BEFORE UPDATE ON public.administrators FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER notify_on_access_request AFTER INSERT ON public.chat_access_requests FOR EACH ROW EXECUTE FUNCTION public.notify_chat_access_request();

CREATE TRIGGER notify_on_access_response AFTER UPDATE ON public.chat_access_requests FOR EACH ROW EXECUTE FUNCTION public.notify_chat_access_response();

CREATE TRIGGER update_chat_access_requests_updated_at BEFORE UPDATE ON public.chat_access_requests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_countries_updated_at BEFORE UPDATE ON public.countries FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_doctors_updated_at BEFORE UPDATE ON public.doctors FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER audit_ecg_results AFTER INSERT OR DELETE OR UPDATE ON public.ecg_results FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();

CREATE TRIGGER update_ecg_results_updated_at BEFORE UPDATE ON public.ecg_results FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER audit_generated_reports AFTER INSERT OR DELETE OR UPDATE ON public.generated_reports FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();

CREATE TRIGGER update_generated_reports_updated_at BEFORE UPDATE ON public.generated_reports FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_hospitals_updated_at BEFORE UPDATE ON public.hospitals FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_llm_context_configs_updated_at BEFORE UPDATE ON public.llm_context_configs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_llm_conversations_updated_at BEFORE UPDATE ON public.llm_conversations FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_conversation_on_message AFTER INSERT ON public.llm_messages FOR EACH ROW EXECUTE FUNCTION public.update_conversation_stats();

CREATE TRIGGER audit_medical_cases AFTER INSERT OR DELETE OR UPDATE ON public.medical_cases FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();

CREATE TRIGGER update_medical_cases_updated_at BEFORE UPDATE ON public.medical_cases FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER audit_medical_files AFTER INSERT OR DELETE OR UPDATE ON public.medical_files FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();

CREATE TRIGGER update_medical_files_updated_at BEFORE UPDATE ON public.medical_files FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_model_versions_updated_at BEFORE UPDATE ON public.model_versions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER audit_mri_results AFTER INSERT OR DELETE OR UPDATE ON public.mri_segmentation_results FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();

CREATE TRIGGER update_mri_results_updated_at BEFORE UPDATE ON public.mri_segmentation_results FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_nurses_updated_at BEFORE UPDATE ON public.nurses FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON public.patients FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_regions_updated_at BEFORE UPDATE ON public.regions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_specialty_types_updated_at BEFORE UPDATE ON public.specialty_types FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON public.system_settings FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER handle_new_user AFTER INSERT OR DELETE OR UPDATE ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


  create policy "avatars_public_select"
  on "storage"."objects"
  as permissive
  for select
  to public
using ((bucket_id = 'avatars'::text));



  create policy "avatars_users_delete"
  on "storage"."objects"
  as permissive
  for delete
  to authenticated
using (((bucket_id = 'avatars'::text) AND ((storage.foldername(name))[1] = (auth.uid())::text)));



  create policy "avatars_users_insert"
  on "storage"."objects"
  as permissive
  for insert
  to authenticated
with check (((bucket_id = 'avatars'::text) AND ((storage.foldername(name))[1] = (auth.uid())::text)));



  create policy "avatars_users_update"
  on "storage"."objects"
  as permissive
  for update
  to authenticated
using (((bucket_id = 'avatars'::text) AND ((storage.foldername(name))[1] = (auth.uid())::text)));



  create policy "ecg_files_authorized_select"
  on "storage"."objects"
  as permissive
  for select
  to authenticated
using (((bucket_id = 'ecg-files'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = ANY (ARRAY['doctor'::public.app_role, 'patient'::public.app_role, 'admin'::public.app_role])) AND (user_roles.is_active = true))))));



  create policy "ecg_files_doctors_insert"
  on "storage"."objects"
  as permissive
  for insert
  to authenticated
with check (((bucket_id = 'ecg-files'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true))))));



  create policy "medical_files_doctors_delete"
  on "storage"."objects"
  as permissive
  for delete
  to authenticated
using (((bucket_id = 'medical-files'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true))))));



  create policy "medical_files_doctors_insert"
  on "storage"."objects"
  as permissive
  for insert
  to authenticated
with check (((bucket_id = 'medical-files'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true))))));



  create policy "medical_files_patients_select"
  on "storage"."objects"
  as permissive
  for select
  to authenticated
using (((bucket_id = 'medical-files'::text) AND (EXISTS ( SELECT 1
   FROM public.patients
  WHERE ((patients.user_id = auth.uid()) AND ((storage.foldername(objects.name))[1] = (patients.id)::text))))));



  create policy "medical_files_staff_select"
  on "storage"."objects"
  as permissive
  for select
  to authenticated
using (((bucket_id = 'medical-files'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = ANY (ARRAY['doctor'::public.app_role, 'admin'::public.app_role, 'nurse'::public.app_role])) AND (user_roles.is_active = true))))));



  create policy "mri_files_authorized_select"
  on "storage"."objects"
  as permissive
  for select
  to authenticated
using (((bucket_id = 'mri-files'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = ANY (ARRAY['doctor'::public.app_role, 'patient'::public.app_role, 'admin'::public.app_role])) AND (user_roles.is_active = true))))));



  create policy "mri_files_doctors_insert"
  on "storage"."objects"
  as permissive
  for insert
  to authenticated
with check (((bucket_id = 'mri-files'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true))))));



  create policy "reports_authorized_select"
  on "storage"."objects"
  as permissive
  for select
  to authenticated
using (((bucket_id = 'reports'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = ANY (ARRAY['doctor'::public.app_role, 'patient'::public.app_role, 'admin'::public.app_role])) AND (user_roles.is_active = true))))));



  create policy "reports_doctors_insert"
  on "storage"."objects"
  as permissive
  for insert
  to authenticated
with check (((bucket_id = 'reports'::text) AND (EXISTS ( SELECT 1
   FROM public.user_roles
  WHERE ((user_roles.user_id = auth.uid()) AND (user_roles.role = 'doctor'::public.app_role) AND (user_roles.is_active = true))))));



