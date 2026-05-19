import frappe
from frappe.utils import formatdate


def after_insert(doc, method=None):
    if not doc.applicant_id:
        return

    try:
        percentage = float(doc.percentage or 0)
    except (ValueError, TypeError):
        percentage = 0

    passed = percentage >= 40
    status = "Test Select" if passed else "Test Reject"

    # Update application status on the registration form
    frappe.db.set_value(
        "Field Registration Form", doc.applicant_id, "application_status", status
    )

    # Use fields already on the Field Offline Result doc
    candidate_name = doc.applicant_name or "Candidate"
    candidate_email = doc.email_id
    job_title = doc.job_title or "Position"
    test_date = formatdate(doc.creation, "dd MMMM yyyy")

    if not candidate_email:
        frappe.log_error(
            f"No email found for applicant {doc.applicant_id}", "Test Result Email"
        )
        return

    # ---------------- TEST SELECT MAIL ----------------
    if passed:

        subject = f"Congratulations – Shortlisted for Next Round at Azim Premji Foundation {job_title} Position"

        message = f"""
        <p>Dear {candidate_name},</p>
 
        <p>
        Thank you for your interest in exploring career opportunities with Azim Premji Foundation.
        </p>
 
        <p>
        We are pleased to inform you that you have successfully cleared the written test conducted on {test_date}.
        Congratulations on reaching the next stage of our selection process!
        </p>
 
        <p>
        To process your application for the next stage of selection process, we request you to log in to your candidate portal and fill in the candidate application form under the “Personal Information” section.
        You can also track the progress of your application through this portal.
        </p>
 
        <p>
        🔗 Portal Link:
        <a href="https://careers.frappe.cloud/login#login">
        https://careers.frappe.cloud/login#login
        </a>
        </p>
 
        <p>
        Once you fill the candidate application form, a member of our recruitment team will get in touch with you via your registered email ID or contact number within the next two weeks to share details about the next steps.
        </p>
 
        <p><b>📩 State Recruitment Contacts</b></p>
 
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
            <tr>
                <th>State</th>
                <th>Email ID</th>
            </tr>
            <tr>
                <td>Chhattisgarh</td>
                <td>recruitment.chhattisgarh@azimpremjifoundation.org</td>
            </tr>
            <tr>
                <td>Karnataka</td>
                <td>recruitment.karnataka@azimpremjifoundation.org</td>
            </tr>
            <tr>
                <td>Madhya Pradesh</td>
                <td>recruitment.madhyapradesh@azimpremjifoundation.org</td>
            </tr>
            <tr>
                <td>Rajasthan</td>
                <td>recruitment.rajasthan@azimpremjifoundation.org</td>
            </tr>
            <tr>
                <td>Telangana</td>
                <td>recruitment.telangana@azimpremjifoundation.org</td>
            </tr>
            <tr>
                <td>Uttarakhand</td>
                <td>recruitment.uttarakhand@azimpremjifoundation.org</td>
            </tr>
            <tr>
                <td>Jharkhand</td>
                <td>recruitment.jharkhand@azimpremjifoundation.org</td>
            </tr>
        </table>
 
        <p>
        For more information about our work and the recruitment process, please visit our website:
        <br>
        🌐 <a href="https://www.azimpremjifoundation.org">
        www.azimpremjifoundation.org
        </a>
        </p>
 
        <p>
        We appreciate your effort and wish you the very best for the next phase.
        </p>
 
        <p>
        Warm regards,<br><br>
        Recruitment Team<br>
        Azim Premji Foundation
        </p>
        """

    # ---------------- TEST REJECT MAIL ----------------
    else:

        subject = (
            f"Result of Written Test for {job_title} Position – Azim Premji Foundation"
        )

        message = f"""
        <p>Dear {candidate_name},</p>
 
        <p>
        Thank you for taking the time to appear for the written test conducted by Azim Premji Foundation on {test_date}.
        </p>
 
        <p>
        After a careful review of your performance, we regret to inform you that you have not been shortlisted for the next stage of the selection process.
        </p>
 
        <p>
        Please note that the test results are final, and we will be unable to consider any requests for re-evaluation.
        However, we encourage you to reapply for relevant opportunities after a period of one year from the date of this test.
        </p>
 
        <p>
        For any further queries, you may write to us at:
        recruitment@azimpremjifoundation.org
        </p>
 
        <p>
        We appreciate your interest in the Foundation and wish you the very best in your future endeavors.
        </p>
 
        <p>
        Warm regards,<br><br>
        Recruitment Team<br>
        Azim Premji Foundation
        </p>
        """

    # Send Email
    frappe.sendmail(recipients=[candidate_email], subject=subject, message=message)
