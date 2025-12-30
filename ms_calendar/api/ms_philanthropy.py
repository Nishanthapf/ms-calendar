import frappe
import os, ast, base64, time, re, requests
from datetime import datetime


@frappe.whitelist()
def create_interview_event(
    start_datetime,
    end_datetime,
    interviewer_emails,
    interviewee_email,
    room_emails,
    is_online,
    Organizer_email,
    InterviewersName,
    Applicants_name,
    Applicants_Role,
    application_id,
    attachment_paths=None
):

    # -------- FLAGS --------
    try:
        is_online = int(is_online)
    except:
        is_online = 0

    Organizer_email = Organizer_email.strip()

    start_dt = datetime.fromisoformat(start_datetime)
    end_dt   = datetime.fromisoformat(end_datetime)

    interview_date = start_dt.strftime("%d %b %Y")
    interview_time = start_dt.strftime("%I:%M %p")
    # Format (example: 10:30 AM)
    start_time = start_dt.strftime("%I:%M %p")
    end_time   = end_dt.strftime("%I:%M %p")
    mode_label   = "Teams Meeting" if is_online == 1 else "Offline"
    meeting_room = ", ".join([r.strip() for r in (room_emails or "").split(",") if r.strip()])

    # -------- GRAPH AUTH --------
    creds = frappe.get_single("MS Graph Credentials")

    token = requests.post(
        f"https://login.microsoftonline.com/{creds.tenant_id}/oauth2/v2.0/token",
        data={
            "grant_type": "client_credentials",
            "client_id": creds.client_id,
            "client_secret": creds.get_password("client_secret"),
            "scope": "https://graph.microsoft.com/.default"
        }
    )
    token.raise_for_status()
    access_token = token.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # -------- CREATE EVENT --------
    create_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events"

    draft_payload = {
        "subject": f"Discussion with {Applicants_name} - ({Applicants_Role})",
        "isOnlineMeeting": True if is_online == 1 else False,
        "onlineMeetingProvider": "teamsForBusiness" if is_online == 1 else None,
        "showAs": "busy",
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        "body": {"contentType": "HTML", "content": "<p>Interview scheduled.</p>"}
    }

    res = requests.post(create_url, headers=headers, json=draft_payload)
    res.raise_for_status()
    event = res.json()
    event_id = event["id"]

    event_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}"

    # -------- FETCH MEETING DETAILS --------
    join_web_url = ""
    join_meeting_id = ""
    join_passcode = ""

    for _ in range(10):
        ev = requests.get(event_url, headers=headers).json()

        # join link
        if ev.get("onlineMeeting"):
            join_web_url = ev["onlineMeeting"].get("joinUrl", "") or join_web_url

        # parse HTML body for ID + passcode
        try:
            html_body = ev.get("body", {}).get("content", "")

            m1 = re.search(r"Meeting ID:\s*</span><span[^>]*>([\d\s]+)<", html_body)
            if not m1:
                m1 = re.search(r"Meeting ID:\s*([\d\s]+)", html_body)
            if m1:
                join_meeting_id = m1.group(1).strip()

            m2 = re.search(r"Passcode:\s*</span><span[^>]*>([\w\d]+)<", html_body)
            if not m2:
                m2 = re.search(r"Passcode:\s*([\w\d]+)", html_body)
            if m2:
                join_passcode = m2.group(1).strip()

        except Exception:
            pass

        if join_web_url and join_meeting_id and join_passcode:
            break

        time.sleep(1)

    # -------- SECONDARY FALLBACK (onlineMeetings filter) --------
    if is_online == 1 and join_web_url and (not join_meeting_id or not join_passcode):
        filter_url = (
            f"https://graph.microsoft.com/v1.0/users/{Organizer_email}"
            f"/onlineMeetings?$filter=JoinWebUrl eq '{join_web_url}'"
        )

        om = requests.get(filter_url, headers=headers)
        if om.status_code == 200:
            values = om.json().get("value", [])
            if values:
                m = values[0]
                join_meeting_id = m.get("joinMeetingId", "") or join_meeting_id
                join_passcode   = m.get("passcode", "") or join_passcode

    # -------- MEETING HTML --------
    if is_online == 1 and join_web_url:
        meeting_html = f"""
        <p><b>Join Teams Meeting:</b>
        <a href="{join_web_url}" target="_blank">Join Now</a></p>

        <p><b>Meeting ID:</b> {join_meeting_id}<br>
        <b>Passcode:</b> {join_passcode}</p>
        """
    else:
        meeting_html = "<p><b>Mode:</b> Offline interview</p>"

    # -------- ATTACH FILES --------
    attachment_files = []

    if attachment_paths:
        try:
            paths = ast.literal_eval(attachment_paths)
        except:
            paths = []
    else:
        paths = []

    for web_path in paths:
        file_doc = frappe.get_all(
            "File",
            filters={"file_url": web_path},
            fields=["file_url", "file_name", "is_private"]
        )
        if not file_doc:
            continue

        file_doc = file_doc[0]
        file_name = file_doc.file_name

        if file_doc.is_private:
            file_path = frappe.get_site_path("private", "files", file_name)
        else:
            file_path = frappe.get_site_path("public", "files", file_name)

        if not os.path.isfile(file_path):
            continue

        with open(file_path, "rb") as f:
            fb64 = base64.b64encode(f.read()).decode()

        attachment_files.append((file_name, fb64))

    attach_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}/attachments"
    for fname, fb64 in attachment_files:
        requests.post(
            attach_url,
            headers=headers,
            json={
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": fname,
                "contentBytes": fb64
            }
        )

    # -------- EMAIL CONTENT --------
    # feedback_url = f"https://careers.frappe.cloud/philanthrophy-feedback-form/new?app_id={application_id}&applicant_name={Applicants_name}"
    feedback_url = (
            f"https://careers.frappe.cloud/philanthrophy-feedback-form/new"
            f"?app_id={application_id}&applicant_name={Applicants_name}&role={Applicants_Role}"
        )
    interviewer_body = f"""
    <p>Hi {InterviewersName},</p>

    <p>Kindly find the details of the interview scheduled:</p>

    <table cellpadding="6">
    <tr><td><b>Applicant name:</b></td><td>{Applicants_name}</td></tr>
    <tr><td><b>Role:</b></td><td>{Applicants_Role}</td></tr>
    <tr><td><b>Date:</b></td><td>{interview_date}</td></tr>
    <tr><td><b>Time:</b></td><td>{start_time} – {end_time}</td></tr>
    <tr><td><b>Mode:</b></td><td>{mode_label}</td></tr>
    <tr><td><b>Meeting room:</b></td><td>{meeting_room}</td></tr>
    </table>

    {meeting_html}

    <p><b>Feedback form:</b>
    <a href="{feedback_url}" target="_blank">Click here</a></p>
    <p>Kindly reach out to us if you have any questions</p>

    <p>Regards,<br>
    People Function<br>
    Azim Premji Foundation</p>
    """

    candidate_body = f"""
    <p>Hi {Applicants_name},</p>

    <p>Kindly find the details of the interview scheduled:</p>

    <table cellpadding="6">
    <tr><td><b>Role:</b></td><td>{Applicants_Role}</td></tr>
    <tr><td><b>Date:</b></td><td>{interview_date}</td></tr>
    <tr><td><b>Time:</b></td><td>{start_time} – {end_time}</td></tr>
    <tr><td><b>Mode:</b></td><td>{mode_label}</td></tr>
    <tr><td><b>Meeting room:</b></td><td>{meeting_room}</td></tr>
    </table>

    {meeting_html}
    <p>Kindly reach out to us if you have any questions</p>

    <p>Regards,<br>
    People Function<br>
    Azim Premji Foundation</p>
    """

    # -------- UPDATE EVENT BODY & ATTENDEES (Outlook will notify interviewers) --------
    interviewer_list = [i.strip() for i in (interviewer_emails or "").split(",") if i.strip()]
    attendees = [{"emailAddress": {"address": i}, "type": "required"} for i in interviewer_list]

    requests.patch(
        event_url,
        headers=headers,
        json={
            "attendees": attendees,
            "body": {"contentType": "HTML", "content": interviewer_body},
            "showAs": "busy"
        }
    )

    # -------- ONLY CANDIDATE EMAIL --------
    frappe.sendmail(
        recipients=[interviewee_email],
        sender=Organizer_email,
        subject=f"Discussion – Azim Premji Foundation ({interview_date})",
        message=candidate_body,
        delayed=False
    )

    frappe.msgprint("✅ Event created successfully — Outlook notified automatically.")

    return {
        "event_id": event_id,
        "join_url": join_web_url,
        "meeting_id": join_meeting_id,
        "passcode": join_passcode,
        "is_online": is_online
    }
