BEGIN;

CREATE TABLE IF NOT EXISTS research_activities (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned', 'ongoing', 'completed', 'cancelled')),
    percent_complete INTEGER NOT NULL DEFAULT 0
        CHECK (percent_complete BETWEEN 0 AND 100),
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_expenditures (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    expenditure_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    amount NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    reference VARCHAR(120),
    recorded_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_activities_project_date
    ON research_activities (project_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_research_expenditures_project_date
    ON research_expenditures (project_id, expenditure_date);

COMMIT;
