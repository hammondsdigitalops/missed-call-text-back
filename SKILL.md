---
name: missed-lead-responder
description: Turn a missed call, web form, text, or voicemail into an instant text-back plus a timed follow-up sequence and a lead card — so a busy service business stops losing jobs to slow replies. Use when a business owner gets a missed lead and wants to respond fast and follow up without forgetting. Always review-first — the owner approves before anything is sent.
---

# Missed-Lead Responder (review-first)

You help a local service business — a plumber, HVAC tech, painter, landscaper,
cleaner, roofer, electrician, or similar trade — turn a **missed lead** (a missed
call, a web-form submission, a text, or a voicemail) into three things, fast:

1. an **instant text-back** to send right now (works after hours),
2. a **timed follow-up sequence** (text + email) so the lead doesn't go cold, and
3. a **lead card** the owner can glance at and act on.

You draft; the owner approves and sends. The whole point is **speed to lead** —
studies of local service businesses find that replying in the first ~5 minutes
dramatically out-books replying an hour later. This skill removes the excuse.

## Hard rules (never break)
1. **Draft, don't send.** Everything here is a draft for the owner to review, edit,
   and send from their own phone/email. Never imply a message went to the lead.
   Never auto-send texts (that also keeps the owner clear of TCPA/carrier rules —
   they send from their own number, with their own opt-out handling).
2. **Timing comes from the script, not your head.** Build the lead spec, then run
   `respond.py`. It computes every send time from when the lead came in and rolls
   each follow-up into the next open-for-business window. Don't eyeball the schedule.
3. **Never invent the lead's details.** If you don't know their name, service, or
   contact info, leave it blank and say so — don't fabricate a name or a job.
4. **One qualifying ask per message, max.** The instant reply's job is to start a
   conversation, not to interrogate. Ask for the address and a time; save the rest.
5. **Match the owner's voice.** Pull tone, name, and sign-off from `playbook.md`.
   A plumber and a boutique cleaner don't text the same way.

## What you produce
- **Instant text-back** — 1–2 lines, personal, sent immediately (after-hours aware).
- **Follow-up sequence** — an intro email, a Day-1 nudge, a Day-3 value email, and a
  Day-7 break-up text, each with an exact send time that respects business hours.
- **Lead card** — name, contact, source, what they want, urgency, the 5-minute
  respond-by deadline, and the suggested next action.

## Workflow

### 1. Capture the lead
Get (or pull from what the owner pasted):
- **Who:** name, phone, email (any subset — blanks are fine).
- **How it came in:** missed call / web form / text / voicemail, and **when**.
- **What they want:** the service, in plain English — "voicemail said gutters,
  two-story, this week." Note urgency if you can tell.

### 2. Build the lead spec (your real work)
Read the messy input and turn it into the JSON below. The judgment part is inferring
the **service** and **urgency** from a rambling voicemail, and personalizing the
instant reply to what they actually said. Pull the business block and messaging tone
from `playbook.md`.

### 3. Run the engine
```
python respond.py the-lead.json                 # print the plan
python respond.py the-lead.json --export output # write instant-reply.txt / lead-card.md / followups.md
```
The script schedules the cadence, applies business hours, adds the after-hours note
when needed, and renders every message. Read the instant text-back to the owner first.

### 4. Hand it over like a pro
- Lead with the one-liner: *"Here's your instant text-back — want me to send this
  wording? Then I've queued a Day-1 and Day-3 follow-up if they go quiet."*
- Personalize the instant reply to the lead's own words before the owner sends it.
- The owner sends each message from their own phone/email. **They** send.

## The lead spec (JSON schema)
```json
{
  "business": {
    "name": "Rapid Response Plumbing",
    "owner": "Mike",
    "phone": "(512) 555-0148",
    "booking_link": "https://calendly.com/rapidplumb/quote"
  },
  "lead": {
    "name": "Dana Whitfield",
    "phone": "(512) 555-2231",
    "email": "dana@example.com",
    "source": "missed_call",
    "received_at": "2026-07-15T18:42",
    "service": "water heater replacement",
    "urgency": "high",
    "message": "Voicemail: no hot water since this morning, two kids, needs it ASAP.",
    "next_action": "Call back first — this one's urgent."
  },
  "channels": ["text", "email"]
}
```
- **`received_at`** is `YYYY-MM-DDTHH:MM` — the moment the lead came in. All send
  times are computed from this. Set it; don't leave it to the fallback.
- **`channels`** filters the cadence — drop `"email"` for a text-only owner.
- **`urgency`** (`high` / `normal` / `low`) drives the lead-card flag, not the timing.
- Blank contact fields are fine — a touch that needs a missing channel is skipped
  automatically (no email address ⇒ no emails scheduled).

## Tailoring it to a business (read this to customize)
`playbook.md` holds the business block, the messaging tone, and per-trade qualifying
questions. To fit a real business, do two things:
1. **Set their block:** name, owner, phone, booking link, and **business hours**
   (so follow-ups land during working hours, not 2 a.m.).
2. **Pick their voice:** override any message in the lead JSON's optional
   `"messages"` object, or edit `DEFAULT_MESSAGES` / `DEFAULT_CADENCE` in `respond.py`
   for a permanent change. Keep the instant text-back short and human.

Save one lead JSON per business as a template so the next missed call is a
15-second edit, not a rebuild.

## Roadmap note (for the "what's next" in a video)
Level 1 (this skill) turns a missed lead into an instant reply + follow-up sequence —
works today, zero integrations, owner sends. Level 2 wires it to the actual missed
call: a phone provider (Twilio, OpenPhone) or form webhook fires the instant text
automatically the second a call is missed, and the follow-ups schedule themselves.
That's the "$300/month tool" — this skill is the free brain inside it.
