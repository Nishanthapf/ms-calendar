import frappe, requests
from datetime import timedelta
from frappe.utils import get_datetime

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
    token_resp = requests.post(token_url, data=token_data)
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    print("DEBUG → Token OK")

    # -------------------------
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
            "startTime": {"dateTime": start_utc.isoformat(), "timeZone": "UTC"},
            "endTime": {"dateTime": end_utc.isoformat(), "timeZone": "UTC"},
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



# ----------------------------------------------------------------------------------------------------------
# Schedule Interview
# ----------------------------------------------------------------------------------------------------------

# import frappe
# import requests
# import base64
# import os
# import ast
# from datetime import datetime
# @frappe.whitelist()
# def create_interview_event(event_title,
#                            start_datetime,
#                            end_datetime,
#                            interviewer_emails,
#                            interviewee_email,
#                            room_emails,
#                            is_online,
#                            Organizer_email,
#                            Interview_round,
#                            Interviewers_namesarray,
#                            InterviewersName,
#                            Applicants_name,
#                            attachment_paths=None):

#     # ----------------------------------------
#     # Convert is_online → 0 or 1
#     # ----------------------------------------
#     try:
#         is_online = int(is_online)
#     except:
#         is_online = 0

#     # Clean organizer email
#     Organizer_email = Organizer_email.strip()
#     Template = frappe.db.get_value(
#         "Email Content for Scheduling",
#         {"interview_round":Interview_round },   # filter
#         ["feedback_url","email_content_interviewee","email_content_interviewer"]                            # field you want
#     )
#     print(Template)
#     # ----------------------------------------
#     # 1. GRAPH TOKEN
#     # ----------------------------------------
#     creds = frappe.get_single("MS Graph Credentials")
#     token_url = f"https://login.microsoftonline.com/{creds.tenant_id.strip()}/oauth2/v2.0/token"

#     tok = requests.post(token_url, data={
#         "grant_type": "client_credentials",
#         "client_id": creds.client_id.strip(),
#         "client_secret": creds.get_password("client_secret"),
#         "scope": "https://graph.microsoft.com/.default"
#     })
#     tok.raise_for_status()
#     access_token = tok.json()["access_token"]

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }

#     # ----------------------------------------
#     # 2. ATTENDEES (CLEANED)
#     # ----------------------------------------
#     interviewer_list = [i.strip() for i in interviewer_emails.split(",") if i.strip()]
#     room_list = [r.strip() for r in room_emails.split(",") if r.strip()]

#     attendees = []

#     # Rooms
#     for r in room_list:
#         attendees.append({
#             "emailAddress": {"address": r},
#             "type": "resource"
#         })

#     # Interviewers
#     for i in interviewer_list:
#         attendees.append({
#             "emailAddress": {"address": i},
#             "type": "required"
#         })

#     # ----------------------------------------
#     # 3. Friendly Dates
#     # ----------------------------------------
#     start_dt = datetime.fromisoformat(start_datetime)
#     end_dt = datetime.fromisoformat(end_datetime)

#     start_str = start_dt.strftime("%I:%M %p, %d %b %Y")
#     end_str = end_dt.strftime("%I:%M %p, %d %b %Y")
#     rooms_str = ", ".join(room_list)

#     # ----------------------------------------
#     # 4. Load Multiple Attachments (<3MB)
#     # ----------------------------------------
#     final_files = []

#     if attachment_paths:
#         try:
#             attachment_list = ast.literal_eval(attachment_paths)
#         except:
#             attachment_list = []
#     else:
#         attachment_list = []

#     for web_path in attachment_list:
#         if not web_path:
#             continue

#         rel = web_path.replace("/files/", "")
#         file_path = frappe.get_site_path("public", "files", rel)

#         if not os.path.isfile(file_path):
#             frappe.log_error("File not found: " + file_path)
#             continue

#         file_name = os.path.basename(file_path)
#         file_size = os.path.getsize(file_path)

#         if file_size > 3 * 1024 * 1024:
#             frappe.throw(f"File '{file_name}' is too large. Only <3MB allowed.")

#         with open(file_path, "rb") as f:
#             file_b64 = base64.b64encode(f.read()).decode()

#         final_files.append((file_name, file_b64))

#     # ----------------------------------------
#     # 5. Create Draft Event (Online/Offline)
#     # ----------------------------------------
#     create_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events"

#     meeting_type = "online Teams" if is_online == 1 else "offline"

#     body_html = f"""
#         <p>Dear Team,</p>
#         <p>The {meeting_type} interview has been scheduled.</p>
#         <p><b>Title:</b> {event_title}<br>
#            <b>Start:</b> {start_str}<br>
#            <b>End:</b> {end_str}<br>
#            <b>Rooms:</b> {rooms_str}</p>
#         <p><b>Attachments:</b><br>
#             {"<br>".join([f[0] for f in final_files])}
#         </p>
#         <p>Best Regards,<br>HR Team</p>
#     """

#     draft_payload = {
#         "subject": event_title,
#         "isDraft": True,
#         "isOnlineMeeting": True if is_online == 1 else False,
#         "showAs": "busy",
#         "start": {
#             "dateTime": start_datetime,
#             "timeZone": "Asia/Kolkata"
#         },
#         "end": {
#             "dateTime": end_datetime,
#             "timeZone": "Asia/Kolkata"
#         },
#         "body": {"contentType": "HTML", "content": body_html}
#     }

#     if is_online == 1:
#         draft_payload["onlineMeetingProvider"] = "teamsForBusiness"

#     d_res = requests.post(create_url, headers=headers, json=draft_payload)
#     d_res.raise_for_status()
#     event_id = d_res.json()["id"]

#     # ----------------------------------------
#     # 6. Attach All Files
#     # ----------------------------------------
#     attach_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}/attachments"

#     for fname, fb64 in final_files:
#         att_payload = {
#             "@odata.type": "#microsoft.graph.fileAttachment",
#             "name": fname,
#             "contentBytes": fb64
#         }
#         a_res = requests.post(attach_url, headers=headers, json=att_payload)
#         a_res.raise_for_status()

#     # ----------------------------------------
#     # 7. Patch Attendees
#     # ----------------------------------------
#     event_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}"

#     patch_payload = {
#         "attendees": attendees,
#         "showAs": "busy",
#         "body": {"contentType": "HTML", "content": body_html}
#     }

#     p_res = requests.patch(event_url, headers=headers, json=patch_payload)
#     p_res.raise_for_status()

#     # ----------------------------------------
#     # 8. Send Event (Only if Draft)
#     # ----------------------------------------
#     ev = requests.get(event_url, headers=headers)
#     ev.raise_for_status()

#     is_draft = ev.json().get("isDraft", False)
#     send_url = f"{event_url}/send"

#     if is_draft:
#         send_res = requests.post(send_url, headers=headers)
#         if send_res.status_code not in (200, 202):
#             frappe.log_error("Send failed but Outlook auto-sent: " + send_res.text)
#     else:
#         frappe.log_error("Skipping /send - Outlook already sent automatically.")

#     # ----------------------------------------
#     # 9. Candidate Email
#     # ----------------------------------------
#     join_url = None
#     if is_online == 1:
#         join_url = ev.json().get("onlineMeeting", {}).get("joinUrl")

#     if is_online == 1:
#         candidate_msg = f"""
#             <p>Dear Candidate,</p>
#             <p>Your online interview has been scheduled.</p>
#             <p><b>Title:</b> {event_title}<br>
#                <b>Start:</b> {start_str}</p>
#             <p><a href="{join_url}">Join Teams Meeting</a></p>
#         """
#     else:
#         candidate_msg = f"""
#             <p>Dear Candidate,</p>
#             <p>Your offline interview has been scheduled.</p>
#             <p><b>Title:</b> {event_title}<br>
#                <b>Start:</b> {start_str}<br>
#                <b>Room:</b> {rooms_str}</p>
#             <p>Please arrive on time.</p>
#         """

#     frappe.sendmail(
#         recipients=[interviewee_email],
#         subject=f"Interview Scheduled - {event_title}",
#         message=Template.email_content_interviewee
#     )

#     frappe.msgprint("✅ Event created successfully. One Outlook invite sent with real attachments.")

#     return {
#         "event_id": event_id,
#         "is_online": is_online,
#         "join_url": join_url
#     }



# import frappe
# import requests
# import base64
# import os
# import ast
# import time
# from datetime import datetime
# from ms_calendar.api.email_data_helper import get_salary_details 

# @frappe.whitelist()
# def create_interview_event(event_title,
#                            start_datetime,
#                            end_datetime,
#                            interviewer_emails,
#                            interviewee_email,
#                            room_emails,
#                            is_online,
#                            Organizer_email,
#                            Interview_round,
#                            Interviewers_namesarray,
#                            InterviewersName,
#                            Applicants_name,
#                            attachment_paths=None):

#     # ----------------------------------------
#     # Convert is_online → 0 or 1
#     # ----------------------------------------
#     try:
#         is_online = int(is_online)
#     except:
#         is_online = 0

#     Organizer_email = Organizer_email.strip()

#     # ----------------------------------------
#     # Load Template from Doctype OR use default
#     # ----------------------------------------
#     Template = frappe.db.get_value(
#         "Email Content for Scheduling",
#         {"interview_round": Interview_round},
#         ["feedback_url", "email_content_interviewee", "email_content_interviewer"]
#     )

#     default_interviewer_template = """
# <p>Hi {Interviewer_name},</p>

# <p>You are scheduled to conduct the interview for <b>{Applicants_name}</b>.</p>

# <p><b>Date:</b> {start_str}<br>
# <b>End:</b> {end_str}</p>

# {meeting_link_section}

# <p><b>Feedback Form:</b> 
# <a href="{feedback_url}" target="_blank">Click here to submit your feedback</a>
# </p>

# <p>Regards,<br>
# People Function<br>
# Azim Premji Foundation</p>
# """

#     default_interviewee_template = """
# <p>Hi {Applicants_name},</p>

# <p>Please find below the details for your interview.</p>

# <p><b>Date:</b> {start_str}<br>
# <b>End:</b> {end_str}<br>
# <b>Interview Panel:</b> {InterviewersName}</p>

# Teams Meeting Link : {meting_link}

# {meeting_link_section}

# <p>Please ensure you are available on time.</p>

# <p>Regards,<br>
# People Function<br>
# Azim Premji Foundation</p>
# """

#     if Template:
#         feedback_url, email_interviewee_template, email_interviewer_template = Template
#         email_interviewer_template = email_interviewer_template or default_interviewer_template
#         email_interviewee_template = email_interviewee_template or default_interviewee_template
#     else:
#         feedback_url = ""
#         email_interviewer_template = default_interviewer_template
#         email_interviewee_template = default_interviewee_template

#     # ----------------------------------------
#     # GRAPH TOKEN
#     # ----------------------------------------
#     creds = frappe.get_single("MS Graph Credentials")
#     token_url = f"https://login.microsoftonline.com/{creds.tenant_id.strip()}/oauth2/v2.0/token"

#     tok = requests.post(token_url, data={
#         "grant_type": "client_credentials",
#         "client_id": creds.client_id.strip(),
#         "client_secret": creds.get_password("client_secret"),
#         "scope": "https://graph.microsoft.com/.default"
#     })
#     tok.raise_for_status()
#     access_token = tok.json()["access_token"]

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }

#     # ----------------------------------------
#     # ATTENDEES
#     # ----------------------------------------
#     interviewer_list = [i.strip() for i in interviewer_emails.split(",") if i.strip()]
#     room_list = [r.strip() for r in room_emails.split(",") if r.strip()]

#     attendees = []

#     for r in room_list:
#         attendees.append({"emailAddress": {"address": r}, "type": "resource"})

#     for i in interviewer_list:
#         attendees.append({"emailAddress": {"address": i}, "type": "required"})

#     # ----------------------------------------
#     # Friendly Dates
#     # ----------------------------------------
#     start_dt = datetime.fromisoformat(start_datetime)
#     end_dt = datetime.fromisoformat(end_datetime)

#     start_str = start_dt.strftime("%I:%M %p, %d %b %Y")
#     end_str = end_dt.strftime("%I:%M %p, %d %b %Y")

#     # ----------------------------------------
#     # Attachments
#     # ----------------------------------------
#     final_files = []
#     if attachment_paths:
#         try:
#             attachment_list = ast.literal_eval(attachment_paths)
#         except:
#             attachment_list = []
#     else:
#         attachment_list = []

#     for web_path in attachment_list:
#         rel = web_path.replace("/files/", "")
#         file_path = frappe.get_site_path("public", "files", rel)

#         if os.path.isfile(file_path):
#             if os.path.getsize(file_path) <= 3 * 1024 * 1024:
#                 with open(file_path, "rb") as f:
#                     final_files.append((os.path.basename(file_path), base64.b64encode(f.read()).decode()))

#     # ----------------------------------------
#     # INITIAL EVENT BODY
#     # ----------------------------------------
#     event_body_html = (
#         email_interviewer_template
#             .replace("{Interviewer_name}", InterviewersName)
#             .replace("{Applicants_name}", Applicants_name)
#             .replace("{start_str}", start_str)
#             .replace("{end_str}", end_str)
#             .replace("{feedback_url}", feedback_url)
#             .replace("{meeting_link_section}", "")
#     )

#     # ----------------------------------------
#     # CREATE EVENT (NOT DRAFT)
#     # ----------------------------------------
#     create_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events"

#     draft_payload = {
#         "subject": event_title,
#         "isOnlineMeeting": True if is_online == 1 else False,
#         "onlineMeetingProvider": "teamsForBusiness" if is_online == 1 else None,
#         "showAs": "busy",
#         "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
#         "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
#         "body": {"contentType": "HTML", "content": event_body_html}
#     }

#     res = requests.post(create_url, headers=headers, json=draft_payload)
#     res.raise_for_status()
#     event_id = res.json()["id"]

#     # ----------------------------------------
#     # ATTACH FILES
#     # ----------------------------------------
#     attach_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}/attachments"

#     for fname, fb64 in final_files:
#         requests.post(
#             attach_url,
#             headers=headers,
#             json={
#                 "@odata.type": "#microsoft.graph.fileAttachment",
#                 "name": fname,
#                 "contentBytes": fb64
#             }
#         ).raise_for_status()

#     # ----------------------------------------
#     # SAFE TEAMS LINK RETRY (with debug)
#     # ----------------------------------------
#     event_fetch_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}"
#     join_url = ""

#     for attempt in range(5):
#         data = requests.get(event_fetch_url, headers=headers)
#         try:
#             json_data = data.json()
#         except:
#             json_data = None

#         print(f"DEBUG FETCH {attempt+1} →", json_data)

#         if json_data and "onlineMeeting" in json_data and json_data["onlineMeeting"]:
#             join_url = json_data["onlineMeeting"].get("joinUrl", "")
#             print("DEBUG JOIN URL FOUND:", join_url)

#             if join_url:
#                 break

#         time.sleep(1)

#     print("DEBUG FINAL JOIN URL:", join_url)

#     join_url = join_url or ""

#     # ----------------------------------------
#     # MEETING LINK HTML
#     # ----------------------------------------
#     meeting_link_section = ""
#     if is_online == 1 and join_url:
#         meeting_link_section = (
#             f"<p><b>Join Teams Meeting:</b> "
#             f"<a href='{join_url}' target='_blank'>Click here</a></p>"
#         )

#     # ----------------------------------------
#     # FINAL EVENT BODY FOR INTERVIEWER
#     # ----------------------------------------
#     final_event_body = (
#         email_interviewer_template
#             .replace("{Interviewer_name}", InterviewersName)
#             .replace("{Applicants_name}", Applicants_name)
#             .replace("{start_str}", start_str)
#             .replace("{end_str}", end_str)
#             .replace("{feedback_url}", feedback_url)
#             .replace("{meeting_link_section}", meeting_link_section)
#     )

#     # ----------------------------------------
#     # PATCH FINAL EVENT
#     # ----------------------------------------
#     requests.patch(
#         event_fetch_url,
#         headers=headers,
#         json={
#             "attendees": attendees,
#             "body": {"contentType": "HTML", "content": final_event_body},
#             "showAs": "busy"
#         }
#     ).raise_for_status()

#     # ----------------------------------------
#     # CANDIDATE EMAIL (NOW WITH JOIN LINK)
#     # ----------------------------------------
#     meeting_link_candidate = ""
#     if is_online == 1 and join_url:
#         meeting_link_candidate = (
#             f"<p><b>Teams Meeting Link:</b> "
#             f"<a href='{join_url}' target='_blank'>Click here to join</a></p>"
#         )

#     print("DEBUG CANDIDATE MEETING LINK HTML:", meeting_link_candidate)

#     email_interviewee_formatted = (
#         email_interviewee_template
#             .replace("{Applicants_name}", Applicants_name)
#             .replace("{start_str}", start_str)
#             .replace("{end_str}", end_str)
#             .replace("{InterviewersName}", InterviewersName)
#             .replace("{meeting_link_section}", meeting_link_candidate)
#             .replace("{meting_link}", join_url)
#     )

#     # ----------------------------------------
#     # SEND EMAILS
#     # ----------------------------------------
#     frappe.sendmail(
#         recipients=[interviewee_email],
#         subject=f"Interview Scheduled - {event_title}",
#         message=email_interviewee_formatted
#     )

#     frappe.msgprint("✅ Event created successfully. Outlook invite sent.")

#     return {
#         "event_id": event_id,
#         "is_online": is_online,
#         "join_url": join_url
#     }

import frappe
import requests
import base64
import os
import ast
import time
from datetime import datetime
from ms_calendar.api.email_data_helper import get_salary_details 

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
                           Interviewers_namesarray,
                           InterviewersName,
                           Applicants_name,
                           application_id,
                           attachment_paths=None):

    # ----------------------------------------
    # Convert is_online → int
    # ----------------------------------------
    try:
        is_online = int(is_online)
    except:
        is_online = 0

    Organizer_email = Organizer_email.strip()

    # ----------------------------------------
    # Load Template from Doctype OR fallback
    # ----------------------------------------
    Template = frappe.db.get_value(
        "Email Content for Scheduling",
        {"interview_round": Interview_round},
        ["feedback_url", "email_content_interviewee", "email_content_interviewer"]
    )

    default_interviewer_template = """
<p>Hi {Interviewer_name},</p>

<p>You are scheduled to conduct the interview for <b>{Applicants_name}</b>.</p>

<p><b>Date:</b> {start_str}<br>
<b>End:</b> {end_str}</p>

{meeting_link_section}

<p><b>Feedback Form:</b> 
<a href="{feedback_url}" target="_blank">Click here to submit your feedback</a>
</p>

<p>Regards,<br>
People Function<br>
Azim Premji Foundation</p>
"""

    default_interviewee_template = """
<p>Hi {Applicants_name},</p>

<p>Please find below the details for your interview.</p>

<p><b>Date:</b> {start_str}<br>
<b>End:</b> {end_str}<br>
<b>Interview Panel:</b> {InterviewersName}</p>

Teams Meeting Link : {meting_link}

{meeting_link_section}

<p>Please ensure you are available on time.</p>

<p>Regards,<br>
People Function<br>
Azim Premji Foundation</p>
"""

    if Template:
        _feedback_url, email_interviewee_template, email_interviewer_template = Template
        email_interviewer_template = email_interviewer_template or default_interviewer_template
        email_interviewee_template = email_interviewee_template or default_interviewee_template
    else:
        email_interviewer_template = default_interviewer_template
        email_interviewee_template = default_interviewee_template

    # ----------------------------------------
    # FEEDBACK URL BASED ON ROUND (FIXED)
    # ----------------------------------------
    round_no = str(Interview_round).lower().strip()

    if "1" in round_no:
        form_key = "one"
    else:
        form_key = "two"

    feedback_url = (
        f"https://careers.frappe.cloud/feedback-form-{form_key}/new"
        f"?app_id={application_id}&applicant_name={Applicants_name}"
    )

    # ----------------------------------------
    # GRAPH TOKEN
    # ----------------------------------------
    creds = frappe.get_single("MS Graph Credentials")
    token_url = f"https://login.microsoftonline.com/{creds.tenant_id.strip()}/oauth2/v2.0/token"

    tok = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": creds.client_id.strip(),
        "client_secret": creds.get_password("client_secret"),
        "scope": "https://graph.microsoft.com/.default"
    })
    tok.raise_for_status()
    access_token = tok.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # ----------------------------------------
    # ATTENDEES (rooms + interviewers)
    # ----------------------------------------
    interviewer_list = [i.strip() for i in interviewer_emails.split(",") if i.strip()]
    room_list = [r.strip() for r in room_emails.split(",") if r.strip()]

    attendees = []

    for r in room_list:
        attendees.append({"emailAddress": {"address": r}, "type": "resource"})

    for i in interviewer_list:
        attendees.append({"emailAddress": {"address": i}, "type": "required"})

    # ----------------------------------------
    # Friendly Dates
    # ----------------------------------------
    start_dt = datetime.fromisoformat(start_datetime)
    end_dt = datetime.fromisoformat(end_datetime)

    start_str = start_dt.strftime("%I:%M %p, %d %b %Y")
    end_str = end_dt.strftime("%I:%M %p, %d %b %Y")

    # ----------------------------------------
    # READ ATTACHMENTS
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
        rel = web_path.replace("/files/", "")
        file_path = frappe.get_site_path("public", "files", rel)

        if os.path.isfile(file_path):
            if os.path.getsize(file_path) <= 3 * 1024 * 1024:
                with open(file_path, "rb") as f:
                    final_files.append((os.path.basename(file_path), base64.b64encode(f.read()).decode()))

    # ----------------------------------------
    # INITIAL EVENT BODY
    # ----------------------------------------
    event_body_html = (
        email_interviewer_template
            .replace("{Interviewer_name}", InterviewersName)
            .replace("{Applicants_name}", Applicants_name)
            .replace("{start_str}", start_str)
            .replace("{end_str}", end_str)
            .replace("{feedback_url}", feedback_url)
            .replace("{meeting_link_section}", "")
    )

    # ----------------------------------------
    # CREATE EVENT IN OUTLOOK
    # ----------------------------------------
    create_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events"

    draft_payload = {
        "subject": event_title,
        "isOnlineMeeting": True if is_online == 1 else False,
        "onlineMeetingProvider": "teamsForBusiness" if is_online == 1 else None,
        "showAs": "busy",
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        "body": {"contentType": "HTML", "content": event_body_html}
    }

    res = requests.post(create_url, headers=headers, json=draft_payload)
    res.raise_for_status()
    event_id = res.json()["id"]

    # ----------------------------------------
    # ATTACH FILES
    # ----------------------------------------
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
    # RETRY SAFE FETCH FOR TEAMS JOIN URL
    # ----------------------------------------
    event_fetch_url = f"https://graph.microsoft.com/v1.0/users/{Organizer_email}/events/{event_id}"
    join_url = ""

    for attempt in range(5):
        data = requests.get(event_fetch_url, headers=headers)

        try:
            json_data = data.json()
        except:
            json_data = None

        print(f"DEBUG FETCH {attempt+1} →", json_data)

        if json_data and "onlineMeeting" in json_data and json_data["onlineMeeting"]:
            join_url = json_data["onlineMeeting"].get("joinUrl", "")
            if join_url:
                break

        time.sleep(1)

    join_url = join_url or ""

    # ----------------------------------------
    # MEETING LINK HTML
    # ----------------------------------------
    meeting_link_section = ""
    if is_online == 1 and join_url:
        meeting_link_section = (
            f"<p><b>Join Teams Meeting:</b> "
            f"<a href='{join_url}' target='_blank'>Click here</a></p>"
        )

    # ----------------------------------------
    # FINAL PATCH WITH ATTENDEES + LINK
    # ----------------------------------------
    final_event_body = (
        email_interviewer_template
            .replace("{Interviewer_name}", InterviewersName)
            .replace("{Applicants_name}", Applicants_name)
            .replace("{start_str}", start_str)
            .replace("{end_str}", end_str)
            .replace("{feedback_url}", feedback_url)
            .replace("{meeting_link_section}", meeting_link_section)
    )

    requests.patch(
        event_fetch_url,
        headers=headers,
        json={
            "attendees": attendees,
            "body": {"contentType": "HTML", "content": final_event_body},
            "showAs": "busy"
        }
    ).raise_for_status()

    # ----------------------------------------
    # EMAIL TO CANDIDATE
    # ----------------------------------------
    meeting_link_candidate = ""
    if is_online == 1 and join_url:
        meeting_link_candidate = (
            f"<p><b>Teams Meeting Link:</b> "
            f"<a href='{join_url}' target='_blank'>Click here to join</a></p>"
        )

    email_interviewee_formatted = (
        email_interviewee_template
            .replace("{Applicants_name}", Applicants_name)
            .replace("{start_str}", start_str)
            .replace("{end_str}", end_str)
            .replace("{InterviewersName}", InterviewersName)
            .replace("{meeting_link_section}", meeting_link_candidate)
            .replace("{meting_link}", join_url)
    )

    # ----------------------------------------
    # SEND EMAIL TO CANDIDATE
    # ----------------------------------------
    frappe.sendmail(
        recipients=[interviewee_email],
        subject=f"Interview Scheduled - {event_title}",
        message=email_interviewee_formatted
    )

    frappe.msgprint("✅ Event created successfully. Outlook invite sent.")

    return {
        "event_id": event_id,
        "is_online": is_online,
        "join_url": join_url
    }
