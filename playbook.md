# Playbook — customize the responder to a real business

This file is the human-editable knobs. `respond.py` has sensible defaults baked in;
use this to fit a specific business and trade. Two things matter most: the
**business block** (so messages are signed right and land during business hours)
and the **voice** (so a plumber doesn't sound like a spa).

---

## 1. The business block

Copy this into the `"business"` field of the lead JSON and fill it in:

```json
"business": {
  "name": "Rapid Response Plumbing",
  "owner": "Mike",
  "phone": "(512) 555-0148",
  "booking_link": "https://calendly.com/rapidplumb/quote"
}
```

- **name / owner** — used in every message and the sign-off.
- **phone** — the number the lead should text back.
- **booking_link** — Calendly, Jobber, Housecall Pro, or a plain contact page. If
  they don't have one, drop the link and the templates still read fine.

## 2. Business hours (so follow-ups aren't sent at 2 a.m.)

Add a top-level `"business_hours"` object to the lead JSON to override the default
(Mon–Fri 8–6, Sat 9–2, Sun closed). Weekday index: Mon=0 … Sun=6.

```json
"business_hours": {
  "0": ["07:00", "19:00"],
  "1": ["07:00", "19:00"],
  "2": ["07:00", "19:00"],
  "3": ["07:00", "19:00"],
  "4": ["07:00", "17:00"],
  "5": ["08:00", "13:00"]
}
```

The **instant text-back ignores hours** on purpose — it fires immediately and adds a
short "it's after hours, I'll follow up first thing" note when the shop is closed.
Every other touch rolls forward to the next open window.

## 3. The cadence (default)

| # | Touch                | When (from the miss) | Channel |
|---|----------------------|----------------------|---------|
| 1 | Instant text-back    | immediately          | text    |
| 2 | Intro email          | +3 min               | email   |
| 3 | Day-1 nudge          | +1 day               | text    |
| 4 | Day-3 value email    | +3 days              | email   |
| 5 | Day-7 break-up       | +7 days              | text    |

To change it permanently, edit `DEFAULT_CADENCE` in `respond.py`. To change it for
one lead, add a `"cadence"` array to the JSON (same shape as the default).

## 4. Voice by trade (starter tone)

Override any message per lead via a `"messages"` object in the JSON, keyed by touch
`key` (`instant_text`, `intro_email`, `day1_text`, `day3_email`, `day7_text`).
Variables you can use: `{first_name} {business} {owner} {service} {phone}
{booking_link} {after_hours_note}`.

- **Plumbing / HVAC / electrical (urgent trades):** fast, reassuring, lead with
  availability. *"I can likely get someone out today."* Speed is the pitch.
- **Painting / remodeling (considered trades):** warm, consultative, no pressure.
  *"Happy to come take a look and give you a free, honest quote."*
- **Cleaning / detailing (recurring trades):** friendly, easy, hint at recurring.
  *"We can get you on the schedule — one-time or regular, whatever's easiest."*
- **Roofing / restoration (insurance-adjacent):** credible, calm. *"We handle the
  inspection and the paperwork — let's start with a free look at the damage."*

## 5. Qualifying questions (keep to ONE in the instant reply)

Pick the single most useful question for the trade; save the rest for the reply.
- Address + preferred time (universal — the default).
- Plumbing/HVAC: "Is it an emergency or can it wait for a scheduled visit?"
- Painting: "Interior or exterior, and roughly how many rooms/sides?"
- Cleaning: "One-time deep clean or recurring?"
- Roofing: "Do you know if you're filing an insurance claim?"

Don't stack these. One ask gets a reply; three asks get ignored.
