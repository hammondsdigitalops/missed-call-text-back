# 📞 Missed-Lead Responder — a Claude Skill

A missed call is a missed job. This turns any **missed lead** — a missed call, a
web-form fill, a text, or a voicemail — into an **instant text-back**, a **timed
follow-up sequence**, and a **lead card**, in about 15 seconds. Built as a
[Claude Skill](https://docs.claude.com), so you run it just by talking to Claude.

> **See it in action (no install):** simulate a missed call and watch the
> auto-text + follow-up sequence fire →
> **https://claude.ai/code/artifact/df646671-8212-41e2-8c64-dae4acd8ad64**

> **👉 New here? Start with [USAGE.md](./USAGE.md)** — use it in 30 seconds with no
> install, install the full skill, or build it yourself from scratch.

> **Review-first by design.** The skill drafts; you approve and send from your own
> phone/email. To make it *auto*-send the instant text the moment a call is missed,
> see [`autosend/`](./autosend/) — the Twilio wiring (Level 2).

## Why it matters
For local service businesses, **speed to lead** is the whole game — replying in the
first few minutes books far more jobs than replying an hour later. Most owners are
under a sink or on a ladder when the call comes in. This gives them a ready-to-send
reply the moment they can look at their phone, and it never lets a lead go cold.

## Who it's for
Trades that live and die by the phone: **plumbers, HVAC techs, electricians,
roofers, painters, landscapers, cleaners, detailers, handymen** — anyone who loses
money every time a call goes to voicemail.

## What it does
- ✅ **Instant text-back** — personal, 1–2 lines, sent immediately (after-hours aware)
- ✅ **Follow-up sequence** — intro email, Day-1 nudge, Day-3 value email, Day-7 break-up
- ✅ **Business-hours smart** — every follow-up lands during working hours, from a script
- ✅ **Lead card** — who, what they want, urgency, and a 5-minute respond-by deadline
- ✅ **Reads plain English** — a rambling voicemail becomes a structured lead
- ✅ **Skips what it can't send** — no email on file ⇒ no emails scheduled, automatically
- ✅ **Exports** clean files (`instant-reply.txt`, `lead-card.md`, `followups.md`)

## Quick start
```bash
# Print the full response plan for the sample lead:
python respond.py samples/sample-lead.json

# Or export ready-to-send files:
python respond.py samples/sample-lead.json --export output
```
Or just tell Claude: *"I missed a call — here's the voicemail…"* and paste it.

## Tailor it to any business
The business block, hours, cadence, and voice-by-trade live in
[`playbook.md`](./playbook.md). Set the owner's name, phone, booking link, and
business hours, pick the tone for their trade, and save one lead JSON as a template.
The next missed call is a 15-second edit.

## Roadmap
- **Level 1 (now):** missed lead → instant reply + follow-up sequence. Owner sends.
- **Level 2 (next):** wire it to the phone (Twilio, OpenPhone) or a form webhook so
  the instant text fires automatically the second a call is missed. This skill is
  the free brain that goes inside the "$300/month" version.

## License
MIT — use it, fork it, tailor it for your clients.

---
_Built with Claude. ⭐ the repo if it helped you save a job._
