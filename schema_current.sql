-- schema_current.sql — généré automatiquement par scripts/dump_schema.py
-- Source de vérité unique pour le schéma public.
-- NE PAS MODIFIER MANUELLEMENT — régénérer via le script.


-- ------------------------------------------------------------------------------
-- EXTENSIONS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ------------------------------------------------------------------------------
-- TABLES
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS action_category (
    id INTEGER DEFAULT nextval('action_category_id_seq'::regclass) NOT NULL,
    name TEXT NOT NULL,
    code VARCHAR(255) DEFAULT NULL::character varying,
    color TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS action_category_meta (
    category_code VARCHAR(255) NOT NULL,
    is_simple BOOLEAN DEFAULT false,
    is_low_value BOOLEAN DEFAULT false,
    typical_duration_min NUMERIC(4,2),
    typical_duration_max NUMERIC(4,2),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (category_code)
);

CREATE TABLE IF NOT EXISTS action_classification_probe (
    id INTEGER DEFAULT nextval('action_classification_probe_id_seq'::regclass) NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    detection_type VARCHAR(50) DEFAULT 'keyword'::character varying,
    suggested_category VARCHAR(255),
    severity VARCHAR(20) DEFAULT 'warning'::character varying,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS action_subcategory (
    id INTEGER DEFAULT nextval('action_subcategory_id_seq'::regclass) NOT NULL,
    category_id INTEGER,
    name TEXT NOT NULL,
    code VARCHAR(255) DEFAULT NULL::character varying,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);

CREATE TABLE IF NOT EXISTS alembic_version_backend (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);

CREATE TABLE IF NOT EXISTS anomaly_threshold (
    id INTEGER DEFAULT nextval('anomaly_threshold_id_seq'::regclass) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    threshold_value NUMERIC,
    threshold_unit VARCHAR(50),
    high_severity_value NUMERIC,
    config_json JSONB,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS api_key (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    name VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    key_hash VARCHAR(64) NOT NULL,
    role_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS auth_attempt (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    email VARCHAR(255),
    ip_address VARCHAR(45) NOT NULL,
    success BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS complexity_factor (
    code VARCHAR(255) NOT NULL,
    label TEXT,
    category VARCHAR(255),
    PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS directus_access (
    id UUID NOT NULL,
    role UUID,
    user UUID,
    policy UUID NOT NULL,
    sort INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_activity (
    id INTEGER DEFAULT nextval('directus_activity_id_seq'::regclass) NOT NULL,
    action VARCHAR(45) NOT NULL,
    user UUID,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip VARCHAR(50),
    user_agent TEXT,
    collection VARCHAR(64) NOT NULL,
    item VARCHAR(255) NOT NULL,
    origin VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_collections (
    collection VARCHAR(64) NOT NULL,
    icon VARCHAR(64),
    note TEXT,
    display_template VARCHAR(255),
    hidden BOOLEAN DEFAULT false NOT NULL,
    singleton BOOLEAN DEFAULT false NOT NULL,
    translations JSON,
    archive_field VARCHAR(64),
    archive_app_filter BOOLEAN DEFAULT true NOT NULL,
    archive_value VARCHAR(255),
    unarchive_value VARCHAR(255),
    sort_field VARCHAR(64),
    accountability VARCHAR(255) DEFAULT 'all'::character varying,
    color VARCHAR(255),
    item_duplication_fields JSON,
    sort INTEGER,
    group VARCHAR(64),
    collapse VARCHAR(255) DEFAULT 'open'::character varying NOT NULL,
    preview_url VARCHAR(255),
    versioning BOOLEAN DEFAULT false NOT NULL,
    PRIMARY KEY (collection)
);

CREATE TABLE IF NOT EXISTS directus_comments (
    id UUID NOT NULL,
    collection VARCHAR(64) NOT NULL,
    item VARCHAR(255) NOT NULL,
    comment TEXT NOT NULL,
    date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    date_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_created UUID,
    user_updated UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_dashboards (
    id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    icon VARCHAR(64) DEFAULT 'dashboard'::character varying NOT NULL,
    note TEXT,
    date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_created UUID,
    color VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_extensions (
    enabled BOOLEAN DEFAULT true NOT NULL,
    id UUID NOT NULL,
    folder VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    bundle UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_fields (
    id INTEGER DEFAULT nextval('directus_fields_id_seq'::regclass) NOT NULL,
    collection VARCHAR(64) NOT NULL,
    field VARCHAR(64) NOT NULL,
    special VARCHAR(64),
    interface VARCHAR(64),
    options JSON,
    display VARCHAR(64),
    display_options JSON,
    readonly BOOLEAN DEFAULT false NOT NULL,
    hidden BOOLEAN DEFAULT false NOT NULL,
    sort INTEGER,
    width VARCHAR(30) DEFAULT 'full'::character varying,
    translations JSON,
    note TEXT,
    conditions JSON,
    required BOOLEAN DEFAULT false,
    group VARCHAR(64),
    validation JSON,
    validation_message TEXT,
    searchable BOOLEAN DEFAULT true NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_files (
    id UUID NOT NULL,
    storage VARCHAR(255) NOT NULL,
    filename_disk VARCHAR(255),
    filename_download VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    type VARCHAR(255),
    folder UUID,
    uploaded_by UUID,
    created_on TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    modified_by UUID,
    modified_on TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    charset VARCHAR(50),
    filesize BIGINT,
    width INTEGER,
    height INTEGER,
    duration INTEGER,
    embed VARCHAR(200),
    description TEXT,
    location TEXT,
    tags TEXT,
    metadata JSON,
    focal_point_x INTEGER,
    focal_point_y INTEGER,
    tus_id VARCHAR(64),
    tus_data JSON,
    uploaded_on TIMESTAMPTZ,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_flows (
    id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    icon VARCHAR(64),
    color VARCHAR(255),
    description TEXT,
    status VARCHAR(255) DEFAULT 'active'::character varying NOT NULL,
    trigger VARCHAR(255),
    accountability VARCHAR(255) DEFAULT 'all'::character varying,
    options JSON,
    operation UUID,
    date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_created UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_folders (
    id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_migrations (
    version VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (version)
);

CREATE TABLE IF NOT EXISTS directus_notifications (
    id INTEGER DEFAULT nextval('directus_notifications_id_seq'::regclass) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(255) DEFAULT 'inbox'::character varying,
    recipient UUID NOT NULL,
    sender UUID,
    subject VARCHAR(255) NOT NULL,
    message TEXT,
    collection VARCHAR(64),
    item VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_operations (
    id UUID NOT NULL,
    name VARCHAR(255),
    key VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    options JSON,
    resolve UUID,
    reject UUID,
    flow UUID NOT NULL,
    date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_created UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_panels (
    id UUID NOT NULL,
    dashboard UUID NOT NULL,
    name VARCHAR(255),
    icon VARCHAR(64) DEFAULT NULL::character varying,
    color VARCHAR(10),
    show_header BOOLEAN DEFAULT false NOT NULL,
    note TEXT,
    type VARCHAR(255) NOT NULL,
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    options JSON,
    date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_created UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_permissions (
    id INTEGER DEFAULT nextval('directus_permissions_id_seq'::regclass) NOT NULL,
    collection VARCHAR(64) NOT NULL,
    action VARCHAR(10) NOT NULL,
    permissions JSON,
    validation JSON,
    presets JSON,
    fields TEXT,
    policy UUID NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_policies (
    id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(64) DEFAULT 'badge'::character varying NOT NULL,
    description TEXT,
    ip_access TEXT,
    enforce_tfa BOOLEAN DEFAULT false NOT NULL,
    admin_access BOOLEAN DEFAULT false NOT NULL,
    app_access BOOLEAN DEFAULT false NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_presets (
    id INTEGER DEFAULT nextval('directus_presets_id_seq'::regclass) NOT NULL,
    bookmark VARCHAR(255),
    user UUID,
    role UUID,
    collection VARCHAR(64),
    search VARCHAR(100),
    layout VARCHAR(100) DEFAULT 'tabular'::character varying,
    layout_query JSON,
    layout_options JSON,
    refresh_interval INTEGER,
    filter JSON,
    icon VARCHAR(64) DEFAULT 'bookmark'::character varying,
    color VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_relations (
    id INTEGER DEFAULT nextval('directus_relations_id_seq'::regclass) NOT NULL,
    many_collection VARCHAR(64) NOT NULL,
    many_field VARCHAR(64) NOT NULL,
    one_collection VARCHAR(64),
    one_field VARCHAR(64),
    one_collection_field VARCHAR(64),
    one_allowed_collections TEXT,
    junction_field VARCHAR(64),
    sort_field VARCHAR(64),
    one_deselect_action VARCHAR(255) DEFAULT 'nullify'::character varying NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_revisions (
    id INTEGER DEFAULT nextval('directus_revisions_id_seq'::regclass) NOT NULL,
    activity INTEGER NOT NULL,
    collection VARCHAR(64) NOT NULL,
    item VARCHAR(255) NOT NULL,
    data JSON,
    delta JSON,
    parent INTEGER,
    version UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_roles (
    id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(64) DEFAULT 'supervised_user_circle'::character varying NOT NULL,
    description TEXT,
    parent UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_sessions (
    token VARCHAR(64) NOT NULL,
    user UUID,
    expires TIMESTAMPTZ NOT NULL,
    ip VARCHAR(255),
    user_agent TEXT,
    share UUID,
    origin VARCHAR(255),
    next_token VARCHAR(64),
    PRIMARY KEY (token)
);

CREATE TABLE IF NOT EXISTS directus_settings (
    id INTEGER DEFAULT nextval('directus_settings_id_seq'::regclass) NOT NULL,
    project_name VARCHAR(100) DEFAULT 'Directus'::character varying NOT NULL,
    project_url VARCHAR(255),
    project_color VARCHAR(255) DEFAULT '#6644FF'::character varying NOT NULL,
    project_logo UUID,
    public_foreground UUID,
    public_background UUID,
    public_note TEXT,
    auth_login_attempts INTEGER DEFAULT 25,
    auth_password_policy VARCHAR(100),
    storage_asset_transform VARCHAR(7) DEFAULT 'all'::character varying,
    storage_asset_presets JSON,
    custom_css TEXT,
    storage_default_folder UUID,
    basemaps JSON,
    mapbox_key VARCHAR(255),
    module_bar JSON,
    project_descriptor VARCHAR(100),
    default_language VARCHAR(255) DEFAULT 'en-US'::character varying NOT NULL,
    custom_aspect_ratios JSON,
    public_favicon UUID,
    default_appearance VARCHAR(255) DEFAULT 'auto'::character varying NOT NULL,
    default_theme_light VARCHAR(255),
    theme_light_overrides JSON,
    default_theme_dark VARCHAR(255),
    theme_dark_overrides JSON,
    report_error_url VARCHAR(255),
    report_bug_url VARCHAR(255),
    report_feature_url VARCHAR(255),
    public_registration BOOLEAN DEFAULT false NOT NULL,
    public_registration_verify_email BOOLEAN DEFAULT true NOT NULL,
    public_registration_role UUID,
    public_registration_email_filter JSON,
    visual_editor_urls JSON,
    project_id UUID,
    mcp_enabled BOOLEAN DEFAULT false NOT NULL,
    mcp_allow_deletes BOOLEAN DEFAULT false NOT NULL,
    mcp_prompts_collection VARCHAR(255) DEFAULT NULL::character varying,
    mcp_system_prompt_enabled BOOLEAN DEFAULT true NOT NULL,
    mcp_system_prompt TEXT,
    project_owner VARCHAR(255),
    project_usage VARCHAR(255),
    org_name VARCHAR(255),
    product_updates BOOLEAN,
    project_status VARCHAR(255),
    ai_openai_api_key TEXT,
    ai_anthropic_api_key TEXT,
    ai_system_prompt TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_shares (
    id UUID NOT NULL,
    name VARCHAR(255),
    collection VARCHAR(64) NOT NULL,
    item VARCHAR(255) NOT NULL,
    role UUID,
    password VARCHAR(255),
    user_created UUID,
    date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    date_start TIMESTAMPTZ,
    date_end TIMESTAMPTZ,
    times_used INTEGER DEFAULT 0,
    max_uses INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_translations (
    id UUID NOT NULL,
    language VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_users (
    id UUID NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(128),
    password VARCHAR(255),
    location VARCHAR(255),
    title VARCHAR(50),
    description TEXT,
    tags JSON,
    avatar UUID,
    language VARCHAR(255) DEFAULT NULL::character varying,
    tfa_secret VARCHAR(255),
    status VARCHAR(16) DEFAULT 'active'::character varying NOT NULL,
    role UUID,
    token VARCHAR(255),
    last_access TIMESTAMPTZ,
    last_page VARCHAR(255),
    provider VARCHAR(128) DEFAULT 'default'::character varying NOT NULL,
    external_identifier VARCHAR(255),
    auth_data JSON,
    email_notifications BOOLEAN DEFAULT true,
    appearance VARCHAR(255),
    theme_dark VARCHAR(255),
    theme_light VARCHAR(255),
    theme_light_overrides JSON,
    theme_dark_overrides JSON,
    text_direction VARCHAR(255) DEFAULT 'auto'::character varying NOT NULL,
    initial VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS directus_versions (
    id UUID NOT NULL,
    key VARCHAR(64) NOT NULL,
    name VARCHAR(255),
    collection VARCHAR(64) NOT NULL,
    item VARCHAR(255) NOT NULL,
    hash VARCHAR(255),
    date_created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    date_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_created UUID,
    user_updated UUID,
    delta JSON,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS email_domain_rule (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    domain VARCHAR(255) NOT NULL,
    allowed BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS equipement_class (
    id UUID NOT NULL,
    code VARCHAR(255),
    label TEXT,
    description TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS equipement_statuts (
    id INTEGER DEFAULT nextval('equipement_statuts_id_seq'::regclass) NOT NULL,
    code VARCHAR(30) NOT NULL,
    libelle VARCHAR(100) NOT NULL,
    interventions BOOLEAN DEFAULT true NOT NULL,
    est_actif BOOLEAN DEFAULT true NOT NULL,
    ordre_affichage INTEGER DEFAULT 0 NOT NULL,
    couleur VARCHAR(7),
    description TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    code VARCHAR(64),
    title VARCHAR(200) NOT NULL,
    machine_id UUID,
    type_inter VARCHAR(10) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal'::character varying,
    reported_by VARCHAR(200),
    tech_initials VARCHAR(255),
    status_actual VARCHAR(255),
    updated_by UUID,
    printed_fiche BOOLEAN DEFAULT false,
    reported_date DATE,
    plan_id UUID,
    tech_id UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_action (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    intervention_id UUID,
    description TEXT,
    time_spent NUMERIC(6,2) DEFAULT 0,
    updated_at TIMESTAMPTZ,
    action_subcategory INTEGER,
    created_at TIMESTAMPTZ,
    tech UUID,
    complexity_score INTEGER,
    complexity_anotation JSON,
    complexity_factor VARCHAR(255),
    action_start TIME,
    action_end TIME,
    task_id UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_action_purchase_request (
    id INTEGER DEFAULT nextval('intervention_action_purchase_request_id_seq'::regclass) NOT NULL,
    intervention_action_id UUID,
    purchase_request_id UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_part (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    intervention_id UUID,
    quantity INTEGER NOT NULL,
    note TEXT,
    unit_price NUMERIC(12,2) DEFAULT NULL::numeric,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_request (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    code VARCHAR(255) NOT NULL,
    machine_id UUID NOT NULL,
    demandeur_nom TEXT NOT NULL,
    demandeur_service_legacy TEXT,
    description TEXT NOT NULL,
    statut VARCHAR(50) NOT NULL,
    intervention_id UUID,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    service_id UUID,
    is_system BOOLEAN DEFAULT false NOT NULL,
    suggested_type_inter VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_status_log (
    id UUID NOT NULL,
    status_from VARCHAR(255),
    status_to VARCHAR(255),
    technician_id UUID,
    intervention_id UUID,
    date TIMESTAMP,
    notes VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_status_ref (
    id VARCHAR(255) NOT NULL,
    value VARCHAR(255),
    code TEXT DEFAULT ''::character varying NOT NULL,
    label TEXT,
    color TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_task (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    gamme_step_id UUID,
    intervention_id UUID,
    status VARCHAR(20) DEFAULT 'pending'::character varying NOT NULL,
    skip_reason TEXT,
    updated_at TIMESTAMPTZ DEFAULT now(),
    closed_by UUID,
    occurrence_id UUID,
    label TEXT,
    origin VARCHAR(10) DEFAULT 'plan'::character varying NOT NULL,
    optional BOOLEAN DEFAULT false NOT NULL,
    assigned_to UUID,
    due_date DATE,
    sort_order INTEGER DEFAULT 0 NOT NULL,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    action_id UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS intervention_type (
    id INTEGER DEFAULT nextval('intervention_type_id_seq'::regclass) NOT NULL,
    code VARCHAR(10) NOT NULL,
    label TEXT NOT NULL,
    color VARCHAR(30),
    is_active BOOLEAN DEFAULT true NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS ip_blocklist (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    reason VARCHAR(255),
    blocked_until TIMESTAMPTZ,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS location (
    id UUID NOT NULL,
    code VARCHAR(255),
    nom VARCHAR(255),
    name TEXT,
    description TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS machine (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    code VARCHAR(50) DEFAULT NULL::character varying NOT NULL,
    name VARCHAR(200) NOT NULL,
    no_machine INTEGER,
    affectation VARCHAR(255),
    equipement_mere UUID,
    is_mere BOOLEAN DEFAULT false,
    fabricant TEXT,
    numero_serie TEXT,
    date_mise_service DATE,
    notes TEXT,
    equipement_class_id UUID,
    statut_id INTEGER DEFAULT 3 NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS machine_hours (
    machine_id UUID NOT NULL,
    hours_total NUMERIC(10,2) DEFAULT 0 NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (machine_id)
);

CREATE TABLE IF NOT EXISTS manufacturer_item (
    id UUID NOT NULL,
    manufacturer_name TEXT NOT NULL,
    manufacturer_ref TEXT NOT NULL,
    designation TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS part_template (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    code VARCHAR(50) NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    label VARCHAR(100) NOT NULL,
    pattern TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS part_template_field (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    template_id UUID NOT NULL,
    field_key VARCHAR(50) NOT NULL,
    label VARCHAR(100) NOT NULL,
    field_type VARCHAR(30) NOT NULL,
    unit VARCHAR(20),
    required BOOLEAN DEFAULT false,
    sortable BOOLEAN DEFAULT true,
    sort_order INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS part_template_field_enum (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    field_id UUID NOT NULL,
    value VARCHAR(50) NOT NULL,
    label VARCHAR(100),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS permission_audit_log (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    changed_by UUID NOT NULL,
    role_id UUID NOT NULL,
    endpoint_id UUID NOT NULL,
    old_allowed BOOLEAN,
    new_allowed BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS preventive_occurrence (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    plan_id UUID NOT NULL,
    machine_id UUID NOT NULL,
    scheduled_date DATE NOT NULL,
    triggered_at TIMESTAMPTZ,
    hours_at_trigger NUMERIC(10,2),
    di_id UUID,
    intervention_id UUID,
    status VARCHAR(20) DEFAULT 'pending'::character varying NOT NULL,
    skip_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS preventive_plan (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    code VARCHAR(50) NOT NULL,
    label TEXT NOT NULL,
    equipement_class_id UUID,
    trigger_type VARCHAR(20) NOT NULL,
    periodicity_days INTEGER,
    hours_threshold INTEGER,
    auto_accept BOOLEAN DEFAULT false NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS preventive_plan_gamme_step (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    plan_id UUID NOT NULL,
    label TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    optional BOOLEAN DEFAULT false NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS preventive_rule (
    id INTEGER DEFAULT nextval('preventive_rule_id_seq'::regclass) NOT NULL,
    keyword TEXT NOT NULL,
    preventive_code TEXT NOT NULL,
    preventive_label TEXT NOT NULL,
    weight INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS preventive_suggestion (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    intervention_action_id UUID NOT NULL,
    machine_id UUID NOT NULL,
    preventive_code TEXT NOT NULL,
    preventive_label TEXT NOT NULL,
    score INTEGER NOT NULL,
    status TEXT DEFAULT 'NEW'::text NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    handled_at TIMESTAMP,
    handled_by UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS purchase_request (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    status VARCHAR(50) DEFAULT 'open'::character varying NOT NULL,
    stock_item_id UUID,
    item_label TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit VARCHAR(50),
    requested_by TEXT,
    urgency VARCHAR(20) DEFAULT 'normal'::character varying,
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    workshop VARCHAR(255),
    intervention_id UUID,
    quantity_approved INTEGER,
    approver_name TEXT,
    approved_at TIMESTAMPTZ,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS purchase_status (
    id VARCHAR(255) NOT NULL,
    value TEXT,
    color VARCHAR(255),
    code TEXT,
    label TEXT,
    order_index INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS refresh_token (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    user_id UUID NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT false NOT NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS request_status_log (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    request_id UUID NOT NULL,
    status_from VARCHAR(50),
    status_to VARCHAR(50) NOT NULL,
    changed_by UUID,
    notes TEXT,
    date TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS request_status_ref (
    code VARCHAR(50) NOT NULL,
    label TEXT NOT NULL,
    color VARCHAR(7) NOT NULL,
    sort_order INTEGER NOT NULL,
    PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER DEFAULT nextval('schema_migrations_id_seq'::regclass) NOT NULL,
    version VARCHAR(100) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    direction VARCHAR(10) NOT NULL,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS security_log (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id UUID,
    ip_address VARCHAR(45),
    detail JSONB,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS service (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    code VARCHAR(50) NOT NULL,
    label TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS stock_family (
    code VARCHAR(20) NOT NULL,
    label TEXT NOT NULL,
    name TEXT,
    PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS stock_item (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    name TEXT NOT NULL,
    family_code VARCHAR(20) NOT NULL,
    sub_family_code VARCHAR(20) NOT NULL,
    spec VARCHAR(50),
    dimension TEXT NOT NULL,
    ref TEXT,
    quantity INTEGER DEFAULT 0,
    unit VARCHAR(50),
    location TEXT,
    standars_spec UUID,
    supplier_refs_count INTEGER DEFAULT 0 NOT NULL,
    manufacturer_item_id UUID,
    template_id UUID,
    template_version INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS stock_item_characteristic (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    stock_item_id UUID NOT NULL,
    field_id UUID NOT NULL,
    value_text TEXT,
    value_number NUMERIC,
    value_enum VARCHAR(50),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS stock_item_standard_spec (
    id UUID NOT NULL,
    stock_item_id UUID,
    title TEXT,
    spec_text TEXT,
    is_default BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS stock_item_supplier (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    stock_item_id UUID NOT NULL,
    supplier_id UUID NOT NULL,
    supplier_ref TEXT NOT NULL,
    unit_price NUMERIC(10,2),
    min_order_quantity INTEGER DEFAULT 1,
    delivery_time_days INTEGER,
    is_preferred BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    manufacturer_item_id UUID,
    product_url TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS stock_sub_family (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    family_code VARCHAR(20) NOT NULL,
    code VARCHAR(20) NOT NULL,
    label TEXT NOT NULL,
    name TEXT,
    template_id UUID,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS subtask (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    intervention_id UUID,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(30) DEFAULT 'open'::character varying,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS supplier (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    code TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS supplier_order (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    order_number TEXT NOT NULL,
    supplier_id UUID NOT NULL,
    status VARCHAR(50) DEFAULT 'OPEN'::character varying NOT NULL,
    total_amount NUMERIC(12,2) DEFAULT 0,
    ordered_at TIMESTAMPTZ,
    expected_delivery_date DATE,
    received_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    currency float4,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS supplier_order_line (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    supplier_order_id UUID NOT NULL,
    stock_item_id UUID NOT NULL,
    supplier_ref_snapshot TEXT,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10,2),
    total_price NUMERIC(12,2),
    quantity_received INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    quote_received BOOLEAN,
    is_selected BOOLEAN,
    quote_price float4,
    manufacturer TEXT,
    manufacturer_ref TEXT,
    quote_received_at TIMESTAMP,
    rejected_reason TEXT,
    lead_time_days INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS supplier_order_line_purchase_request (
    id UUID DEFAULT uuid_generate_v4() NOT NULL,
    supplier_order_line_id UUID NOT NULL,
    purchase_request_id UUID NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS tunnel_endpoint (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    code VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(200) NOT NULL,
    description VARCHAR(255),
    module VARCHAR(50),
    is_sensitive BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS tunnel_permission (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    role_id UUID NOT NULL,
    endpoint_id UUID NOT NULL,
    allowed BOOLEAN DEFAULT true NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS tunnel_role (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    code VARCHAR(20) NOT NULL,
    label VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS tunnel_user (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    initial VARCHAR(5) NOT NULL,
    role_id UUID NOT NULL,
    auth_provider VARCHAR(20) DEFAULT 'local'::character varying NOT NULL,
    external_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true NOT NULL,
    provisioning VARCHAR(20) DEFAULT 'manual'::character varying NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);


-- ------------------------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------------------------
CREATE INDEX action_category_code_index ON public.action_category USING btree (code);
CREATE INDEX action_category_meta_low_value_index ON public.action_category_meta USING btree (is_low_value);
CREATE INDEX action_category_meta_simple_index ON public.action_category_meta USING btree (is_simple);
CREATE INDEX action_classification_probe_active_index ON public.action_classification_probe USING btree (is_active);
CREATE INDEX action_classification_probe_keyword_index ON public.action_classification_probe USING btree (keyword);
CREATE INDEX action_classification_probe_severity_index ON public.action_classification_probe USING btree (severity);
CREATE INDEX anomaly_threshold_active_index ON public.anomaly_threshold USING btree (is_active);
CREATE INDEX anomaly_threshold_type_index ON public.anomaly_threshold USING btree (anomaly_type);
CREATE INDEX idx_api_key_hash ON public.api_key USING btree (key_hash) WHERE (is_active = true);
CREATE INDEX directus_activity_timestamp_index ON public.directus_activity USING btree ("timestamp");
CREATE INDEX directus_revisions_activity_index ON public.directus_revisions USING btree (activity);
CREATE INDEX directus_revisions_parent_index ON public.directus_revisions USING btree (parent);
CREATE INDEX equipement_class_code_index ON public.equipement_class USING btree (code);
CREATE INDEX intervention_machine_id_index ON public.intervention USING btree (machine_id);
CREATE INDEX idx_intervention_action_complexity_factor ON public.intervention_action USING btree (complexity_factor);
CREATE INDEX idx_intervention_action_task_id ON public.intervention_action USING btree (task_id);
CREATE INDEX intervention_action_created_at_index ON public.intervention_action USING btree (created_at);
CREATE INDEX idx_intervention_request_is_system ON public.intervention_request USING btree (is_system) WHERE (is_system = true);
CREATE INDEX idx_gamme_step_validation_occurrence_id ON public.intervention_task USING btree (occurrence_id);
CREATE INDEX idx_intervention_task_action_id ON public.intervention_task USING btree (action_id);
CREATE INDEX idx_intervention_task_assigned_to ON public.intervention_task USING btree (assigned_to);
CREATE INDEX idx_intervention_task_intervention_id ON public.intervention_task USING btree (intervention_id);
CREATE INDEX idx_intervention_task_occurrence_id ON public.intervention_task USING btree (occurrence_id);
CREATE INDEX idx_intervention_task_status ON public.intervention_task USING btree (status);
CREATE INDEX machine_code_index ON public.machine USING btree (code);
CREATE INDEX machine_equipement_mere_index ON public.machine USING btree (equipement_mere);
CREATE INDEX idx_part_template_active_code ON public.part_template USING btree (code, version) WHERE (is_active = true);
CREATE INDEX idx_part_template_code ON public.part_template USING btree (code);
CREATE INDEX idx_part_template_is_active ON public.part_template USING btree (is_active) WHERE (is_active = true);
CREATE INDEX idx_part_template_field_sort_order ON public.part_template_field USING btree (template_id, sort_order);
CREATE INDEX idx_part_template_field_template_id ON public.part_template_field USING btree (template_id);
CREATE INDEX idx_part_template_field_enum_field_id ON public.part_template_field_enum USING btree (field_id);
CREATE INDEX idx_prev_occurrence_machine_id ON public.preventive_occurrence USING btree (machine_id);
CREATE INDEX idx_prev_occurrence_plan_id ON public.preventive_occurrence USING btree (plan_id);
CREATE INDEX idx_prev_occurrence_status ON public.preventive_occurrence USING btree (status);
CREATE INDEX idx_preventive_plan_active ON public.preventive_plan USING btree (active) WHERE (active = true);
CREATE INDEX idx_preventive_plan_equipment_class ON public.preventive_plan USING btree (equipement_class_id);
CREATE INDEX idx_gamme_step_plan_id ON public.preventive_plan_gamme_step USING btree (plan_id);
CREATE INDEX idx_preventive_rule_active ON public.preventive_rule USING btree (active) WHERE (active = true);
CREATE INDEX idx_preventive_rule_keyword ON public.preventive_rule USING btree (keyword);
CREATE INDEX idx_preventive_suggestion_code ON public.preventive_suggestion USING btree (preventive_code);
CREATE INDEX idx_preventive_suggestion_detected_at ON public.preventive_suggestion USING btree (detected_at);
CREATE INDEX idx_preventive_suggestion_machine ON public.preventive_suggestion USING btree (machine_id);
CREATE INDEX idx_preventive_suggestion_machine_status ON public.preventive_suggestion USING btree (machine_id, status);
CREATE INDEX idx_preventive_suggestion_status ON public.preventive_suggestion USING btree (status);
CREATE INDEX idx_purchase_request_created ON public.purchase_request USING btree (created_at DESC);
CREATE INDEX idx_purchase_request_status ON public.purchase_request USING btree (status);
CREATE INDEX idx_purchase_request_stock_item ON public.purchase_request USING btree (stock_item_id);
CREATE INDEX idx_schema_migrations_version ON public.schema_migrations USING btree (version, direction, success);
CREATE INDEX idx_stock_item_supplier_refs_count ON public.stock_item USING btree (supplier_refs_count);
CREATE INDEX idx_stock_item_template_id ON public.stock_item USING btree (template_id);
CREATE INDEX idx_stock_item_template_version ON public.stock_item USING btree (template_id, template_version);
CREATE INDEX idx_stock_item_char_item_field ON public.stock_item_characteristic USING btree (stock_item_id, field_id);
CREATE INDEX idx_stock_item_characteristic_field_id ON public.stock_item_characteristic USING btree (field_id);
CREATE INDEX idx_stock_item_characteristic_item_id ON public.stock_item_characteristic USING btree (stock_item_id);
CREATE INDEX idx_stock_item_characteristic_value_enum ON public.stock_item_characteristic USING btree (value_enum) WHERE (value_enum IS NOT NULL);
CREATE INDEX idx_stock_item_characteristic_value_number ON public.stock_item_characteristic USING btree (value_number) WHERE (value_number IS NOT NULL);
CREATE INDEX idx_stock_item_supplier_preferred ON public.stock_item_supplier USING btree (stock_item_id, is_preferred) WHERE (is_preferred = true);
CREATE INDEX stock_item_supplier_manufacturer_item_id_index ON public.stock_item_supplier USING btree (manufacturer_item_id);
CREATE INDEX idx_stock_sub_family_template_id ON public.stock_sub_family USING btree (template_id);
CREATE INDEX idx_supplier_order_status ON public.supplier_order USING btree (status);
CREATE INDEX idx_supplier_order_supplier ON public.supplier_order USING btree (supplier_id);
CREATE INDEX idx_supplier_order_line_order ON public.supplier_order_line USING btree (supplier_order_id);
CREATE INDEX idx_supplier_order_line_stock_item ON public.supplier_order_line USING btree (stock_item_id);
CREATE INDEX idx_sol_pr_line ON public.supplier_order_line_purchase_request USING btree (supplier_order_line_id);
CREATE INDEX idx_sol_pr_request ON public.supplier_order_line_purchase_request USING btree (purchase_request_id);


-- ------------------------------------------------------------------------------
-- UNIQUE & CHECK CONSTRAINTS
-- ------------------------------------------------------------------------------
ALTER TABLE action_subcategory ADD CONSTRAINT action_subcategory_code_unique UNIQUE ({, c, o, d, e, });
ALTER TABLE anomaly_threshold ADD CONSTRAINT anomaly_threshold_anomaly_type_key UNIQUE ({, a, n, o, m, a, l, y, _, t, y, p, e, });
ALTER TABLE api_key ADD CONSTRAINT api_key_key_hash_key UNIQUE ({, k, e, y, _, h, a, s, h, });
ALTER TABLE directus_flows ADD CONSTRAINT directus_flows_operation_unique UNIQUE ({, o, p, e, r, a, t, i, o, n, });
ALTER TABLE directus_operations ADD CONSTRAINT directus_operations_reject_unique UNIQUE ({, r, e, j, e, c, t, });
ALTER TABLE directus_operations ADD CONSTRAINT directus_operations_resolve_unique UNIQUE ({, r, e, s, o, l, v, e, });
ALTER TABLE directus_users ADD CONSTRAINT directus_users_email_unique UNIQUE ({, e, m, a, i, l, });
ALTER TABLE directus_users ADD CONSTRAINT directus_users_external_identifier_unique UNIQUE ({, e, x, t, e, r, n, a, l, _, i, d, e, n, t, i, f, i, e, r, });
ALTER TABLE directus_users ADD CONSTRAINT directus_users_token_unique UNIQUE ({, t, o, k, e, n, });
ALTER TABLE email_domain_rule ADD CONSTRAINT email_domain_rule_domain_key UNIQUE ({, d, o, m, a, i, n, });
ALTER TABLE equipement_class ADD CONSTRAINT equipement_class_code_unique UNIQUE ({, c, o, d, e, });
ALTER TABLE equipement_statuts ADD CONSTRAINT equipement_statuts_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE intervention ADD CONSTRAINT intervention_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE intervention_request ADD CONSTRAINT chk_suggested_type_inter CHECK ((((suggested_type_inter IS NULL) OR ((suggested_type_inter)::text = ANY ((ARRAY['CUR'::character varying, 'PRE'::character varying, 'REA'::character varying, 'BAT'::character varying, 'PRO'::character varying, 'COF'::character varying, 'PIL'::character varying, 'MES'::character varying])::text[])))));
ALTER TABLE intervention_request ADD CONSTRAINT intervention_request_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE intervention_request ADD CONSTRAINT intervention_request_intervention_id_key UNIQUE ({, i, n, t, e, r, v, e, n, t, i, o, n, _, i, d, });
ALTER TABLE intervention_task ADD CONSTRAINT intervention_task_origin_check CHECK ((((origin)::text = ANY ((ARRAY['plan'::character varying, 'resp'::character varying, 'tech'::character varying])::text[]))));
ALTER TABLE intervention_task ADD CONSTRAINT intervention_task_skip_reason_check CHECK (((((status)::text <> 'skipped'::text) OR (skip_reason IS NOT NULL))));
ALTER TABLE intervention_task ADD CONSTRAINT intervention_task_status_check CHECK ((((status)::text = ANY ((ARRAY['todo'::character varying, 'in_progress'::character varying, 'done'::character varying, 'skipped'::character varying])::text[]))));
ALTER TABLE intervention_task ADD CONSTRAINT intervention_task_gamme_step_unique UNIQUE ({, g, a, m, m, e, _, s, t, e, p, _, i, d, ,, o, c, c, u, r, r, e, n, c, e, _, i, d, });
ALTER TABLE intervention_type ADD CONSTRAINT intervention_type_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE ip_blocklist ADD CONSTRAINT ip_blocklist_ip_address_key UNIQUE ({, i, p, _, a, d, d, r, e, s, s, });
ALTER TABLE machine ADD CONSTRAINT machine_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE part_template ADD CONSTRAINT part_template_version_positive CHECK (((version > 0)));
ALTER TABLE part_template ADD CONSTRAINT part_template_code_version_unique UNIQUE ({, c, o, d, e, ,, v, e, r, s, i, o, n, });
ALTER TABLE part_template_field ADD CONSTRAINT part_template_field_sort_order_positive CHECK (((sort_order > 0)));
ALTER TABLE part_template_field ADD CONSTRAINT part_template_field_type_check CHECK ((((field_type)::text = ANY ((ARRAY['number'::character varying, 'text'::character varying, 'enum'::character varying])::text[]))));
ALTER TABLE part_template_field ADD CONSTRAINT part_template_field_unique UNIQUE ({, t, e, m, p, l, a, t, e, _, i, d, ,, f, i, e, l, d, _, k, e, y, });
ALTER TABLE part_template_field_enum ADD CONSTRAINT part_template_field_enum_unique UNIQUE ({, f, i, e, l, d, _, i, d, ,, v, a, l, u, e, });
ALTER TABLE preventive_occurrence ADD CONSTRAINT preventive_occurrence_skip_reason_check CHECK (((((status)::text <> 'skipped'::text) OR (skip_reason IS NOT NULL))));
ALTER TABLE preventive_occurrence ADD CONSTRAINT preventive_occurrence_plan_machine_date_key UNIQUE ({, p, l, a, n, _, i, d, ,, m, a, c, h, i, n, e, _, i, d, ,, s, c, h, e, d, u, l, e, d, _, d, a, t, e, });
ALTER TABLE preventive_plan ADD CONSTRAINT preventive_plan_trigger_type_check CHECK ((((((trigger_type)::text = 'periodicity'::text) AND (periodicity_days IS NOT NULL)) OR (((trigger_type)::text = 'hours'::text) AND (hours_threshold IS NOT NULL)))));
ALTER TABLE preventive_plan ADD CONSTRAINT preventive_plan_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE preventive_plan_gamme_step ADD CONSTRAINT preventive_plan_gamme_step_plan_sort_key UNIQUE ({, p, l, a, n, _, i, d, ,, s, o, r, t, _, o, r, d, e, r, });
ALTER TABLE preventive_rule ADD CONSTRAINT preventive_rule_keyword_key UNIQUE ({, k, e, y, w, o, r, d, });
ALTER TABLE preventive_suggestion ADD CONSTRAINT check_handled_at_with_status CHECK (((((handled_at IS NULL) AND (status = 'NEW'::text)) OR ((handled_at IS NOT NULL) AND (status = ANY (ARRAY['REVIEWED'::text, 'ACCEPTED'::text, 'REJECTED'::text]))))));
ALTER TABLE preventive_suggestion ADD CONSTRAINT preventive_suggestion_intervention_action_id_key UNIQUE ({, i, n, t, e, r, v, e, n, t, i, o, n, _, a, c, t, i, o, n, _, i, d, });
ALTER TABLE preventive_suggestion ADD CONSTRAINT preventive_suggestion_machine_id_preventive_code_key UNIQUE ({, m, a, c, h, i, n, e, _, i, d, ,, p, r, e, v, e, n, t, i, v, e, _, c, o, d, e, });
ALTER TABLE purchase_request ADD CONSTRAINT purchase_request_quantity_check CHECK (((quantity > 0)));
ALTER TABLE refresh_token ADD CONSTRAINT refresh_token_token_hash_key UNIQUE ({, t, o, k, e, n, _, h, a, s, h, });
ALTER TABLE service ADD CONSTRAINT service_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE stock_item ADD CONSTRAINT stock_item_template_version_positive CHECK ((((template_version IS NULL) OR (template_version > 0))));
ALTER TABLE stock_item ADD CONSTRAINT stock_item_ref_key UNIQUE ({, r, e, f, });
ALTER TABLE stock_item_characteristic ADD CONSTRAINT stock_item_characteristic_single_value_check CHECK (((((value_text IS NOT NULL) AND (value_number IS NULL) AND (value_enum IS NULL)) OR ((value_text IS NULL) AND (value_number IS NOT NULL) AND (value_enum IS NULL)) OR ((value_text IS NULL) AND (value_number IS NULL) AND (value_enum IS NOT NULL)))));
ALTER TABLE stock_item_characteristic ADD CONSTRAINT stock_item_characteristic_unique UNIQUE ({, s, t, o, c, k, _, i, t, e, m, _, i, d, ,, f, i, e, l, d, _, i, d, });
ALTER TABLE stock_item_supplier ADD CONSTRAINT uq_stock_item_supplier UNIQUE ({, s, t, o, c, k, _, i, t, e, m, _, i, d, ,, s, u, p, p, l, i, e, r, _, i, d, });
ALTER TABLE stock_sub_family ADD CONSTRAINT uq_stock_sub_family UNIQUE ({, f, a, m, i, l, y, _, c, o, d, e, ,, c, o, d, e, });
ALTER TABLE supplier_order ADD CONSTRAINT supplier_order_order_number_key UNIQUE ({, o, r, d, e, r, _, n, u, m, b, e, r, });
ALTER TABLE supplier_order_line ADD CONSTRAINT supplier_order_line_quantity_check CHECK (((quantity > 0)));
ALTER TABLE supplier_order_line ADD CONSTRAINT uq_supplier_order_line UNIQUE ({, s, u, p, p, l, i, e, r, _, o, r, d, e, r, _, i, d, ,, s, t, o, c, k, _, i, t, e, m, _, i, d, });
ALTER TABLE supplier_order_line_purchase_request ADD CONSTRAINT supplier_order_line_purchase_request_quantity_check CHECK (((quantity > 0)));
ALTER TABLE supplier_order_line_purchase_request ADD CONSTRAINT uq_line_request UNIQUE ({, s, u, p, p, l, i, e, r, _, o, r, d, e, r, _, l, i, n, e, _, i, d, ,, p, u, r, c, h, a, s, e, _, r, e, q, u, e, s, t, _, i, d, });
ALTER TABLE tunnel_endpoint ADD CONSTRAINT tunnel_endpoint_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE tunnel_permission ADD CONSTRAINT tunnel_permission_role_id_endpoint_id_key UNIQUE ({, r, o, l, e, _, i, d, ,, e, n, d, p, o, i, n, t, _, i, d, });
ALTER TABLE tunnel_role ADD CONSTRAINT tunnel_role_code_key UNIQUE ({, c, o, d, e, });
ALTER TABLE tunnel_user ADD CONSTRAINT tunnel_user_email_key UNIQUE ({, e, m, a, i, l, });


-- ------------------------------------------------------------------------------
-- FOREIGN KEY CONSTRAINTS
-- ------------------------------------------------------------------------------
ALTER TABLE action_subcategory ADD CONSTRAINT action_subcategory_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES action_category(id) ON DELETE SET NULL;
ALTER TABLE api_key ADD CONSTRAINT api_key_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES tunnel_user(id);
ALTER TABLE api_key ADD CONSTRAINT api_key_role_id_fkey
    FOREIGN KEY (role_id) REFERENCES tunnel_role(id);
ALTER TABLE directus_access ADD CONSTRAINT directus_access_policy_foreign
    FOREIGN KEY (policy) REFERENCES directus_policies(id) ON DELETE CASCADE;
ALTER TABLE directus_access ADD CONSTRAINT directus_access_role_foreign
    FOREIGN KEY (role) REFERENCES directus_roles(id) ON DELETE CASCADE;
ALTER TABLE directus_access ADD CONSTRAINT directus_access_user_foreign
    FOREIGN KEY (user) REFERENCES directus_users(id) ON DELETE CASCADE;
ALTER TABLE directus_collections ADD CONSTRAINT directus_collections_group_foreign
    FOREIGN KEY (group) REFERENCES directus_collections(collection);
ALTER TABLE directus_comments ADD CONSTRAINT directus_comments_user_created_foreign
    FOREIGN KEY (user_created) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE directus_comments ADD CONSTRAINT directus_comments_user_updated_foreign
    FOREIGN KEY (user_updated) REFERENCES directus_users(id);
ALTER TABLE directus_dashboards ADD CONSTRAINT directus_dashboards_user_created_foreign
    FOREIGN KEY (user_created) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE directus_files ADD CONSTRAINT directus_files_folder_foreign
    FOREIGN KEY (folder) REFERENCES directus_folders(id) ON DELETE SET NULL;
ALTER TABLE directus_files ADD CONSTRAINT directus_files_modified_by_foreign
    FOREIGN KEY (modified_by) REFERENCES directus_users(id);
ALTER TABLE directus_files ADD CONSTRAINT directus_files_uploaded_by_foreign
    FOREIGN KEY (uploaded_by) REFERENCES directus_users(id);
ALTER TABLE directus_flows ADD CONSTRAINT directus_flows_user_created_foreign
    FOREIGN KEY (user_created) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE directus_folders ADD CONSTRAINT directus_folders_parent_foreign
    FOREIGN KEY (parent) REFERENCES directus_folders(id);
ALTER TABLE directus_notifications ADD CONSTRAINT directus_notifications_recipient_foreign
    FOREIGN KEY (recipient) REFERENCES directus_users(id) ON DELETE CASCADE;
ALTER TABLE directus_notifications ADD CONSTRAINT directus_notifications_sender_foreign
    FOREIGN KEY (sender) REFERENCES directus_users(id);
ALTER TABLE directus_operations ADD CONSTRAINT directus_operations_flow_foreign
    FOREIGN KEY (flow) REFERENCES directus_flows(id) ON DELETE CASCADE;
ALTER TABLE directus_operations ADD CONSTRAINT directus_operations_reject_foreign
    FOREIGN KEY (reject) REFERENCES directus_operations(id);
ALTER TABLE directus_operations ADD CONSTRAINT directus_operations_resolve_foreign
    FOREIGN KEY (resolve) REFERENCES directus_operations(id);
ALTER TABLE directus_operations ADD CONSTRAINT directus_operations_user_created_foreign
    FOREIGN KEY (user_created) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE directus_panels ADD CONSTRAINT directus_panels_dashboard_foreign
    FOREIGN KEY (dashboard) REFERENCES directus_dashboards(id) ON DELETE CASCADE;
ALTER TABLE directus_panels ADD CONSTRAINT directus_panels_user_created_foreign
    FOREIGN KEY (user_created) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE directus_permissions ADD CONSTRAINT directus_permissions_policy_foreign
    FOREIGN KEY (policy) REFERENCES directus_policies(id) ON DELETE CASCADE;
ALTER TABLE directus_presets ADD CONSTRAINT directus_presets_role_foreign
    FOREIGN KEY (role) REFERENCES directus_roles(id) ON DELETE CASCADE;
ALTER TABLE directus_presets ADD CONSTRAINT directus_presets_user_foreign
    FOREIGN KEY (user) REFERENCES directus_users(id) ON DELETE CASCADE;
ALTER TABLE directus_revisions ADD CONSTRAINT directus_revisions_activity_foreign
    FOREIGN KEY (activity) REFERENCES directus_activity(id) ON DELETE CASCADE;
ALTER TABLE directus_revisions ADD CONSTRAINT directus_revisions_parent_foreign
    FOREIGN KEY (parent) REFERENCES directus_revisions(id);
ALTER TABLE directus_revisions ADD CONSTRAINT directus_revisions_version_foreign
    FOREIGN KEY (version) REFERENCES directus_versions(id) ON DELETE CASCADE;
ALTER TABLE directus_roles ADD CONSTRAINT directus_roles_parent_foreign
    FOREIGN KEY (parent) REFERENCES directus_roles(id);
ALTER TABLE directus_sessions ADD CONSTRAINT directus_sessions_share_foreign
    FOREIGN KEY (share) REFERENCES directus_shares(id) ON DELETE CASCADE;
ALTER TABLE directus_sessions ADD CONSTRAINT directus_sessions_user_foreign
    FOREIGN KEY (user) REFERENCES directus_users(id) ON DELETE CASCADE;
ALTER TABLE directus_settings ADD CONSTRAINT directus_settings_project_logo_foreign
    FOREIGN KEY (project_logo) REFERENCES directus_files(id);
ALTER TABLE directus_settings ADD CONSTRAINT directus_settings_public_background_foreign
    FOREIGN KEY (public_background) REFERENCES directus_files(id);
ALTER TABLE directus_settings ADD CONSTRAINT directus_settings_public_favicon_foreign
    FOREIGN KEY (public_favicon) REFERENCES directus_files(id);
ALTER TABLE directus_settings ADD CONSTRAINT directus_settings_public_foreground_foreign
    FOREIGN KEY (public_foreground) REFERENCES directus_files(id);
ALTER TABLE directus_settings ADD CONSTRAINT directus_settings_public_registration_role_foreign
    FOREIGN KEY (public_registration_role) REFERENCES directus_roles(id) ON DELETE SET NULL;
ALTER TABLE directus_settings ADD CONSTRAINT directus_settings_storage_default_folder_foreign
    FOREIGN KEY (storage_default_folder) REFERENCES directus_folders(id) ON DELETE SET NULL;
ALTER TABLE directus_shares ADD CONSTRAINT directus_shares_collection_foreign
    FOREIGN KEY (collection) REFERENCES directus_collections(collection) ON DELETE CASCADE;
ALTER TABLE directus_shares ADD CONSTRAINT directus_shares_role_foreign
    FOREIGN KEY (role) REFERENCES directus_roles(id) ON DELETE CASCADE;
ALTER TABLE directus_shares ADD CONSTRAINT directus_shares_user_created_foreign
    FOREIGN KEY (user_created) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE directus_users ADD CONSTRAINT directus_users_role_foreign
    FOREIGN KEY (role) REFERENCES directus_roles(id) ON DELETE SET NULL;
ALTER TABLE directus_versions ADD CONSTRAINT directus_versions_collection_foreign
    FOREIGN KEY (collection) REFERENCES directus_collections(collection) ON DELETE CASCADE;
ALTER TABLE directus_versions ADD CONSTRAINT directus_versions_user_created_foreign
    FOREIGN KEY (user_created) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE directus_versions ADD CONSTRAINT directus_versions_user_updated_foreign
    FOREIGN KEY (user_updated) REFERENCES directus_users(id);
ALTER TABLE intervention ADD CONSTRAINT intervention_machine_id_fkey
    FOREIGN KEY (machine_id) REFERENCES machine(id) ON DELETE SET NULL;
ALTER TABLE intervention ADD CONSTRAINT intervention_plan_id_fkey
    FOREIGN KEY (plan_id) REFERENCES preventive_plan(id) ON DELETE SET NULL;
ALTER TABLE intervention ADD CONSTRAINT intervention_status_actual_foreign
    FOREIGN KEY (status_actual) REFERENCES intervention_status_ref(id) ON DELETE SET NULL;
ALTER TABLE intervention ADD CONSTRAINT intervention_tech_id_fkey
    FOREIGN KEY (tech_id) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE intervention ADD CONSTRAINT intervention_updated_by_foreign
    FOREIGN KEY (updated_by) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE intervention_action ADD CONSTRAINT fk_intervention_action_complexity_factor
    FOREIGN KEY (complexity_factor) REFERENCES complexity_factor(code) ON DELETE SET NULL;
ALTER TABLE intervention_action ADD CONSTRAINT intervention_action_action_subcategory_foreign
    FOREIGN KEY (action_subcategory) REFERENCES action_subcategory(id) ON DELETE SET NULL;
ALTER TABLE intervention_action ADD CONSTRAINT intervention_action_intervention_id_fkey
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE CASCADE;
ALTER TABLE intervention_action ADD CONSTRAINT intervention_action_task_id_fkey
    FOREIGN KEY (task_id) REFERENCES intervention_task(id) ON DELETE SET NULL;
ALTER TABLE intervention_action ADD CONSTRAINT intervention_action_tech_foreign
    FOREIGN KEY (tech) REFERENCES directus_users(id);
ALTER TABLE intervention_action_purchase_request ADD CONSTRAINT intervention_action_purchase_request_inter__58223902_foreign
    FOREIGN KEY (intervention_action_id) REFERENCES intervention_action(id) ON DELETE SET NULL;
ALTER TABLE intervention_action_purchase_request ADD CONSTRAINT intervention_action_purchase_request_purch__1ea27a8f_foreign
    FOREIGN KEY (purchase_request_id) REFERENCES purchase_request(id) ON DELETE SET NULL;
ALTER TABLE intervention_part ADD CONSTRAINT intervention_part_intervention_id_fkey
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE CASCADE;
ALTER TABLE intervention_request ADD CONSTRAINT intervention_request_intervention_id_fkey
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE SET NULL;
ALTER TABLE intervention_request ADD CONSTRAINT intervention_request_machine_id_fkey
    FOREIGN KEY (machine_id) REFERENCES machine(id) ON DELETE RESTRICT;
ALTER TABLE intervention_request ADD CONSTRAINT intervention_request_service_id_fkey
    FOREIGN KEY (service_id) REFERENCES service(id) ON DELETE SET NULL;
ALTER TABLE intervention_request ADD CONSTRAINT intervention_request_statut_fkey
    FOREIGN KEY (statut) REFERENCES request_status_ref(code);
ALTER TABLE intervention_status_log ADD CONSTRAINT intervention_status_log_intervention_id_foreign
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE CASCADE;
ALTER TABLE intervention_status_log ADD CONSTRAINT intervention_status_log_status_from_foreign
    FOREIGN KEY (status_from) REFERENCES intervention_status_ref(id) ON DELETE SET NULL;
ALTER TABLE intervention_status_log ADD CONSTRAINT intervention_status_log_status_to_foreign
    FOREIGN KEY (status_to) REFERENCES intervention_status_ref(id) ON DELETE SET NULL;
ALTER TABLE intervention_status_log ADD CONSTRAINT intervention_status_log_technician_id_foreign
    FOREIGN KEY (technician_id) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE intervention_task ADD CONSTRAINT gamme_step_validation_intervention_id_fkey
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE RESTRICT;
ALTER TABLE intervention_task ADD CONSTRAINT gamme_step_validation_occurrence_id_fkey
    FOREIGN KEY (occurrence_id) REFERENCES preventive_occurrence(id) ON DELETE RESTRICT;
ALTER TABLE intervention_task ADD CONSTRAINT gamme_step_validation_step_id_fkey
    FOREIGN KEY (gamme_step_id) REFERENCES preventive_plan_gamme_step(id) ON DELETE RESTRICT;
ALTER TABLE intervention_task ADD CONSTRAINT intervention_task_action_id_fkey
    FOREIGN KEY (action_id) REFERENCES intervention_action(id) ON DELETE SET NULL;
ALTER TABLE intervention_task ADD CONSTRAINT intervention_task_assigned_to_fkey
    FOREIGN KEY (assigned_to) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE intervention_task ADD CONSTRAINT intervention_task_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES directus_users(id) ON DELETE SET NULL;
ALTER TABLE ip_blocklist ADD CONSTRAINT ip_blocklist_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES tunnel_user(id);
ALTER TABLE machine ADD CONSTRAINT machine_equipement_class_id_foreign
    FOREIGN KEY (equipement_class_id) REFERENCES equipement_class(id) ON DELETE SET NULL;
ALTER TABLE machine ADD CONSTRAINT machine_equipement_mere_foreign
    FOREIGN KEY (equipement_mere) REFERENCES machine(id);
ALTER TABLE machine ADD CONSTRAINT machine_statut_id_fkey
    FOREIGN KEY (statut_id) REFERENCES equipement_statuts(id);
ALTER TABLE machine_hours ADD CONSTRAINT machine_hours_machine_id_fkey
    FOREIGN KEY (machine_id) REFERENCES machine(id) ON DELETE CASCADE;
ALTER TABLE part_template_field ADD CONSTRAINT part_template_field_template_fk
    FOREIGN KEY (template_id) REFERENCES part_template(id) ON DELETE CASCADE;
ALTER TABLE part_template_field_enum ADD CONSTRAINT part_template_field_enum_field_fk
    FOREIGN KEY (field_id) REFERENCES part_template_field(id) ON DELETE CASCADE;
ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_changed_by_fkey
    FOREIGN KEY (changed_by) REFERENCES tunnel_user(id);
ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_endpoint_id_fkey
    FOREIGN KEY (endpoint_id) REFERENCES tunnel_endpoint(id);
ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_role_id_fkey
    FOREIGN KEY (role_id) REFERENCES tunnel_role(id);
ALTER TABLE preventive_occurrence ADD CONSTRAINT preventive_occurrence_di_id_fkey
    FOREIGN KEY (di_id) REFERENCES intervention_request(id) ON DELETE SET NULL;
ALTER TABLE preventive_occurrence ADD CONSTRAINT preventive_occurrence_intervention_id_fkey
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE SET NULL;
ALTER TABLE preventive_occurrence ADD CONSTRAINT preventive_occurrence_machine_id_fkey
    FOREIGN KEY (machine_id) REFERENCES machine(id) ON DELETE RESTRICT;
ALTER TABLE preventive_occurrence ADD CONSTRAINT preventive_occurrence_plan_id_fkey
    FOREIGN KEY (plan_id) REFERENCES preventive_plan(id) ON DELETE RESTRICT;
ALTER TABLE preventive_plan ADD CONSTRAINT preventive_plan_equipement_class_id_fkey
    FOREIGN KEY (equipement_class_id) REFERENCES equipement_class(id) ON DELETE RESTRICT;
ALTER TABLE preventive_plan_gamme_step ADD CONSTRAINT preventive_plan_gamme_step_plan_id_fkey
    FOREIGN KEY (plan_id) REFERENCES preventive_plan(id) ON DELETE CASCADE;
ALTER TABLE preventive_suggestion ADD CONSTRAINT fk_preventive_suggestion_action
    FOREIGN KEY (intervention_action_id) REFERENCES intervention_action(id) ON DELETE RESTRICT;
ALTER TABLE preventive_suggestion ADD CONSTRAINT fk_preventive_suggestion_machine
    FOREIGN KEY (machine_id) REFERENCES machine(id) ON DELETE RESTRICT;
ALTER TABLE purchase_request ADD CONSTRAINT purchase_request_intervention_id_foreign
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE SET NULL;
ALTER TABLE purchase_request ADD CONSTRAINT purchase_request_stock_item_id_fkey
    FOREIGN KEY (stock_item_id) REFERENCES stock_item(id) ON DELETE SET NULL;
ALTER TABLE refresh_token ADD CONSTRAINT refresh_token_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES tunnel_user(id) ON DELETE CASCADE;
ALTER TABLE request_status_log ADD CONSTRAINT request_status_log_request_id_fkey
    FOREIGN KEY (request_id) REFERENCES intervention_request(id) ON DELETE CASCADE;
ALTER TABLE request_status_log ADD CONSTRAINT request_status_log_status_from_fkey
    FOREIGN KEY (status_from) REFERENCES request_status_ref(code);
ALTER TABLE request_status_log ADD CONSTRAINT request_status_log_status_to_fkey
    FOREIGN KEY (status_to) REFERENCES request_status_ref(code);
ALTER TABLE security_log ADD CONSTRAINT security_log_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES tunnel_user(id) ON DELETE SET NULL;
ALTER TABLE stock_item ADD CONSTRAINT fk_item_sub_family
    FOREIGN KEY (family_code) REFERENCES stock_sub_family(code);
ALTER TABLE stock_item ADD CONSTRAINT fk_item_sub_family
    FOREIGN KEY (sub_family_code) REFERENCES stock_sub_family(code);
ALTER TABLE stock_item ADD CONSTRAINT fk_item_sub_family
    FOREIGN KEY (family_code) REFERENCES stock_sub_family(family_code);
ALTER TABLE stock_item ADD CONSTRAINT fk_item_sub_family
    FOREIGN KEY (sub_family_code) REFERENCES stock_sub_family(family_code);
ALTER TABLE stock_item ADD CONSTRAINT stock_item_family_code_fkey
    FOREIGN KEY (family_code) REFERENCES stock_family(code);
ALTER TABLE stock_item ADD CONSTRAINT stock_item_manufacturer_item_id_foreign
    FOREIGN KEY (manufacturer_item_id) REFERENCES manufacturer_item(id);
ALTER TABLE stock_item ADD CONSTRAINT stock_item_standars_spec_foreign
    FOREIGN KEY (standars_spec) REFERENCES stock_item_standard_spec(id) ON DELETE SET NULL;
ALTER TABLE stock_item ADD CONSTRAINT stock_item_template_fk
    FOREIGN KEY (template_id) REFERENCES part_template(id) ON DELETE RESTRICT;
ALTER TABLE stock_item_characteristic ADD CONSTRAINT stock_item_characteristic_field_fk
    FOREIGN KEY (field_id) REFERENCES part_template_field(id) ON DELETE RESTRICT;
ALTER TABLE stock_item_characteristic ADD CONSTRAINT stock_item_characteristic_item_fk
    FOREIGN KEY (stock_item_id) REFERENCES stock_item(id) ON DELETE CASCADE;
ALTER TABLE stock_item_standard_spec ADD CONSTRAINT stock_item_standard_spec_stock_item_id_foreign
    FOREIGN KEY (stock_item_id) REFERENCES stock_item(id) ON DELETE SET NULL;
ALTER TABLE stock_item_supplier ADD CONSTRAINT stock_item_supplier_manufacturer_item_id_fkey
    FOREIGN KEY (manufacturer_item_id) REFERENCES manufacturer_item(id) ON DELETE SET NULL;
ALTER TABLE stock_item_supplier ADD CONSTRAINT stock_item_supplier_stock_item_id_fkey
    FOREIGN KEY (stock_item_id) REFERENCES stock_item(id) ON DELETE CASCADE;
ALTER TABLE stock_item_supplier ADD CONSTRAINT stock_item_supplier_supplier_id_fkey
    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE CASCADE;
ALTER TABLE stock_sub_family ADD CONSTRAINT stock_sub_family_family_code_fkey
    FOREIGN KEY (family_code) REFERENCES stock_family(code) ON DELETE CASCADE;
ALTER TABLE stock_sub_family ADD CONSTRAINT stock_sub_family_template_fk
    FOREIGN KEY (template_id) REFERENCES part_template(id) ON DELETE SET NULL;
ALTER TABLE subtask ADD CONSTRAINT subtask_intervention_id_fkey
    FOREIGN KEY (intervention_id) REFERENCES intervention(id) ON DELETE CASCADE;
ALTER TABLE supplier_order ADD CONSTRAINT supplier_order_supplier_id_fkey
    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT;
ALTER TABLE supplier_order_line ADD CONSTRAINT supplier_order_line_stock_item_id_fkey
    FOREIGN KEY (stock_item_id) REFERENCES stock_item(id) ON DELETE RESTRICT;
ALTER TABLE supplier_order_line ADD CONSTRAINT supplier_order_line_supplier_order_id_fkey
    FOREIGN KEY (supplier_order_id) REFERENCES supplier_order(id) ON DELETE CASCADE;
ALTER TABLE supplier_order_line_purchase_request ADD CONSTRAINT supplier_order_line_purchase_reques_supplier_order_line_id_fkey
    FOREIGN KEY (supplier_order_line_id) REFERENCES supplier_order_line(id) ON DELETE CASCADE;
ALTER TABLE supplier_order_line_purchase_request ADD CONSTRAINT supplier_order_line_purchase_request_purchase_request_id_fkey
    FOREIGN KEY (purchase_request_id) REFERENCES purchase_request(id) ON DELETE CASCADE;
ALTER TABLE tunnel_permission ADD CONSTRAINT tunnel_permission_endpoint_id_fkey
    FOREIGN KEY (endpoint_id) REFERENCES tunnel_endpoint(id);
ALTER TABLE tunnel_permission ADD CONSTRAINT tunnel_permission_role_id_fkey
    FOREIGN KEY (role_id) REFERENCES tunnel_role(id);
ALTER TABLE tunnel_user ADD CONSTRAINT tunnel_user_role_id_fkey
    FOREIGN KEY (role_id) REFERENCES tunnel_role(id);


-- ------------------------------------------------------------------------------
-- FUNCTIONS & PROCEDURES
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.calculate_line_total()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  IF NEW.unit_price IS NOT NULL AND NEW.quantity IS NOT NULL THEN
    NEW.total_price = NEW.unit_price * NEW.quantity;
  END IF;
  
  RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.check_intervention_closable()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
    DECLARE
        blocking_count INTEGER;
    BEGIN
        IF NEW.status_actual != 'ferme' OR OLD.status_actual = 'ferme' THEN
            RETURN NEW;
        END IF;

        IF NEW.plan_id IS NULL THEN
            RETURN NEW;
        END IF;

        SELECT COUNT(*) INTO blocking_count
        FROM public.intervention_task
        WHERE intervention_id = NEW.id
          AND status IN ('todo', 'in_progress')
          AND optional = FALSE;

        IF blocking_count > 0 THEN
            RAISE EXCEPTION 'GAMME_INCOMPLETE: % tache(s) obligatoire(s) en attente', blocking_count;
        END IF;

        RETURN NEW;
    END;
    $function$;

CREATE OR REPLACE FUNCTION public.detect_preventive_suggestions()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
  v_rule RECORD;
  v_machine_id UUID;
  v_description_lower TEXT;
  v_action_subcategory_code TEXT;
  v_count_inserted INT := 0;
BEGIN
  -- ─────────────────────────────────────────────────────────────────
  -- 1. Sécurité minimale
  -- ─────────────────────────────────────────────────────────────────
  
  -- Pas de description = pas d'analyse
  IF new.description IS NULL OR length(trim(new.description)) < 10 THEN
    RETURN new;
  END IF;
  
  -- Minuscule une seule fois pour la boucle
  v_description_lower := lower(new.description);
  
  -- ─────────────────────────────────────────────────────────────────
  -- 2. Filtre métier : uniquement dépannage (DEP_*)
  -- ─────────────────────────────────────────────────────────────────
  
  -- Récupérer le code de la sous-catégorie d'action
  SELECT sc.code
  INTO v_action_subcategory_code
  FROM action_subcategory sc
  WHERE sc.id = new.action_subcategory;
  
  -- Si pas de sous-catégorie ou n'est pas un dépannage, arrêt
  IF v_action_subcategory_code IS NULL OR NOT v_action_subcategory_code LIKE 'DEP_%' THEN
    RETURN new;
  END IF;
  
  -- ─────────────────────────────────────────────────────────────────
  -- 3. Récupérer machine_id de l'intervention
  -- ─────────────────────────────────────────────────────────────────
  
  SELECT i.machine_id
  INTO v_machine_id
  FROM intervention i
  WHERE i.id = new.intervention_id;
  
  -- Si pas d'intervention ou pas de machine, arrêt
  IF v_machine_id IS NULL THEN
    RETURN new;
  END IF;
  
  -- ─────────────────────────────────────────────────────────────────
  -- 4. Boucle de détection : mots-clés → précos
  -- ─────────────────────────────────────────────────────────────────
  
  FOR v_rule IN
    SELECT 
      pr.id,
      pr.keyword,
      pr.preventive_code,
      pr.preventive_label,
      pr.weight
    FROM preventive_rule pr
    WHERE pr.active = TRUE
    ORDER BY pr.weight DESC
  LOOP
    -- Vérifier si le mot-clé est dans la description
    -- Recherche sensible au contexte : ' mot ' ou début/fin
    IF (
      v_description_lower LIKE '%' || v_rule.keyword || '%'
    ) THEN
      -- Insérer la préconisation (CONFLICT sur UNIQUE constraint)
      INSERT INTO preventive_suggestion (
        intervention_action_id,
        machine_id,
        preventive_code,
        preventive_label,
        score
      )
      VALUES (
        new.id,
        v_machine_id,
        v_rule.preventive_code,
        v_rule.preventive_label,
        v_rule.weight
      )
      ON CONFLICT (machine_id, preventive_code) DO NOTHING;
      
      v_count_inserted := v_count_inserted + 1;
    END IF;
  END LOOP;
  
  -- ─────────────────────────────────────────────────────────────────
  -- 5. Logging (optionnel, à adapter selon ta config)
  -- ─────────────────────────────────────────────────────────────────
  
  -- Décommenter pour debug :
  -- RAISE NOTICE 'detect_preventive_suggestions: action_id=%, machine_id=%, inserted=%',
  --   new.id, v_machine_id, v_count_inserted;
  
  RETURN new;
END;
$function$;

CREATE OR REPLACE FUNCTION public.dispatch_purchase_requests()
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
  v_dispatched TEXT[] := ARRAY[]::TEXT[];
  v_to_qualify TEXT[] := ARRAY[]::TEXT[];
  v_errors json[] := ARRAY[]::json[];
  
  v_req RECORD;
  v_pref_supplier_id UUID;
  v_pref_supplier_ref VARCHAR;
  v_supplier_order_id UUID;
BEGIN
  -- Loop sur toutes les demandes ouvertes avec article lié
  FOR v_req IN
    SELECT 
      pr.id,
      pr.stock_item_id,
      pr.quantity,
      pr.status
    FROM public.purchase_request pr
    WHERE pr.status = 'open' 
      AND pr.stock_item_id IS NOT NULL
  LOOP
    -- Trouver le fournisseur préféré pour cet article
    SELECT 
      sis.supplier_id,
      sis.supplier_ref
    INTO v_pref_supplier_id, v_pref_supplier_ref
    FROM public.stock_item_supplier sis
    WHERE sis.stock_item_id = v_req.stock_item_id
      AND sis.is_preferred = TRUE
    LIMIT 1;

    -- Si pas de fournisseur préféré
    IF v_pref_supplier_id IS NULL THEN
      v_to_qualify := array_append(v_to_qualify, v_req.id::TEXT);
      CONTINUE;
    END IF;

    BEGIN
      -- Chercher panier OPEN du fournisseur, sinon en créer un
      SELECT so.id
      INTO v_supplier_order_id
      FROM public.supplier_order so
      WHERE so.supplier_id = v_pref_supplier_id
        AND so.status = 'OPEN'
      ORDER BY so.created_at DESC
      LIMIT 1;

      IF v_supplier_order_id IS NULL THEN
        -- Créer nouveau panier
        INSERT INTO public.supplier_order (supplier_id, status, total_amount)
        VALUES (v_pref_supplier_id, 'OPEN', 0)
        RETURNING id INTO v_supplier_order_id;
      END IF;

      -- Créer ou mettre à jour la ligne dans le panier (évite l'unicité supplier_order_id + stock_item_id)
      INSERT INTO public.supplier_order_line (
        supplier_order_id,
        stock_item_id,
        supplier_ref_snapshot,
        quantity,
        unit_price,
        total_price
      )
      VALUES (
        v_supplier_order_id,
        v_req.stock_item_id,
        v_pref_supplier_ref,
        COALESCE(v_req.quantity, 1),
        NULL,
        NULL
      )
      ON CONFLICT (supplier_order_id, stock_item_id)
      DO UPDATE SET quantity = COALESCE(public.supplier_order_line.quantity, 0) + COALESCE(EXCLUDED.quantity, 1);

      -- Mettre à jour statut demande à 'in_progress'
      UPDATE public.purchase_request
      SET status = 'in_progress'
      WHERE id = v_req.id;

      v_dispatched := array_append(v_dispatched, v_req.id::TEXT);

    EXCEPTION WHEN OTHERS THEN
      -- Log erreur et continue
      v_errors := array_append(
        v_errors,
        json_build_object(
          'id', v_req.id::TEXT,
          'error', SQLERRM
        )
      );
    END;
  END LOOP;

  -- Retourner résultat au format JSON
  RETURN json_build_object(
    'dispatched', COALESCE(v_dispatched, ARRAY[]::TEXT[]),
    'toQualify', COALESCE(v_to_qualify, ARRAY[]::TEXT[]),
    'errors', COALESCE(v_errors, ARRAY[]::json[])
  );
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_apply_request_status()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE public.intervention_request
    SET statut = NEW.status_to
    WHERE id = NEW.request_id;
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_compute_action_time()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
        DECLARE
            has_bounds BOOLEAN := (NEW.action_start IS NOT NULL AND NEW.action_end IS NOT NULL);
            has_time   BOOLEAN := (NEW.time_spent IS NOT NULL);
        BEGIN
            IF has_bounds AND has_time THEN
                RAISE EXCEPTION 'Ambiguïté : fournir soit les bornes horaires soit time_spent, pas les deux';
            END IF;
            IF NOT has_bounds AND NOT has_time THEN
                RAISE EXCEPTION 'time_spent ou les bornes action_start/action_end sont requis';
            END IF;
            IF has_bounds THEN
                IF EXTRACT(MINUTE FROM NEW.action_start) NOT IN (0, 15, 30, 45) THEN
                    RAISE EXCEPTION 'action_start doit être un multiple de 15 minutes';
                END IF;
                IF EXTRACT(MINUTE FROM NEW.action_end) NOT IN (0, 15, 30, 45) THEN
                    RAISE EXCEPTION 'action_end doit être un multiple de 15 minutes';
                END IF;
                IF NEW.action_end <= NEW.action_start THEN
                    RAISE EXCEPTION 'action_end doit être postérieur à action_start';
                END IF;
                NEW.time_spent := EXTRACT(EPOCH FROM (NEW.action_end - NEW.action_start)) / 3600.0;
            END IF;
            IF has_time THEN
                IF (NEW.time_spent * 4) <> FLOOR(NEW.time_spent * 4) THEN
                    RAISE EXCEPTION 'time_spent doit être un multiple de 0.25';
                END IF;
                IF NEW.time_spent < 0.25 THEN
                    RAISE EXCEPTION 'time_spent minimum est 0.25h';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $function$;

CREATE OR REPLACE FUNCTION public.fn_generate_request_code()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_year TEXT := to_char(now(), 'YYYY');
    v_seq  INT;
BEGIN
    SELECT COUNT(*) + 1
    INTO v_seq
    FROM public.intervention_request
    WHERE code LIKE 'DI-' || v_year || '-%';

    NEW.code := 'DI-' || v_year || '-' || lpad(v_seq::TEXT, 4, '0');
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_init_request_status_log()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    PERFORM set_config('app.skip_request_status_log', 'true', true);

    INSERT INTO public.request_status_log (request_id, status_from, status_to, notes)
    VALUES (NEW.id, NULL, 'nouvelle', 'Création demande');

    PERFORM set_config('app.skip_request_status_log', 'false', true);
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_log_request_status_change()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF current_setting('app.skip_request_status_log', true) = 'true' THEN
        RETURN NEW;
    END IF;

    IF NEW.statut IS DISTINCT FROM OLD.statut THEN
        -- Vérifie que le statut actuel correspond à la dernière entrée du log
        IF OLD.statut IS DISTINCT FROM (
            SELECT status_to FROM public.request_status_log
            WHERE request_id = NEW.id
            ORDER BY date DESC
            LIMIT 1
        ) THEN
            RAISE EXCEPTION
                'Incohérence statut : statut actuel "%" ne correspond pas à la dernière entrée du log',
                OLD.statut;
        END IF;

        INSERT INTO public.request_status_log (request_id, status_from, status_to)
        VALUES (NEW.id, OLD.statut, NEW.statut);
    END IF;

    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_machine_hours_update()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
        DECLARE
            v_machine_id UUID;
            v_delta      NUMERIC(10,2);
        BEGIN
            SELECT i.machine_id INTO v_machine_id
            FROM public.intervention i
            WHERE i.id = NEW.intervention_id;

            IF v_machine_id IS NULL THEN RETURN NEW; END IF;

            IF TG_OP = 'INSERT' THEN
                v_delta := COALESCE(NEW.time_spent, 0);
            ELSE
                v_delta := COALESCE(NEW.time_spent, 0) - COALESCE(OLD.time_spent, 0);
            END IF;

            INSERT INTO public.machine_hours (machine_id, hours_total, updated_at)
            VALUES (v_machine_id, GREATEST(0, v_delta), NOW())
            ON CONFLICT (machine_id) DO UPDATE
                SET hours_total = GREATEST(0, public.machine_hours.hours_total + v_delta),
                    updated_at  = NOW();

            RETURN NEW;
        END;
        $function$;

CREATE OR REPLACE FUNCTION public.fn_set_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $function$;

CREATE OR REPLACE FUNCTION public.fn_sync_status_log_to_intervention()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
        DECLARE
            v_status_code TEXT;
            v_occurrence_id UUID;
            v_request_id UUID;
            v_request_statut TEXT;
        BEGIN
            -- 1. Mettre à jour intervention.status_actual avec le nouveau statut
            UPDATE public.intervention
            SET status_actual = NEW.status_to
            WHERE id = NEW.intervention_id;

            -- 2. Résoudre le code du statut cible
            SELECT code INTO v_status_code
            FROM public.intervention_status_ref
            WHERE id = NEW.status_to;

            -- 3. Si fermeture : propager sur l'occurrence préventive + la demande
            IF v_status_code = 'ferme' THEN

                -- Chercher l'occurrence liée à cette intervention
                SELECT id INTO v_occurrence_id
                FROM public.preventive_occurrence
                WHERE intervention_id = NEW.intervention_id
                LIMIT 1;

                IF v_occurrence_id IS NOT NULL THEN
                    UPDATE public.preventive_occurrence
                    SET status = 'completed'
                    WHERE id = v_occurrence_id;
                END IF;

                -- Clôturer la demande liée si elle est encore 'acceptee'
                SELECT id, statut INTO v_request_id, v_request_statut
                FROM public.intervention_request
                WHERE intervention_id = NEW.intervention_id
                  AND statut = 'acceptee'
                LIMIT 1;

                IF v_request_id IS NOT NULL THEN
                    UPDATE public.intervention_request
                    SET statut = 'cloturee'
                    WHERE id = v_request_id;

                    INSERT INTO public.request_status_log
                        (request_id, status_from, status_to, changed_by, notes)
                    VALUES (
                        v_request_id,
                        v_request_statut,
                        'cloturee',
                        NULL,
                        'Clôture automatique suite à la fermeture de l''intervention (via log de statut)'
                    );
                END IF;

            END IF;

            RETURN NEW;
        END;
        $function$;

CREATE OR REPLACE FUNCTION public.fn_update_supplier_refs_count()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Cas INSERT : incrémenter le compte de l'article
    IF (TG_OP = 'INSERT') THEN
        UPDATE public.stock_item
        SET supplier_refs_count = supplier_refs_count + 1
        WHERE id = NEW.stock_item_id;
        RETURN NEW;
    END IF;

    -- Cas DELETE : décrémenter le compte de l'article
    IF (TG_OP = 'DELETE') THEN
        UPDATE public.stock_item
        SET supplier_refs_count = GREATEST(0, supplier_refs_count - 1)
        WHERE id = OLD.stock_item_id;
        RETURN OLD;
    END IF;

    -- Cas UPDATE : si stock_item_id change, ajuster les deux articles
    IF (TG_OP = 'UPDATE') THEN
        IF (OLD.stock_item_id != NEW.stock_item_id) THEN
            -- Décrémenter l'ancien article
            UPDATE public.stock_item
            SET supplier_refs_count = GREATEST(0, supplier_refs_count - 1)
            WHERE id = OLD.stock_item_id;
            
            -- Incrémenter le nouvel article
            UPDATE public.stock_item
            SET supplier_refs_count = supplier_refs_count + 1
            WHERE id = NEW.stock_item_id;
        END IF;
        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_updated_at_preventive_plan()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
        BEGIN
            NEW.updated_at := NOW();
            RETURN NEW;
        END;
        $function$;

CREATE OR REPLACE FUNCTION public.generate_intervention_code()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
  machine_code TEXT;
  today TEXT := to_char(current_date, 'YYYYMMDD');
BEGIN
  SELECT code INTO machine_code
  FROM machine
  WHERE id = NEW.machine_id;

  IF machine_code IS NULL THEN
    RAISE EXCEPTION 'Machine % inconnue', NEW.machine_id;
  END IF;

  IF NEW.type_inter IS NULL THEN
    RAISE EXCEPTION 'type_inter est requis pour générer le code intervention';
  END IF;

  IF NEW.tech_initials IS NULL THEN
    RAISE EXCEPTION 'tech_initials est requis pour générer le code intervention';
  END IF;

  NEW.code := machine_code || '-' || NEW.type_inter || '-' || today || '-' || NEW.tech_initials;

  RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.generate_stock_item_ref()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  -- Génère référence : FAM-SFAM-SPEC-DIM (sans tirets inutiles)
  -- Ne concatène le séparateur que si la valeur existe
  NEW.ref := NEW.family_code;
  
  IF NEW.sub_family_code IS NOT NULL AND NEW.sub_family_code != '' THEN
    NEW.ref := NEW.ref || '-' || NEW.sub_family_code;
  END IF;
  
  IF NEW.spec IS NOT NULL AND NEW.spec != '' THEN
    NEW.ref := NEW.ref || '-' || NEW.spec;
  END IF;
  
  IF NEW.dimension IS NOT NULL AND NEW.dimension != '' THEN
    NEW.ref := NEW.ref || '-' || NEW.dimension;
  END IF;
  
  RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.generate_supplier_order_number()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
    NEW.order_number := 'CMD-' || 
                        to_char(current_date, 'YYYYMMDD') || '-' || 
                        LPAD(nextval('supplier_order_seq')::TEXT, 4, '0');
  END IF;
  
  RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.trg_init_status_log()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    new_log_id UUID := uuid_generate_v4();
BEGIN
    -- Initialise statut à "ouvert"
    UPDATE public.intervention
    SET status_actual = 'ouvert'
    WHERE id = NEW.id;

    -- Crée log initial
    INSERT INTO public.intervention_status_log (
        id,
        intervention_id,
        status_from,
        status_to,
        date,
        technician_id,
        notes
    )
    VALUES (
        new_log_id,
        NEW.id,
        NULL, -- Pas de statut précédent
        'ouvert',
        NOW(),
        NULL,
        'Création intervention'
    );

    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.trg_log_status_change()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    new_log_id UUID := uuid_generate_v4();
BEGIN
    -- ⚠️ Ignore les créations (OLD.status_actual IS NULL)
    IF OLD.status_actual IS NOT NULL AND NEW.status_actual IS DISTINCT FROM OLD.status_actual THEN
        INSERT INTO public.intervention_status_log (
            id,
            intervention_id,
            status_from,
            status_to,
            date,
            technician_id,
            notes
        )
        VALUES (
            new_log_id,
            NEW.id,
            OLD.status_actual,
            NEW.status_actual,
            NOW(),
            NEW.updated_by,
            'Changement statut automatique'
        );
    END IF;

    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.uuid_generate_v1()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v1$function$;

CREATE OR REPLACE FUNCTION public.uuid_generate_v1mc()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v1mc$function$;

CREATE OR REPLACE FUNCTION public.uuid_generate_v3(namespace uuid, name text)
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v3$function$;

CREATE OR REPLACE FUNCTION public.uuid_generate_v4()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v4$function$;

CREATE OR REPLACE FUNCTION public.uuid_generate_v5(namespace uuid, name text)
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v5$function$;

CREATE OR REPLACE FUNCTION public.uuid_nil()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_nil$function$;

CREATE OR REPLACE FUNCTION public.uuid_ns_dns()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_dns$function$;

CREATE OR REPLACE FUNCTION public.uuid_ns_oid()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_oid$function$;

CREATE OR REPLACE FUNCTION public.uuid_ns_url()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_url$function$;

CREATE OR REPLACE FUNCTION public.uuid_ns_x500()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_x500$function$;



-- ------------------------------------------------------------------------------
-- TRIGGERS
-- ------------------------------------------------------------------------------
CREATE TRIGGER update_action_category_meta_updated_at BEFORE UPDATE ON public.action_category_meta FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_action_classification_probe_updated_at BEFORE UPDATE ON public.action_classification_probe FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_anomaly_threshold_updated_at BEFORE UPDATE ON public.anomaly_threshold FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_check_intervention_closable BEFORE UPDATE ON public.intervention FOR EACH ROW EXECUTE FUNCTION check_intervention_closable();
CREATE TRIGGER trg_init_status_log AFTER INSERT ON public.intervention FOR EACH ROW EXECUTE FUNCTION trg_init_status_log();
CREATE TRIGGER trg_interv_code BEFORE INSERT ON public.intervention FOR EACH ROW EXECUTE FUNCTION generate_intervention_code();
CREATE TRIGGER trg_log_status_change AFTER UPDATE ON public.intervention FOR EACH ROW WHEN (((old.status_actual)::text IS DISTINCT FROM (new.status_actual)::text)) EXECUTE FUNCTION trg_log_status_change();
CREATE TRIGGER trg_compute_action_time_insert BEFORE INSERT ON public.intervention_action FOR EACH ROW EXECUTE FUNCTION fn_compute_action_time();
CREATE TRIGGER trg_compute_action_time_update BEFORE UPDATE OF time_spent, action_start, action_end ON public.intervention_action FOR EACH ROW EXECUTE FUNCTION fn_compute_action_time();
CREATE TRIGGER trg_detect_preventive AFTER INSERT ON public.intervention_action FOR EACH ROW EXECUTE FUNCTION detect_preventive_suggestions();
CREATE TRIGGER trg_machine_hours_update AFTER INSERT OR UPDATE OF time_spent ON public.intervention_action FOR EACH ROW EXECUTE FUNCTION fn_machine_hours_update();
CREATE TRIGGER trg_init_request_status_log AFTER INSERT ON public.intervention_request FOR EACH ROW EXECUTE FUNCTION fn_init_request_status_log();
CREATE TRIGGER trg_log_request_status_change AFTER UPDATE OF statut ON public.intervention_request FOR EACH ROW EXECUTE FUNCTION fn_log_request_status_change();
CREATE TRIGGER trg_request_code BEFORE INSERT ON public.intervention_request FOR EACH ROW EXECUTE FUNCTION fn_generate_request_code();
CREATE TRIGGER trg_request_updated_at BEFORE UPDATE ON public.intervention_request FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_sync_status_log_to_intervention AFTER INSERT ON public.intervention_status_log FOR EACH ROW EXECUTE FUNCTION fn_sync_status_log_to_intervention();
CREATE TRIGGER trg_updated_at_preventive_plan BEFORE UPDATE ON public.preventive_plan FOR EACH ROW EXECUTE FUNCTION fn_updated_at_preventive_plan();
CREATE TRIGGER trg_purchase_request_updated_at BEFORE UPDATE ON public.purchase_request FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_apply_request_status AFTER INSERT ON public.request_status_log FOR EACH ROW EXECUTE FUNCTION fn_apply_request_status();
CREATE TRIGGER trg_generate_stock_item_ref BEFORE INSERT OR UPDATE OF family_code, sub_family_code, spec, dimension ON public.stock_item FOR EACH ROW EXECUTE FUNCTION generate_stock_item_ref();
CREATE TRIGGER trg_stock_item_supplier_refs_count_delete AFTER DELETE ON public.stock_item_supplier FOR EACH ROW EXECUTE FUNCTION fn_update_supplier_refs_count();
CREATE TRIGGER trg_stock_item_supplier_refs_count_insert AFTER INSERT ON public.stock_item_supplier FOR EACH ROW EXECUTE FUNCTION fn_update_supplier_refs_count();
CREATE TRIGGER trg_stock_item_supplier_refs_count_update AFTER UPDATE ON public.stock_item_supplier FOR EACH ROW WHEN ((old.stock_item_id IS DISTINCT FROM new.stock_item_id)) EXECUTE FUNCTION fn_update_supplier_refs_count();
CREATE TRIGGER trg_stock_item_supplier_updated_at BEFORE UPDATE ON public.stock_item_supplier FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_supplier_updated_at BEFORE UPDATE ON public.supplier FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_generate_supplier_order_number BEFORE INSERT ON public.supplier_order FOR EACH ROW EXECUTE FUNCTION generate_supplier_order_number();
CREATE TRIGGER trg_supplier_order_updated_at BEFORE UPDATE ON public.supplier_order FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_calculate_line_total BEFORE INSERT OR UPDATE OF unit_price, quantity ON public.supplier_order_line FOR EACH ROW EXECUTE FUNCTION calculate_line_total();
CREATE TRIGGER trg_supplier_order_line_updated_at BEFORE UPDATE ON public.supplier_order_line FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_tunnel_user_updated_at BEFORE UPDATE ON public.tunnel_user FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- ------------------------------------------------------------------------------
-- VIEWS
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW preventive_suggestion_by_status AS
SELECT ps.id,
    ps.intervention_action_id,
    ps.machine_id,
    ps.preventive_code,
    ps.preventive_label,
    ps.score,
    ps.status,
    ps.detected_at,
    ps.handled_at,
    ps.handled_by,
    m.code AS machine_code,
    m.name AS machine_name
   FROM (preventive_suggestion ps
     LEFT JOIN machine m ON ((ps.machine_id = m.id)))
  ORDER BY ps.detected_at DESC;;

