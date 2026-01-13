-- Reporting schema for the application's Postgres database
-- Generated from current SQLModel models and Alembic migrations
-- This schema targets the latest state after UUID migration and length adjustments.

-- Enable uuid-ossp for UUID generation if not already present
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS "user" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL,
    is_superuser BOOLEAN NOT NULL,
    full_name VARCHAR(255),
    hashed_password TEXT NOT NULL
);

-- Unique email index (as per Alembic migration)
CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email ON "user"(email);

-- Items table
CREATE TABLE IF NOT EXISTS item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    owner_id UUID NOT NULL
);

-- Foreign key with cascade delete (as per Alembic migration 1a31ce608336)
ALTER TABLE item
    ADD CONSTRAINT item_owner_id_fkey
    FOREIGN KEY (owner_id) REFERENCES "user"(id)
    ON DELETE CASCADE;

-- Helpful views for reporting

-- Count of items per user
CREATE OR REPLACE VIEW reporting_user_item_counts AS
SELECT
    u.id AS user_id,
    u.email,
    COALESCE(COUNT(i.id), 0) AS item_count
FROM "user" u
LEFT JOIN item i ON i.owner_id = u.id
GROUP BY u.id, u.email
ORDER BY item_count DESC;

-- Items with owner details
CREATE OR REPLACE VIEW reporting_items_with_owners AS
SELECT
    i.id AS item_id,
    i.title,
    i.description,
    i.owner_id,
    u.email AS owner_email,
    u.full_name AS owner_full_name,
    u.is_active AS owner_is_active
FROM item i
JOIN "user" u ON u.id = i.owner_id;

-- Recent items (last 30 days) — requires created_at if available.
-- NOTE: The current models/migrations do not include timestamps.
-- If timestamps are added later, you can implement:
-- CREATE OR REPLACE VIEW reporting_recent_items AS
-- SELECT * FROM item WHERE created_at >= now() - interval '30 days';