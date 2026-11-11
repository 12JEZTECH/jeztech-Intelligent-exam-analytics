# JEZTECH Intelligent Exam Analytics — Clean Rebuild

A multi-school assessment and examination platform for Kenyan schools using CBC/CBE and 8-4-4.

## Product rules
- One school is one tenant. Every school-owned record is scoped to the authenticated user's school.
- PostgreSQL is the production database; SQLite is local-development only.
- No fabricated AI, payment, messaging, backup or analytics success states.
- Grade calculations and reports use saved marks and school-configured grade bands.
- Permissions are enforced in API endpoints, not only hidden in the UI.

## Foundation being built
School registration and authentication; learners, classes, subjects, exams and papers; mark entry and moderation; teacher and parent portals; practical assessment; scanned scripts; room allocation; report cards; discipline; exports; subscription and integrations.

## Local development
Backend: install `backend/requirements.txt`, set `DATABASE_URL=sqlite:///./jeztech_dev.db` and `JWT_SECRET`, then run `uvicorn app.main:app --reload` from `backend`.
Frontend: run `npm install && npm run dev` from `frontend`, with `VITE_API_URL=http://localhost:8000`.

## Production
Provision PostgreSQL, set `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, deploy API and frontend separately, and apply schema migrations before release. Never rely on ephemeral SQLite for school records.

This is a clean foundation. Each module will be implemented and tested before being marked complete.
