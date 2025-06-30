-- PostgreSQL database setup for IoT Connectivity Layer
-- This script is automatically executed when Docker container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Grant additional privileges to the user
GRANT ALL ON SCHEMA public TO iotflow_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iotflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iotflow_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO iotflow_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO iotflow_user;

-- Create indexes that will be useful for the IoT data
-- These will be created by SQLAlchemy models, but we can prepare some general ones

-- Log the setup completion
SELECT 'Database setup completed successfully!' as message;
