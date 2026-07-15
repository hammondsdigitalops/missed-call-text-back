#!/usr/bin/env python3
"""
Missed-Lead Responder engine.

Turns a single missed lead (missed call, web form, text, or voicemail) into:
  1. an instant text-back to send right now (works 24/7, after-hours aware),
  2. a timed follow-up sequence (text + email) that respects business hours,
  3. a lead card the owner can glance at and act on.

The SCRIPT owns the deterministic part: computing exact send times from the
moment the lead came in, rolling each follow-up into the next open-for-business
window, and rendering every message consistently. Claude owns the judgment:
reading the plain-English lead and personalizing the wording.

Usage:
    python respond.py the-lead.json
    python respond.py the-lead.json --export output
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

# Windows consoles default to cp1252 and choke on emoji; force UTF-8 output.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# ---------------------------------------------------------------------------
# Defaults — overridable per lead in the JSON (see SKILL.md schema).
# ---------------------------------------------------------------------------

# Business hours: weekday index (Mon=0 .. Sun=6) -> ["HH:MM open", "HH:MM close"]
DEFAULT_HOURS = {
    "0": ["08:00", "18:00"],
    "1": ["08:00", "18:00"],
    "2": ["08:00", "18:00"],
    "3": ["08:00", "18:00"],
    "4": ["08:00", "18:00"],
    "5": ["09:00", "14:00"],
    # Sunday (6) omitted = closed
}

# The follow-up cadence. delay_min is measured from when the lead came in.
# respect_hours=False means "send immediately, even after hours" (the whole
# point of an instant text-back). channel is "text" or "email".
DEFAULT_CADENCE = [
    {
        "key": "instant_text",
        "label": "Instant text-back (send NOW)",
        "channel": "text",
        "delay_min": 0,
        "respect_hours": False,
        "needs": ["phone"],
    },
    {
        "key": "intro_email",
        "label": "Intro email",
        "channel": "email",
        "delay_min": 3,
        "respect_hours": True,
        "needs": ["email"],
    },
    {
        "key": "day1_text",
        "label": "Day 1 nudge (text)",
        "channel": "text",
        "delay_min": 1440,
        "respect_hours": True,
        "needs": ["phone"],
    },
    {
        "key": "day3_email",
        "label": "Day 3 value email",
        "channel": "email",
        "delay_min": 4320,
        "respect_hours": True,
        "needs": ["email"],
    },
    {
        "key": "day7_text",
        "label": "Day 7 break-up (text)",
        "channel": "text",
        "delay_min": 10080,
        "respect_hours": True,
        "needs": ["phone"],
    },
]

# Message templates. Variables: {first_name} {business} {owner} {service}
# {phone} {booking_link} {after_hours_note}
DEFAULT_MESSAGES = {
    "instant_text": (
        "Hi {first_name}, this is {owner} at {business} — sorry we missed you! "
        "I saw you reached out about {service}. I can help. "
        "What's the best address and when works for a quick look?{after_hours_note}"
    ),
    "intro_email": (
        "Subject: {business} — following up on your {service} request\n\n"
        "Hi {first_name},\n\n"
        "Thanks for reaching out to {business} about {service}. I'd love to help "
        "and get you a fast, no-pressure quote.\n\n"
        "Two quick questions so I can price it right:\n"
        "  1. What's the job address?\n"
        "  2. When would you like this done?\n\n"
        "You can reply here, text me at {phone}, or grab a time directly: "
        "{booking_link}\n\n"
        "Talk soon,\n{owner}\n{business}"
    ),
    "day1_text": (
        "Hi {first_name}, {owner} with {business} again — still want to get that "
        "{service} handled? Happy to hold a spot this week. Just reply with your "
        "address and I'll send a quote."
    ),
    "day3_email": (
        "Subject: Still here when you're ready, {first_name}\n\n"
        "Hi {first_name},\n\n"
        "Just checking back on your {service} request. Most folks we help are "
        "surprised how quick and affordable it is — and the quote is always free.\n\n"
        "If now's not the time, no worries at all. If it is, book here: "
        "{booking_link}\nor text me at {phone}.\n\n"
        "Best,\n{owner}\n{business}"
    ),
    "day7_text": (
        "Hi {first_name}, last note from {business} — I'll close out your {service} "
        "request for now so I'm not bugging you. If you still need it, just text "
        "back and I'll jump right on it. Thanks!"
    ),
}

AFTER_HOURS_NOTE = (
    " (It's after hours here, so I'll follow up first thing — but text me anytime.)"
)


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def parse_dt(s):
    """Parse 'YYYY-MM-DDTHH:MM' (or with seconds)."""
    s = s.strip().replace(" ", "T", 1) if " " in s and "T" not in s else s.strip()
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse received_at: {s!r} (use YYYY-MM-DDTHH:MM)")


def _hm(s):
    h, m = s.split(":")
    return int(h), int(m)


def is_open(dt, hours):
    day = hours.get(str(dt.weekday()))
    if not day:
        return False
    (oh, om), (ch, cm) = _hm(day[0]), _hm(day[1])
    open_t = dt.replace(hour=oh, minute=om, second=0, microsecond=0)
    close_t = dt.replace(hour=ch, minute=cm, second=0, microsecond=0)
    return open_t <= dt <= close_t


def next_open(dt, hours):
    """Roll dt forward to the next moment the business is open."""
    guard = 0
    cur = dt
    while guard < 14:  # at most two weeks out
        day = hours.get(str(cur.weekday()))
        if day:
            (oh, om), (ch, cm) = _hm(day[0]), _hm(day[1])
            open_t = cur.replace(hour=oh, minute=om, second=0, microsecond=0)
            close_t = cur.replace(hour=ch, minute=cm, second=0, microsecond=0)
            if cur < open_t:
                return open_t
            if open_t <= cur <= close_t:
                return cur
        # closed today or past close -> jump to start of next day
        cur = (cur + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        guard += 1
    return dt  # fallback


def fmt(dt):
    stamp = dt.strftime("%a %b %d, %I:%M %p")
    return stamp.replace(" 0", " ", 1)  # trim leading zero on day-of-month


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def first_name(name):
    name = (name or "").strip()
    return name.split()[0] if name else "there"


def build_context(biz, lead):
    return {
        "first_name": first_name(lead.get("name")),
        "business": biz.get("name", "our team"),
        "owner": biz.get("owner", "the team"),
        "service": lead.get("service", "your project"),
        "phone": biz.get("phone", ""),
        "booking_link": biz.get("booking_link", "(add your booking link)"),
        "after_hours_note": "",
    }


def render(template, ctx):
    out = template
    for k, v in ctx.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def has_needs(touch, lead):
    for field in touch.get("needs", []):
        if not str(lead.get(field, "")).strip():
            return False
    return True


def build_plan(data):
    biz = data.get("business", {})
    lead = data.get("lead", {})
    channels = set(data.get("channels", ["text", "email"]))
    hours = data.get("business_hours", DEFAULT_HOURS)
    cadence = data.get("cadence", DEFAULT_CADENCE)
    messages = {**DEFAULT_MESSAGES, **data.get("messages", {})}

    received = parse_dt(lead.get("received_at") or _fallback_now())
    ctx = build_context(biz, lead)

    steps = []
    for touch in cadence:
        if touch["channel"] not in channels:
            continue
        if not has_needs(touch, lead):
            continue

        target = received + timedelta(minutes=touch["delay_min"])
        if touch.get("respect_hours", True):
            send_at = next_open(target, hours)
        else:
            send_at = target

        local_ctx = dict(ctx)
        if not touch.get("respect_hours", True) and not is_open(send_at, hours):
            local_ctx["after_hours_note"] = AFTER_HOURS_NOTE

        body = render(messages.get(touch["key"], ""), local_ctx)
        steps.append({
            "label": touch["label"],
            "channel": touch["channel"],
            "send_at": send_at,
            "body": body,
        })

    steps.sort(key=lambda s: s["send_at"])
    return biz, lead, received, steps


def _fallback_now():
    # Only used if received_at is missing; encourages the caller to set it.
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def lead_card(biz, lead, received):
    deadline = received + timedelta(minutes=5)
    urgency = (lead.get("urgency") or "normal").lower()
    flag = {"high": "🔴 HIGH", "normal": "🟡 normal", "low": "🟢 low"}.get(urgency, urgency)
    lines = [
        "# Lead card",
        "",
        f"- **Name:** {lead.get('name') or '(unknown)'}",
        f"- **Phone:** {lead.get('phone') or '—'}",
        f"- **Email:** {lead.get('email') or '—'}",
        f"- **Source:** {lead.get('source') or '—'}",
        f"- **Wants:** {lead.get('service') or '(unclear — ask)'}",
        f"- **Came in:** {fmt(received)}",
        f"- **Urgency:** {flag}",
        f"- **Respond by:** {fmt(deadline)}  ← speed-to-lead beats everything",
    ]
    if lead.get("message"):
        lines += ["", f"> {lead['message'].strip()}"]
    nxt = lead.get("next_action") or "Send the instant text-back, then let the sequence run."
    lines += ["", f"**Next action:** {nxt}"]
    return "\n".join(lines)


def render_report(biz, lead, received, steps):
    out = []
    out.append("=" * 64)
    out.append(f"  MISSED-LEAD RESPONSE PLAN — {biz.get('name', '')}".rstrip())
    out.append("=" * 64)
    out.append("")
    out.append(lead_card(biz, lead, received))
    out.append("")
    out.append("-" * 64)
    out.append("  MESSAGE SEQUENCE (drafts — you approve & send each one)")
    out.append("-" * 64)
    for i, s in enumerate(steps, 1):
        chan = s["channel"].upper()
        out.append("")
        out.append(f"[{i}] {s['label']}")
        out.append(f"    when: {fmt(s['send_at'])}   ·   via: {chan}")
        out.append("    " + "-" * 56)
        for line in s["body"].splitlines():
            out.append("    " + line)
    out.append("")
    out.append("-" * 64)
    out.append("  Nothing here has been sent. Review, tweak, and send from your")
    out.append("  own phone/email. Reply STOP handling is on you per your carrier.")
    out.append("-" * 64)
    return "\n".join(out)


def export(biz, lead, received, steps, folder):
    import os
    os.makedirs(folder, exist_ok=True)

    # Instant text-back on its own, for a fast copy-paste.
    instant = next((s for s in steps if s["channel"] == "text"), None)
    if instant:
        with open(os.path.join(folder, "instant-reply.txt"), "w", encoding="utf-8") as f:
            f.write(instant["body"] + "\n")

    with open(os.path.join(folder, "lead-card.md"), "w", encoding="utf-8") as f:
        f.write(lead_card(biz, lead, received) + "\n")

    with open(os.path.join(folder, "followups.md"), "w", encoding="utf-8") as f:
        f.write(f"# Follow-up sequence — {lead.get('name') or 'lead'}\n\n")
        for i, s in enumerate(steps, 1):
            f.write(f"## [{i}] {s['label']}\n")
            f.write(f"*{fmt(s['send_at'])} · via {s['channel']}*\n\n")
            f.write(s["body"] + "\n\n")

    return folder


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Missed-lead responder")
    ap.add_argument("lead_file", help="Path to the lead JSON")
    ap.add_argument("--export", metavar="DIR", help="Write files to DIR")
    args = ap.parse_args()

    try:
        with open(args.lead_file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"File not found: {args.lead_file}")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in {args.lead_file}: {e}")

    biz, lead, received, steps = build_plan(data)

    if not steps:
        sys.exit("No messages to send — check that the lead has a phone/email and "
                 "that 'channels' includes text and/or email.")

    print(render_report(biz, lead, received, steps))

    if args.export:
        folder = export(biz, lead, received, steps, args.export)
        print(f"\nExported to: {folder}/  (instant-reply.txt, lead-card.md, followups.md)")


if __name__ == "__main__":
    main()
