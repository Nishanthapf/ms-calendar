import frappe
 
def get_context(context):
    context.no_cache = 1
 
    jobs = frappe.get_all(
        "Job Opening",
        filters={"status": "Open", "publish": 1},
        fields=[
            "name", "job_title", "unit", "department", "location",
            "employment_type", "designation", "experience",
            "route", "posted_on", "vacancies"
        ],
        order_by="posted_on desc"
    )
 
    context.jobs = jobs
    context.total = len(jobs)
 
    # Load filter options from ALL job openings so every possible value appears
    all_jobs = frappe.get_all(
        "Job Opening",
        fields=["unit", "department", "location", "employment_type", "designation", "experience"]
    )
 
    context.units = sorted({j.unit for j in all_jobs if j.unit})
    context.departments = sorted({j.department for j in all_jobs if j.department})
    context.locations = sorted({j.location for j in all_jobs if j.location})
    context.employment_types = sorted({j.employment_type for j in all_jobs if j.employment_type})
    context.designations = sorted({j.designation for j in all_jobs if j.designation})
    context.experiences = sorted({j.experience for j in all_jobs if j.experience})