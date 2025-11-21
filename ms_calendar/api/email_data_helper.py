import frappe

@frappe.whitelist()
def get_salary_details(application_id):
    result = frappe.db.get_value(
        "Scholarship Recruitment Form",
        {"name": application_id},
        ["total_years_of_experience", "current_ctc", "expected_ctc"],
        as_dict=True
    )
    return result
