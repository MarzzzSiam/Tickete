# Review and verification

Current evidence: all supplied requirement text and ERD entity fields reviewed; Phase 0 code and preview now exist. See `11-phase-0-review.md` for executed checks, screenshots and remaining database/infrastructure limitations.

Planning review completed: the user confirmed MD precedence, per-order plus per-email/event cap, and approved the implementation plan. Later-phase choices remain in ADR 0001. The next review concerns Phase 0 visuals and the database setup prerequisite.

Phase review evidence must include executed commands and outcomes, meaningful permission/business tests, responsive screenshots, known limitations and updated task status. Do not mark an external integration verified from a mock or console adapter.

Launch demo: organizer verifies email -> creates event with three categories -> admin approves -> guest purchases and gifts -> recipient downloads PDF -> scanner admits once and rejects repeat -> owner closes -> report reconciles sales and attendance.

Track zero overselling/duplicate admission, delivery latency, scan latency, checkout completion and approval turnaround using real pilot measurements. PRD targets are not marketing claims before evidence exists.
