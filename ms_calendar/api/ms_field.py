import frappe, requests
from datetime import timedelta
from frappe.utils import get_datetime

# ── Feedback URL lookup: (role lowercase, round lowercase) → URL ─────────────
_FEEDBACK_URL_MAP = {
    # URLs include {app_id} and {applicant_name} — filled at runtime
    # School Teacher
    ("school teacher", "recruiter round"): "https://careers.frappe.cloud/recruiter-assessment-form-feed-back-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("school teacher", "round one"):       "https://careers.frappe.cloud/school-teacher-functional-feedback/new?app_id={app_id}&applicant_name={applicant_name}",
    ("school teacher", "round two"):       "https://careers.frappe.cloud/demo-lesson-observation-feedback-form-feed-back-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("school teacher", "round three"):     "https://careers.frappe.cloud/leader-final-feedback/new?app_id={app_id}&applicant_name={applicant_name}",

    # Resource Person
    ("resource person", "recruiter round"): "https://careers.frappe.cloud/recruiter-assessment-form-feed-back-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("resource person", "round one"):       "https://careers.frappe.cloud/educational-capacity-interview---feedback-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("resource person", "round two"):       "https://careers.frappe.cloud/leader-final-feedback/new?app_id={app_id}&applicant_name={applicant_name}",

    # Livelihood Resource Person
    ("livelihood resource person", "recruiter round"): "https://careers.frappe.cloud/livelihoods-recruiter-feedback-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("livelihood resource person", "round one"):       "https://careers.frappe.cloud/livelihoods-functional-round-feedback-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("livelihood resource person", "round two"):       "https://careers.frappe.cloud/livelihoods-final-round-feedback-form/new?app_id={app_id}&applicant_name={applicant_name}",

    # Health Resource Person
    ("health resource person", "recruiter round"): "https://careers.frappe.cloud/health-recruitment-feedback-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("health resource person", "round one"):       "https://careers.frappe.cloud/health-functional-round-feedback-form/new?app_id={app_id}&applicant_name={applicant_name}",
    ("health resource person", "round two"):       "https://careers.frappe.cloud/health-final-round-feedback-form/new?app_id={app_id}&applicant_name={applicant_name}",
}

@frappe.whitelist()
def get_schedule_free_slots(interviewer_emails, interview_date):
    """
    Fetches busy intervals for multiple interviewers using MS Graph getSchedule endpoint.
    interviewer_emails can be a Python list or JSON string like '["a@x.com","b@x.com"]'.
    """
    if isinstance(interviewer_emails, str):
        try:
            import json
            interviewer_emails = json.loads(interviewer_emails)
        except Exception:
            interviewer_emails = [interviewer_emails]

    if not isinstance(interviewer_emails, list) or not interviewer_emails:
        frappe.throw("interviewer_emails must be a non-empty list of email IDs")

    try:
        credentials = frappe.get_single("MS Graph Credentials")
        tenant_id = credentials.tenant_id
        client_id = credentials.client_id
        try:
            client_secret = credentials.get_password("client_secret")
        except frappe.ValidationError:
            frappe.throw(
                "Could not decrypt MS Graph client_secret. "
                "⚠️ Please check that your site_config.json contains the correct encryption_key. "
                "If you recently migrated/restored this site and do not have the old encryption key, "
                "you must re-enter the client_secret in the MS Graph Credentials doctype."
            )
    except Exception as e:
        frappe.throw(f"Could not fetch MS Graph Credentials: {e}")

    start_date = get_datetime(interview_date)
    end_date = start_date + timedelta(days=1)

    # Get access token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }

    try:
        token_resp = requests.post(token_url, data=token_data)
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            frappe.throw(f"Failed to fetch access token: {token_resp.json()}")
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Token request failed: {e}")

    # Use the first interviewer as the context user for getSchedule
    context_user = interviewer_emails[0]
    url = f"https://graph.microsoft.com/v1.0/users/{context_user}/calendar/getSchedule"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "schedules": interviewer_emails,
        "startTime": {
            "dateTime": start_date.isoformat(),
            "timeZone": "UTC"
        },
        "endTime": {
            "dateTime": end_date.isoformat(),
            "timeZone": "UTC"
        },
        "availabilityViewInterval": 30
    }

    try:
        resp = requests.post(url, headers=headers, json=body)
        resp.raise_for_status()
        schedules = resp.json().get("value", [])
        result = {
            s["scheduleId"]: s.get("scheduleItems", [])
            for s in schedules
        }
        return result
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Graph API error: {resp.status_code} - {resp.text}")

import frappe, requests, uuid

@frappe.whitelist()
def create_calendar_event(event_title, start_datetime, end_datetime, interviewer_email, interviewee_email):
    """
    Schedules a new calendar event using Microsoft Graph (HR as organizer),
    and sends different custom emails to interviewer and candidate.
    """
    # --- 1. Get credentials ---
    try:
        credentials = frappe.get_single("MS Graph Credentials")
        tenant_id = credentials.tenant_id.strip()
        client_id = credentials.client_id.strip()
        client_secret = credentials.get_password("client_secret")
    except Exception as e:
        frappe.throw(f"Could not fetch MS Graph Credentials: {e}")
    
    # --- 2. Get access token ---
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }
    
    try:
        token_resp = requests.post(token_url, data=token_data).json()
        access_token = token_resp.get("access_token")
        if not access_token:
            frappe.throw(f"Failed to fetch access token: {token_resp}")
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Token request failed: {e}")

    # --- 3. Organizer email (HR official mailbox) ---
    organizer_email = "health.fellowship@azimpremjifoundation.org"   # 👈 replace with your official organizer email
    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events?sendUpdates=none"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # --- 4. Event body (seen only by HR) ---
    event_body = {
        "subject": event_title,
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        "location": {"displayName": "Microsoft Teams Meeting"},
        "attendees": [
            {"emailAddress": {"address": interviewer_email, "name": "Interviewer"}, "type": "required"},
            {"emailAddress": {"address": interviewee_email, "name": "Candidate"}, "type": "required"}
        ],
        "responseRequested": True,
        "allowNewTimeProposals": True,
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness",
        "transactionId": str(uuid.uuid4()),
        "body": {
            "contentType": "HTML",
            "content": f"""
                <p>Dear HR,</p>
                <p>This interview has been scheduled via the system.</p>
                <p><b>Title:</b> {event_title}<br>
                <b>Start:</b> {start_datetime}<br>
                <b>End:</b> {end_datetime}<br>
                <b>Location:</b> Microsoft Teams Meeting</p>
            """
        }
    }

    # --- 5. Create event ---
    try:
        resp = requests.post(url, headers=headers, json=event_body)
        resp.raise_for_status()
        event = resp.json()
        join_url = event.get("onlineMeeting", {}).get("joinUrl")

        # --- 6. Send custom email to Interviewer ---
        frappe.sendmail(
            recipients=[interviewer_email],
            subject=f"Interview Scheduled (Interviewer) - {event_title}",
            message=f"""
                <p>Dear Interviewer,</p>
                <p>You are scheduled to conduct an interview.</p>
                <p><b>Title:</b> {event_title}<br>
                   <b>Start:</b> {start_datetime}<br>
                   <b>End:</b> {end_datetime}<br>
                   <b>Join Link:</b> <a href="{join_url}">Join Teams Meeting</a></p>
                <p>Please be on time and review the candidate details before the meeting.</p>
                <p>Best regards,<br>HR Team</p>
            """
        )

        # --- 7. Send custom email to Candidate ---
        frappe.sendmail(
            recipients=[interviewee_email],
            subject=f"Interview Invitation - {event_title}",
            message=f"""
                <p>Dear Candidate,</p>
                <p>Your interview has been scheduled.</p>
                <p><b>Title:</b> {event_title}<br>
                   <b>Start:</b> {start_datetime}<br>
                   <b>End:</b> {end_datetime}<br>
                   <b>Join Link:</b> <a href="{join_url}">Join Teams Meeting</a></p>
                <p>Please ensure you are in a quiet place with stable internet connectivity.</p>
                <p>Best regards,<br>HR Team</p>
            """
        )

        frappe.msgprint("Interview scheduled. HR notified, and custom invites sent to interviewer and candidate.")

        return {"event_id": event.get("id"), "join_url": join_url}
    
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Graph API error: {resp.status_code} - {resp.text}")


@frappe.whitelist()
def get_org_rooms_and_availability(interview_date, start_time, end_time):
    import frappe
    import requests
    import time
    from frappe.utils import get_datetime
    from datetime import datetime, timezone, timedelta

    print("\n===================== DEBUG START =====================")

    creds = frappe.get_single("MS Graph Credentials")
    tenant = creds.tenant_id
    client = creds.client_id
    secret = creds.get_password("client_secret")

    # -------------------------
    # ACCESS TOKEN
    # -------------------------
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client,
        "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default"
    }
    try:
        token_resp = requests.post(token_url, data=token_data, timeout=30)
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            frappe.throw(f"Failed to fetch MS access token: {token_resp.json()}")
    except requests.exceptions.ConnectionError:
        frappe.throw("Cannot reach Microsoft login servers. Check network connectivity and try again.")
    except requests.exceptions.Timeout:
        frappe.throw("Microsoft login server timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Token request failed: {e}")
    headers = {"Authorization": f"Bearer {access_token}"}

    print("DEBUG → Token OK")

    
    # GET ALL ROOMS (PAGINATED)
    # -------------------------
    rooms = []
    url = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"
    page = 1

    while url:
        print(f"DEBUG → Fetching rooms PAGE {page}")
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        page_rooms = data.get("value", [])
        print(f"DEBUG → PAGE {page} has {len(page_rooms)} rooms")
        rooms.extend(page_rooms)

        url = data.get("@odata.nextLink")
        page += 1

    print("DEBUG → TOTAL ROOMS FETCHED =", len(rooms))

    # Extract emails
    room_emails = [r.get("emailAddress") for r in rooms if r.get("emailAddress")]

    # -------------------------
    # TIME RANGE (UTC)
    # -------------------------
    offset = -time.timezone if time.localtime().tm_isdst == 0 else -time.altzone
    system_tz = timezone(timedelta(seconds=offset))

    start_local = get_datetime(f"{interview_date} {start_time}")
    end_local = get_datetime(f"{interview_date} {end_time}")

    start_utc = start_local.replace(tzinfo=system_tz).astimezone(timezone.utc)
    end_utc = end_local.replace(tzinfo=system_tz).astimezone(timezone.utc)

    # -------------------------
    # GET AVAILABILITY IN BATCHES
    # -------------------------
    MAX_BATCH = 20
    schedule_url = (
        "https://graph.microsoft.com/v1.0/"
        "users/health.fellowship@azimpremjifoundation.org/calendar/getSchedule"
    )

    schedule_map = {}
    total_batches = (len(room_emails) + MAX_BATCH - 1) // MAX_BATCH

    for i in range(0, len(room_emails), MAX_BATCH):
        batch = room_emails[i:i + MAX_BATCH]
        body = {
            "schedules": batch,
            "startTime": {"dateTime": start_utc.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "UTC"},
            "endTime":   {"dateTime": end_utc.strftime("%Y-%m-%dT%H:%M:%S"),   "timeZone": "UTC"},
            "availabilityViewInterval": 30
        }

        resp = requests.post(
            schedule_url,
            headers={**headers, "Content-Type": "application/json"},
            json=body
        )
        resp.raise_for_status()

        for item in resp.json().get("value", []):
            schedule_map[item["scheduleId"].lower()] = item.get("scheduleItems", [])

        time.sleep(0.1)

    # -------------------------
    # FINAL OUTPUT
    # -------------------------
    final = []

    for r in rooms:
        email = r.get("emailAddress")
        busy = schedule_map.get(email.lower(), [])

        available = True
        for slot in busy:
            s = datetime.fromisoformat(slot["start"]["dateTime"]).replace(tzinfo=timezone.utc)
            e = datetime.fromisoformat(slot["end"]["dateTime"]).replace(tzinfo=timezone.utc)

            if not (e <= start_utc or s >= end_utc):
                available = False
                break

        final.append({
            "name": r.get("displayName"),
            "email": email,
            "capacity": r.get("capacity"),
            "availability": busy,
            "is_available": available
        })

    print("===================== DEBUG END =====================\n")
    return {"rooms": final}


@frappe.whitelist()
def create_interview_event(event_title,
                           start_datetime,
                           end_datetime,
                           interviewer_emails,
                           interviewee_email,
                           room_emails,
                           is_online,
                           Organizer_email,
                           Interview_round,
                           InterviewersName,
                           Applicants_name,
                           Applicants_Role,
                           application_id,
                           interview_mode=None,
                           Map_location=None,
                           address=None,
                           candidate_phone=None,
                           commands_to_candidate=None,
                           commands_to_interviewer=None,
                           attachment_paths=None,
                           demo_feed_back_form=0,
                           doc_name=None,
                           ms_event_id=None,
                           feedback_form_link=None):

    import re
    import ast
    import os
    import base64
    import time
    import requests
    from datetime import datetime
    from ms_calendar.api.email_data_helper import get_salary_details

    # ----------------------------------------
    # Convert is_online → int
    # ----------------------------------------
    try:
        is_online = int(is_online)
    except:
        is_online = 0

    Organizer_email  = Organizer_email.strip()
    Applicants_name  = (Applicants_name or "").strip()
    Applicants_Role  = (Applicants_Role or "").strip()
    InterviewersName = (InterviewersName or "").strip()
    Map_location = Map_location or ""
    address = address or ""
    commands_to_candidate = commands_to_candidate or ""
    commands_to_interviewer = commands_to_interviewer or ""

    # ----------------------------------------
    # Friendly date
    # ----------------------------------------
    start_dt = datetime.fromisoformat(start_datetime)
    end_dt = datetime.fromisoformat(end_datetime)
    when_str = start_dt.strftime("%A, %d %b %Y at %I:%M %p")

    interview_date_str = start_dt.strftime("%d %B %Y")
    interview_time_str = start_dt.strftime("%I:%M %p")
    end_time_str       = end_dt.strftime("%I:%M %p")
    round_label        = str(Interview_round).strip()
    display_mode       = (interview_mode or "").strip() or ("Online" if is_online == 1 else "Face-to-Face")
    mode_is_online     = (is_online == 1) or (display_mode.lower() == "online")
    candidate_phone    = candidate_phone or ""

    # Phone number HTML for interviewer email (Phone mode only)
    phone_info_html = (
        f"<b>Candidate Phone No.:</b> {candidate_phone}<br>"
        if display_mode.lower() == "phone" and candidate_phone
        else ""
    )

    round_raw  = str(Interview_round).strip().lower()
    role_raw   = str(Applicants_Role or "").strip().lower()

    # ── Round flags ──────────────────────────────────────────────────────────
    is_recruiter_round = ("recruiter" in round_raw)
    is_round1          = ("round one"  in round_raw or round_raw == "round 1")
    is_round2          = ("round two"  in round_raw or round_raw == "round 2")
    is_round3          = ("round three" in round_raw or round_raw == "round 3")

    # ── Feedback URL: resolved entirely in backend (3-level priority) ──────────
    # Priority 1 → value passed from JS (or manually filled on the form)
    # Priority 2 → feedback_form_link stored on the Field Interview Schedule record in DB
    # Priority 3 → role + round lookup from _FEEDBACK_URL_MAP
    _demo_checked = str(demo_feed_back_form or "0").strip().lower() in ("1", "true", "yes")
    feedback_url  = str(feedback_form_link or "").strip()

    # Priority 2: read from Field Interview Schedule record in DB
    if not feedback_url and application_id:
        try:
            _fis = frappe.get_all(
                "Field Interview Schedule",
                filters={
                    "application_id": application_id,
                    "interview_round": Interview_round
                },
                fields=["feedback_form_link"],
                order_by="modified desc",
                limit=1
            )
            if _fis and _fis[0].get("feedback_form_link"):
                feedback_url = str(_fis[0]["feedback_form_link"]).strip()
        except Exception:
            pass

    # Priority 3: auto-resolve from role + round lookup table
    if not feedback_url:
        from urllib.parse import quote as _quote
        _role_key  = str(Applicants_Role or "").strip().lower()
        _round_key = str(Interview_round or "").strip().lower()
        _template  = _FEEDBACK_URL_MAP.get((_role_key, _round_key), "")
        if _template:
            feedback_url = _template.format(
                app_id=_quote(str(application_id or ""), safe=""),
                applicant_name=_quote(str(Applicants_name or ""), safe="")
            )

    # For Priority 1 & 2 URLs (manually filled), append params if not already present
    if feedback_url and "app_id=" not in feedback_url:
        from urllib.parse import quote as _quote
        _sep = "&" if "?" in feedback_url else "?"
        feedback_url = (
            f"{feedback_url}{_sep}"
            f"app_id={_quote(str(application_id or ''), safe='')}"
            f"&applicant_name={_quote(str(Applicants_name or ''), safe='')}"
        )

    # Ensure absolute URL so Outlook doesn't treat it as a relative path
    if feedback_url and not feedback_url.startswith("http"):
        feedback_url = "https://" + feedback_url

    # Build demo feedback URL separately when checkbox is checked
    demo_feedback_url = ""
    if _demo_checked:
        from urllib.parse import quote as _quote
        demo_feedback_url = (
            "https://careers.frappe.cloud/demo-lesson-observation-feedback-form-feed-back-form/new"
            f"?app_id={_quote(str(application_id or ''), safe='')}"
            f"&applicant_name={_quote(str(Applicants_name or ''), safe='')}"
        )
    demo_feedback_html = ""

    from urllib.parse import unquote as _unquote

    def _link_block(url, label):
        display = _unquote(url)
        return (
            f'<p><b>{label}:</b><br>'
            f'<a href="{url}" target="_blank" '
            f'style="display:inline-block;margin-top:6px;padding:8px 18px;'
            f'background-color:#1d4ed8;color:#ffffff;text-decoration:none;'
            f'border-radius:4px;font-weight:600;font-size:13px;">'
            f'Click Here to Open Feedback Form</a><br>'
            f'<span style="font-size:11px;color:#6b7280;word-break:break-all;">'
            f'Or copy this link: {display}</span></p>'
        )

    feedback_html_block = ""
    if feedback_url:
        feedback_html_block += _link_block(feedback_url, "Feedback Form Link")
    if demo_feedback_url:
        feedback_html_block += _link_block(demo_feedback_url, "Demo Lesson Observation Feedback Form")

    if display_mode.lower() == "face-to-face" and (address or Map_location):
        venue_row = ""
        if address:
            venue_row = f"""
            <tr>
              <td style="padding:4px 0 2px;">
                <span style="font-size:12px;font-weight:600;color:#64748b;
                             text-transform:uppercase;letter-spacing:0.05em;">
                  Venue Address
                </span>
              </td>
            </tr>
            <tr>
              <td style="padding:0 0 10px;">
                <span style="font-size:14px;color:#1e293b;font-weight:500;">
                  {address}
                </span>
              </td>
            </tr>"""

        map_btn = ""
        if Map_location:
            map_btn = f"""
            <tr>
              <td style="padding:4px 0 0;">
                <a href="{Map_location}" target="_blank"
                   style="display:inline-block;padding:8px 18px;
                          background:#1d4ed8;color:#ffffff;
                          font-size:13px;font-weight:600;
                          text-decoration:none;border-radius:6px;">
                  &#128205; View on Google Maps
                </a>
              </td>
            </tr>"""

        map_html = f"""
<table width="100%" cellpadding="0" cellspacing="0"
       style="margin:16px 0;border-collapse:collapse;">
  <tr>
    <td style="background:#eff6ff;border-left:4px solid #1d4ed8;
               border-radius:0 8px 8px 0;padding:14px 18px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:0 0 8px;">
            <span style="font-size:15px;font-weight:700;color:#1e3a8a;">
              &#x1F3E2;&nbsp; Interview Venue
            </span>
          </td>
        </tr>
        {venue_row}
        {map_btn}
      </table>
    </td>
  </tr>
</table>"""
    else:
        map_html = ""

    note_to_candidate_html = (
        f'<p><strong>For your information:</strong> {commands_to_candidate}</p>'
        if commands_to_candidate else ""
    )
    note_to_interviewer_html = (
        f'<p><strong>For your information:</strong> {commands_to_interviewer}</p>'
        if commands_to_interviewer else ""
    )
    # ----------------------------------------
    # ROUND 2 → SALARY DETAILS
    # ----------------------------------------
    total_exp = current_ctc = expected_ctc = ""
    if is_round2:
        try:
            salary_result = get_salary_details(application_id)
            if salary_result:
                total_exp = salary_result.get("total_years_of_experience") or ""
                current_ctc = salary_result.get("current_ctc") or ""
                expected_ctc = salary_result.get("expected_ctc") or ""
        except:
            pass

    # ----------------------------------------
    # GRAPH AUTH
    # ----------------------------------------
    creds = frappe.get_single("MS Graph Credentials")
    token_url = f"https://login.microsoftonline.com/{creds.tenant_id.strip()}/oauth2/v2.0/token"

    try:
        tok = requests.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": creds.client_id.strip(),
            "client_secret": creds.get_password("client_secret"),
            "scope": "https://graph.microsoft.com/.default"
        }, timeout=30)
        tok.raise_for_status()
        access_token = tok.json().get("access_token")
        if not access_token:
            frappe.throw(f"Failed to fetch MS access token: {tok.json()}")
    except requests.exceptions.ConnectionError:
        frappe.throw("Cannot reach Microsoft login servers. Check network connectivity and try again.")
    except requests.exceptions.Timeout:
        frappe.throw("Microsoft login server timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Token request failed: {e}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # --------------------------------------
    # CANCEL OLD EVENT (reschedule case)
    # --------------------------------------
    if ms_event_id:
        try:
            requests.delete(
                f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{ms_event_id}"
                f"?sendUpdates=all",
                headers=headers
            )
            # Do not raise — if old event already gone, that's fine
        except Exception:
            pass

    # ----------------------------------------
    # ATTENDEES
    # ----------------------------------------
    interviewer_list = [i.strip() for i in (interviewer_emails or "").split(",") if i.strip()]
    room_list = [r.strip() for r in (room_emails or "").split(",") if r.strip()]

    attendees = []
    for r in room_list:
        attendees.append({"emailAddress": {"address": r}, "type": "resource"})
    for i in interviewer_list:
        attendees.append({"emailAddress": {"address": i}, "type": "required"})
    # ----------------------------------------
    # ATTACHMENTS (PUBLIC + PRIVATE FIXED)
    # ----------------------------------------
    final_files = []

    if attachment_paths:
        try:
            attachment_list = ast.literal_eval(attachment_paths)
        except:
            attachment_list = []
    else:
        attachment_list = []

    for web_path in attachment_list:
        file_doc = frappe.get_all(
            "File",
            filters={"file_url": web_path},
            fields=["file_url", "file_name", "is_private"]
        )

        if not file_doc:
            frappe.log_error(f"File Doc not found: {web_path}", "Interview Event File Error")
            continue

        file_doc = file_doc[0]
        file_name = file_doc.file_name

        if file_doc.is_private:
            file_path = frappe.get_site_path("private", "files", file_name)
        else:
            file_path = frappe.get_site_path("public", "files", file_name)

        if not os.path.isfile(file_path):
            frappe.log_error(f"File missing on disk: {file_path}", "Interview Event File Error")
            continue

        if os.path.getsize(file_path) > 3 * 1024 * 1024:
            frappe.log_error(f"File too large: {file_name}", "Interview Event File Error")
            continue

        with open(file_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode()

        final_files.append((file_name, file_content))

    # ----------------------------------------
    # AUTO-ATTACH FEEDBACK FORMS FROM Field Registration Form
    # Round One   → recruiter_round_feedback_form
    # Round Two   → recruiter_round_feedback_form + round_one_feedback_from + resume
    # Round Three → recruiter_round_feedback_form + round_one_feedback_from
    #               + round_two_feedback_form + resume
    # ----------------------------------------
    if application_id:
        try:
            _frf_doctype = (
                "Field Registration Form"
                if frappe.db.exists("DocType", "Field Registration Form")
                else "Field Registration Form"
            )
            if not frappe.db.exists(_frf_doctype, application_id):
                frappe.log_error(
                    f"Skipping auto-attach: {_frf_doctype} '{application_id}' not found",
                    "Interview Auto-Attach Skip"
                )
                srf = None
            else:
                srf = frappe.get_doc(_frf_doctype, application_id)

            if not srf:
                raise Exception("srf not loaded, skipping auto-attach")

            # If resume was already manually attached via candidate_cv__resume,
            # skip resume_upload to avoid sending two resumes
            _has_manual_resume = len(final_files) > 0

            # Determine which fields to attach based on round
            # application_forms is always attached for all rounds
            if is_recruiter_round:
                auto_attach_fields = ([] if _has_manual_resume else ["resume_upload"]) + ["application_forms"]
            elif is_round1:
                auto_attach_fields = ([] if _has_manual_resume else ["resume_upload"]) + ["recruiter_round_feedback_form", "application_forms"]
            elif is_round2:
                auto_attach_fields = ([] if _has_manual_resume else ["resume_upload"]) + [
                    "recruiter_round_feedback_form",
                    "round_one_feedback_from",
                    "application_forms"
                ]
            elif is_round3:
                auto_attach_fields = ([] if _has_manual_resume else ["resume_upload"]) + [
                    "recruiter_round_feedback_form",
                    "round_one_feedback_from",
                    "round_two_feedback_form",
                    "application_forms"
                ]
            else:
                auto_attach_fields = ["application_forms"]

            # Track filenames already added (from manual attachments) to avoid duplicates
            _already_added = {fname.lower() for fname, _ in final_files}

            for field in auto_attach_fields:
                web_path = getattr(srf, field, None)
                if not web_path:
                    continue

                # Resolve physical path
                f_docs = frappe.get_all(
                    "File",
                    filters={"file_url": web_path},
                    fields=["file_name", "is_private"],
                    limit=1
                )
                if f_docs:
                    f_name = f_docs[0]["file_name"]
                    f_private = f_docs[0]["is_private"]
                else:
                    # Fallback: derive filename from URL
                    f_name = web_path.split("/")[-1]
                    f_private = False

                if f_private:
                    f_path = frappe.get_site_path("private", "files", f_name)
                else:
                    f_path = frappe.get_site_path("public", "files", f_name)

                if not os.path.isfile(f_path):
                    frappe.log_error(
                        f"Auto-attach file missing: {f_path} (field={field})",
                        "Interview Auto-Attach Error"
                    )
                    continue

                if os.path.getsize(f_path) > 5 * 1024 * 1024:
                    frappe.log_error(
                        f"Auto-attach file too large: {f_name}",
                        "Interview Auto-Attach Error"
                    )
                    continue

                # Skip if this file was already added (avoid duplicate resume)
                if f_name.lower() in _already_added:
                    continue

                with open(f_path, "rb") as fh:
                    file_bytes = fh.read()
                final_files.append((f_name, base64.b64encode(file_bytes).decode()))
                _already_added.add(f_name.lower())

        except Exception as e:
            frappe.log_error(
                f"Auto-attach from SRF failed for {application_id}: {e}",
                "Interview Auto-Attach Error"
            )

    # ----------------------------------------
    # ROUND 1 TEMPLATES
    # ----------------------------------------
    # ── INTERVIEWER TEMPLATE (Round 1) ──────────────────────────────────────
    round1_interviewer_template = """
<p>Hi,</p>

<p>An interview with <b>{Applicants_name}</b> for the role of <b>{Applicants_Role}</b> has been confirmed.
Please find the details of the interview below.</p>

<p>
<b>Date:</b> {interview_date_str}<br>
(UTC+05:30) Asia/Calcutta<br>
<b>Interview Mode:</b> {display_mode}<br>
{meeting_info}
{phone_info}
<b>Interview Round:</b> {round_label}<br>
<b>Interview Time:</b> {interview_time_str} – {end_time_str}<br>
<b>Interviewers:</b> {InterviewersName}
</p>

{Map_html}
{Note_to_interviewer_html}

{feedback_html_block}

{demo_feedback_html}

<p>Regards,<br>People Function</p>
"""

    # ── CANDIDATE TEMPLATE (all rounds, mode-based) ──────────────────────────
    candidate_template = """
<p>Dear {Applicants_name},</p>

<p>We are pleased to inform you that your interview for the position of
<b>{Applicants_Role}</b> at Azim Premji Foundation has been scheduled
as per the details below:</p>

<p><b>Interview Details</b></p>
<ul>
  <li><b>Interview Round:</b> {round_label}</li>
  <li><b>Date:</b> {interview_date_str}</li>
  <li><b>Time:</b> {interview_time_str} – {end_time_str} (UTC+05:30) Asia/Calcutta</li>
  <li><b>Mode:</b> {display_mode}</li>
</ul>

{candidate_mode_html}

{Note_to_candidate_html}

{candidate_advice_html}

<p>We wish you all the best for your interview.</p>

<p>Warm regards,<br>Recruitment Team<br>Azim Premji Foundation</p>
"""

    # ── INTERVIEWER TEMPLATE (Round 2) 
    round2_interviewer_template = """
<p>Hi,</p>

<p>An interview with <b>{Applicants_name}</b> for the role of <b>{Applicants_Role}</b> has been confirmed.
Please find the details of the interview below.</p>


<p>
<b>Date:</b> {interview_date_str}<br>
(UTC+05:30) Asia/Calcutta<br>
<b>Interview Mode:</b> {display_mode}<br>
{meeting_info}
{phone_info}
<b>Interview Round:</b> {round_label}<br>
<b>Interview Time:</b> {interview_time_str} – {end_time_str}<br>
<b>Interviewers:</b> {InterviewersName}
</p>

{Map_html}
{Note_to_interviewer_html}

{feedback_html_block}

<p>Regards,<br>People Function</p>
"""

    # ----------------------------------------
    # INITIAL EVENT BODY
    # ----------------------------------------
    if is_round1:
        calendar_subject = f"Discussion With - {Applicants_name} ({Applicants_Role} Role) | {candidate_phone} | {display_mode}, Azim Premji Scholarship"
        # initial_body = round1_interviewer_template.format(
        #     Interviewer_name=InterviewersName,
        #     when_str=when_str,
        #     meeting_info="",
        #     feedback_url=feedback_url
        # )
        initial_body = round1_interviewer_template.format(
            Applicants_name=Applicants_name,
            Applicants_Role=Applicants_Role,
            interview_date_str=interview_date_str,
            display_mode=display_mode,
            round_label=round_label,
            interview_time_str=interview_time_str,
            end_time_str=end_time_str,
            InterviewersName=InterviewersName,
            meeting_info="",
            phone_info=phone_info_html,
            Map_html=map_html,
            feedback_html_block=feedback_html_block,
            demo_feedback_html=demo_feedback_html,
            Note_to_interviewer_html=note_to_interviewer_html
        )

    else:
        calendar_subject = f"Discussion With - {Applicants_name} ({Applicants_Role} Role) | {candidate_phone} | {display_mode}, Azim Premji Scholarship"
        initial_body = round2_interviewer_template.format(
            Applicants_name=Applicants_name,
            Applicants_Role=Applicants_Role,
            total_exp=total_exp,
            current_ctc=current_ctc,
            expected_ctc=expected_ctc,
            interview_date_str=interview_date_str,
            display_mode=display_mode,
            round_label=round_label,
            interview_time_str=interview_time_str,
            end_time_str=end_time_str,
            InterviewersName=InterviewersName,
            meeting_info="",
            phone_info=phone_info_html,
            Map_html=map_html,
            feedback_html_block=feedback_html_block,
            Note_to_interviewer_html=note_to_interviewer_html
        )

    create_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events"

    draft_payload = {
        "subject": calendar_subject,
        "isOnlineMeeting": mode_is_online,
        "onlineMeetingProvider": "teamsForBusiness" if mode_is_online else None,
        "showAs": "busy",
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end":   {"dateTime": end_datetime,   "timeZone": "Asia/Kolkata"},
        "body":  {"contentType": "HTML", "content": initial_body},
        # NO attendees here — adding attendees at creation triggers a first invite
        # even with sendUpdates=none. Attendees are added in the PATCH so only
        # ONE invite (with the complete final body + Teams URL) is ever sent.
    }

    # Create event without attendees so no premature invite is fired
    res = requests.post(create_url + "?sendUpdates=none", headers=headers, json=draft_payload)
    res.raise_for_status()
    event_id = res.json()["id"]

    
    # ATTACH FILES  (CV / feedback form)
    # Attached to the event so interviewers can access them from the calendar.
   
    attach_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}/attachments"
    for fname, fb64 in final_files:
        requests.post(
            attach_url,
            headers=headers,
            json={
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": fname,
                "contentBytes": fb64
            }
        ).raise_for_status()

    # ----------------------------------------
    # FETCH MEETING DETAILS
    # ----------------------------------------
    event_fetch_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}"

    join_web_url = ""
    online_meeting_id = ""

    for attempt in range(10):
        data = requests.get(event_fetch_url, headers=headers)
        json_data = data.json()

        if "onlineMeeting" in json_data and json_data["onlineMeeting"]:
            join_web_url = json_data["onlineMeeting"].get("joinUrl", "")
            online_meeting_id = json_data["onlineMeeting"].get("id", "")
            break

        time.sleep(1)

    join_meeting_id = ""
    join_passcode = ""

    # ---------------------------------------
    # SECONDARY (THE ORIGINAL): onlineMeetings filter (may return empty)
    # ---------------------------------------
    if mode_is_online and join_web_url:
        filter_url = (
            f"https://graph.microsoft.com/v1.0/users/{Organizer_email}"
            f"/onlineMeetings?$filter=JoinWebUrl eq '{join_web_url}'"
        )

        om_res = requests.get(filter_url, headers=headers)
        if om_res.status_code == 200:
            values = om_res.json().get("value", [])
            print("ONLINE MEETING DEBUG:", values)

            if values:
                meeting = values[0]
                join_meeting_id = meeting.get("joinMeetingId", "") or ""
                join_passcode = meeting.get("passcode", "") or ""

    # ----------------------------------------
    # PRIMARY RELIABLE FIX → Extract Meeting ID + Passcode from HTML
    # ----------------------------------------
    if mode_is_online and (not join_meeting_id or not join_passcode):
        try:
            html_body = json_data.get("body", {}).get("content", "")

            # Meeting ID
            m1 = re.search(r"Meeting ID:\s*</span><span[^>]*>([\d\s]+)<", html_body)
            if m1:
                join_meeting_id = m1.group(1).strip()
            else:
                m1b = re.search(r"Meeting ID:\s*([\d\s]+)", html_body)
                if m1b:
                    join_meeting_id = m1b.group(1).strip()

            # Passcode
            m2 = re.search(r"Passcode:\s*</span><span[^>]*>([\w\d]+)<", html_body)
            if m2:
                join_passcode = m2.group(1).strip()
            else:
                m2b = re.search(r"Passcode:\s*([\w\d]+)", html_body)
                if m2b:
                    join_passcode = m2b.group(1).strip()

        except Exception as e:
            print("MEETING HTML PARSE ERROR:", e)

    # ----------------------------------------
    # ONLINE OR OFFLINE HTML
    # ----------------------------------------
    is_valid_online = (mode_is_online and join_web_url)

    if is_valid_online:
        meeting_html = (
            f"<p><b>Join Teams Meeting:</b> "
            f"<a href='{join_web_url}' target='_blank'>Join Now</a><br>"
            f"<p><b>Meeting ID:</b> {join_meeting_id}<br>"
            f"<b>Passcode:</b> {join_passcode}</p>"
        )
    else:
        meeting_html = ""

    # ----------------------------------------
    # MODE-SPECIFIC CONTENT FOR CANDIDATE EMAIL
    # ----------------------------------------
    _mode_lower = display_mode.lower()
    if _mode_lower == "online":
        candidate_mode_html = meeting_html
    elif _mode_lower == "phone":
        candidate_mode_html = (
            f'<p><b>Candidate Phone No.:</b> {candidate_phone}</p>'
            if candidate_phone else ""
        )
    else:  # Face-to-Face (default)
        candidate_mode_html = map_html

    if _mode_lower == "online":
        candidate_advice_html = (
            "<p>Please ensure you are available on time. "
            "If you are attending online, be in a suitable environment "
            "(quiet, well-lit, with minimal disturbance) for the interview "
            "and kindly test your internet connection, webcam, and microphone "
            "in advance.</p>"
        )
    else:
        candidate_advice_html = (
            "<p>Please ensure you are available on time and carry a copy of "
            "your resume and any relevant documents.</p>"
        )

    # ----------------------------------------
    # FINAL EVENT BODY
    # ----------------------------------------
    if is_round1:
        final_body = round1_interviewer_template.format(
            Applicants_name=Applicants_name,
            Applicants_Role=Applicants_Role,
            interview_date_str=interview_date_str,
            display_mode=display_mode,
            round_label=round_label,
            interview_time_str=interview_time_str,
            end_time_str=end_time_str,
            InterviewersName=InterviewersName,
            meeting_info=meeting_html,
            phone_info=phone_info_html,
            Map_html=map_html,
            feedback_html_block=feedback_html_block,
            demo_feedback_html=demo_feedback_html,
            Note_to_interviewer_html=note_to_interviewer_html
        )

    elif is_round2:
        final_body = round2_interviewer_template.format(
            Applicants_name=Applicants_name,
            Applicants_Role=Applicants_Role,
            total_exp=total_exp,
            current_ctc=current_ctc,
            expected_ctc=expected_ctc,
            interview_date_str=interview_date_str,
            display_mode=display_mode,
            round_label=round_label,
            interview_time_str=interview_time_str,
            end_time_str=end_time_str,
            InterviewersName=InterviewersName,
            meeting_info=meeting_html,
            phone_info=phone_info_html,
            Map_html=map_html,
            feedback_html_block=feedback_html_block,
            Note_to_interviewer_html=note_to_interviewer_html
        )

    else:
        final_body = initial_body

    # ── PATCH 1: update body silently (no email yet) 
    # Set the final body (with Teams link / venue info) BEFORE adding
    # attendees so that when the invite lands in their inbox, it already
    # contains the complete content. Using sendUpdates=none means no
    # notification is fired for this body change.
    requests.patch(
        event_fetch_url + "?sendUpdates=none",
        headers=headers,
        json={
            "body":   {"contentType": "HTML", "content": final_body},
            "showAs": "busy"
        }
    ).raise_for_status()

    # ── PATCH 2: add attendees silently (no Outlook calendar invite email) ──
    # sendUpdates=none → attendees are added to the event (it appears in their
    # calendar) but the automatic Outlook invite notification email is blocked.
    # Custom emails are sent below instead.
    # MS Graph can return 504 Gateway Timeout — the event is already created,
    # so we log and continue.
    try:
        patch2_res = requests.patch(
            event_fetch_url + "?sendUpdates=none",
            headers=headers,
            json={"attendees": attendees},
            timeout=60
        )
        patch2_res.raise_for_status()
    except requests.exceptions.Timeout:
        frappe.log_error(
            title="Attendees PATCH timeout",
            message=f"504/timeout patching attendees for event {event_id}. Event was created; invites may still arrive."
        )
    except requests.exceptions.HTTPError as patch_err:
        if patch2_res.status_code in (502, 503, 504):
            frappe.log_error(
                title="Attendees PATCH gateway error",
                message=f"{patch_err} — event {event_id} created; invites may still arrive."
            )
        else:
            raise

    # ----------------------------------------
    # EMAIL TO CANDIDATE
    # ----------------------------------------
    candidate_email_subject = f"Interview Scheduled \u2013 {round_label} for {Applicants_Role} | {candidate_phone} | {display_mode}"

    candidate_email_body = candidate_template.format(
        Applicants_name=Applicants_name,
        Applicants_Role=Applicants_Role,
        round_label=round_label,
        interview_date_str=interview_date_str,
        interview_time_str=interview_time_str,
        end_time_str=end_time_str,
        display_mode=display_mode,
        candidate_mode_html=candidate_mode_html,
        Note_to_candidate_html=note_to_candidate_html,
        candidate_advice_html=candidate_advice_html,
    )

    # Send candidate email — always use frappe.sendmail (reliable fallback)
    if not interviewee_email:
        frappe.log_error(
            f"Candidate email (attendees) is empty for doc {doc_name}. Skipping candidate email.",
            "Candidate Email Skipped"
        )
    else:
        try:
            send_mail_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/sendMail"
            mail_payload = {
                "message": {
                    "subject": candidate_email_subject,
                    "body": {"contentType": "HTML", "content": candidate_email_body},
                    "toRecipients": [
                        {"emailAddress": {"address": interviewee_email}}
                    ],
                    "ccRecipients": [
                        {"emailAddress": {"address": Organizer_email}}
                    ]
                },
                "saveToSentItems": True
            }
            send_res = requests.post(send_mail_url, headers=headers, json=mail_payload)
            send_res.raise_for_status()
        except Exception as mail_err:
            try:
                frappe.log_error(title="sendMail fallback", message=str(mail_err))
            except Exception:
                pass
            try:
                frappe.sendmail(
                    recipients=[interviewee_email, Organizer_email],
                    subject=candidate_email_subject,
                    message=candidate_email_body,
                    delayed=False
                )
            except Exception as fallback_err:
                frappe.log_error(
                    f"Candidate email fallback also failed: {fallback_err}",
                    "Candidate Email Error"
                )

    # Save event_id to the document so reschedule can cancel it later
    if doc_name:
        try:
            frappe.db.set_value(
                "Field Schedule interview", doc_name, "ms_event_id", event_id,
                update_modified=False
            )
        except Exception:
            pass

    frappe.msgprint("✅ Event created successfully. Outlook invite sent.")

    return {
        "event_id":   event_id,
        "join_url":   join_web_url,
        "meeting_id": join_meeting_id,
        "passcode":   join_passcode,
        "is_online":  is_online
    }