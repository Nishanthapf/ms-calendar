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


# import frappe
# import requests
# from frappe.utils import get_datetime
# from datetime import datetime, timezone, timedelta
# import time  

# @frappe.whitelist()
# def get_org_rooms_and_availability(interview_date, start_time, end_time):
#     """
#     Fetch all rooms and their availability for the given date and time range.
#     Uses system timezone detected automatically.
#     """

#     # -------------------------
#     # STEP 1: Fetch MS Graph Credentials
#     # -------------------------
#     credentials = frappe.get_single("MS Graph Credentials")
#     tenant_id = credentials.tenant_id
#     client_id = credentials.client_id
#     client_secret = credentials.get_password("client_secret")

#     # -------------------------
#     # STEP 2: Get Access Token
#     # -------------------------
#     token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
#     token_data = {
#         "grant_type": "client_credentials",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "scope": "https://graph.microsoft.com/.default"
#     }
#     token_resp = requests.post(token_url, data=token_data)
#     token_resp.raise_for_status()
#     access_token = token_resp.json().get("access_token")

#     headers = {"Authorization": f"Bearer {access_token}"}

#     # -------------------------
#     # STEP 3: Fetch All Rooms
#     # -------------------------
#     rooms_url = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"
#     rooms_resp = requests.get(rooms_url, headers=headers)
#     rooms_resp.raise_for_status()
#     rooms = rooms_resp.json().get("value", [])
#     room_emails = [r["emailAddress"] for r in rooms if "emailAddress" in r]

#     # -------------------------
#     # STEP 4: Build DateTime Range (convert to UTC)
#     # -------------------------
#     # detect system timezone offset
#     offset_sec = -time.timezone if (time.localtime().tm_isdst == 0) else -time.altzone
#     system_tz = timezone(timedelta(seconds=offset_sec))

#     start_dt_local = get_datetime(f"{interview_date} {start_time}")
#     end_dt_local = get_datetime(f"{interview_date} {end_time}")

#     # Localize and convert to UTC
#     start_dt_utc = start_dt_local.replace(tzinfo=system_tz).astimezone(timezone.utc)
#     end_dt_utc = end_dt_local.replace(tzinfo=system_tz).astimezone(timezone.utc)

#     # -------------------------
#     # STEP 5: Fetch Availability
#     # -------------------------
#     schedule_url = "https://graph.microsoft.com/v1.0/users/health.fellowship@azimpremjifoundation.org/calendar/getSchedule"
#     body = {
#         "schedules": room_emails,
#         "startTime": {"dateTime": start_dt_utc.isoformat(), "timeZone": "UTC"},
#         "endTime": {"dateTime": end_dt_utc.isoformat(), "timeZone": "UTC"},
#         "availabilityViewInterval": 30
#     }
#     schedule_resp = requests.post(
#         schedule_url,
#         headers={**headers, "Content-Type": "application/json"},
#         json=body
#     )
#     schedule_resp.raise_for_status()
#     availability_data = schedule_resp.json().get("value", [])

#     # -------------------------
#     # STEP 6: Merge Rooms + Availability
#     # -------------------------
#     availability_map = {a.get("scheduleId"): a.get("scheduleItems", []) for a in availability_data}
#     rooms_list = []

#     for room in rooms:
#         email = room.get("emailAddress")
#         busy_slots = availability_map.get(email, [])
#         is_available = True

#         for slot in busy_slots:
#             slot_start = datetime.fromisoformat(slot["start"]["dateTime"]).replace(tzinfo=timezone.utc)
#             slot_end = datetime.fromisoformat(slot["end"]["dateTime"]).replace(tzinfo=timezone.utc)

#             if not (slot_end <= start_dt_utc or slot_start >= end_dt_utc):
#                 is_available = False
#                 break

#         rooms_list.append({
#             "name": room.get("displayName"),
#             "email": email,
#             "capacity": room.get("capacity", ""),
#             "availability": busy_slots,
#             "is_available": is_available
#         })

#     return {"rooms": rooms_list}

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


@frappe.whitelist()
def get_member_objects(user_email):
    import frappe
    import requests

    # -------------------------------
    # Credentials
    # -------------------------------
    creds = frappe.get_single("MS Graph Credentials")
    tenant = creds.tenant_id
    client = creds.client_id
    secret = creds.get_password("client_secret")

    # -------------------------------
    # Token
    # -------------------------------
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

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # -------------------------------
    # getMemberObjects
    # -------------------------------
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/getMemberObjects"

    body = {"securityEnabledOnly": False}

    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()

    data = resp.json().get("value", [])

    return {
        "user": user_email,
        "member_objects": data
    }
@frappe.whitelist()
def get_all_members():
    import frappe
    import requests

    # -------------------------------
    # Load Credentials
    # -------------------------------
    creds = frappe.get_single("MS Graph Credentials")
    tenant = creds.tenant_id
    client = creds.client_id
    secret = creds.get_password("client_secret")

    # -------------------------------
    # Get Access Token
    # -------------------------------
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client,
        "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default"
    }

    resp = requests.post(token_url, data=token_data)
    resp.raise_for_status()
    access_token = resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    # -------------------------------
    # Fetch ALL users (NO FILTER -> ALWAYS WORKS)
    # -------------------------------
    all_users = []
    url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,userType"

    page = 1
    while url:
        print(f"DEBUG → Users Page {page}")

        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        all_users.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        page += 1

    # -------------------------------
    # Filter ONLY Members
    # -------------------------------
    members = [u for u in all_users if u.get("userType") == "Member"]

    print("DEBUG → Total Members Found =", len(members))

    return {
        "total_members": len(members),
        "members": members
    }

@frappe.whitelist()
def get_all_rooms():
    import frappe
    import requests

    # -------------------------------
    # Load Credentials
    # -------------------------------
    creds = frappe.get_single("MS Graph Credentials")
    tenant = creds.tenant_id
    client = creds.client_id
    secret = creds.get_password("client_secret")

    # -------------------------------
    # Get Access Token
    # -------------------------------
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client,
        "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default"
    }

    resp = requests.post(token_url, data=token_data)
    resp.raise_for_status()
    access_token = resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    # -------------------------------
    # Fetch ALL users (NO FILTERS) → Always works
    # -------------------------------
    all_users = []
    url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,userType,mailNickname"

    page = 1
    while url:
        print(f"DEBUG → Users Page {page}")

        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        all_users.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        page += 1

    # -------------------------------
    # Detect ROOM mailboxes
    # PRIMARY CHECK → userType == Room
    # FALLBACK CHECK → name/nickname contains "room"
    # -------------------------------
    rooms = []

    for u in all_users:
        name = (u.get("displayName") or "").lower()
        nick = (u.get("mailNickname") or "").lower()
        utype = u.get("userType")
        mail = u.get("mail")

        if not mail:
            continue

        # Main rule
        if utype == "Room":
            rooms.append(u)
            continue

        # Extra fallback (some older tenants do not set userType correctly)
        if "room" in name or "room" in nick or "mr" in name:
            rooms.append(u)
            continue

    print("DEBUG → TOTAL ROOMS FOUND =", len(rooms))

    return {
        "total_rooms": len(rooms),
        "rooms": rooms,
    }

@frappe.whitelist()
def get_total_rooms():
    import frappe
    import requests

    creds = frappe.get_single("MS Graph Credentials")
    tenant = creds.tenant_id
    client = creds.client_id
    secret = creds.get_password("client_secret")

    # ---------------------------
    # Get Access Token
    # ---------------------------
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client,
        "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default"
    }

    resp = requests.post(token_url, data=token_data)
    resp.raise_for_status()
    access_token = resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    # ---------------------------
    # Fetch ALL users (no filters)
    # ---------------------------
    rooms = []
    url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,mail,userType,mailNickname"

    while url:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()

        for u in data.get("value", []):
            name = u.get("displayName", "") or ""
            nickname = u.get("mailNickname", "") or ""
            utype = u.get("userType", "")

            # ---------------------------
            # Detect Room Mailboxes
            # ---------------------------
            if utype == "Room":
                rooms.append(u)
            elif "room" in nickname.lower():
                rooms.append(u)
            elif "room" in name.lower() or "mr" in name.lower():
                rooms.append(u)

        url = data.get("@odata.nextLink")

    return {
        "total_rooms": len(rooms),
        "rooms": rooms
    }

# def get_all_rooms(access_token):
    rooms = []
    headers = {"Authorization": f"Bearer {access_token}"}

    url = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"

    page = 1
    while url:
        print(f"DEBUG → Fetching Rooms PAGE {page}")

        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        page_rooms = data.get("value", [])
        print(f"DEBUG → PAGE {page} returned {len(page_rooms)} rooms")

        rooms.extend(page_rooms)

        url = data.get("@odata.nextLink")  # follow next page
        page += 1

    print("DEBUG → FINAL ROOM COUNT =", len(rooms))
    return rooms

# import frappe
# import requests
# import uuid
# from datetime import datetime
# from requests.exceptions import RequestException
# import os
# import ast

# @frappe.whitelist()
# def create_interview_event(event_title, start_datetime, end_datetime, interviewer_emails, interviewee_email,  room_emails, attachment_paths=None):
#     # --- 1. Get credentials ---
#     print("DEBUG: Received attachment_paths:", attachment_paths)
#     frappe.log_error(message=f"Received attachment_paths: {attachment_paths}", title="Attachment Debug")
#     print("DEBUG: Received room_emails:", room_emails)
#     frappe.log_error(message=f"Received room_emails: {room_emails}", title="Room Email Debug")

#     try:
#         credentials = frappe.get_single("MS Graph Credentials")
#         tenant_id = credentials.tenant_id.strip()
#         client_id = credentials.client_id.strip()
#         client_secret = credentials.get_password("client_secret")
#     except Exception as e:
#         frappe.throw(f"Could not fetch MS Graph Credentials: {e}")

#     # --- 2. Get access token ---
#     token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
#     token_data = {
#         "grant_type": "client_credentials",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "scope": "https://graph.microsoft.com/.default"
#     }

#     try:
#         token_resp = requests.post(token_url, data=token_data, timeout=10)
#         token_resp.raise_for_status()
#         token_json = token_resp.json()
#         access_token = token_json.get("access_token")
#         if not access_token:
#             frappe.throw(f"Failed to fetch access token: {token_json}")
#     except RequestException as e:
#         frappe.throw(f"Token request failed. Check server internet/DNS connection: {e}")

#      # --- 3. Prepare rooms ---
#     room_list = [r.strip() for r in room_emails.split(",") if r.strip()]
#     room_list_text = ", ".join(room_list)

#     start_str = datetime.fromisoformat(start_datetime).strftime("%I:%M %p, %d %b %Y")
#     end_str = datetime.fromisoformat(end_datetime).strftime("%I:%M %p, %d %b %Y")

#     # --- 4. Create event in organizer calendar ---
#     organizer_email = "health.fellowship@azimpremjifoundation.org"
#     url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events?sendUpdates=none"
#     headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

#     calendar_body_content = f"""
#         <p>Dear HR,</p>
#         <p>The interview has been scheduled.</p>
#         <p><b>Title:</b> {event_title}<br>
#            <b>Start:</b> {start_str}<br>
#            <b>End:</b> {end_str}<br>
#            <b>Rooms:</b> {room_list_text}</p>
#         <p>Please follow up with interviewers and candidate.</p>
#         <p>Best regards,<br>HR Team</p>
#     """
#     # Prepare room attendees for MS Graph
#     room_attendees = []
#     if room_emails:
#         room_list = [r.strip() for r in room_emails.split(",") if r.strip()]
#         for room in room_list:
#             room_attendees.append({
#                 "emailAddress": {"address": room, "name": room},
#                 "type": "resource"  # important: type resource = room booking
#             })

#     # Prepare interviewer attendees (optional: if you want them to appear in calendar)
#     interviewer_list = [email.strip() for email in interviewer_emails.split(",") if email.strip()]
#     interviewer_attendees = [
#         {"emailAddress": {"address": intr, "name": intr}, "type": "required"}
#         for intr in interviewer_list
#     ]

#     # Merge attendees
#     all_attendees = room_attendees

#     frappe.log_error(message=f"Room attendees payload: {room_attendees}", title="Room Debug")
#     print("DEBUG: Room attendees payload:", room_attendees)
#     event_body = {
#         "subject": event_title,
#         "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
#         "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
#         "location": {"displayName": "Microsoft Teams Meeting"},
#         "responseRequested": False,
#         "allowNewTimeProposals": False,
#         "isOnlineMeeting": True,
#         "onlineMeetingProvider": "teamsForBusiness",
#         "transactionId": str(uuid.uuid4()),
#         "body": {"contentType": "HTML", "content": calendar_body_content},
#         "attendees": all_attendees  # <-- this blocks the rooms automatically

#     }

#     try:
#         resp = requests.post(url, headers=headers, json=event_body, timeout=10)
#         resp.raise_for_status()
#         event = resp.json()
#         join_url = event.get("onlineMeeting", {}).get("joinUrl")
#     except RequestException as e:
#         frappe.throw(f"Graph API event creation failed: {e}")

#     for intr in interviewer_list:
#         intr_url = f"https://graph.microsoft.com/v1.0/users/{intr}/events?sendUpdates=none"

#         # Copy event body but remove self-attendance
#         intr_event_body = event_body.copy()
#         intr_event_body["attendees"] = room_attendees  # only rooms, not interviewers

#         try:
#             intr_resp = requests.post(intr_url, headers=headers, json=intr_event_body, timeout=10)
#             intr_resp.raise_for_status()
#             frappe.log_error(message=f"Event created in {intr}'s calendar", title="Interviewer Calendar")
#         except RequestException as e:
#             frappe.log_error(message=f"Failed to create event in {intr}'s calendar: {e}", title="Interviewer Calendar Error")

#     # --- 5. Prepare attachment for Frappe email ---

#     if attachment_paths and isinstance(attachment_paths, str):
#         try:
#             attachment_paths = ast.literal_eval(attachment_paths)
#         except Exception as e:
#             frappe.log_error(message=f"Failed to parse attachment_paths: {attachment_paths}\nError: {e}", title="Attachment Debug")
#             attachment_paths = []
#     attachments = []
#     if attachment_paths:
#         for path in attachment_paths:
#             if not path:
#                 continue

#             if path.startswith("/files/"):
#                 relative_path = path[len("/files/"):]
#                 file_path = frappe.get_site_path("public", "files", relative_path)
#             else:
#                 file_path = path

#             if os.path.isfile(file_path):
#                 with open(file_path, "rb") as f:
#                     fcontent = f.read()
#                 attachments.append({"fname": os.path.basename(file_path), "fcontent": fcontent})
#             else:
#                 frappe.log_error(message=f"Skipped non-file path: {file_path}", title="Attachment Debug")


#     # --- 6. Send emails to interviewers ---
#     interviewer_list = [email.strip() for email in interviewer_emails.split(",") if email.strip()]
#     for intr_email in interviewer_list:  # <-- remove enumerate
#         email_body = f"""
#             <p>Dear Interviewer ,</p>
#             <p>You are scheduled to conduct an interview.</p>
#             <p><b>Title:</b> {event_title}<br>
#             <b>Start:</b> {start_str}<br>
#             <b>End:</b> {end_str}<br>
#             <b>Rooms:</b> {room_list_text}<br>
#             <b>Join Link:</b> <a href="{join_url}">Join Teams Meeting</a></p>
#             <p>Please review candidate details before the meeting.</p>
#             <p>Best regards,<br>HR Team</p>
#         """
#     frappe.sendmail(
#         recipients=[intr_email],
#         subject=f"Interview Scheduled - {event_title}",
#         message=email_body,
#         now=True,
#         attachments=attachments
#     )

#     # --- 7. Send email to candidate ---
#     candidate_body = f"""
#         <p>Dear Candidate,</p>
#         <p>Your interview has been scheduled.</p>
#         <p><b>Title:</b> {event_title}<br>
#            <b>Start:</b> {start_str}<br>
#            <b>End:</b> {end_str}<br>
#            <b>Rooms:</b> {room_list_text}<br>
#            <b>Join Link:</b> <a href="{join_url}">Join Teams Meeting</a></p>
#         <p>Please ensure you are in a quiet place with stable internet connectivity.</p>
#         <p>Best regards,<br>HR Team</p>
#     """
#     frappe.sendmail(
#         recipients=[interviewee_email],
#         subject=f"Interview Scheduled - {event_title}",
#         message=candidate_body,
#         now=True,
#     )

#     frappe.msgprint("✅ Interview scheduled. Custom emails sent.")
#     return {"event_id": event.get("id"), "join_url": join_url}







# import frappe
# import requests
# import uuid
# from datetime import datetime
# from requests.exceptions import RequestException
# import os
# import ast

# @frappe.whitelist()
# def create_interview_event(event_title, start_datetime, end_datetime,
#                            interviewer_emails, interviewee_email,
#                            room_emails, attachment_paths=None):

#     # -----------------------------
#     # 1. Fetch MS Graph Credentials
#     # -----------------------------
#     try:
#         credentials = frappe.get_single("MS Graph Credentials")
#         tenant_id = credentials.tenant_id.strip()
#         client_id = credentials.client_id.strip()
#         client_secret = credentials.get_password("client_secret")
#     except Exception as e:
#         frappe.throw(f"Could not fetch MS Graph Credentials: {e}")

#     # -----------------------------
#     # 2. Generate Access Token
#     # -----------------------------
#     token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
#     token_data = {
#         "grant_type": "client_credentials",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "scope": "https://graph.microsoft.com/.default"
#     }

#     try:
#         token_resp = requests.post(token_url, data=token_data, timeout=10)
#         token_resp.raise_for_status()
#         access_token = token_resp.json().get("access_token")
#         if not access_token:
#             frappe.throw("Failed to fetch access token")
#     except RequestException as e:
#         frappe.throw(f"Token request failed: {e}")

#     # -----------------------------
#     # 3. Prepare Data
#     # -----------------------------
#     organizer_email = "health.fellowship@azimpremjifoundation.org"

#     # Rooms
#     room_list = [r.strip() for r in room_emails.split(",") if r.strip()]
#     room_list_text = ", ".join(room_list)

#     # Interviewers (will not be added to event)
#     interviewer_list = [i.strip() for i in interviewer_emails.split(",") if i.strip()]

#     # Email-friendly time format
#     start_str = datetime.fromisoformat(start_datetime).strftime("%I:%M %p, %d %b %Y")
#     end_str = datetime.fromisoformat(end_datetime).strftime("%I:%M %p, %d %b %Y")

#     # Prepare only room attendees (NO interviewers)
#     room_attendees = []
#     for room in room_list:
#         room_attendees.append({
#             "emailAddress": {"address": room, "name": room},
#             "type": "resource"       # Room booking
#         })

#     # -----------------------------
#     # 4. Create ONE event (NO attendee default emails)
#     # -----------------------------
#     url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events?sendUpdates=none"

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }

#     calendar_body_content = f"""
#         <p>Interview Scheduled</p>
#         <p><b>Title:</b> {event_title}<br>
#         <b>Start:</b> {start_str}<br>
#         <b>End:</b> {end_str}<br>
#         <b>Rooms:</b> {room_list_text}</p>
#     """

#     event_body = {
#         "subject": event_title,
#         "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
#         "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
#         "location": {"displayName": "Microsoft Teams Meeting"},

#         "responseRequested": False,
#         "allowNewTimeProposals": False,
#         "isReminderOn": False,
#         "hideAttendees": True,

#         "isOnlineMeeting": True,
#         "onlineMeetingProvider": "teamsForBusiness",

#         "transactionId": str(uuid.uuid4()),
#         "body": {"contentType": "HTML", "content": calendar_body_content},

#         "attendees": room_attendees      # ONLY rooms added
#     }

#     try:
#         resp = requests.post(url, headers=headers, json=event_body, timeout=10)
#         resp.raise_for_status()
#         event = resp.json()
#         join_url = event.get("onlineMeeting", {}).get("joinUrl")
#     except RequestException as e:
#         frappe.throw(f"Graph API event creation failed: {resp.text}")

#     # -----------------------------
#     # 5. Parse attachments
#     # -----------------------------
#     if attachment_paths and isinstance(attachment_paths, str):
#         try:
#             attachment_paths = ast.literal_eval(attachment_paths)
#         except:
#             attachment_paths = []

#     attachments = []
#     for path in attachment_paths or []:
#         if path.startswith("/files/"):
#             file_path = frappe.get_site_path("public", "files", path[7:])
#         else:
#             file_path = path

#         if os.path.isfile(file_path):
#             with open(file_path, "rb") as f:
#                 attachments.append({
#                     "fname": os.path.basename(file_path),
#                     "fcontent": f.read()
#                 })

#     # -----------------------------
#     # 6. Send custom email → Interviewers
#     # -----------------------------
#     for intr in interviewer_list:
#         email_body = f"""
#             <p>Dear Interviewer,</p>
#             <p>You are scheduled to conduct an interview.</p>
#             <p><b>Title:</b> {event_title}<br>
#             <b>Start:</b> {start_str}<br>
#             <b>End:</b> {end_str}<br>
#             <b>Rooms:</b> {room_list_text}<br>
#             <b>Join Link:</b> <a href="{join_url}">Join Meeting</a></p>
#         """
#         frappe.sendmail(
#             recipients=[intr],
#             subject=f"Interview Scheduled - {event_title}",
#             message=email_body,
#             now=True,
#             attachments=attachments
#         )

#     # -----------------------------
#     # 7. Send custom email → Candidate
#     # -----------------------------
#     candidate_body = f"""
#         <p>Dear Candidate,</p>
#         <p>Your interview is scheduled.</p>
#         <p><b>Title:</b> {event_title}<br>
#            <b>Start:</b> {start_str}<br>
#            <b>End:</b> {end_str}<br>
#            <b>Join Link:</b> <a href="{join_url}">Join Meeting</a></p>
#     """

#     frappe.sendmail(
#         recipients=[interviewee_email],
#         subject=f"Interview Scheduled - {event_title}",
#         message=candidate_body,
#         now=True,
#     )

#     return {"event_id": event.get("id"), "join_url": join_url}

























# import frappe
# import requests
# import uuid


# @frappe.whitelist()
# def create_interview_event(event_title, start_datetime, end_datetime,
#                            interviewer_emails, interviewee_email,
#                            room_emails):

#     # ---------------------------
#     # 1. Credentials
#     # ---------------------------
#     creds = frappe.get_single("MS Graph Credentials")
#     tenant_id = creds.tenant_id.strip()
#     client_id = creds.client_id.strip()
#     client_secret = creds.get_password("client_secret")

#     # ---------------------------
#     # 2. Access Token
#     # ---------------------------
#     token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
#     data = {
#         "grant_type": "client_credentials",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "scope": "https://graph.microsoft.com/.default"
#     }
#     access_token = requests.post(token_url, data=data).json()["access_token"]

#     organizer_email = "tech4socialsector@azimpremjifoundation.org"
#     headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

#     # ---------------------------
#     # Prepare attendees
#     # ---------------------------
#     room_list = [r.strip() for r in room_emails.split(",") if r.strip()]
#     interviewer_list = [i.strip() for i in interviewer_emails.split(",") if i.strip()]

#     room_attendees = [
#         {"emailAddress": {"address": room}, "type": "resource"}
#         for room in room_list
#     ]

#     # ============================================================
#     # 3. CREATE MAIN EVENT (ONLY ROOMS) → Creates Teams Meeting
#     # ============================================================
#     create_url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events?sendUpdates=all"

#     main_body = {
#         "subject": event_title,
#         "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
#         "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},

#         "isOnlineMeeting": True,
#         "onlineMeetingProvider": "teamsForBusiness",

#         "attendees": room_attendees,
#         "responseRequested": False
#     }

#     created_event = requests.post(create_url, headers=headers, json=main_body).json()
#     event_id = created_event["id"]

#     # extract generated online meeting info (joinUrl, conference IDs, etc)
#     online_meeting = created_event.get("onlineMeeting", {})
#     join_url = online_meeting.get("joinUrl")

#     # ============================================================
#     # 4. CREATE TEAMS MEETING COPIES ON INTERVIEWER CALENDARS
#     # ============================================================
#     # Each gets SAME Teams meeting → "Join" button shows
#     # And NO Outlook invite is sent (attendees = [])
#     for intr in interviewer_list:

#         interviewer_body = {
#             "subject": event_title + " (Interview)",
#             "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
#             "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
#             "showAs": "busy",

#             # Key: real teams meeting without triggering invite
#             "isOnlineMeeting": True,
#             "onlineMeetingProvider": "teamsForBusiness",
#             "onlineMeeting": online_meeting,     # copy the same meeting object

#             "attendees": [],                    # NO ATTENDEES → NO INVITE
#             "responseRequested": False,
#             "isReminderOn": False
#         }

#         requests.post(
#             f"https://graph.microsoft.com/v1.0/users/{intr}/events",
#             headers=headers,
#             json=interviewer_body
#         )

#     # ============================================================
#     # 5. SEND CUSTOM EMAILS (NO OUTLOOK INVITES)
#     # ============================================================
#     for intr in interviewer_list:
#         frappe.sendmail(
#             recipients=[intr],
#             subject=f"Interview Scheduled - {event_title}",
#             message=f"""
#                 <p>Dear Interviewer,</p>
#                 Your interview has been scheduled.<br><br>
#                 <b>Teams Meeting Link:</b><br>
#                 <a href="{join_url}">Join Meeting</a>
#             """,
#             now=True
#         )

#     frappe.sendmail(
#         recipients=[interviewee_email],
#         subject=f"Interview Scheduled - {event_title}",
#         message=f"""
#             <p>Dear Candidate,</p>
#             Your interview has been scheduled.<br>
#             <b>Teams Link:</b> <a href="{join_url}">Join Meeting</a>
#         """,
#         now=True
#     )

#     return {
#         "event_id": event_id,
#         "join_url": join_url
#     }



import frappe
import requests
import uuid


@frappe.whitelist()
def create_interview_event(event_title, start_datetime, end_datetime,
                           interviewer_emails, interviewee_email,
                           room_emails):

    # ---------------------------
    # 1. Credentials
    # ---------------------------
    creds = frappe.get_single("MS Graph Credentials")
    tenant_id = creds.tenant_id.strip()
    client_id = creds.client_id.strip()
    client_secret = creds.get_password("client_secret")

    # ---------------------------
    # 2. Access Token
    # ---------------------------
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }
    access_token = requests.post(token_url, data=data).json()["access_token"]

    organizer_email = "tech4socialsector@azimpremjifoundation.org"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # ---------------------------
    # Parse Lists
    # ---------------------------
    room_list = [r.strip() for r in room_emails.split(",") if r.strip()]
    interviewer_list = [i.strip() for i in interviewer_emails.split(",") if i.strip()]

    room_attendees = [
        {"emailAddress": {"address": room}, "type": "resource"}
        for room in room_list
    ]

    # ============================================================
    # 3. CREATE MAIN EVENT (Organizer + Rooms → Teams meeting)
    # ============================================================
    create_url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events?sendUpdates=all"

    main_event_body = {
        "subject": event_title,
        "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        "attendees": room_attendees,
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness",
        "responseRequested": False
    }

    created_event = requests.post(create_url, headers=headers, json=main_event_body).json()
    event_id = created_event["id"]

    # ============================================================
    # 4. FETCH THE REAL FULL TEAMS MEETING OBJECT (RELIABLE)
    # ============================================================
    fetch_meeting_url = (
        f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events/{event_id}/onlineMeeting"
    )

    meeting_data = requests.get(fetch_meeting_url, headers=headers).json()

    # ---------------------------
    # 🔥 DEBUG: Print + Log full Teams meeting JSON
    # ---------------------------
    frappe.log_error(str(meeting_data), "FULL_ONLINE_MEETING_DEBUG")
    print("===== FULL ONLINE MEETING OBJECT =====")
    print(meeting_data)
    # ---------------------------

    full_online_meeting = meeting_data
    join_url = meeting_data.get("joinUrl")

    # Safety fallback:
    if not join_url:
        join_url = created_event.get("onlineMeeting", {}).get("joinUrl")

    # ============================================================
    # 5. CREATE INTERVIEWER EVENTS — still wrong join button for now
    # ============================================================
    for intr in interviewer_list:

        interviewer_event_body = {
            "subject": f"{event_title} (Interview)",
            "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
            "showAs": "busy",

            # Temporary: This is where we will fix after debugging
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness",
            "onlineMeeting": full_online_meeting,
            "onlineMeetingUrl": join_url,

            "attendees": [],
            "responseRequested": False,
            "isReminderOn": False
        }

        requests.post(
            f"https://graph.microsoft.com/v1.0/users/{intr}/events",
            headers=headers,
            json=interviewer_event_body
        )

    # ============================================================
    # 6. SEND CUSTOM EMAILS
    # ============================================================
    for intr in interviewer_list:
        frappe.sendmail(
            recipients=[intr],
            subject=f"Interview Scheduled - {event_title}",
            message=f"""
                Dear Interviewer,<br><br>
                Your interview is scheduled.<br>
                <b>Join Meeting:</b> <a href="{join_url}">Join</a><br>
            """,
            now=True
        )

    frappe.sendmail(
        recipients=[interviewee_email],
        subject="Interview Meeting Link",
        message=f"""
            Dear Candidate,<br>
            <b>Join Meeting:</b> <a href="{join_url}">Join</a>
        """,
        now=True
    )

    return {
        "event_id": event_id,
        "join_url": join_url
    }
