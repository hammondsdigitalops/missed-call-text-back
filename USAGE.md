# How to use Missed-Call Text-Back

Three ways in, from "zero setup" to "build it yourself." Pick your lane.

---

## ① Use it right now — no install (paste into Claude)

Don't want to install anything? Open [claude.ai](https://claude.ai) (or Claude Code),
paste the prompt below, fill in the bracketed bits, and hit send. Claude becomes your
missed-lead responder on the spot.

```text
You are my Missed-Lead Responder. When I describe a missed call, web form, text,
or voicemail, turn it into three things I can send:

1. An INSTANT text-back (1–2 lines) to send right now. If it's after my business
   hours, add a short "it's after hours, I'll follow up first thing" note.
2. A FOLLOW-UP sequence — a Day-1 text, a Day-3 email, and a Day-7 "break-up" text —
   each with the exact date and time to send it (keep follow-ups inside business hours).
3. A LEAD CARD: caller, source, what they want, urgency, when it came in, and the
   single best next action.

Rules:
- You only DRAFT. I approve and send from my own phone/email. Never say anything was
  sent. Keep the instant text to ONE question (their address + best time).
- Never invent the caller's name or details. If you don't know it, leave it blank.
- Match my voice and sign every message as me.

MY BUSINESS
- Business name: [FILL IN]
- My name: [FILL IN]
- Phone / booking link: [FILL IN]
- Business hours: [e.g. Mon–Fri 8–6, Sat 9–2]

THE MISSED LEAD
- How it came in: [missed call / web form / voicemail] at [time]
- Their number or email: [FILL IN]
- What they said or want: [paste the voicemail or a quick note]

Give me the instant text first, then the follow-up sequence, then the lead card.
```

---

## ② Install the real skill (Claude Code)

This makes it permanent — just say *"I missed a call…"* any time and the skill runs,
math and scheduling handled by the included script.

```bash
# Clone it into your Claude Code skills folder:
git clone https://github.com/hammondsdigitalops/missed-call-text-back.git \
  ~/.claude/skills/missed-call-text-back
```

Then restart Claude Code and just talk to it:

> *"I missed a call — voicemail: no hot water since this morning, two kids, needs it ASAP. Number is (512) 555-2231."*

**Make it yours (once):** open `playbook.md` and set your business name, hours, phone,
booking link, and the tone for your trade. Save one lead file as a template and the
next missed call is a 15-second edit. You can also run the engine directly:

```bash
python respond.py samples/sample-lead.json                 # print the plan
python respond.py samples/sample-lead.json --export output # write ready-to-send files
```

---

## ③ Build it yourself from scratch (for creators)

Want to build it live, like the video? Paste this into Claude Code and it will
generate the whole skill:

```text
Build me a Claude Skill called "missed-lead-responder" that helps a local service
business (plumber, HVAC, electrician, roofer, painter, landscaper, cleaner) never
lose a job to a slow reply. When they miss a call, web form, text, or voicemail, it
turns that lead into three things:

  1. an INSTANT text-back to send right now (works after hours),
  2. a timed FOLLOW-UP sequence (intro email, Day-1 text, Day-3 email, Day-7 break-up),
  3. a LEAD CARD: name, contact, source, what they want, urgency, and a 5-minute
     "respond by" deadline.

Hard rules:
  - REVIEW-FIRST: it only drafts. The owner approves and sends from their own phone/
    email. It never auto-sends and never claims a message went out.
  - Never invent the lead's name, service, or contact info — leave blanks.
  - Keep the instant text to 1-2 lines with ONE qualifying question (address + time),
    matched to the business's voice.

Build it like a real skill:
  - SKILL.md with YAML frontmatter (name + a "use it when…" description), the hard
    rules, the workflow, and a JSON "lead spec" schema.
  - respond.py — a dependency-free Python engine that owns the DETERMINISTIC part:
    read the lead JSON, compute every send time from when the lead came in, and roll
    each follow-up forward into the next business-hours window. The instant text
    ignores hours and adds an after-hours note when the shop is closed. Skip any touch
    whose channel is missing (no email = no emails). It prints the plan and, with
    --export DIR, writes instant-reply.txt, lead-card.md, and followups.md. Force
    stdout to UTF-8 so emoji print on Windows.
  - playbook.md — business block, business hours (weekday index Mon=0..Sun=6), the
    cadence, and voice-by-trade tone guidance.
  - samples/sample-lead.json, README.md, an MIT LICENSE, and a .gitignore.

Then run respond.py on the sample and show me the output.
```

---

### Want it to *auto*-send (Level 2)
The `autosend/` folder has the Twilio wiring so the instant text fires the moment a
call is missed — no tap. Heads-up: sending business texts in the U.S. requires a quick
**A2P 10DLC registration** on your own number (a few days to approve). See
[`autosend/README.md`](./autosend/README.md).
