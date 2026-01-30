import frappe
from frappe.utils.file_manager import save_file
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def generate_feedback_pdf(applicant_id):

    if not applicant_id:
        return {"status": "error", "message": "Applicant ID required"}

    # ---------------------------
    # 1️⃣ Fetch Feedbacks
    # ---------------------------
    feedbacks = frappe.get_all(
        "Philanthrophy Feedback Form",
        filters={"applicant_id": applicant_id},
        fields=[
            "name",
            "application_status",
            "interviewer_name",
            "phil_feedback",
            "feedback_date",
            "interview_status"
        ],
        order_by="creation asc"
    )

    if not feedbacks:
        return {"status": "error", "message": "No feedback found"}

    # ---------------------------
    # 2️⃣ Applicant Info
    # ---------------------------
    try:
        health_reg = frappe.get_doc("Phil Registration Form", applicant_id)
        applicant_name = health_reg.name1 or applicant_id
        role = health_reg.role or "N/A"
    except:
        applicant_name = applicant_id
        role = "N/A"

    # ---------------------------
    # 3️⃣ HTML
    # ---------------------------
    html = f"""
    <h1>Interview Feedback Summary</h1>
    <p><b>Applicant ID:</b> {applicant_id}</p>
    <p><b>Applicant Name:</b> {applicant_name}</p>
    <p><b>Role:</b> {role}</p>
    <hr>
    """

    for fb in feedbacks:
        html += f"""
        <p><b>Round:</b> {fb.application_status}</p>
        <p><b>Interviewer:</b> {fb.interviewer_name}</p>
        <p><b>Date:</b> {fb.feedback_date}</p>
        <p><b>Status:</b> {fb.interview_status}</p>
        <p><b>Feedback:</b> {fb.phil_feedback}</p>

        <hr>
        """

    # ---------------------------
    # 4️⃣ Generate PDF
    # ---------------------------
    pdf = get_pdf(html)

    filename = f"feedback_{applicant_id}.pdf"

    # ---------------------------
    # 5️⃣ Delete Old File
    # ---------------------------
    old_files = frappe.get_all(
        "File",
        filters={
            "file_name": filename,
            "attached_to_doctype": "Phil Registration Form",
            "attached_to_name": applicant_id
        },
        pluck="name"
    )

    for f in old_files:
        frappe.delete_doc("File", f, force=True)

    # ---------------------------
    # 6️⃣ Save New File
    # ---------------------------
    file_doc = save_file(
        fname=filename,
        content=pdf,
        dt="Phil Registration Form",
        dn=applicant_id,
        is_private=0
    )

    # ---------------------------
    # 7️⃣ Update Health Reg
    # ---------------------------
    health_reg = frappe.get_doc("Phil Registration Form", applicant_id)
    health_reg.feedback_form = file_doc.file_url
    health_reg.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "status": "success",
        "file_url": file_doc.file_url,
        "message": "PDF regenerated successfully"
    }
