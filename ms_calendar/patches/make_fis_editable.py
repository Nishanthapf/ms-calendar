import frappe


def execute():
    if frappe.db.exists("DocType", "Field Interview Schedule"):
        frappe.db.set_value("DocType", "Field Interview Schedule", "custom", 1)
        frappe.db.commit()
