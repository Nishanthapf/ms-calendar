frappe.pages['field-dashboard'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Field Recruitment Dashboard',
		single_column: true
	});

	const STATUS_CARDS = [
		{ status: 'New Applicant', label: 'NEW APPLICANT', color: '#7c3aed' },
		{ status: 'On Hold', label: 'ON HOLD', color: '#6b7280' },
		{ status: 'Blocklisted', label: 'BLOCKLISTED', color: '#dc2626' },
		{ status: 'CV Shortlist', label: 'CV SHORTLIST', color: '#2563eb' },
		{ status: 'CV Reject', label: 'CV REJECT', color: '#d97706' },
		{ status: 'Test Process', label: 'TEST PROCESS', color: '#9333ea' },
		{ status: 'Test Select', label: 'TEST SELECT', color: '#0891b2' },
		{ status: 'Test Reject', label: 'TEST REJECT', color: '#be123c' },
		{ status: 'Recruiter Round', label: 'RECRUITER ROUND', color: '#15803d' },
		{ status: 'Recruiter Reject', label: 'RECRUITER REJECT', color: '#b45309' },
		{ status: 'Round One', label: 'ROUND ONE', color: '#16a34a' },
		{ status: 'Round 1 Reject', label: 'ROUND 1 REJECT', color: '#db2777' },
		{ status: 'Round Two', label: 'ROUND TWO', color: '#2563eb' },
		{ status: 'Round 2 Reject', label: 'ROUND 2 REJECT', color: '#ea580c' },
		{ status: 'Round Three', label: 'ROUND THREE', color: '#7c3aed' },
		{ status: 'Round 3 Reject', label: 'ROUND 3 REJECT', color: '#dc2626' },
		{ status: 'Document Collection', label: 'DOCUMENT COLLECTION', color: '#0d9488' },
		{ status: 'Offer', label: 'OFFER', color: '#ca8a04' },
	];

	$(wrapper).find('.page-content').append(`
        <style>
            .recruit-filters {
                display: flex;
                gap: 12px;
                padding: 16px 20px 4px;
            }
            .recruit-filters select {
                flex: 1;
                padding: 7px 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 13px;
                color: #111827;
                background: #fff;
                cursor: pointer;
            }
            .recruit-filters select:focus {
                outline: none;
                border-color: #2563eb;
            }
            .recruit-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                padding: 16px 20px 20px;
            }
            .recruit-card {
                background: #fff;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 18px 20px;
                cursor: pointer;
                transition: box-shadow 0.25s, transform 0.25s, border-color 0.25s;
                position: relative;
                overflow: hidden;
            }
            .recruit-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 3px;
                background: var(--card-color, #7c3aed);
                transform: scaleX(0);
                transform-origin: left;
                transition: transform 0.3s ease;
            }
            .recruit-card:hover::before { transform: scaleX(1); }
            .recruit-card:hover {
                box-shadow: 0 6px 20px rgba(0,0,0,0.12);
                transform: translateY(-2px);
            }
            .recruit-card .card-count {
                animation: countPop 0.4s ease;
            }
            @keyframes countPop {
                0%   { transform: scale(0.7); opacity: 0; }
                70%  { transform: scale(1.15); }
                100% { transform: scale(1);   opacity: 1; }
            }
            .recruit-card .card-label {
                font-size: 11px;
                font-weight: 600;
                color: #6b7280;
                letter-spacing: 0.05em;
                margin-bottom: 8px;
            }
            .recruit-card .card-count {
                font-size: 32px;
                font-weight: 700;
            }
        </style>
        <div class="recruit-filters">
            <select id="filter-role"><option value="">All Roles</option></select>
            <select id="filter-department"><option value="">All Departments</option></select>
            <select id="filter-location"><option value="">All Locations</option></select>
        </div>
        <div class="recruit-grid" id="recruit-grid"></div>
    `);

	const $grid = $(wrapper).find('#recruit-grid');
	const $roleFilter = $(wrapper).find('#filter-role');
	const $deptFilter = $(wrapper).find('#filter-department');
	const $locFilter = $(wrapper).find('#filter-location');

	// Render cards
	STATUS_CARDS.forEach(function (cfg) {
		$grid.append(`
            <div class="recruit-card" data-status="${cfg.status}" style="--card-color:${cfg.color}">
                <div class="card-label">${cfg.label}</div>
                <div class="card-count" style="color:${cfg.color}" id="count-${frappe.scrub(cfg.status)}">…</div>
            </div>
        `);
	});

	// Populate Role dropdown from Field Role doctype
	frappe.call({
		method: 'frappe.client.get_list',
		args: { doctype: 'Field Role', fields: ['name'], limit_page_length: 0 },
		callback: function (r) {
			(r.message || []).sort(function (a, b) { return a.name.localeCompare(b.name); })
				.forEach(function (d) {
					$roleFilter.append(`<option value="${d.name}">${d.name}</option>`);
				});
		}
	});

	// Populate Department dropdown from Field Department doctype
	frappe.call({
		method: 'frappe.client.get_list',
		args: { doctype: 'Field Department', fields: ['name'], limit_page_length: 0 },
		callback: function (r) {
			(r.message || []).sort(function (a, b) { return a.name.localeCompare(b.name); })
				.forEach(function (d) {
					$deptFilter.append(`<option value="${d.name}">${d.name}</option>`);
				});
		}
	});

	// Populate Location dropdown from Field Location doctype
	frappe.call({
		method: 'frappe.client.get_list',
		args: { doctype: 'Field Location', fields: ['name'], limit_page_length: 0 },
		callback: function (r) {
			(r.message || []).sort(function (a, b) { return a.name.localeCompare(b.name); })
				.forEach(function (d) {
					$locFilter.append(`<option value="${d.name}">${d.name}</option>`);
				});
		}
	});

	// Load counts based on active filters
	function loadCounts() {
		STATUS_CARDS.forEach(function (cfg) {
			$(`#count-${frappe.scrub(cfg.status)}`).text('…');
		});

		const filters = [['name', '!=', '']];
		if ($roleFilter.val()) filters.push(['role', '=', $roleFilter.val()]);
		if ($deptFilter.val()) filters.push(['department', '=', $deptFilter.val()]);
		if ($locFilter.val()) filters.push(['location', '=', $locFilter.val()]);

		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Field Registration Form',
				fields: ['name', 'application_status'],
				filters: filters,
				limit_page_length: 0,
			},
			callback: function (r) {
				const records = r && r.message ? r.message : [];
				const counts = {};
				records.forEach(function (row) {
					const s = row.application_status || 'New Applicant';
					counts[s] = (counts[s] || 0) + 1;
				});
				STATUS_CARDS.forEach(function (cfg) {
					$(`#count-${frappe.scrub(cfg.status)}`).text(counts[cfg.status] || 0);
				});
			}
		});
	}

	// Re-load counts when filter changes
	$roleFilter.on('change', loadCounts);
	$deptFilter.on('change', loadCounts);
	$locFilter.on('change', loadCounts);

	// Initial count load
	loadCounts();

	// Card click → open filtered list view
	$grid.on('click', '.recruit-card', function () {
		const status = $(this).data('status');
		let url = '/app/field-registration-form?application_status=' + encodeURIComponent(status);
		if ($roleFilter.val()) url += '&role=' + encodeURIComponent($roleFilter.val());
		if ($deptFilter.val()) url += '&department=' + encodeURIComponent($deptFilter.val());
		if ($locFilter.val()) url += '&location=' + encodeURIComponent($locFilter.val());
		window.location.href = url;
	});
};