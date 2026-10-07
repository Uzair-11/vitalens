-- VitaLens PostgreSQL Initialization Script
-- Automatically executed upon container first initialization

SELECT 'CREATE DATABASE vitalens_test_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vitalens_test_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE vitalens_test_db TO postgres;
