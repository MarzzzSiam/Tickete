# Transactional email setup — 2026-10-18

**2026-10-21 acceptance update:** the owner reports Gmail SMTP delivery now works and emails arrive directly in the inbox. The disconnect notes below describe the earlier troubleshooting history. Continue with local synchronous processing for zero-cost development; no hosted worker is required for that mode. This verifies account email delivery by user report, not ticket-PDF delivery, which is still being implemented in Phase 2.

On 2026-10-20 the owner explicitly selected Django + Gmail SMTP using `hello.tickete@gmail.com`, superseding the original brief's transactional-provider restriction. Both SMTP and the optional Brevo adapter are supported. Neither is verified live until configured and tested. Ticket PDF generation/delivery belongs to Phase 2.

## Gmail setup — current choice

**2026-10-20 budget update:** do not create a paid Render worker. For local development, add `LOCAL_ACCOUNT_EMAIL_SYNC=True` to `backend/.env` and restart Django. Verification/reset requests then execute on the PC, without Celery queueing or background retries. SMTP failures still fail the request. Production settings never enable this shortcut. Redis remains required for existing authentication throttling.

If Gmail is unavailable, set `EMAIL_PROVIDER=console` locally to print verification/reset links in the backend terminal. These are private account tokens: open them locally, do not share screenshots of them. This enables development but does not send mail or prove inbox delivery. Gmail connections currently reach TLS successfully but disconnect during authentication; that is not a confirmed wrong-password response.

The Render instructions below are an optional future hosted setup, not a requirement for the current zero-cost local workflow.

1. Sign in to the Google account for `hello.tickete@gmail.com`. Enable **2-Step Verification**, then open [App passwords](https://myaccount.google.com/apppasswords) and create one named `TICKETÉ`. Use this app password, never the normal Google password. Google may restrict app passwords for some account/security configurations; see [Google's instructions](https://support.google.com/accounts/answer/185833).
2. Edit **`D:\TICKETÉ\backend\.env`** in VS Code. Replace existing entries with these values (avoid duplicate keys). Paste the app password in the password value, removing display spaces. Do not paste it into chat or GitHub.

```dotenv
EMAIL_PROVIDER=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=hello.tickete@gmail.com
EMAIL_HOST_PASSWORD=PASTE_GOOGLE_APP_PASSWORD_HERE
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=15
DEFAULT_FROM_EMAIL=TICKETÉ <hello.tickete@gmail.com>
SUPPORT_EMAIL=hello.tickete@gmail.com
```

3. Add the same variables separately under **Render → your background worker → Environment**. Deploy the branch containing this SMTP change, then save/redeploy the worker. Account email jobs run on the worker, so changing only the PC's `.env` is insufficient. Keep `FRONTEND_ORIGIN` accessible to the person opening the email (local testing on this PC uses `http://127.0.0.1:3000`).
4. Restart Django. From `D:\TICKETÉ\backend`, run:

```powershell
.\.venv\Scripts\python.exe manage.py test_email --to hello.tickete@gmail.com
```

This sends one plain test email directly from the PC. It verifies provider acceptance, not inbox receipt or Celery. Check inbox/spam, then request verification from the app's Account screen and check worker logs plus the inbox to verify the full background flow.

Gmail uses [authenticated STARTTLS on port 587](https://support.google.com/mail/answer/7104828). Render [blocks SMTP ports on free web services](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports); use the background worker for sending, and diagnose its actual network access if it times out. Gmail quotas can limit delivery; assess a transactional provider before public launch. SMTP failures produce sanitized errors and reuse the existing bounded Celery retries. An ambiguous network failure can produce duplicate messages; use the newest account link.

## Optional alternative: Brevo

1. Create a Brevo account using an existing Gmail or Outlook address. Complete any account/transactional-sending activation required by Brevo.
2. Add a sender named TICKETÉ and verify the sender email using the code Brevo sends. A free mailbox domain cannot be authenticated; Brevo may rewrite the sender to its own domain for testing. Before launch, obtain a TICKETÉ domain and install the authentication records Brevo gives you.
3. Generate an **API key**, not an SMTP key. Keep it private; never paste it into this chat, GitHub, or frontend variables.
4. Edit `backend/.env` locally and the Render **worker** environment:

```dotenv
EMAIL_PROVIDER=brevo
BREVO_API_KEY=replace_privately_with_your_api_key
DEFAULT_FROM_EMAIL=TICKETÉ <your_verified_sender_address>
SUPPORT_EMAIL=your_support_address
```

Set `FRONTEND_ORIGIN` on the worker to the frontend address the email recipient can actually open. `http://127.0.0.1:3000` works only for development users opening the link on the same PC. Hosted users need the deployed HTTPS frontend URL. Keep the web API CORS/CSRF origin aligned with its frontend.

5. Deploy the worker from the branch containing this implementation and restart local Django. Request verification from Account or a reset from Forgot password. Confirm the job ran, inspect the provider activity status, then open the received email link. Do not share the secret token URL in screenshots or logs.

The local console adapter is still available for development. Production/worker settings never fall back to console email. Missing configuration fails explicitly. HTTP failures are reported without provider response content, headers or credentials. Background account delivery retries up to three times with backoff; a provider timeout can produce duplicate emails, and a later retry invalidates an earlier challenge. Use the most recent valid email link. Durable provider event tracking and PDF delivery are future work.

## Sources checked

- [Brevo sender setup](https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email)
- [Brevo domain authentication](https://help.brevo.com/hc/en-us/articles/12163873383186-Authenticate-your-domain-with-Brevo-Brevo-code-DKIM-DMARC)
- [Brevo transactional API](https://developers.brevo.com/docs/send-a-transactional-email)
- [Render free service limits](https://render.com/docs/free): free web services block outbound SMTP ports 25, 465 and 587. HTTPS avoids that restriction.
