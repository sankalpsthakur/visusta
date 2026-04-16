-- 003_seed_norwegian_locales.sql
-- Seed Norwegian Bokmål (nb) and Nynorsk (nn) so the locale alias map
-- (no / NO / no-NO / nor / nob → nb, nno → nn) resolves to a real
-- locale row and /translate stops 422-ing on target_locale=no.
-- INSERT OR IGNORE is idempotent if the migration ever re-runs.

INSERT OR IGNORE INTO locales (code, name, native_name) VALUES
    ('nb', 'Norwegian Bokmål',  'Norsk bokmål'),
    ('nn', 'Norwegian Nynorsk', 'Norsk nynorsk');
