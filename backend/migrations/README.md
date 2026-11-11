# Database migrations

Apply schema changes with `alembic upgrade head` from the backend directory.
Production deployments run this command as the Render pre-deploy step.
The first revision establishes the SQLAlchemy metadata baseline. Future revisions
must use explicit Alembic operations for incremental, reviewable changes.
