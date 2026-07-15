#!/usr/bin/env python3
"""
Missed-Lead Auto-Responder — the Level 2 trigger around the skill's brain.

Flow:
  1. A lead calls your Twilio number.
  2. Twilio rings your real cell (call forwarding).
  3. If you DON'T answer (no-answer / busy / failed), this app INSTANTLY
     texts the caller back from your Twilio number — no tap required.
  4. It then auto-schedules the follow-up sequence (Day 1 / Day 3 / Day 7),
     sending each during business hours.

This is the actual "missed-call text-back" tool that services sell for
$200-300/month. The message wording mirrors the missed-lead-responder skill.

Run it, expose it with ngrok, point your Twilio number's Voice webhook at
/voice, and it works. See autosend/README.md for click-by-click setup.
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

load_dotenv()

# --- Config (from .env) ----------------------------------------------------
ACCOUNT_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN    = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER", "")          # your Twilio # (E.164, e.g. +15125550148)
OWNER_CELL    = os.environ.get("OWNER_CELL", "")            # your real phone to ring first
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "our team")
OWNER_NAME    = os.environ.get("OWNER_NAME", "the team")
BOOKING_LINK  = os.environ.get("BOOKING_LINK", "")
RING_SECONDS  = int(os.environ.get("RING_SECONDS", "18"))    # how long to ring your cell before it's "missed"
SEND_FOLLOWUPS = os.environ.get("SEND_FOLLOWUPS", "true").lower() == "true"

# Business hours: "Mon-Fri 08:00-18:00, Sat 09:00-14:00" style, index Mon=0..Sun=6
BUSINESS_HOURS = {
    0: ("08:00", "18:00"), 1: ("08:00", "18:00"), 2: ("08:00", "18:00"),
    3: ("08:00", "18:00"), 4: ("08:00", "18:00"), 5: ("09:00", "14:00"),
}

client = Client(ACCOUNT_SID, AUTH_TOKEN) if ACCOUNT_SID and AUTH_TOKEN else None

app = Flask(__name__)

scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url="sqlite:///followups.sqlite")}
)
scheduler.start()


# --- Message templates (mirror the missed-lead-responder skill) ------------
def _ctx(first_name):
    return {
        "first_name": first_name or "there",
        "business": BUSINESS_NAME,
        "owner": OWNER_NAME,
        "booking_link": BOOKING_LINK or "just reply here",
        "phone": TWILIO_NUMBER,
    }


def instant_text(first_name, after_hours):
    note = (" (It's after hours, so I'll follow up first thing — but text me "
            "anytime.)") if after_hours else ""
    c = _ctx(first_name)
    return (f"Hi {c['first_name']}, this is {c['owner']} at {c['business']} — "
            f"sorry we missed your call! I can help. What's the best address and "
            f"when works for a quick look?{note}")


def followup_text(first_name, day):
    c = _ctx(first_name)
    if day == 1:
        return (f"Hi {c['first_name']}, {c['owner']} with {c['business']} again — "
                f"still want to get that handled? Happy to hold a spot this week. "
                f"Just reply with your address and I'll send a quote.")
    if day == 3:
        return (f"Hi {c['first_name']}, checking back in. The quote is always free "
                f"and we can usually get out fast. Want me to take a look? "
                f"{('Book: ' + BOOKING_LINK) if BOOKING_LINK else 'Just reply here.'}")
    return (f"Hi {c['first_name']}, last note from {c['business']} — I'll close out "
            f"your request so I'm not bugging you. Still need it? Just text back and "
            f"I'll jump right on it. Thanks!")


# --- Business-hours helper (mirrors respond.py) ----------------------------
def _hm(s):
    h, m = s.split(":")
    return int(h), int(m)


def is_open(dt):
    day = BUSINESS_HOURS.get(dt.weekday())
    if not day:
        return False
    (oh, om), (ch, cm) = _hm(day[0]), _hm(day[1])
    return dt.replace(hour=oh, minute=om) <= dt <= dt.replace(hour=ch, minute=cm)


def next_open(dt):
    cur = dt
    for _ in range(14):
        day = BUSINESS_HOURS.get(cur.weekday())
        if day:
            (oh, om), (ch, cm) = _hm(day[0]), _hm(day[1])
            open_t = cur.replace(hour=oh, minute=om, second=0, microsecond=0)
            close_t = cur.replace(hour=ch, minute=cm, second=0, microsecond=0)
            if cur < open_t:
                return open_t
            if open_t <= cur <= close_t:
                return cur
        cur = (cur + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return dt


# --- Sending ---------------------------------------------------------------
def send_sms(to_number, body):
    if not client:
        app.logger.error("Twilio not configured — SMS not sent. Set your .env.")
        return
    client.messages.create(to=to_number, from_=TWILIO_NUMBER, body=body)
    app.logger.info("Sent SMS to %s: %s", to_number, body[:60])


def send_followup(to_number, first_name, day):
    send_sms(to_number, followup_text(first_name, day))


def schedule_followups(to_number, first_name):
    if not SEND_FOLLOWUPS:
        return
    now = datetime.now()
    plan = {1: now + timedelta(days=1), 3: now + timedelta(days=3), 7: now + timedelta(days=7)}
    for day, when in plan.items():
        run_at = next_open(when)
        scheduler.add_job(
            send_followup, "date", run_date=run_at,
            args=[to_number, first_name, day],
            id=f"fu-{to_number}-{day}-{run_at.isoformat()}",
            replace_existing=True,
        )
        app.logger.info("Scheduled Day-%s follow-up to %s at %s", day, to_number, run_at)


# --- Routes ----------------------------------------------------------------
@app.route("/voice", methods=["POST"])
def voice():
    """Twilio hits this on an incoming call. Ring the owner's cell first."""
    resp = VoiceResponse()
    dial = Dial(timeout=RING_SECONDS, action="/dial-status", method="POST",
                caller_id=request.form.get("To", TWILIO_NUMBER))
    dial.number(OWNER_CELL)
    resp.append(dial)
    return Response(str(resp), mimetype="text/xml")


@app.route("/dial-status", methods=["POST"])
def dial_status():
    """After the ring, decide if it was missed → auto-text the caller."""
    status = request.form.get("DialCallStatus", "")
    caller = request.form.get("From", "")   # the lead's number
    app.logger.info("Dial status=%s from=%s", status, caller)

    if status in ("no-answer", "busy", "failed") and caller:
        first = ""  # we only have their number on a cold call
        send_sms(caller, instant_text(first, after_hours=not is_open(datetime.now())))
        schedule_followups(caller, first)

    # Empty TwiML — call flow is done.
    return Response(str(VoiceResponse()), mimetype="text/xml")


@app.route("/sms", methods=["POST"])
def sms_in():
    """Optional: when a lead replies, ping the owner so a human takes over.
    (Cancels remaining automated follow-ups for that number.)"""
    frm = request.form.get("From", "")
    body = request.form.get("Body", "")
    if OWNER_CELL and frm:
        send_sms(OWNER_CELL, f"↩️ Lead {frm} replied: \"{body[:120]}\" — take it from here.")
    for job in scheduler.get_jobs():
        if job.id.startswith(f"fu-{frm}-"):
            job.remove()
    return Response(str(VoiceResponse()), mimetype="text/xml")


@app.route("/health")
def health():
    ok = bool(client and TWILIO_NUMBER and OWNER_CELL)
    return {"ok": ok, "business": BUSINESS_NAME, "followups": SEND_FOLLOWUPS}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"Missed-Lead Auto-Responder for {BUSINESS_NAME} on :{port}")
    if not client:
        print("⚠  Twilio keys missing — copy .env.example to .env and fill it in.")
    app.run(host="0.0.0.0", port=port)
