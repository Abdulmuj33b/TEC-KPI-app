BEGIN;

-- Replace the original role and role/unit constraints with versions
-- that recognise the dedicated institutional R&D Officer role.
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_check;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_allowed_check;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_unit_assignment_check;

ALTER TABLE users
    ADD CONSTRAINT users_role_allowed_check
    CHECK (role IN (
        'director',
        'administrator',
        'head_of_unit',
        'research_officer'
    ));

ALTER TABLE users
    ADD CONSTRAINT users_unit_assignment_check
    CHECK (
        (role = 'head_of_unit' AND unit_id IS NOT NULL)
        OR
        (role IN ('director', 'administrator', 'research_officer')
            AND unit_id IS NULL)
    );

COMMIT;
