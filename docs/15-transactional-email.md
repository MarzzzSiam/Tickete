# Transactional email setup — 2026-10-18

The approved build brief requires a transactional provider, not personal Gmail/Outlook SMTP credentials. The optional Brevo HTTPS adapter is prepared for verification/reset messages. It remains disabled unless explicitly configured. Ticket PDF attachments will be added with Phase 2; the current adapter rejects unsupported attachments rather than silently dropping them.

## What the owner needs to do

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
