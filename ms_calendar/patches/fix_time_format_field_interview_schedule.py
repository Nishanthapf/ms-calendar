import frappe


def execute():
	"""Convert start_time/end_time from '07:00 AM' format to '07:00:00' so the
	Time column migration does not raise OperationalError 1292."""
	for col in ("start_time", "end_time"):
		frappe.db.sql(f"""
			UPDATE `tabField Interview Schedule`
			SET `{col}` = TIME(STR_TO_DATE(`{col}`, '%h:%i %p'))
			WHERE `{col}` REGEXP '^[0-9]{{1,2}}:[0-9]{{2}} [AP]M$'
		""")
	frappe.db.commit()
