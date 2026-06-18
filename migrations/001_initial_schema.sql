CREATE TABLE IF NOT EXISTS page (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    content TEXT NOT NULL DEFAULT '',
    meta_title VARCHAR(255) NOT NULL DEFAULT '',
    meta_description TEXT NOT NULL DEFAULT '',
    status VARCHAR(30) NOT NULL DEFAULT 'published',
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_page_slug ON page (slug);

CREATE TABLE IF NOT EXISTS page_section (
    id INTEGER PRIMARY KEY,
    page_id INTEGER NOT NULL,
    name VARCHAR(120) NOT NULL,
    section_type VARCHAR(80) NOT NULL DEFAULT 'content',
    content TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(page_id) REFERENCES page (id)
);

CREATE TABLE IF NOT EXISTS site_setting (
    id INTEGER PRIMARY KEY,
    key VARCHAR(120) NOT NULL UNIQUE,
    value TEXT NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_site_setting_key ON site_setting (key);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(40) NOT NULL DEFAULT 'admin',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS volunteer_profile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL DEFAULT '',
    city VARCHAR(100) NOT NULL DEFAULT '',
    date_of_birth DATE,
    interests TEXT NOT NULL DEFAULT '',
    skills TEXT NOT NULL DEFAULT '',
    availability VARCHAR(120) NOT NULL DEFAULT '',
    motivation TEXT NOT NULL DEFAULT '',
    emergency_contact VARCHAR(160) NOT NULL DEFAULT '',
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    hours_contributed FLOAT NOT NULL DEFAULT 0,
    admin_notes TEXT NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS media_asset (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(80) NOT NULL,
    alt_text VARCHAR(255) NOT NULL DEFAULT '',
    uploaded_by VARCHAR(120) NOT NULL DEFAULT 'system-import',
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS certificate (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    image VARCHAR(500) NOT NULL,
    issue_date DATE,
    certificate_type VARCHAR(120) NOT NULL DEFAULT 'registration',
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS media_recognition (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    image VARCHAR(500) NOT NULL,
    publication_name VARCHAR(255) NOT NULL DEFAULT '',
    publication_date DATE,
    article_link VARCHAR(500) NOT NULL DEFAULT '',
    category VARCHAR(120) NOT NULL DEFAULT 'newspaper',
    created_at DATETIME NOT NULL
);
