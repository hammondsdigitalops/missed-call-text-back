# autosend/ — the Level 2 auto-sender (Twilio)

The skill in the parent folder *drafts* the messages. This little app makes the
**instant text fire by itself** the moment a call goes unanswered — the actual
"missed-call text-back" product that services sell for $200–300/month.

> **Honest heads-up:** this is the reference build. It's written correctly but
> assumes you plug in your own Twilio account and a registered number. Sending
> business texts in the U.S. requires **A2P 10DLC registration** (a few days to
> approve). Until that's done, Twilio trial accounts can only text *verified*
> numbers. That's expected — not a bug.

## What it does
1. A lead calls your Twilio number → it rings your real cell.
2. You don't pick up → the app **texts the caller back instantly** from your number.
3. It **auto-schedules** the Day-1 / Day-3 / Day-7 follow-ups (business hours only).
4. If the lead texts back, remaining follow-ups cancel and you get a heads-up.

## Setup (about 15 minutes)

**1. Get a Twilio number**
- Make a free account at [twilio.com](https://www.twilio.com/try-twilio).
- Buy a phone number with **Voice + SMS** (Console → Phone Numbers → Buy a number).

**2. Install and configure**
```bash
cd autosend
pip install -r requirements.txt
cp .env.example .env          # then open .env and fill in your values
```

**3. Run it**
```bash
python app.py                 # starts on http://localhost:5000
```

**4. Expose it so Twilio can reach it** (for testing, use ngrok)
```bash
ngrok http 5000               # gives you a public https URL
```

**5. Point your number at the app**
- In the Twilio Console, open your number's settings.
- **A call comes in** → Webhook → `https://YOUR-NGROK-URL/voice` (HTTP POST)
- **A message comes in** (optional) → `https://YOUR-NGROK-URL/sms` (HTTP POST)

**6. Test it**
- Call your Twilio number from another phone and let it ring out.
- Your cell rings first; ignore it. Seconds later the calling phone gets the text.

## Going live (beyond the demo)
- **Register A2P 10DLC** in the Twilio Console so carriers stop filtering your texts.
- **Host it 24/7** instead of ngrok — Twilio Functions, Render, Railway, Fly.io, or
  a small always-on box. Set the webhook to the real URL.
- `SEND_FOLLOWUPS`, `RING_SECONDS`, business hours, and message wording are all in
  `app.py` / `.env`.

## Files
- `app.py` — the Flask app (voice webhook, missed-call detection, SMS, scheduler).
- `requirements.txt` — Python dependencies.
- `.env.example` — copy to `.env` and fill in.
