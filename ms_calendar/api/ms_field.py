import frappe, requests
from datetime import timedelta
from frappe.utils import get_datetime

@frappe.whitelist()
def get_schedule_free_slots(interviewer_emails, interview_date):
    """
    Fetches busy intervals for multiple interviewers using MS Graph getSchedule endpoint.
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
                "Please check that your site_config.json contains the correct encryption_key."
            )
    except Exception as e:
        frappe.throw(f"Could not fetch MS Graph Credentials: {e}")

    start_date = get_datetime(interview_date)
    end_date = start_date + timedelta(days=1)

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

    context_user = interviewer_emails[0]
    url = f"https://graph.microsoft.com/v1.0/users/{context_user}/calendar/getSchedule"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "schedules": interviewer_emails,
        "startTime": {"dateTime": start_date.isoformat(), "timeZone": "UTC"},
        "endTime":   {"dateTime": end_date.isoformat(),   "timeZone": "UTC"},
        "availabilityViewInterval": 30
    }

    try:
        resp = requests.post(url, headers=headers, json=body)
        resp.raise_for_status()
        schedules = resp.json().get("value", [])
        return {s["scheduleId"]: s.get("scheduleItems", []) for s in schedules}
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Graph API error: {resp.status_code} - {resp.text}")


import frappe, requests, uuid

@frappe.whitelist()
def create_calendar_event(event_title, start_datetime, end_datetime, interviewer_email, interviewee_email):
    try:
        credentials  = frappe.get_single("MS Graph Credentials")
        tenant_id    = credentials.tenant_id.strip()
        client_id    = credentials.client_id.strip()
        client_secret = credentials.get_password("client_secret")
    except Exception as e:
        frappe.throw(f"Could not fetch MS Graph Credentials: {e}")

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

    organizer_email = "health.fellowship@azimpremjifoundation.org"
    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events?sendUpdates=none"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    event_body = {
        "subject": event_title,
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end":   {"dateTime": end_datetime,   "timeZone": "Asia/Kolkata"},
        "location": {"displayName": "Microsoft Teams Meeting"},
        "attendees": [
            {"emailAddress": {"address": interviewer_email, "name": "Interviewer"}, "type": "required"},
            {"emailAddress": {"address": interviewee_email, "name": "Candidate"},   "type": "required"}
        ],
        "responseRequested": True,
        "allowNewTimeProposals": True,
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness",
        "transactionId": str(uuid.uuid4()),
        "body": {"contentType": "HTML", "content": f"<p>Interview: {event_title}</p>"}
    }

    try:
        resp = requests.post(url, headers=headers, json=event_body)
        resp.raise_for_status()
        event    = resp.json()
        join_url = event.get("onlineMeeting", {}).get("joinUrl")
        frappe.msgprint("Interview scheduled.")
        return {"event_id": event.get("id"), "join_url": join_url}
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Graph API error: {resp.status_code} - {resp.text}")


@frappe.whitelist()
def get_org_rooms_and_availability(interview_date, start_time, end_time):
    import time
    from datetime import datetime, timezone, timedelta

    print("\n===================== DEBUG START =====================")

    creds  = frappe.get_single("MS Graph Credentials")
    tenant = creds.tenant_id
    client = creds.client_id
    secret = creds.get_password("client_secret")

    token_url  = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    token_resp = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id":  client,
        "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default"
    })
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    rooms = []
    url   = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"
    page  = 1

    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data       = resp.json()
        page_rooms = data.get("value", [])
        rooms.extend(page_rooms)
        url  = data.get("@odata.nextLink")
        page += 1

    print("DEBUG → TOTAL ROOMS FETCHED =", len(rooms))

    room_emails = [r.get("emailAddress") for r in rooms if r.get("emailAddress")]

    offset     = -time.timezone if time.localtime().tm_isdst == 0 else -time.altzone
    system_tz  = timezone(timedelta(seconds=offset))
    start_local = get_datetime(f"{interview_date} {start_time}")
    end_local   = get_datetime(f"{interview_date} {end_time}")
    start_utc   = start_local.replace(tzinfo=system_tz).astimezone(timezone.utc)
    end_utc     = end_local.replace(tzinfo=system_tz).astimezone(timezone.utc)

    MAX_BATCH    = 20
    schedule_url = (
        "https://graph.microsoft.com/v1.0/"
        "users/health.fellowship@azimpremjifoundation.org/calendar/getSchedule"
    )
    schedule_map = {}

    for i in range(0, len(room_emails), MAX_BATCH):
        batch = room_emails[i:i + MAX_BATCH]
        body  = {
            "schedules": batch,
            "startTime": {"dateTime": start_utc.isoformat(), "timeZone": "UTC"},
            "endTime":   {"dateTime": end_utc.isoformat(),   "timeZone": "UTC"},
            "availabilityViewInterval": 5
        }
        resp = requests.post(schedule_url, headers={**headers, "Content-Type": "application/json"}, json=body)
        resp.raise_for_status()
        for item in resp.json().get("value", []):
            schedule_map[item["scheduleId"].lower()] = item.get("scheduleItems", [])
        time.sleep(0.1)

    final = []
    for r in rooms:
        email = r.get("emailAddress")
        busy  = schedule_map.get(email.lower(), [])
        available = True
        for slot in busy:
            from datetime import datetime, timezone
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


# ================================================================
# ROUND DETECTION HELPER
# ================================================================
def detect_round(interview_round_raw):
    """
    Detects interview round from ANY format string.
    Round 1: Round One / Round 1 / Shortlist / Recruiter / Screening
    Round 2: Round Two / Round 2 / Functional / Leadership / Final / HR
    """
    raw   = str(interview_round_raw).strip().lower()
    clean = raw.replace(" ", "").replace("-", "").replace("_", "").replace("–", "")

    round2_keywords = ["roundtwo", "round2", "functional", "leadership", "finalround", "final", "hrround"]
    for kw in round2_keywords:
        if kw in clean:
            return "round2"

    round1_keywords = ["roundone", "round1", "shortlist", "recruiter", "screening"]
    for kw in round1_keywords:
        if kw in clean:
            return "round1"

    if "round" in clean:
        return "round1"

    return "other"


# ================================================================
# MAIN: CREATE INTERVIEW EVENT
# ================================================================
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
                           interview_mode=None,       # "Online" | "Face-to-Face" | "Phone"
                           Map_location=None,
                           address=None,
                           candidate_phone=None,
                           commands_to_candidate=None,
                           commands_to_interviewer=None,
                           attachment_paths=None):

    import re
    import ast
    import os
    import base64
    import time
    import requests
    from datetime import datetime
    from ms_calendar.api.email_data_helper import get_salary_details

    # ----------------------------------------
    # Normalize inputs
    # ----------------------------------------
    try:
        is_online = int(is_online)
    except:
        is_online = 0

    Organizer_email         = Organizer_email.strip()
    interview_mode          = (interview_mode or "").strip()
    Map_location            = Map_location or ""
    address                 = address or ""
    candidate_phone         = candidate_phone or ""
    commands_to_candidate   = commands_to_candidate or ""
    commands_to_interviewer = commands_to_interviewer or ""

    # Determine mode flags
    mode_is_online      = (interview_mode.lower() == "online"       or is_online == 1)
    mode_is_facetoface  = (interview_mode.lower() == "face-to-face")
    mode_is_phone       = (interview_mode.lower() == "phone")

    # ----------------------------------------
    # Date/time strings
    # ----------------------------------------
    start_dt = datetime.fromisoformat(start_datetime)
    end_dt   = datetime.fromisoformat(end_datetime)

    interview_date_str = start_dt.strftime("%d-%b-%Y")
    interview_time_str = start_dt.strftime("%I:%M %p")
    end_time_str       = end_dt.strftime("%I:%M %p")
    display_mode       = interview_mode if interview_mode else ("Online" if is_online == 1 else "Offline")

    # ----------------------------------------
    # Round detection
    # ----------------------------------------
    round_detected = detect_round(Interview_round)
    is_round1      = (round_detected == "round1")
    is_round2      = (round_detected == "round2")
    round_label    = str(Interview_round).strip()

    print(f"DEBUG → Interview_round='{Interview_round}'  detected='{round_detected}'  mode='{interview_mode}'")

    # ----------------------------------------
    # Feedback URL
    # ----------------------------------------
    form_key     = "two" if is_round2 else "one"
    feedback_url = (
        f"https://careers.frappe.cloud/feedback-form-{form_key}/new"
        f"?app_id={application_id}&applicant_name={Applicants_name}"
    )

    # ----------------------------------------
    # Note blocks
    # ----------------------------------------
    note_to_candidate_html = (
        f'<p><strong>Note:</strong> {commands_to_candidate}</p>'
        if commands_to_candidate else ""
    )
    note_to_interviewer_html = (
        f'<p><strong>For your information:</strong> {commands_to_interviewer}</p>'
        if commands_to_interviewer else ""
    )

    # ----------------------------------------
    # Round 2: salary details
    # ----------------------------------------
    total_exp = current_ctc = expected_ctc = ""
    if is_round2:
        try:
            salary_result = get_salary_details(application_id)
            if salary_result:
                total_exp    = salary_result.get("total_years_of_experience") or ""
                current_ctc  = salary_result.get("current_ctc") or ""
                expected_ctc = salary_result.get("expected_ctc") or ""
        except:
            pass

    # ----------------------------------------
    # Graph auth
    # ----------------------------------------
    creds     = frappe.get_single("MS Graph Credentials")
    token_url = f"https://login.microsoftonline.com/{creds.tenant_id.strip()}/oauth2/v2.0/token"

    tok = requests.post(token_url, data={
        "grant_type":    "client_credentials",
        "client_id":     creds.client_id.strip(),
        "client_secret": creds.get_password("client_secret"),
        "scope":         "https://graph.microsoft.com/.default"
    })
    tok.raise_for_status()
    access_token = tok.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json"
    }

    # ----------------------------------------
    # Attendees
    # ----------------------------------------
    interviewer_list = [i.strip() for i in (interviewer_emails or "").split(",") if i.strip()]
    room_list        = [r.strip() for r in (room_emails or "").split(",") if r.strip()]

    attendees = []
    for r in room_list:
        attendees.append({"emailAddress": {"address": r}, "type": "resource"})
    for i in interviewer_list:
        attendees.append({"emailAddress": {"address": i}, "type": "required"})

    # ----------------------------------------
    # Attachments
    # ----------------------------------------
    final_files     = []
    attachment_list = []

    if attachment_paths:
        try:
            attachment_list = ast.literal_eval(attachment_paths)
        except:
            attachment_list = []

    for web_path in attachment_list:
        file_doc = frappe.get_all("File", filters={"file_url": web_path},
                                  fields=["file_url", "file_name", "is_private"])
        if not file_doc:
            frappe.log_error(f"File Doc not found: {web_path}", "Interview Event File Error")
            continue

        file_doc  = file_doc[0]
        file_name = file_doc.file_name
        file_path = (
            frappe.get_site_path("private", "files", file_name)
            if file_doc.is_private
            else frappe.get_site_path("public", "files", file_name)
        )

        if not os.path.isfile(file_path):
            frappe.log_error(f"File missing on disk: {file_path}", "Interview Event File Error")
            continue
        if os.path.getsize(file_path) > 3 * 1024 * 1024:
            frappe.log_error(f"File too large: {file_name}", "Interview Event File Error")
            continue

        with open(file_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode()
        final_files.append((file_name, file_content))

    # ============================================================
    # INTERVIEWER / CALENDAR BODY TEMPLATES
    # ============================================================

    round1_interviewer_template = """
<p>Hi,</p>

<p>An interview with <b>{Applicants_name}</b> for the role of <b>{Applicants_Role}</b> has been confirmed.</p>

<p>Please find the details of the interview below.</p>

<p>
<b>Date:</b> {interview_date_str}<br>
(UTC+05:30) Asia/Calcutta<br>
<b>Interview Mode:</b> {display_mode}<br>
{meeting_info}
<b>Interview Round:</b> {round_label}<br>
<b>Interview Time:</b> {interview_time_str} – {end_time_str}<br>
<b>Interviewers:</b> {InterviewersName}
</p>

{Note_to_interviewer_html}

<p><b>Feedback form link:</b>
<a href="{feedback_url}" target="_blank">Click here</a></p>

<p>Regards,<br>People Function</p>
"""

    round2_interviewer_template = """
<p>Hi,</p>

<p>An interview with <b>{Applicants_name}</b> for the role of <b>{Applicants_Role}</b> has been confirmed.</p>

<p>Please find the details of the interview below.</p>

<p>
<b>Total Experience:</b> {total_exp}<br>
<b>Current CTC:</b> {current_ctc}<br>
<b>Expected CTC:</b> {expected_ctc}
</p>

<p>
<b>Date:</b> {interview_date_str}<br>
(UTC+05:30) Asia/Calcutta<br>
<b>Interview Mode:</b> {display_mode}<br>
{meeting_info}
<b>Interview Round:</b> {round_label}<br>
<b>Interview Time:</b> {interview_time_str} – {end_time_str}<br>
<b>Interviewers:</b> {InterviewersName}
</p>

{Note_to_interviewer_html}

<p><b>Feedback form link:</b>
<a href="{feedback_url}" target="_blank">Click here</a></p>

<p>Regards,<br>People Function</p>
"""

    # ============================================================
    # CANDIDATE EMAIL TEMPLATES — 3 MODES
    # ============================================================

    # ── ONLINE ──────────────────────────────────────────────────
    online_candidate_template = """
<p>Dear {Applicants_name},</p>

<p>We are pleased to inform you that your interview for the position of <b>{Applicants_Role}</b> at Azim Premji Foundation has been scheduled as per the details below:</p>

<p><b>Interview Details</b></p>
<ul>
  <li><b>Interview Round:</b> {round_label}</li>
  <li><b>Date:</b> {interview_date_str}</li>
  <li><b>Interview Time:</b> {interview_time_str} – {end_time_str} (UTC+05:30) Asia/Calcutta</li>
  <li><b>Interview Mode:</b> Online</li>
</ul>

{meeting_info}

{Note_to_candidate_html}
<p>Please ensure you are available on time. Be in a suitable environment (quiet, well-lit, with minimal disturbance) and kindly test your internet connection, webcam, and microphone in advance.</p>

<p>We wish you all the best for your interview.</p>

<p>Warm regards,<br>Recruitment Team<br>Azim Premji Foundation</p>
"""

    # ── FACE-TO-FACE ─────────────────────────────────────────────
    facetoface_candidate_template = """
<p>Dear {Applicants_name},</p>

<p>We are pleased to inform you that your interview for the position of <b>{Applicants_Role}</b> at Azim Premji Foundation has been scheduled as per the details below:</p>

<p><b>Interview Details</b></p>
<ul>
  <li><b>Interview Round:</b> {round_label}</li>
  <li><b>Date:</b> {interview_date_str}</li>
  <li><b>Interview Time:</b> {interview_time_str} – {end_time_str} (UTC+05:30) Asia/Calcutta</li>
  <li><b>Interview Mode:</b> Face-to-Face</li>
  <li><b>Location:</b> {address}</li>
</ul>

{map_link_html}
<p><b>Interviewers:</b> {InterviewersName}</p>

{Note_to_candidate_html}
<p>Please ensure you are available on time and carry a copy of your resume and any relevant documents.</p>

<p>We wish you all the best for your interview.</p>

<p>Warm regards,<br>Recruitment Team<br>Azim Premji Foundation</p>
"""

    # ── PHONE ────────────────────────────────────────────────────
    phone_candidate_template = """
<p>Dear {Applicants_name},</p>

<p>We are pleased to inform you that your interview for the position of <b>{Applicants_Role}</b> at Azim Premji Foundation has been scheduled as per the details below:</p>

<p><b>Interview Details</b></p>
<ul>
  <li><b>Interview Round:</b> {round_label}</li>
  <li><b>Date:</b> {interview_date_str}</li>
  <li><b>Interview Time:</b> {interview_time_str} – {end_time_str} (UTC+05:30) Asia/Calcutta</li>
  <li><b>Interview Mode:</b> Phone</li>
  <li><b>Your Phone Number on record:</b> {candidate_phone}</li>
</ul>

<p><b>Interviewers:</b> {InterviewersName}</p>

{Note_to_candidate_html}
<p>Please ensure you are in a quiet place with a good network connection and keep your phone available at the scheduled time. Our interviewer will call you on the number above.</p>

<p>We wish you all the best for your interview.</p>

<p>Warm regards,<br>Recruitment Team<br>Azim Premji Foundation</p>
"""

    # ============================================================
    # INTERVIEWER EMAIL TEMPLATES — 3 MODES
    # ============================================================

    # ── PHONE INTERVIEWER ────────────────────────────────────────
    phone_interviewer_template = """
<p>Hi,</p>

<p>You have confirmed the interview of <b>{Applicants_name}</b> for the post of <b>{Applicants_Role}</b> to be scheduled at the below time.</p>

<p>
<b>Date:</b> {interview_date_str}<br>
(UTC+05:30) Asia/Calcutta<br>
<b>Interview Mode:</b> Phone<br>
<b>Candidate Phone No.:</b> {candidate_phone}<br>
<b>Interview Round:</b> {round_label}<br>
<b>Interview Time:</b> {interview_time_str} – {end_time_str}<br>
<b>Interviewers:</b> {InterviewersName}
</p>

{Note_to_interviewer_html}

<p><b>Feedback form link:</b>
<a href="{feedback_url}" target="_blank">Click here</a></p>

<p>Regards,<br>People Function</p>
"""

    # ── FACE-TO-FACE INTERVIEWER ─────────────────────────────────
    facetoface_interviewer_template = """
<p>Hi,</p>

<p>An interview with <b>{Applicants_name}</b> for the role of <b>{Applicants_Role}</b> has been confirmed. Please find the details below.</p>

<p>
<b>Date:</b> {interview_date_str}<br>
<b>Interview Mode:</b> Face-to-Face<br>
<b>Location:</b> {address}<br>
<b>Interview Round:</b> {round_label}<br>
<b>Interview Time:</b> {interview_time_str} – {end_time_str} (UTC+05:30) Asia/Calcutta<br>
<b>Interviewers:</b> {InterviewersName}
</p>

{map_link_html}
{Note_to_interviewer_html}

<p><b>Feedback form link:</b>
<a href="{feedback_url}" target="_blank">Click here</a></p>

<p>Regards,<br>People Function</p>
"""

    # ============================================================
    # BUILD MODE-SPECIFIC HTML BLOCKS
    # ============================================================

    map_link_html = ""
    if Map_location:
        map_link_html = f'<p><b>Google Map:</b> <a href="{Map_location}" target="_blank">Click here for directions</a></p>'

    # This will be filled after we get the Teams join URL (for Online)
    meeting_info     = ""
    mode_detail_html = ""

    # ----------------------------------------
    # Build initial calendar event body (no Teams link yet)
    # ----------------------------------------
    if mode_is_facetoface:
        mode_detail_html = (
            f"<p><b>Location:</b> {address}</p>" if address else ""
        ) + map_link_html
    elif mode_is_phone:
        mode_detail_html = f"<p><b>Candidate Phone No.:</b> {candidate_phone}</p>"

    def build_interviewer_body(meeting_info_block=""):
        if mode_is_phone:
            return phone_interviewer_template.format(
                Applicants_name=Applicants_name,
                Applicants_Role=Applicants_Role,
                interview_date_str=interview_date_str,
                candidate_phone=candidate_phone,
                round_label=round_label,
                interview_time_str=interview_time_str,
                end_time_str=end_time_str,
                InterviewersName=InterviewersName,
                Note_to_interviewer_html=note_to_interviewer_html,
                feedback_url=feedback_url
            )
        elif mode_is_facetoface:
            return facetoface_interviewer_template.format(
                Applicants_name=Applicants_name,
                Applicants_Role=Applicants_Role,
                interview_date_str=interview_date_str,
                address=address,
                round_label=round_label,
                interview_time_str=interview_time_str,
                end_time_str=end_time_str,
                InterviewersName=InterviewersName,
                map_link_html=map_link_html,
                Note_to_interviewer_html=note_to_interviewer_html,
                feedback_url=feedback_url
            )
        else:
            # Online — use round-specific template
            tmpl = round2_interviewer_template if is_round2 else round1_interviewer_template
            kwargs = dict(
                Applicants_name=Applicants_name,
                Applicants_Role=Applicants_Role,
                interview_date_str=interview_date_str,
                interview_time_str=interview_time_str,
                end_time_str=end_time_str,
                display_mode=display_mode,
                round_label=round_label,
                meeting_info=meeting_info_block,
                InterviewersName=InterviewersName,
                Note_to_interviewer_html=note_to_interviewer_html,
                feedback_url=feedback_url
            )
            if is_round2:
                kwargs.update(total_exp=total_exp, current_ctc=current_ctc, expected_ctc=expected_ctc)
            return tmpl.format(**kwargs)

    calendar_subject = f"Discussion With - {Applicants_name} ({Applicants_Role} Role), Azim Premji Scholarship"

    initial_body = build_interviewer_body("")

    # ----------------------------------------
    # Create calendar event
    # ----------------------------------------
    create_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events"

    draft_payload = {
        "subject":               calendar_subject,
        "isOnlineMeeting":       True if mode_is_online else False,
        "onlineMeetingProvider": "teamsForBusiness" if mode_is_online else None,
        "showAs":                "busy",
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end":   {"dateTime": end_datetime,   "timeZone": "Asia/Kolkata"},
        "body":  {"contentType": "HTML", "content": initial_body}
    }

    res = requests.post(create_url, headers=headers, json=draft_payload)
    res.raise_for_status()
    event_id = res.json()["id"]

    # ----------------------------------------
    # Attach files — parallel uploads for speed
    # ----------------------------------------
    if final_files:
        from concurrent.futures import ThreadPoolExecutor
        attach_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}/attachments"

        def _upload_file(item):
            fname, fb64 = item
            requests.post(attach_url, headers=headers, json={
                "@odata.type":  "#microsoft.graph.fileAttachment",
                "name":         fname,
                "contentBytes": fb64
            }).raise_for_status()

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(_upload_file, final_files))

    # ----------------------------------------
    # Poll for Teams meeting details (only for Online)
    # Reduced: 5 attempts × 0.5s = max 2.5s wait
    # ----------------------------------------
    event_fetch_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}"
    join_web_url    = ""
    json_data       = {}
    join_meeting_id = ""
    join_passcode   = ""

    if mode_is_online:
        for attempt in range(5):                      # ← was range(10)
            data      = requests.get(event_fetch_url, headers=headers)
            json_data = data.json()
            if "onlineMeeting" in json_data and json_data["onlineMeeting"]:
                join_web_url = json_data["onlineMeeting"].get("joinUrl", "")
                break
            time.sleep(0.5)                           # ← was time.sleep(1)

        # Extract meeting ID + passcode from the event HTML body (fast, no extra API call)
        try:
            html_body = json_data.get("body", {}).get("content", "")
            m1 = re.search(r"Meeting ID:\s*</span><span[^>]*>([\d\s]+)<", html_body)
            if m1:
                join_meeting_id = m1.group(1).strip()
            else:
                m1b = re.search(r"Meeting ID:\s*([\d\s]+)", html_body)
                if m1b:
                    join_meeting_id = m1b.group(1).strip()
            m2 = re.search(r"Passcode:\s*</span><span[^>]*>([\w\d]+)<", html_body)
            if m2:
                join_passcode = m2.group(1).strip()
            else:
                m2b = re.search(r"Passcode:\s*([\w\d]+)", html_body)
                if m2b:
                    join_passcode = m2b.group(1).strip()
        except Exception as e:
            print("MEETING HTML PARSE ERROR:", e)

    is_valid_online = (mode_is_online and join_web_url)

    if is_valid_online:
        meeting_info = (
            f"<p><b>Join Teams Meeting:</b> "
            f"<a href='{join_web_url}' target='_blank'>Join Now</a></p>"
            f"<p><b>Meeting ID:</b> {join_meeting_id}<br>"
            f"<b>Passcode:</b> {join_passcode}</p>"
        )
    else:
        meeting_info = ""

    # ----------------------------------------
    # Update calendar event with final body + attendees
    # ----------------------------------------
    final_body = build_interviewer_body(meeting_info)

    requests.patch(
        event_fetch_url,
        headers=headers,
        json={
            "attendees": attendees,
            "body": {"contentType": "HTML", "content": final_body},
            "showAs": "busy"
        }
    ).raise_for_status()

    # ============================================================
    # SEND CANDIDATE EMAIL — based on Interview Mode
    # ============================================================

    if mode_is_phone:
        email_subject = f"{round_label}: {Applicants_name} - {Applicants_Role}"
        email_body = phone_candidate_template.format(
            Applicants_name=Applicants_name,
            Applicants_Role=Applicants_Role,
            round_label=round_label,
            interview_date_str=interview_date_str,
            interview_time_str=interview_time_str,
            end_time_str=end_time_str,
            candidate_phone=candidate_phone,
            InterviewersName=InterviewersName,
            Note_to_candidate_html=note_to_candidate_html,
        )

    elif mode_is_facetoface:
        email_subject = f"Interview Scheduled – {round_label} for {Applicants_Role}"
        email_body = facetoface_candidate_template.format(
            Applicants_name=Applicants_name,
            Applicants_Role=Applicants_Role,
            round_label=round_label,
            interview_date_str=interview_date_str,
            interview_time_str=interview_time_str,
            end_time_str=end_time_str,
            address=address,
            map_link_html=map_link_html,
            InterviewersName=InterviewersName,
            Note_to_candidate_html=note_to_candidate_html,
        )

    else:
        email_subject = f"Interview Scheduled – {round_label} for {Applicants_Role}"
        email_body = online_candidate_template.format(
            Applicants_name=Applicants_name,
            Applicants_Role=Applicants_Role,
            round_label=round_label,
            interview_date_str=interview_date_str,
            interview_time_str=interview_time_str,
            end_time_str=end_time_str,
            meeting_info=meeting_info if is_valid_online else "",
            Note_to_candidate_html=note_to_candidate_html,
        )

    frappe.sendmail(
        recipients=[interviewee_email],
        sender=Organizer_email,
        subject=email_subject,
        message=email_body,
        delayed=False
    )

    # ============================================================
    # SEND INTERVIEWER EMAIL — based on Interview Mode
    # ============================================================
    if mode_is_phone:
        interviewer_email_subject = f"{round_label}: {Applicants_name} - {Applicants_Role}"
    else:
        interviewer_email_subject = f"Interview Scheduled – {round_label} for {Applicants_Role} | {Applicants_name}"

    if interviewer_list:
        sendmail_attachments = []
        for fname, fb64 in final_files:
            import base64 as _base64
            sendmail_attachments.append({
                "fname": fname,
                "fcontent": _base64.b64decode(fb64),
            })

        frappe.sendmail(
            recipients=interviewer_list,
            sender=Organizer_email,
            subject=interviewer_email_subject,
            message=final_body,
            attachments=sendmail_attachments if sendmail_attachments else None,
            delayed=False
        )

    frappe.msgprint("✅ Event created successfully. Outlook invite sent.")

    return {
        "event_id":   event_id,
        "join_url":   join_web_url,
        "meeting_id": join_meeting_id,
        "passcode":   join_passcode,
        "is_online":  is_online,
        "mode":       interview_mode
    }