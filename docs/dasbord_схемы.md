-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE dashboard.alerts (
  id bigint NOT NULL DEFAULT nextval('dashboard.alerts_id_seq'::regclass),
  kind character varying NOT NULL,
  threshold numeric,
  actual numeric,
  severity character varying NOT NULL DEFAULT 'warning'::character varying,
  triggered_at timestamp without time zone NOT NULL,
  acknowledged_at timestamp without time zone,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  description text,
  notification_sent_at timestamp without time zone,
  tenant_id uuid,
  CONSTRAINT alerts_pkey PRIMARY KEY (id)
);
CREATE TABLE dashboard.ar_internal_metadata (
  key character varying NOT NULL,
  value character varying,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT ar_internal_metadata_pkey PRIMARY KEY (key)
);
CREATE TABLE dashboard.audits (
  id bigint NOT NULL DEFAULT nextval('dashboard.audits_id_seq'::regclass),
  user_id bigint,
  tenant_id uuid,
  action character varying NOT NULL,
  description text NOT NULL,
  metadata json NOT NULL DEFAULT '"{}"'::json,
  ip_address character varying,
  user_agent character varying,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT audits_pkey PRIMARY KEY (id),
  CONSTRAINT fk_rails_e6d7b3fb68 FOREIGN KEY (user_id) REFERENCES dashboard.users(id)
);
CREATE TABLE dashboard.bookings (
  id bigint NOT NULL DEFAULT nextval('dashboard.bookings_id_seq'::regclass),
  external_id character varying NOT NULL,
  client_id character varying NOT NULL,
  start_at timestamp without time zone NOT NULL,
  service_code character varying,
  status character varying NOT NULL DEFAULT 'created'::character varying,
  verified_at timestamp without time zone,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  yclients_attendance integer,
  verification_data json,
  tenant_id uuid,
  CONSTRAINT bookings_pkey PRIMARY KEY (id)
);
CREATE TABLE dashboard.conversations (
  id bigint NOT NULL DEFAULT nextval('dashboard.conversations_id_seq'::regclass),
  client_id character varying NOT NULL,
  status character varying NOT NULL DEFAULT 'active'::character varying,
  escalated boolean NOT NULL DEFAULT false,
  last_message_at timestamp without time zone,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  tenant_id uuid,
  escalated_at timestamp without time zone,
  escalation_reason text,
  closed_at timestamp without time zone,
  closure_reason text,
  CONSTRAINT conversations_pkey PRIMARY KEY (id)
);
CREATE TABLE dashboard.metrics_dailies (
  id bigint NOT NULL DEFAULT nextval('dashboard.metrics_dailies_id_seq'::regclass),
  day date NOT NULL,
  dialogs_started integer NOT NULL DEFAULT 0,
  bookings integer NOT NULL DEFAULT 0,
  conversion numeric NOT NULL DEFAULT 0.0,
  avg_response_ms integer NOT NULL DEFAULT 0,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  digest_sent_at timestamp without time zone,
  tenant_id uuid,
  CONSTRAINT metrics_dailies_pkey PRIMARY KEY (id)
);
CREATE TABLE dashboard.schema_migrations (
  version character varying NOT NULL,
  CONSTRAINT schema_migrations_pkey PRIMARY KEY (version)
);
CREATE TABLE dashboard.session_activities (
  id bigint NOT NULL DEFAULT nextval('dashboard.session_activities_id_seq'::regclass),
  conversation_id bigint NOT NULL,
  event_id character varying NOT NULL,
  event_type character varying NOT NULL,
  latency_ms integer DEFAULT 0,
  payload json NOT NULL,
  occurred_at timestamp without time zone NOT NULL,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT session_activities_pkey PRIMARY KEY (id),
  CONSTRAINT fk_rails_cc47b7e087 FOREIGN KEY (conversation_id) REFERENCES dashboard.conversations(id)
);
CREATE TABLE dashboard.solid_cable_messages (
  id bigint NOT NULL DEFAULT nextval('dashboard.solid_cable_messages_id_seq'::regclass),
  channel text,
  payload text,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT solid_cable_messages_pkey PRIMARY KEY (id)
);
CREATE TABLE dashboard.solid_cache_entries (
  id bigint NOT NULL DEFAULT nextval('dashboard.solid_cache_entries_id_seq'::regclass),
  key bytea NOT NULL,
  value bytea NOT NULL,
  created_at timestamp without time zone NOT NULL,
  key_hash bigint NOT NULL,
  byte_size integer NOT NULL,
  CONSTRAINT solid_cache_entries_pkey PRIMARY KEY (id)
);
CREATE TABLE dashboard.tenants (
  id bigint NOT NULL DEFAULT nextval('dashboard.tenants_id_seq'::regclass),
  name character varying NOT NULL,
  domain character varying NOT NULL,
  plan character varying NOT NULL DEFAULT 'basic'::character varying,
  settings json NOT NULL DEFAULT '"{}"'::json,
  active boolean NOT NULL DEFAULT true,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  webhook_token character varying,
  time_zone character varying,
  CONSTRAINT tenants_pkey PRIMARY KEY (id)
);
CREATE TABLE dashboard.users (
  id bigint NOT NULL DEFAULT nextval('dashboard.users_id_seq'::regclass),
  email character varying NOT NULL DEFAULT ''::character varying,
  encrypted_password character varying NOT NULL DEFAULT ''::character varying,
  reset_password_token character varying,
  reset_password_sent_at timestamp without time zone,
  remember_created_at timestamp without time zone,
  first_name character varying,
  last_name character varying,
  role character varying NOT NULL DEFAULT 'staff'::character varying,
  active boolean NOT NULL DEFAULT true,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  tenant_id uuid,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);