BEGIN;

CREATE TABLE IF NOT EXISTS units (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    unit_type VARCHAR(30) NOT NULL DEFAULT 'production'
        CHECK (unit_type IN ('production', 'administration')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL
        CHECK (role IN ('director', 'administrator', 'head_of_unit')),
    unit_id BIGINT REFERENCES units(id) ON DELETE RESTRICT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (role = 'head_of_unit' AND unit_id IS NOT NULL)
        OR
        (role IN ('director', 'administrator') AND unit_id IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS production_records (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_id BIGINT NOT NULL REFERENCES units(id) ON DELETE RESTRICT,
    record_date DATE NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    quantity NUMERIC(14, 2) NOT NULL CHECK (quantity >= 0),
    unit_of_measure VARCHAR(40) NOT NULL,
    unit_cost NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (unit_cost >= 0),
    total_cost NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (total_cost >= 0),
    revenue NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (revenue >= 0),
    notes TEXT,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_programmes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_skills (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    programme_id BIGINT NOT NULL
        REFERENCES training_programmes(id) ON DELETE RESTRICT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (programme_id, name)
);

CREATE TABLE IF NOT EXISTS facilitators (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(40),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_activities (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    programme_id BIGINT NOT NULL
        REFERENCES training_programmes(id) ON DELETE RESTRICT,
    skill_id BIGINT NOT NULL
        REFERENCES training_skills(id) ON DELETE RESTRICT,
    unit_id BIGINT REFERENCES units(id) ON DELETE RESTRICT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    level VARCHAR(150) NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    enrolled INTEGER NOT NULL DEFAULT 0 CHECK (enrolled >= 0),
    trained INTEGER NOT NULL DEFAULT 0 CHECK (trained >= 0),
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed >= 0),
    status VARCHAR(30) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'ongoing', 'completed', 'cancelled')),
    notes TEXT,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_date >= start_date),
    CHECK (trained <= enrolled),
    CHECK (completed <= trained)
);

CREATE TABLE IF NOT EXISTS training_activity_facilitators (
    activity_id BIGINT NOT NULL
        REFERENCES training_activities(id) ON DELETE CASCADE,
    facilitator_id BIGINT NOT NULL
        REFERENCES facilitators(id) ON DELETE RESTRICT,
    PRIMARY KEY (activity_id, facilitator_id)
);

CREATE TABLE IF NOT EXISTS research_projects (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_id BIGINT REFERENCES units(id) ON DELETE RESTRICT,
    title VARCHAR(250) NOT NULL,
    description TEXT,
    lead_name VARCHAR(150),
    start_date DATE,
    end_date DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'proposed'
        CHECK (status IN (
            'proposed', 'ongoing', 'completed', 'suspended', 'cancelled'
        )),
    budget NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (budget >= 0),
    expenditure NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (expenditure >= 0),
    notes TEXT,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS research_outputs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES research_projects(id) ON DELETE CASCADE,
    output_type VARCHAR(80) NOT NULL,
    title VARCHAR(250) NOT NULL,
    output_date DATE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_production_unit_date
    ON production_records (unit_id, record_date);

CREATE INDEX IF NOT EXISTS idx_training_start_date
    ON training_activities (start_date);

CREATE INDEX IF NOT EXISTS idx_training_programme
    ON training_activities (programme_id);

CREATE INDEX IF NOT EXISTS idx_research_unit_status
    ON research_projects (unit_id, status);

INSERT INTO units (name) VALUES
    ('Fashion'),
    ('Leather'),
    ('Graphics'),
    ('Paint'),
    ('Consumables'),
    ('Smart Farm'),
    ('Aquaculture')
ON CONFLICT (name) DO NOTHING;

COMMIT;
