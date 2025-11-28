import random
import string
import frappe
import json
from frappe.utils import get_datetime

@frappe.whitelist(allow_guest=True)
def test_result_api():
    try:
        # ---------------------------
        # 1️⃣ Robust API KEY VALIDATION
        # ---------------------------
        def get_request_header(name):
            # Try frappe.request.headers (case-insensitive)
            try:
                headers = {k.lower(): v for k, v in (frappe.request.headers or {}).items()}
                val = headers.get(name.lower())
                if val:
                    
                    return val
            except Exception:
                pass
            # Fallback to environment variable (HTTP_<NAME_UPPER_WITH_UNDERSCORES>)
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

        # ---------------------------
        # 2️⃣ READ JSON BODY
        # ---------------------------
        raw = frappe.request.data
        if not raw:
            frappe.local.response.http_status_code = 400
            return {
                "status": "error",
                "http_status": 400,
                "message": "Empty request body"
            }

        try:
            payload = json.loads(raw)
        except Exception:
            frappe.local.response.http_status_code = 400
            return {
                "status": "error",
                "http_status": 400,
                "message": "Invalid JSON body"
            }

        records = payload.get("data")
        if not records:
            frappe.local.response.http_status_code = 400
            return {
                "status": "error",
                "http_status": 400,
                "message": "'data' array missing"
            }

        inserted = 0

        # Convert ISO datetime to MySQL format
        def fix_datetime(dt):
            if not dt:
                return None
            try:
                return get_datetime(dt).strftime("%Y-%m-%d %H:%M:%S")
            except:
                return None

        # ---------------------------
        # 3️⃣ PROCESS EACH RECORD
        # ---------------------------
        for item in records:

            candidate_id = item.get("candidateId")
            percentage = item.get("overAllPercentageScore")
            attempt_id = item.get("attemptId")
            assessment_id = item.get("assessmentId")
            attempt_status = item.get("attempt_status")
            report_url = item.get("TnReport")
            score = item.get("score")
            max_score = item.get("maxScore")
            total_questions = item.get("totalQuestion")
            total_attempted = item.get("totalAttempted")
            updated_at = fix_datetime(item.get("updatedAt"))
            created_at = fix_datetime(item.get("createdAt"))

            if not candidate_id:
                frappe.local.response.http_status_code = 400
                return {
                    "status": "error",
                    "http_status": 400,
                    "message": "candidateId missing"
                }

            # --------------------------------------------------------------
            # INSERT TEST RESULT
            # --------------------------------------------------------------
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
            inserted += 1

            # --------------------------------------------------------------
            # UPDATE SCHOLARSHIP FORM
            # --------------------------------------------------------------
            srf = frappe.db.get_value(
                "Scholarship Recruitment Form",
                {"name": candidate_id},
                ["name", "applicant_name", "email", "srt_mail"],
                as_dict=True
            )

            if srf:
                try:
                    passed = (percentage is not None and float(percentage) >= 50)
                except:
                    passed = False

                status = "Recruiter Round" if passed else "Recruiter Reject"

                # Update SRF
                srf_doc = frappe.get_doc("Scholarship Recruitment Form", srf.name)
                srf_doc.application_status = status
                srf_doc.save(ignore_permissions=True)

                applicant_name = srf.applicant_name or "Applicant"
                applicant_email = srf.email
                # safe get for sender: if field missing or empty, use fallback sender
                SenderEmail = None
                try:
                    SenderEmail = srf.get("srt_mail") or None
                except Exception:
                    SenderEmail = None
                if not SenderEmail:
                    SenderEmail = "noreply@azimpremjifoundation.org"

                # --------------------------------------------------------------
                # EMAIL TEMPLATES
                # --------------------------------------------------------------
                pass_email_html = f"""
                <html>
                <body>
                <p>Dear {applicant_name},</p>
                <p>You have cleared the online test. Please upload your updated CV.</p>
                <a href="https://careers.frappe.cloud/cv-submission/new?app_id={candidate_id}&applicant_name={applicant_name}">
                    Upload your CV
                </a>
                </body>
                </html>
                """

                fail_email_html = f"""
                <html>
                <body>
                <p>Dear {applicant_name},</p>
                <p>Thank you for your interest. We are unable to proceed further.</p>
                </body>
                </html>
                """

                # --------------------------------------------------------------
                # SEND EMAIL
                # --------------------------------------------------------------
                if applicant_email:
                    try:
                        if passed:
                            frappe.sendmail(
                                sender=SenderEmail,
                                recipients=[applicant_email],
                                subject="Next Step – Upload Your CV",
                                message=pass_email_html,
                                delayed=False,
                                reference_doctype="Scholarship Recruitment Form",
                                reference_name=candidate_id
                            )
                        else:
                            frappe.sendmail(
                                sender=SenderEmail,
                                recipients=[applicant_email],
                                subject="Update on Your Scholarship Application",
                                message=fail_email_html,
                                delayed=False,
                                reference_doctype="Scholarship Recruitment Form",
                                reference_name=candidate_id
                            )
                    except Exception as mail_exc:
                        frappe.log_error(f"Mail error: {mail_exc}", "MERIT_TRAC_MAIL_ERROR")

        frappe.db.commit()

        # ---------------------------
        # SUCCESS RESPONSE
        # ---------------------------
        frappe.local.response.http_status_code = 200
        random_code = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(16))

        return {
            "status": 200,
            "message": "Data inserted, SRF updated, emails sent",
            "data":[]
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MERIT_TRAC_API_ERROR")
        frappe.local.response.http_status_code = 500
        return {
            "status": 500,
            "message": str(e)
        }
