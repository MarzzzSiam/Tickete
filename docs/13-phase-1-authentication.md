# Phase 1 authentication — 2026-10-16

## 2026-10-18 implementation update

The routes below are now implemented under `/api/v1/auth/` (all with a trailing slash):

| Method | Route | Behavior |
|---|---|---|
| POST | register | Validates password, normalizes email, allows buyer/organizer only; returns profile, not a login session |
| POST | login | Returns profile; writes HttpOnly access/refresh cookies and rotates CSRF |
| POST | refresh | Single-use refresh rotation under a database row lock; rotates CSRF |
| POST | logout | Revokes the session and clears cookies; requires CSRF even after access expiry |
| GET/PATCH | me | Current profile; only full name and phone can be edited |
| POST | change-password | Requires current password; revokes every session and outstanding challenge |
| POST | verify-email/request | Authenticated email verification request queued to Celery |
| POST | verify-email/confirm | Consumes a purpose-bound 30-minute link |
| POST | password-reset/request | Same 202 response and dispatch for known/unknown email |
| POST | password-reset/confirm | Consumes a reset link, updates password and revokes all sessions |

Login sessions have UUID identifiers embedded in JWTs. Only a digest of the current refresh JWT is stored; access authentication checks active user and live session on every request. Access expires after five minutes; refresh expires after seven days and extends when rotated. Password changes and logout immediately revoke subsequent access. All session/challenge mutations use database transactions. Refresh replay is rejected; clients must serialize refresh attempts across tabs to avoid stale-token failures.

Verification/reset use 256-bit random link tokens, not six-digit OTPs. Tokens are hashed in storage, purpose-bound and single-use; issuing a new link invalidates the preceding link of that purpose. The queue carries email and purpose only, never the secret link. The worker constructs a link fragment so the token is not sent in HTTP requests/referrers. Frontend fragment handlers are still pending, so this is not yet an end-to-end usable recovery flow.

The worker must deploy the authentication branch before processing `apps.accounts.tasks.deliver_account_link`. Its existing production email backend intentionally fails until a provider is configured. A 202 response means queued/requested, never delivered. Registration is separate from verification dispatch so queue outages cannot turn committed account creation into an ambiguous failure. After registering, log in and explicitly request verification. Real sender/domain integration remains pending; console email is development only.

DRF shared-cache throttles apply per IP (30/minute) and normalized email (10/hour). These are application-level best-effort limits, not atomic abuse prevention under concurrency. The IP uses `REMOTE_ADDR`; reverse-proxy routing must be verified before web deployment to avoid grouping every user under a proxy address. Shared-cache failures return a generic 503. No raw IP/email is stored in throttle keys.

The `0002_authsession_emailchallenge` migration is additive. Do not deploy the new API before migrating. Isolated PostgreSQL integration tests are being verified; no test suite is run against shared Supabase data. The sections below preserve the October 16 increment and its original follow-up plan.

The user requested Phase 1 after reporting worker deployment. Proceed with independent authentication work while preserving the unresolved infrastructure checks; this is not a declaration that Phase 0 acceptance is complete.

## Implemented first increment

- `GET /api/v1/auth/csrf/`: anonymous, returns a masked `csrf_token`, establishes Django's CSRF cookie and uses `Cache-Control: no-store`.
- API authentication reads only the `tickete_access` cookie and validates it with SimpleJWT. User lookup uses the existing Django user model. Missing cookie means anonymous; malformed, expired and refresh tokens are rejected as access credentials.
- Unsafe cookie-authenticated requests require Django CSRF validation, including origin checks. The reusable enforcement function is also intended for anonymous login and refresh handlers, which must enforce CSRF independently of an access token.
- Health and CSRF bootstrap explicitly allow anonymous access. Other endpoints remain protected by default.

The client will fetch the CSRF endpoint with credentials included, keep the returned token in memory and send `X-CSRFToken` with unsafe requests. Login will rotate the CSRF token; clients must obtain the replacement. JWTs will be issued only in HttpOnly cookies, Secure in hosted environments. Token issuance and cookie writing are not implemented in this increment.

## Next implementation steps

1. Registration and password validation; prevent client assignment of staff/admin privileges.
2. Login, refresh rotation/revocation and logout; enforce CSRF even without a valid access cookie. Add shared throttling and database-backed session/revocation tests.
3. Verification and password reset: purpose-bound, expiring, single-use challenges, attempt limits, generic recovery responses and delivery status. Integrate a transactional email provider before claiming real delivery.
4. Current-user profile and password changes, then frontend forms against stable contracts.
5. Event models, organizer draft/submission APIs, admin moderation and public approved-event pages.

## Verification and limits

Twelve authentication tests cover CSRF bootstrap, missing cookie, all unsafe write methods, allowed/disallowed origin behavior, anonymous CSRF enforcement and malformed/expired/wrong-type tokens. User lookup is mocked in successful authentication tests; database-backed login is not claimed tested. Django system checks and OpenAPI validation pass. No migrations or changes to the shared Supabase data are needed for this increment.

The reported worker deployment still needs live acceptance. A task/result check failed and a subsequent Redis readiness check failed from this workstation. Obtain worker logs, confirm its environment and re-establish stable Redis access before calling background delivery operational.
