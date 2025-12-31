-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.active_sessions_v2 (
  session_id uuid NOT NULL DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  user_id uuid NOT NULL,
  current_step text NOT NULL DEFAULT 'start'::text,
  intent text,
  state_data jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(state_data) = 'object'::text),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  last_activity_at timestamp with time zone NOT NULL DEFAULT now(),
  entities jsonb,
  dialog_context jsonb,
  CONSTRAINT active_sessions_v2_pkey PRIMARY KEY (session_id),
  CONSTRAINT active_sessions_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id),
  CONSTRAINT active_sessions_v2_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.clients_v2(id)
);
CREATE TABLE public.agent_trajectories_v2 (
  id bigint NOT NULL DEFAULT nextval('agent_trajectories_v2_id_seq'::regclass),
  tenant_id uuid NOT NULL,
  session_id uuid,
  user_id uuid,
  step_type text NOT NULL,
  step_order integer NOT NULL,
  correlation_id text,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'::text),
  status text,
  error_code text,
  error_message text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT agent_trajectories_v2_pkey PRIMARY KEY (id),
  CONSTRAINT agent_trajectories_v2_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.active_sessions_v2(session_id),
  CONSTRAINT agent_trajectories_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id),
  CONSTRAINT agent_trajectories_v2_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.clients_v2(id)
);
CREATE TABLE public.clients_v2 (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  telegram_chat_id bigint,
  whatsapp_id text,
  phone text,
  yclients_client_id bigint,
  full_name text,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(meta) = 'object'::text),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT clients_v2_pkey PRIMARY KEY (id),
  CONSTRAINT clients_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id)
);
CREATE TABLE public.complex_services (
  service_id bigint NOT NULL,
  service_name text,
  reason text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT complex_services_pkey PRIMARY KEY (service_id)
);
CREATE TABLE public.consultant_knowledge_base (
  id bigint NOT NULL DEFAULT nextval('consultant_knowledge_base_id_seq'::regclass),
  content text NOT NULL,
  metadata jsonb,
  embedding USER-DEFINED,
  CONSTRAINT consultant_knowledge_base_pkey PRIMARY KEY (id)
);
CREATE TABLE public.conversation_sessions_v2 (
  id bigint NOT NULL DEFAULT nextval('conversation_sessions_v2_id_seq'::regclass),
  session_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  user_id uuid NOT NULL,
  channel text NOT NULL,
  started_at timestamp with time zone NOT NULL,
  ended_at timestamp with time zone,
  duration_sec integer DEFAULT 
CASE
    WHEN (ended_at IS NOT NULL) THEN (GREATEST((0)::numeric, EXTRACT(epoch FROM (ended_at - started_at))))::integer
    ELSE NULL::integer
END,
  final_status text NOT NULL,
  final_intent text,
  final_summary text,
  booking_id text,
  booking_source text,
  booking_status text,
  booking_datetime timestamp with time zone,
  booking_amount numeric,
  booking_currency text,
  messages_count integer,
  agent_messages_count integer,
  user_messages_count integer,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(meta) = 'object'::text),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  summary text,
  CONSTRAINT conversation_sessions_v2_pkey PRIMARY KEY (id),
  CONSTRAINT conversation_sessions_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id),
  CONSTRAINT conversation_sessions_v2_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.clients_v2(id)
);
CREATE TABLE public.guardian_subscriptions_v2 (
  id bigint NOT NULL DEFAULT nextval('guardian_subscriptions_v2_id_seq'::regclass),
  tenant_id uuid NOT NULL,
  user_id uuid NOT NULL,
  channel text NOT NULL,
  target_type text NOT NULL,
  target_id text,
  event_type text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  schedule jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(schedule) = 'object'::text),
  meta jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(meta) = 'object'::text),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT guardian_subscriptions_v2_pkey PRIMARY KEY (id),
  CONSTRAINT guardian_subscriptions_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id),
  CONSTRAINT guardian_subscriptions_v2_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.clients_v2(id)
);
CREATE TABLE public.recent_history_v2 (
  id bigint NOT NULL DEFAULT nextval('recent_history_v2_id_seq'::regclass),
  tenant_id uuid NOT NULL,
  user_id uuid NOT NULL,
  session_id uuid,
  role text NOT NULL,
  channel text NOT NULL DEFAULT 'unknown'::text,
  message text NOT NULL,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(meta) = 'object'::text),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT recent_history_v2_pkey PRIMARY KEY (id),
  CONSTRAINT recent_history_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id),
  CONSTRAINT recent_history_v2_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.clients_v2(id)
);
CREATE TABLE public.schema_migrations (
  version character varying NOT NULL,
  CONSTRAINT schema_migrations_pkey PRIMARY KEY (version)
);
CREATE TABLE public.tenants_v2 (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE,
  is_active boolean NOT NULL DEFAULT true,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT tenants_v2_pkey PRIMARY KEY (id)
);
CREATE TABLE public.user_ltm_v2 (
  id bigint NOT NULL DEFAULT nextval('user_ltm_v2_id_seq'::regclass),
  tenant_id uuid NOT NULL,
  user_id uuid NOT NULL,
  preferred_staff_id text,
  preferred_service_id text,
  preferred_time text,
  language text,
  allow_notifications boolean NOT NULL DEFAULT true,
  ltm_data jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(ltm_data) = 'object'::text),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT user_ltm_v2_pkey PRIMARY KEY (id),
  CONSTRAINT user_ltm_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id),
  CONSTRAINT user_ltm_v2_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.clients_v2(id)
);
CREATE TABLE public.wishlist_v2 (
  id bigint NOT NULL DEFAULT nextval('wishlist_v2_id_seq'::regclass),
  tenant_id uuid NOT NULL,
  user_id uuid NOT NULL,
  item_type text NOT NULL,
  item_id text NOT NULL,
  source text,
  comment text,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(meta) = 'object'::text),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'pending'::text,
  processed_at timestamp with time zone,
  CONSTRAINT wishlist_v2_pkey PRIMARY KEY (id),
  CONSTRAINT wishlist_v2_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants_v2(id),
  CONSTRAINT wishlist_v2_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.clients_v2(id)
);