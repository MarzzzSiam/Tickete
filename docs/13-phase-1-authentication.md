# Phase 1 authentication — 2026-10-16

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
