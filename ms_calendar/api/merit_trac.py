# import datetime
# import random
# import string
# import frappe
# import json
# from frappe.utils import get_datetime

# @frappe.whitelist(allow_guest=True)
# def test_result_api():
#     try:
#         # ---------------------------
#         # 1️⃣ Robust API KEY VALIDATION
#         # ---------------------------
#         def get_request_header(name):
#             # Try frappe.request.headers (case-insensitive)
#             try:
#                 headers = {k.lower(): v for k, v in (frappe.request.headers or {}).items()}
#                 val = headers.get(name.lower())
#                 if val:
                    
#                     return val
#             except Exception:
#                 pass
#             # Fallback to environment variable (HTTP_<NAME_UPPER_WITH_UNDERSCORES>)
#             env_key = "HTTP_" + name.upper().replace("-", "_")
#             return frappe.request.environ.get(env_key)

#         api_key = get_request_header("Patner-key")
#         EXPECTED_KEY = "ToNnhB5chOh23fWz"

#         if not api_key or api_key != EXPECTED_KEY:
#             frappe.local.response.http_status_code = 401
#             return {
#                 "status": "error",
#                 "http_status": 401,
#                 "message": "Unauthorized: Invalid Patner Key"
#             }

#         # ---------------------------
#         # 2️⃣ READ JSON BODY
#         # ---------------------------
#         raw = frappe.request.data
#         if not raw:
#             frappe.local.response.http_status_code = 400
#             return {
#                 "status": "error",
#                 "http_status": 400,
#                 "message": "Empty request body"
#             }

#         try:
#             payload = json.loads(raw)
#         except Exception:
#             frappe.local.response.http_status_code = 400
#             return {
#                 "status": "error",
#                 "http_status": 400,
#                 "message": "Invalid JSON body"
#             }

#         records = payload.get("data")
#         if not records:
#             frappe.local.response.http_status_code = 400
#             return {
#                 "status": "error",
#                 "http_status": 400,
#                 "message": "'data' array missing"
#             }

#         inserted = 0

#         # Convert ISO datetime to MySQL format
#         def fix_datetime(dt):
#             if not dt:
#                 return None
#             try:
#                 return get_datetime(dt).strftime("%Y-%m-%d %H:%M:%S")
#             except:
#                 return None

#         # ---------------------------
#         # 3️⃣ PROCESS EACH RECORD
#         # ---------------------------
#         for item in records:

#             candidate_id = item.get("candidateId")
#             percentage = item.get("overAllPercentageScore")
#             attempt_id = item.get("attemptId")
#             assessment_id = item.get("assessmentId")
#             attempt_status = item.get("attempt_status")
#             report_url = item.get("TnReport")
#             score = item.get("score")
#             max_score = item.get("maxScore")
#             total_questions = item.get("totalQuestion")
#             total_attempted = item.get("totalAttempted")
#             updated_at = fix_datetime(item.get("updatedAt"))
#             created_at = fix_datetime(item.get("createdAt"))

#             if not candidate_id:
#                 frappe.local.response.http_status_code = 400
#                 return {
#                     "status": "error",
#                     "http_status": 400,
#                     "message": "candidateId missing"
#                 }

#             # --------------------------------------------------------------
#             # INSERT TEST RESULT
#             # --------------------------------------------------------------
#             test_doc = frappe.get_doc({
#                 "doctype": "MeritTrac Test Result",
#                 "applicant_id": candidate_id,
#                 "score_percentile": percentage,
#                 "attempt_id": attempt_id,
#                 "assessment_id": assessment_id,
#                 "attempt_status": attempt_status,
#                 "score_report": report_url,
#                 "total_score": score,
#                 "max_score": max_score,
#                 "total_questions": total_questions,
#                 "total_attempted": total_attempted,
#                 "updated_at": updated_at,
#                 "created_at": created_at
#             })

#             test_doc.insert(ignore_permissions=True)
#             inserted += 1

#             # --------------------------------------------------------------
#             # UPDATE SCHOLARSHIP FORM
#             # --------------------------------------------------------------
#             srf = frappe.db.get_value(
#                 "Scholarship Recruitment Form",
#                 {"name": candidate_id},
#                 ["name", "applicant_name", "email", "srt_mail"],
#                 as_dict=True
#             )

#             if srf:
#                 try:
#                     passed = (percentage is not None and float(percentage) >= 50)
#                 except:
#                     passed = False

#                 status = "Recruiter Round" if passed else "Recruiter Reject"

#                 # Update SRF
#                 srf_doc = frappe.get_doc("Scholarship Recruitment Form", srf.name)
#                 srf_doc.application_status = status
#                 srf_doc.save(ignore_permissions=True)

#                 applicant_name = srf.applicant_name or "Applicant"
#                 applicant_email = srf.email
#                 # safe get for sender: if field missing or empty, use fallback sender
#                 SenderEmail = None
#                 try:
#                     SenderEmail = srf.get("srt_mail") or None
#                 except Exception:
#                     SenderEmail = None
#                 if not SenderEmail:
#                     SenderEmail = "noreply@azimpremjifoundation.org"

#                 # --------------------------------------------------------------
#                 # EMAIL TEMPLATES
#                 # --------------------------------------------------------------
#                 # pass_email_html = f"""
#                 # <html>
#                 # <body>
#                 # <p>Dear {applicant_name},</p>
#                 # <p>You have cleared the online test. Please upload your updated CV.</p>
#                 # <a href="https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}">
#                 #     Upload your CV
#                 # </a>
#                 # </body>
#                 # </html>
#                 # """
                # pass_email_html = f"""
                #         <!doctype html>
                #         <html lang="en">
                #         <head>
                #         <meta charset="UTF-8">
                #         <meta name="viewport" content="width=device-width,initial-scale=1">
                #         </head>

                #         <body style="margin:0; padding:0; font-family:Arial, Helvetica, sans-serif; background:#ffffff; color:#000;">

                #         <table width="100%" cellpadding="0" cellspacing="0" border="0" style="padding:20px;">
                #             <tr>
                #             <td style="text-align:left;">
                #                 <p>Dear <strong>{applicant_name}</strong>,</p>

                #                 <p>
                #                 You have cleared the online test, and we request you to upload your updated CV (PDF or Word) for the next steps.
                #                 </p>

                #                 <p>Please click the button below to upload your CV:</p>

                #                 <p style="margin:20px 0;">
                #                 <a href="https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}"
                #                     style="background:#0078D4; color:#ffffff; padding:8px 14px; text-decoration:none; border-radius:4px; font-weight:500; font-size:14px; display:inline-block;">
                #                     Upload your CV
                #                 </a>
                #                 </p>

                #                 <p>
                #                 <strong>Accepted formats:</strong> .pdf, .doc, .docx<br>
                #                 <strong>Maximum size:</strong> 5 MB
                #                 </p>

                #                 <p>Our team will reach out to you soon.</p>

                #                 <p>
                #                 Regards,<br>
                #                 <strong>People Function</strong><br>
                #                 Azim Premji Foundation
                #                 </p>

                #                 <p style="font-size:13px; margin-top:28px;">
                #                 If the button doesn't work, use the link below:<br>
                #                 <a href="https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}">
                #                     https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}
                #                 </a>
                #                 </p>

                #             </td>
                #             </tr>
                #         </table>

                #         </body>
                #         </html>
                #         """


#                 # fail_email_html = f"""
#                 # <html>
#                 # <body>
#                 # <p>Dear {applicant_name},</p>
#                 # <p>Thank you for your interest. We are unable to proceed further.</p>
#                 # </body>
#                 # </html>
#                 # """
#                 fail_email_html = f"""
#                     <!DOCTYPE html>
#                     <html>
#                     <head>
#                     <meta charset="UTF-8">
#                     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#                     </head>

#                     <body style="margin:0; padding:20px; background:#ffffff; font-family:'Segoe UI', sans-serif; color:#333; line-height:1.6;">

#                     <p style="font-size:16px; margin:0 0 20px 0;">
#                     Dear {applicant_name},
#                     </p>

#                     <p style="font-size:16px; margin:0 0 20px 0;">
#                     Thank you for your interest in the opportunities with the Azim Premji Scholarship Initiative.
#                     We appreciate the time and effort you have invested in exploring an opportunity with us.
#                     </p>

#                     <p style="font-size:16px; margin:0 0 20px 0;">
#                     After careful consideration of your candidature, unfortunately, we will not be able to
#                     take your application forward at this point of time.
#                     </p>

#                     <p style="font-size:16px; margin:0 0 25px 0;">
#                     We would like to thank you for your time, and we wish you the very best!
#                     </p>

#                     <p style="font-size:16px; margin:0 0 40px 0;">
#                     Regards,<br>
#                     People Function<br>
#                     Azim Premji Foundation
#                     </p>

#                     </body>
#                     </html>
#                     """

#                 # --------------------------------------------------------------
#                 # SEND EMAIL
#                 # --------------------------------------------------------------
#                 if applicant_email:
#                     try:
#                         if passed:
#                             frappe.sendmail(
#                                 sender=SenderEmail,
#                                 recipients=[applicant_email],
#                                 subject=f"Azim Premji Scholarship – Your Application, {applicant_name}",
#                                 message=pass_email_html,
#                                 delayed=False,
#                                 reference_doctype="Scholarship Recruitment Form",
#                                 reference_name=candidate_id
#                             )
#                         else:
#                                 send_time = datetime.now() + datetime.timedelta(days=3)
#                                 frappe.enqueue(
#                                     "frappe.sendmail",
#                                     queue="default",
#                                     enqueue_at=send_time,
#                                     sender=SenderEmail,
#                                     recipients=[applicant_email],
#                                     subject=f"Azim Premji Scholarship – Your Application, {applicant_name}",
#                                     message=fail_email_html,
#                                     delayed=False,
#                                     reference_doctype="Scholarship Recruitment Form",
#                                     reference_name=candidate_id
#                                 )
#                     except Exception as mail_exc:
#                         frappe.log_error(f"Mail error: {mail_exc}", "MERIT_TRAC_MAIL_ERROR")

#         frappe.db.commit()

#         # ---------------------------
#         # SUCCESS RESPONSE
#         # ---------------------------
#         frappe.local.response.http_status_code = 200
#         random_code = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(16))

#         return {
#             "status": 200,
#             "message": "Data inserted, SRF updated, emails sent",
#             "data":[]
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "MERIT_TRAC_API_ERROR")
#         frappe.local.response.http_status_code = 500
#         return {
#             "status": 500,
#             "message": str(e)
#         }


import frappe
import json
from frappe.utils import get_datetime
from datetime import datetime, timedelta


@frappe.whitelist(allow_guest=True)
def test_result_api():
    try:
        # ------------------------------------------------------------
        # 1️⃣ API KEY VALIDATION (robust)
        # ------------------------------------------------------------
        def get_request_header(name):
            try:
                headers = {k.lower(): v for k, v in (frappe.request.headers or {}).items()}
                if name.lower() in headers:
                    return headers[name.lower()]
            except Exception:
                pass
            env_key = "HTTP_" + name.upper().replace("-", "_")
            return frappe.request.environ.get(env_key)

        api_key = get_request_header("Patner-key")
        EXPECTED_KEY = "ToNnhB5chOh23fWz"
        if not api_key or api_key != EXPECTED_KEY:
            frappe.local.response.http_status_code = 401
            return {
                "status": "error",
                "http_status": 401,
                "message": "Unauthorized: Invalid Patner Key"
            }

        # ------------------------------------------------------------
        # 2️⃣ READ JSON BODY
        # ------------------------------------------------------------
        raw = frappe.request.data
        if not raw:
            frappe.local.response.http_status_code = 400
            return {"status": "error", "http_status": 400, "message": "Empty request body"}

        try:
            payload = json.loads(raw)
        except Exception:
            frappe.local.response.http_status_code = 400
            return {"status": "error", "http_status": 400, "message": "Invalid JSON body"}

        # ------------------------------------------------------------
        # 3️⃣ Accept either top-level object or {"data": {...}}
        # ------------------------------------------------------------
        if isinstance(payload, dict) and "data" in payload and isinstance(payload.get("data"), dict):
            item = payload.get("data")
        elif isinstance(payload, dict) and payload.get("candidateId"):
            # support callers that send object directly (no "data" wrapper)
            item = payload
        else:
            frappe.local.response.http_status_code = 400
            return {
                "status": "error",
                "http_status": 400,
                "message": "Request must be a JSON object with candidateId (either top-level or inside 'data')"
            }

        # ------------------------------------------------------------
        # 4️⃣ field extractor + datetime helper
        # ------------------------------------------------------------
        def fix_datetime(dt):
            if not dt:
                return None
            try:
                return get_datetime(dt).strftime("%Y-%m-%d %H:%M:%S")
            except:
                return None

        candidate_id     = item.get("candidateId")
        percentage       = item.get("overAllPercentageScore")
        attempt_id       = item.get("attemptId")
        assessment_id    = item.get("assessmentId")
        attempt_status   = item.get("attempt_status")
        report_url       = item.get("TnReport")
        score            = item.get("score")
        max_score        = item.get("maxScore")
        total_questions  = item.get("totalQuestion")
        total_attempted  = item.get("totalAttempted")
        updated_at       = fix_datetime(item.get("updatedAt"))
        created_at       = fix_datetime(item.get("createdAt"))

        if not candidate_id:
            frappe.local.response.http_status_code = 400
            return {"status": "error", "http_status": 400, "message": "candidateId missing"}

        # ------------------------------------------------------------
        # 5️⃣ INSERT MeritTrac Test Result
        # ------------------------------------------------------------
        test_doc = frappe.get_doc({
            "doctype": "MeritTrac Test Result",
            "applicant_id": candidate_id,
            "score_percentile": percentage,
            "attempt_id": attempt_id,
            "assessment_id": assessment_id,
            "attempt_status": attempt_status,
            "score_report": report_url,
            "total_score": score,
            "max_score": max_score,
            "total_questions": total_questions,
            "total_attempted": total_attempted,
            "updated_at": updated_at,
            "created_at": created_at
        })
        test_doc.insert(ignore_permissions=True)

        # ------------------------------------------------------------
        # 6️⃣ UPDATE SCHOLARSHIP RECRUITMENT FORM
        # ------------------------------------------------------------
        # Request full_name_as_per_aadhar too (fall back to applicant_name)
        srf = frappe.db.get_value(
            "Scholarship Recruitment Form",
            {"name": candidate_id},
            ["name", "applicant_name", "full_name_as_per_aadhar", "email", "srt_mail"],
            as_dict=True
        )

        if not srf:
            frappe.db.commit()
            frappe.local.response.http_status_code = 200
            return {
                "status": 200,
                "http_status": 200,
                "message": "Data inserted (No SRF found for candidate)",
                "data": []
            }

        # determine pass/fail
        try:
            passed = (percentage is not None and float(percentage) >= 50)
        except:
            passed = False
        status = "Recruiter Round" if passed else "Test Reject"

        # update SRF doc
        srf_name = srf.get("name")
        srf_doc = frappe.get_doc("Scholarship Recruitment Form", srf_name)
        srf_doc.application_status = status
        srf_doc.save(ignore_permissions=True)

        # applicant details (prefer full_name_as_per_aadhar)
        applicant_name = srf.get("full_name_as_per_aadhar") or  "Applicant"
        applicant_email = srf.get("email")

        # sender: safe lookup, fallback to a single fixed sender
        SenderEmail = srf.get("srt_mail") if srf.get("srt_mail") else "tech4socialsector@azimpremjifoundation.org"

        # ------------------------------------------------------------
        # 7️⃣ EMAIL TEMPLATES
        # ------------------------------------------------------------
        pass_email_html = f"""
     <!doctype html>
                        <html lang="en">
                        <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width,initial-scale=1">
                        </head>

                        <body style="margin:0; padding:0; font-family:Arial, Helvetica, sans-serif; background:#ffffff; color:#000;">

                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="padding:20px;">
                            <tr>
                            <td style="text-align:left;">
                                <p>Dear <strong>{applicant_name}</strong>,</p>

                                <p>
                                You have cleared the online test, and we request you to upload your updated CV (PDF or Word) for the next steps.
                                </p>

                                <p>Please click the button below to upload your CV:</p>

                                <p style="margin:20px 0;">
                                <a href="https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}"
                                    style="background:#0078D4; color:#ffffff; padding:8px 14px; text-decoration:none; border-radius:4px; font-weight:500; font-size:14px; display:inline-block;">
                                    Upload your CV
                                </a>
                                </p>

                                <p>
                                <strong>Accepted formats:</strong> .pdf, .doc, .docx<br>
                                <strong>Maximum size:</strong> 5 MB
                                </p>

                                <p>Our team will reach out to you soon.</p>

                                <p>
                                Regards,<br>
                                <strong>People Function</strong><br>
                                Azim Premji Foundation
                                </p>

                                <p style="font-size:13px; margin-top:28px;">
                                If the button doesn't work, use the link below:<br>
                                <a href="https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}">
                                    https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}
                                </a>
                                </p>

                            </td>
                            </tr>
                        </table>

                        </body>
                        </html>
"""

        fail_email_html = f"""
 <!DOCTYPE html>
                    <html>
                    <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    </head>

                    <body style="margin:0; padding:20px; background:#ffffff; font-family:'Segoe UI', sans-serif; color:#333; line-height:1.6;">

                    <p style="font-size:16px; margin:0 0 20px 0;">
                    Dear {applicant_name},
                    </p>

                    <p style="font-size:16px; margin:0 0 20px 0;">
                    Thank you for your interest in the opportunities with the Azim Premji Scholarship Initiative.
                    We appreciate the time and effort you have invested in exploring an opportunity with us.
                    </p>

                    <p style="font-size:16px; margin:0 0 20px 0;">
                    After careful consideration of your candidature, unfortunately, we will not be able to
                    take your application forward at this point of time.
                    </p>

                    <p style="font-size:16px; margin:0 0 25px 0;">
                    We would like to thank you for your time, and we wish you the very best!
                    </p>

                    <p style="font-size:16px; margin:0 0 40px 0;">
                    Regards,<br>
                    People Function<br>
                    Azim Premji Foundation
                    </p>

                    </body>
                    </html>
"""

        # ------------------------------------------------------------
        # 8️⃣ SEND EMAILS (PASS immediate / FAIL immediate )
        # ------------------------------------------------------------
        if applicant_email:
            try:
                if passed:
                    # send now
                    frappe.sendmail(
                        sender=SenderEmail,
                        recipients=[applicant_email],
                        subject=f"Azim Premji Scholarship – Your Application, {applicant_name}",
                        message=pass_email_html,
                        delayed=False,
                        reference_doctype="Scholarship Recruitment Form",
                        reference_name=candidate_id
                    )
                else:
                   # Send FAIL email immediately
                    frappe.sendmail(
                        sender=SenderEmail,
                        recipients=[applicant_email],
                        subject=f"Azim Premji Scholarship – Your Application, {applicant_name}",
                        message=fail_email_html,
                        delayed=False,
                        reference_doctype="Scholarship Recruitment Form",
                        reference_name=candidate_id
                    )
                  
            except Exception as mail_exc:
                frappe.log_error(f"Mail error: {mail_exc}", "MERIT_TRAC_MAIL_ERROR")

        frappe.db.commit()

        # ------------------------------------------------------------
        # SUCCESS RESPONSE
        # ------------------------------------------------------------
        frappe.local.response.http_status_code = 200
        return {
            "status": 200,
            "http_status": 200,
            "message": "Data inserted, SRF updated, email processed",
            "data": [SenderEmail]
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MERIT_TRAC_API_ERROR")
        frappe.local.response.http_status_code = 500
        return {"status": 500, "http_status": 500, "message": str(e)}
