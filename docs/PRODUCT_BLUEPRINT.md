# JEZTECH Intelligent Exam Analytics — Product Blueprint

This blueprint is derived from the uploaded **exam analysis.html** and its navigation, forms, tables and workflows. The uploaded file is treated as a feature reference, not as code to copy wholesale.

## Product scope

### 1. School and account foundation
- Multi-school tenancy with school identity, curriculum selection (CBC/CBE, 8-4-4 or both), academic year and term.
- Role-based access for School Administrator, Principal, Director of Studies (DOS), HOD, Teacher, Learner and Parent.
- Account creation, password hashing, session expiry, account activation and audit trail.
- School data isolation at every API query and write.

### 2. Academic setup
- Class and stream management.
- Learner register with admission number, name, gender, class and active status.
- Teacher and staff register with staff/TSC reference.
- Subject catalogue and class/subject/teacher allocation.
- Configurable grading scales for the school's curriculum and assessment model.

### 3. Examinations and assessment
- Academic year, term, exam type and exam status.
- Exam creation, subject papers, class mapping, maximum score, weight and instructions.
- Room creation, capacity and supervisor.
- Exam-to-room mapping and conflict/capacity validation.
- Marks entry by class and subject, validation against maximum marks, draft/final states and moderation.
- CBC/CBE assessment support and 8-4-4 grading support without forcing both systems into one grading formula.
- Practical assessment and teacher-uploaded learning evidence.
- Scanned PDF/photo submissions, manual marking, moderation and downloadable source attachment.

### 4. Analytics and reports
- Exam summary, class analysis, subject analysis, learner performance and teacher/class comparisons.
- Mean score, mean percentage, grade distribution, subject ranking, class ranking and trend comparisons.
- Learner progress only when prior comparable assessment data exists; no random or fabricated improvement values.
- Missing-mark and incomplete-assessment warnings.
- Print-ready learner report cards, class reports and exportable result schedules.
- Report filters for academic year, term, exam, class, subject and learner.

### 5. Learner welfare and parent engagement
- Discipline incident register, action taken, status and follow-up history.
- Parent register and learner-parent relationship mapping.
- Parent onboarding and contact verification status.
- Parent communications queue for SMS and WhatsApp, delivery receipts and failure states.
- Parent portal for viewing approved reports and notices (separate authentication and scoped learner access).

### 6. Platform operations
- School backup and restore with validation and pre-restore snapshot.
- Subscription plans, learner limits, termly/annual billing and invoice history.
- M-PESA integration through official Daraja credentials, signed callbacks and reconciliation.
- AI question drafting as an optional provider-backed assistant; generated questions must be reviewed by a teacher.
- Practical/tutorial media metadata and protected file storage.

## Delivery sequence
1. Secure foundation: tenancy, authentication, role permissions, database migrations, audit log.
2. Academic setup: classes, learners, staff, subjects and grade scales.
3. Assessment: exams, papers, room allocations, marks entry, moderation and practicals.
4. Analytics: verified calculations, report cards, exports and trend analysis.
5. Parent and learner portals, discipline and notifications.
6. Subscription, M-PESA, AI and file/backup integrations.

## Non-negotiable quality gates
- Every API endpoint has authentication and tenant-scope tests.
- No passwords or API secrets in browser storage or source control.
- No integration is described as active until a real provider response is confirmed.
- No analytics value is invented to fill missing records.
- Every mark edit records who changed it and when.
- Database changes are versioned migrations; production uses managed PostgreSQL.
- Each release must pass backend tests and frontend production build.
