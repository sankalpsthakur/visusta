-- 002_seed_locales.sql
-- Seed all 24 EU official languages

INSERT OR IGNORE INTO locales (code, name, native_name) VALUES
    ('bg', 'Bulgarian',   'Български'),
    ('hr', 'Croatian',    'Hrvatski'),
    ('cs', 'Czech',       'Čeština'),
    ('da', 'Danish',      'Dansk'),
    ('nl', 'Dutch',       'Nederlands'),
    ('en', 'English',     'English'),
    ('et', 'Estonian',    'Eesti'),
    ('fi', 'Finnish',     'Suomi'),
    ('fr', 'French',      'Français'),
    ('de', 'German',      'Deutsch'),
    ('el', 'Greek',       'Ελληνικά'),
    ('hu', 'Hungarian',   'Magyar'),
    ('ga', 'Irish',       'Gaeilge'),
    ('it', 'Italian',     'Italiano'),
    ('lv', 'Latvian',     'Latviešu'),
    ('lt', 'Lithuanian',  'Lietuvių'),
    ('mt', 'Maltese',     'Malti'),
    ('pl', 'Polish',      'Polski'),
    ('pt', 'Portuguese',  'Português'),
    ('ro', 'Romanian',    'Română'),
    ('sk', 'Slovak',      'Slovenčina'),
    ('sl', 'Slovenian',   'Slovenščina'),
    ('es', 'Spanish',     'Español'),
    ('sv', 'Swedish',     'Svenska');
