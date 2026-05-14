frappe.pages['recruitment-dashboar'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: 'Recruitment Dashboard', single_column: true });

	// ── dark-mode palette ─────────────────────────────────────────────────────
	const BG   = '#091823';          // page background
	const CARD = '#0f2335';          // card surface
	const AC   = '#00d4a8';          // teal accent
	const ACG  = 'rgba(0,212,168,'; // teal with alpha helper
	const BORD = 'rgba(255,255,255,.07)';
	const T1   = '#e2e8f0';          // primary text
	const T2   = '#64748b';          // secondary text

	// ── unit config ───────────────────────────────────────────────────────────
	const UNITS = [
		{
			doctype: 'Field Registration Form1',
			label: 'Field Recruitment', short: 'Field',
			icon: `<svg fill="none" stroke="${AC}" stroke-width="2" viewBox="0 0 24 24" width="24" height="24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
			desc: 'Ground-level field officers & educators',
			status_field: 'application_status',
			nameField: 'full_name_aadhaar',
			columns: [
				{ label: 'Full Name', field: 'full_name_aadhaar' },
				{ label: 'Email',     field: 'email_address' },
				{ label: 'Phone',     field: 'phone_number' },
				{ label: 'Role',      field: 'role' },
				{ label: 'Location',  field: 'location' },
				{ label: 'Gender',    field: 'gender' },
				{ label: 'Education', field: 'highest_education' },
			],
			statuses: ['New Applicant','On Hold','Blocklisted','CV Shortlist','CV Reject','Online Test','Offline Test','Test Process','Recruiter Round','Recruiter Reject','Round One','Round 1 Reject','Round Two','Round 2 Reject','Round Three','Round 3 Reject','Calibration Process','Document Collection','Offer'],
			offerStatuses: ['Offer'],
			profileFields: [
				{ section: 'Application', cols: [
					{ label: 'Status', field: 'application_status' }, { label: 'Role', field: 'role' },
					{ label: 'Location', field: 'location' }, { label: 'Department', field: 'department' },
					{ label: 'Shortlist Reason', field: 'reasons_for_shortlist' }, { label: 'Reject Reason', field: 'reasons_for_reject' },
					{ label: 'On Hold Reason', field: 'hold_reason' },
				]},
				{ section: 'Personal Details', cols: [
					{ label: 'Full Name', field: 'full_name_aadhaar' }, { label: 'Email Address', field: 'email_address' },
					{ label: 'Phone', field: 'phone_number' }, { label: 'Alternate Phone', field: 'alternate_no' },
					{ label: 'Date of Birth', field: 'dob' }, { label: 'Age', field: 'age' },
					{ label: 'Gender', field: 'gender' }, { label: 'Native State', field: 'native_state' },
					{ label: 'Native District', field: 'native_district' },
				]},
				{ section: 'Education & Experience', cols: [
					{ label: 'Highest Education', field: 'highest_education' },
					{ label: 'Teaching Exp. (Yrs)', field: 'teaching_year' }, { label: 'Teaching Exp. (Mo)', field: 'teaching_month' },
					{ label: 'Languages Known', field: 'languages_known' }, { label: 'Other Languages', field: 'other_languages' },
					{ label: 'Former APF Employee?', field: 'former_employee' }, { label: 'Source', field: 'opportunity' },
					{ label: 'Test Location', field: 'test_location' },
				]},
			],
		},
		{
			doctype: 'Scholarship Recruitment Form',
			label: 'Scholarship Recruitment', short: 'Scholarship',
			icon: `<svg fill="none" stroke="${AC}" stroke-width="2" viewBox="0 0 24 24" width="24" height="24"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>`,
			desc: 'Scholarship programme associates & resource persons',
			status_field: 'application_status',
			nameField: 'full_name_as_per_aadhar',
			columns: [
				{ label: 'Full Name', field: 'full_name_as_per_aadhar' },
				{ label: 'Email',     field: 'email' },
				{ label: 'Phone',     field: 'phone_number' },
				{ label: 'Role',      field: 'role' },
				{ label: 'State',     field: 'state_of_residence' },
				{ label: 'Gender',    field: 'gender' },
				{ label: 'Education', field: 'highest_level_of_education' },
			],
			statuses: ['New Applicant','Application Reject','Test Process','Test Reject','Recruiter Round','Recruiter Reject','Round One','Round Two','Reject - Round 1','Reject - Round 2','Document Collection','Offer'],
			offerStatuses: ['Offer'],
			profileFields: [
				{ section: 'Application', cols: [
					{ label: 'Status', field: 'application_status' }, { label: 'Role', field: 'role' },
				]},
				{ section: 'Personal Details', cols: [
					{ label: 'Full Name', field: 'full_name_as_per_aadhar' }, { label: 'Email Address', field: 'email' },
					{ label: 'Phone', field: 'phone_number' }, { label: 'Gender', field: 'gender' },
					{ label: 'State of Residence', field: 'state_of_residence' },
				]},
				{ section: 'Experience & Compensation', cols: [
					{ label: 'Total Experience (Yrs)', field: 'total_years_of_experience' },
					{ label: 'Current CTC', field: 'current_ctc' }, { label: 'Expected CTC', field: 'expected_ctc' },
					{ label: 'Willing to Relocate?', field: 'relocation' },
				]},
				{ section: 'Education', cols: [
					{ label: 'Highest Education', field: 'highest_level_of_education' },
					{ label: 'Year of Completion', field: 'year_completion' },
				]},
			],
		},
		{
			doctype: 'Phil Registration Form',
			label: 'Philanthropy Recruitment', short: 'Philanthropy',
			icon: `<svg fill="none" stroke="${AC}" stroke-width="2" viewBox="0 0 24 24" width="24" height="24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
			desc: 'Philanthropy programme managers & resource persons',
			status_field: 'application_status',
			nameField: 'name1',
			columns: [
				{ label: 'Full Name', field: 'name1' },
				{ label: 'Email',     field: 'email' },
				{ label: 'Phone',     field: 'phone' },
				{ label: 'Role',      field: 'role' },
				{ label: 'Location',  field: 'location' },
				{ label: 'Geo',       field: 'geo' },
				{ label: 'Education', field: 'highest_level_of_education' },
			],
			statuses: ['New Applicant','CV Shortlist','On Hold','CV Reject','Recruiter Round','Recruiter Reject','Round One','Round 1 Reject','Round Two','Round 2 Reject','Round Three','Round 3 Reject','Round Four','Round 4 Reject','Document Collection','Offer'],
			offerStatuses: ['Offer'],
			profileFields: [
				{ section: 'Application', cols: [
					{ label: 'Status', field: 'application_status' }, { label: 'Role', field: 'role' },
					{ label: 'Geo', field: 'geo' }, { label: 'Theme', field: 'themes' },
					{ label: 'Position', field: 'position' }, { label: 'Location', field: 'location' },
				]},
				{ section: 'Personal Details', cols: [
					{ label: 'Full Name', field: 'name1' }, { label: 'Email Address', field: 'email' },
					{ label: 'Phone', field: 'phone' }, { label: 'Date of Birth', field: 'date_of_birth' },
					{ label: 'Age', field: 'age' }, { label: 'Current Location', field: 'current_location' },
				]},
				{ section: 'Education & Experience', cols: [
					{ label: 'Highest Education', field: 'highest_level_of_education' },
					{ label: 'Completion Year', field: 'completion_year' },
					{ label: 'Total Experience (Yrs)', field: 'total_experience' },
				]},
			],
		},
		{
			doctype: 'Health Registration Form',
			label: 'Health Fellowship', short: 'Health',
			icon: `<svg fill="none" stroke="${AC}" stroke-width="2" viewBox="0 0 24 24" width="24" height="24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
			desc: 'Health fellowship doctors & medical professionals',
			status_field: 'application_status',
			nameField: 'full_name',
			columns: [
				{ label: 'Full Name',     field: 'full_name' },
				{ label: 'Email',         field: 'email_address' },
				{ label: 'Phone',         field: 'phone_number' },
				{ label: 'Education',     field: 'education_qualification' },
				{ label: 'Experience',    field: 'mbbs_experience' },
				{ label: 'State Council', field: 'state_medical_council' },
				{ label: 'Former APF?',   field: 'foundation_selection' },
			],
			statuses: ['New Applicant','Shortlist - CV','On hold - CV','Regret - CV','Shortlist - R1','On hold - R1','Regret - R1','Shortlist - R2','On hold - R2','Regret - R2','Offered','Offer accepted','Offer declined','Joined','Document Collection','Offer'],
			offerStatuses: ['Offered', 'Offer accepted'],
			profileFields: [
				{ section: 'Application', cols: [
					{ label: 'Status', field: 'application_status' },
					{ label: 'Former APF?', field: 'foundation_selection' },
				]},
				{ section: 'Personal Details', cols: [
					{ label: 'Full Name', field: 'full_name' }, { label: 'Email Address', field: 'email_address' },
					{ label: 'Phone', field: 'phone_number' }, { label: 'Date of Birth', field: 'date_of_birth' },
					{ label: 'Age', field: 'age' }, { label: 'State', field: 'state' },
				]},
				{ section: 'Medical Qualifications', cols: [
					{ label: 'Education Qualification', field: 'education_qualification' },
					{ label: 'MBBS Experience (Yrs)', field: 'mbbs_experience' },
					{ label: 'State Medical Council', field: 'state_medical_council' },
				]},
				{ section: 'Preferences & Source', cols: [
					{ label: 'Monthly Salary', field: 'monthly_salary' },
					{ label: 'Preferred Location', field: 'first_prefered' },
					{ label: 'Open to Travel?', field: 'are_you_open' },
					{ label: 'Heard From', field: 'opportunity' },
				]},
			],
		},
	];

	// ── CSS ───────────────────────────────────────────────────────────────────
	const S = document.createElement('style');
	S.textContent = `
	/* ── page background ── */
	.rd-wrap {
		background:${BG}; min-height:calc(100vh - 60px);
		margin:-15px -15px 0; padding:15px 28px 80px;
	}

	/* ── sticky nav bar ── */
	.rd-dbar {
		display:flex; align-items:center; gap:12px;
		padding:13px 28px; border-bottom:1px solid ${ACG}.15);
		margin:0 -28px 28px; position:sticky; top:0; z-index:50;
		background:#06111e; box-shadow:0 2px 20px rgba(0,0,0,.4);
	}
	.rd-back {
		display:inline-flex; align-items:center; gap:7px;
		padding:7px 16px; background:${ACG}.1); border:1px solid ${ACG}.2);
		border-radius:8px; font-size:13px; font-weight:600; color:${AC};
		cursor:pointer; transition:all .18s;
	}
	.rd-back:hover { background:${AC}; color:#06111e; border-color:${AC}; }
	.rd-dbreadcrumb { font-size:13px; color:${T2}; }
	.rd-dbreadcrumb b { color:${T1}; }
	.rd-dbar-sp { flex:1; }
	.rd-dbar-date { font-size:12px; color:${T2}; }
	.rd-section-label {
		font-size:11px; font-weight:700; color:${T2};
		text-transform:uppercase; letter-spacing:.08em; margin:28px 0 14px;
	}

	/* ══════════════════════════════════
	   FRONT PAGE
	══════════════════════════════════ */
	.rd-hero {
		margin:20px 0 28px; padding:36px 40px; border-radius:20px;
		background:linear-gradient(135deg,#0a2a1c 0%,#091823 50%,#0a1a2e 100%);
		border:1px solid ${ACG}.15); position:relative; overflow:hidden;
	}
	.rd-hero::before {
		content:''; position:absolute; right:-100px; top:-100px;
		width:400px; height:400px; border-radius:50%;
		background:radial-gradient(circle,${ACG}.12) 0%,transparent 65%);
		pointer-events:none;
	}
	.rd-hero::after {
		content:''; position:absolute; left:30%; bottom:-120px;
		width:300px; height:300px; border-radius:50%;
		background:radial-gradient(circle,rgba(99,102,241,.08) 0%,transparent 65%);
		pointer-events:none;
	}
	.rd-hero-eyebrow {
		display:inline-flex; align-items:center; gap:8px;
		background:${ACG}.08); border:1px solid ${ACG}.2);
		border-radius:20px; padding:5px 14px; font-size:11px; font-weight:700;
		letter-spacing:.07em; text-transform:uppercase; color:${AC}; margin-bottom:16px;
	}
	.rd-hero-dot { width:6px; height:6px; background:${AC}; border-radius:50%; box-shadow:0 0 8px ${AC}; }
	.rd-hero-title { font-size:30px; font-weight:900; color:${T1}; margin-bottom:6px; line-height:1.15; }
	.rd-hero-sub { font-size:13.5px; color:${T2}; margin-bottom:28px; }
	.rd-hero-stats { display:flex; gap:0; }
	.rd-hstat {
		padding:16px 36px 16px 0; display:flex; flex-direction:column;
		border-right:1px solid ${ACG}.12); margin-right:36px;
	}
	.rd-hstat:last-child { border-right:none; margin-right:0; }
	.rd-hstat-v { font-size:34px; font-weight:900; color:${AC}; line-height:1; text-shadow:0 0 20px ${ACG}.4); }
	.rd-hstat-k { font-size:11px; color:${T2}; text-transform:uppercase; letter-spacing:.07em; margin-top:6px; }

	/* unit nav cards */
	.rd-units { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }
	.rd-ucard {
		background:${CARD}; border:1px solid ${BORD};
		border-radius:16px; padding:26px 28px; cursor:pointer;
		position:relative; overflow:hidden; transition:all .22s;
	}
	.rd-ucard::before {
		content:''; position:absolute; inset:0; border-radius:16px;
		background:linear-gradient(135deg,${ACG}.04) 0%,transparent 60%);
		opacity:0; transition:opacity .22s;
	}
	.rd-ucard:hover { border-color:${ACG}.35); box-shadow:0 8px 32px ${ACG}.15); transform:translateY(-3px); }
	.rd-ucard:hover::before { opacity:1; }
	.rd-ucard::after {
		content:''; position:absolute; bottom:0; left:0; right:0; height:2px;
		background:${AC}; transform:scaleX(0); transform-origin:left; transition:transform .25s;
		box-shadow:0 0 8px ${AC};
	}
	.rd-ucard:hover::after { transform:scaleX(1); }
	.rd-ucard-top { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:16px; }
	.rd-ucard-icon {
		width:48px; height:48px; border-radius:13px;
		display:flex; align-items:center; justify-content:center;
		background:${ACG}.1); border:1px solid ${ACG}.2);
	}
	.rd-ucard-num { font-size:38px; font-weight:900; color:${AC}; line-height:1; text-shadow:0 0 24px ${ACG}.5); }
	.rd-ucard-label { font-size:16px; font-weight:800; color:${T1}; margin-bottom:4px; }
	.rd-ucard-desc  { font-size:12.5px; color:${T2}; margin-bottom:18px; }
	.rd-ucard-foot  { display:flex; align-items:center; justify-content:space-between; }
	.rd-ucard-pill {
		font-size:11px; font-weight:700; padding:4px 12px; border-radius:20px;
		background:${ACG}.08); color:${AC}; border:1px solid ${ACG}.2);
	}
	.rd-ucard-arrow {
		width:32px; height:32px; border-radius:9px;
		background:${ACG}.1); color:${AC}; border:1px solid ${ACG}.2);
		display:flex; align-items:center; justify-content:center; font-size:15px;
		transition:all .2s;
	}
	.rd-ucard:hover .rd-ucard-arrow { background:${AC}; color:#06111e; box-shadow:0 0 12px ${ACG}.6); }

	/* ══════════════════════════════════
	   DETAIL PAGE
	══════════════════════════════════ */
	.rd-detail { display:none; }

	/* 4 stat cards */
	.rd-dstats { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:26px; }
	.rd-dstat {
		background:${CARD}; border:1px solid ${BORD}; border-radius:14px;
		padding:20px 22px; display:flex; align-items:center; gap:16px;
		transition:all .2s;
	}
	.rd-dstat:hover { border-color:${ACG}.25); box-shadow:0 4px 20px rgba(0,0,0,.3); transform:translateY(-2px); }
	.rd-dstat-icon {
		width:46px; height:46px; border-radius:12px; flex-shrink:0;
		display:flex; align-items:center; justify-content:center;
	}
	.rd-dstat-icon svg { width:22px; height:22px; }
	.rd-dstat-body { flex:1; min-width:0; }
	.rd-dstat .dsv { font-size:30px; font-weight:900; line-height:1; margin-bottom:4px; }
	.rd-dstat .dsk { font-size:11.5px; font-weight:600; color:${T2}; }

	/* chart */
	.rd-dchart-wrap {
		background:${CARD}; border:1px solid ${BORD}; border-radius:14px;
		padding:22px 26px 18px; margin-bottom:26px; box-shadow:0 2px 12px rgba(0,0,0,.2);
	}
	.rd-dchart-hdr { display:flex; align-items:baseline; justify-content:space-between; margin-bottom:20px; }
	.rd-dchart-ttl { font-size:14px; font-weight:700; color:${T1}; }
	.rd-dchart-sub { font-size:12px; color:${T2}; }
	.rd-dchart-wrap .chart-container svg { cursor:pointer; }
	.rd-dchart-wrap .chart-container text { fill:${T2} !important; }
	.rd-dchart-wrap .chart-container .x.axis line,
	.rd-dchart-wrap .chart-container .y.axis line { stroke:${BORD} !important; }

	/* status cards */
	.rd-dgrid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:26px; }
	.rd-dcard {
		background:${CARD}; border:1px solid ${BORD}; border-radius:12px;
		padding:16px 18px 14px; cursor:pointer; position:relative; overflow:hidden;
		transition:all .18s;
	}
	.rd-dcard::before {
		content:''; position:absolute; top:0; left:0; right:0; height:2px;
		background:${AC}; transform:scaleX(0); transform-origin:left; transition:transform .25s;
		box-shadow:0 0 8px ${AC};
	}
	.rd-dcard:hover::before { transform:scaleX(1); }
	.rd-dcard:hover { border-color:${ACG}.3); box-shadow:0 6px 24px ${ACG}.12); transform:translateY(-2px); }
	.rd-dcard.zero { opacity:.35; cursor:default; }
	.rd-dcard.zero:hover { border-color:${BORD}; box-shadow:none; transform:none; }
	.rd-dcard.zero::before { display:none; }
	.rd-dcard .dl {
		font-size:10.5px; font-weight:700; color:${T2};
		letter-spacing:.05em; text-transform:uppercase; margin-bottom:10px; line-height:1.4;
	}
	.rd-dcard .dn { font-size:34px; font-weight:900; color:${AC}; line-height:1; text-shadow:0 0 16px ${ACG}.45); }
	@keyframes dnPop { 0%{transform:scale(.5);opacity:0} 65%{transform:scale(1.15)} 100%{transform:scale(1);opacity:1} }
	.rd-dcard .dn.pop { animation:dnPop .3s cubic-bezier(.34,1.56,.64,1) forwards; }

	/* ══════════════════════════════════
	   RECORDS PAGE
	══════════════════════════════════ */
	.rd-records { display:none; }
	.rd-rpage-hero {
		border-radius:16px; padding:30px 34px; margin-bottom:24px;
		background:linear-gradient(135deg,#0a2a1c 0%,#091823 60%,#0a1a2e 100%);
		border:1px solid ${ACG}.15); position:relative; overflow:hidden;
	}
	.rd-rpage-hero::before {
		content:''; position:absolute; right:-60px; top:-60px;
		width:260px; height:260px; border-radius:50%;
		background:radial-gradient(circle,${ACG}.12) 0%,transparent 65%);
		pointer-events:none;
	}
	.rd-rpage-unit  { font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:${AC}; opacity:.7; margin-bottom:8px; }
	.rd-rpage-title { font-size:26px; font-weight:900; color:${T1}; margin-bottom:6px; }
	.rd-rpage-meta  { font-size:13px; color:${T2}; }
	.rd-rpage-big   { position:absolute; top:16px; right:32px; font-size:80px; font-weight:900; color:${ACG}.08); line-height:1; pointer-events:none; }
	.rd-rpage-card  { background:${CARD}; border:1px solid ${BORD}; border-radius:14px; overflow:hidden; }
	.rd-rpage-toolbar { display:flex; align-items:center; gap:12px; padding:14px 20px; border-bottom:1px solid ${BORD}; background:rgba(0,0,0,.2); }
	.rd-rpage-tlabel { font-size:14px; font-weight:700; color:${T1}; flex:1; }
	.rd-rpage-tcnt { font-size:12px; font-weight:600; padding:4px 12px; border-radius:20px; background:${ACG}.1); color:${AC}; border:1px solid ${ACG}.25); }
	.rd-rpage-srch {
		padding:8px 14px; border:1px solid ${BORD}; border-radius:8px;
		font-size:13px; width:240px; outline:none;
		background:rgba(255,255,255,.05); color:${T1};
		transition:border-color .18s,box-shadow .18s;
	}
	.rd-rpage-srch::placeholder { color:${T2}; }
	.rd-rpage-srch:focus { border-color:${AC}; box-shadow:0 0 0 3px ${ACG}.12); }
	.rd-rpage-body { overflow-x:auto; max-height:560px; overflow-y:auto; }
	.rd-rpage-foot { display:flex; align-items:center; justify-content:space-between; padding:11px 20px; border-top:1px solid ${BORD}; font-size:12px; color:${T2}; background:rgba(0,0,0,.15); }

	/* ══════════════════════════════════
	   PROFILE PAGE
	══════════════════════════════════ */
	.rd-profile { display:none; }
	.rdp-hero {
		background:linear-gradient(130deg,#0a2a1c 0%,#091823 55%,#0a1a2e 100%);
		border:1px solid ${ACG}.15); border-radius:18px; padding:32px 36px; margin-bottom:24px;
		display:flex; align-items:center; gap:28px; position:relative; overflow:hidden;
	}
	.rdp-hero::before {
		content:''; position:absolute; right:-60px; top:-60px;
		width:280px; height:280px; border-radius:50%;
		background:radial-gradient(circle,${ACG}.1) 0%,transparent 65%); pointer-events:none;
	}
	.rdp-avatar {
		width:72px; height:72px; border-radius:18px; flex-shrink:0;
		background:${ACG}.15); border:2px solid ${ACG}.4);
		color:${AC}; display:flex; align-items:center; justify-content:center;
		font-size:28px; font-weight:900; box-shadow:0 0 24px ${ACG}.3);
	}
	.rdp-hero-info { flex:1; min-width:0; }
	.rdp-hero-name { font-size:24px; font-weight:900; color:${T1}; margin-bottom:4px; }
	.rdp-hero-id   { font-size:12px; color:${T2}; margin-bottom:12px; font-family:monospace; }
	.rdp-hero-badges { display:flex; gap:8px; flex-wrap:wrap; }
	.rdp-badge {
		display:inline-block; padding:4px 14px; border-radius:20px; font-size:12px; font-weight:700;
		border:1px solid; letter-spacing:.02em;
	}
	.rdp-badge-unit { background:${ACG}.08); color:${AC}; border-color:${ACG}.2); font-size:11px; }

	.rdp-body { display:flex; flex-direction:column; gap:14px; }
	.rdp-section { background:${CARD}; border:1px solid ${BORD}; border-radius:14px; overflow:hidden; }
	.rdp-section-hdr {
		padding:13px 22px; background:rgba(0,0,0,.2); border-bottom:1px solid ${BORD};
		display:flex; align-items:center; gap:10px;
	}
	.rdp-section-dot { width:8px; height:8px; border-radius:3px; background:${AC}; box-shadow:0 0 6px ${AC}; }
	.rdp-section-ttl { font-size:11.5px; font-weight:700; color:${AC}; text-transform:uppercase; letter-spacing:.07em; }
	.rdp-fields { display:grid; grid-template-columns:repeat(3,1fr); }
	.rdp-field { padding:14px 22px; border-bottom:1px solid ${BORD}; transition:background .12s; }
	.rdp-field:hover { background:${ACG}.05); }
	.rdp-field-label { font-size:10.5px; font-weight:700; color:${T2}; text-transform:uppercase; letter-spacing:.05em; margin-bottom:5px; }
	.rdp-field-value { font-size:14px; font-weight:600; color:${T1}; word-break:break-word; }
	.rdp-nodata { padding:48px; text-align:center; color:${T2}; font-size:14px; }
	.rdp-loading { padding:60px; text-align:center; color:${T2}; font-size:13px; }

	/* ── shared table ── */
	.rd-tbl { width:100%; border-collapse:collapse; font-size:13.5px; }
	.rd-tbl thead tr { position:sticky; top:0; z-index:2; background:#0a1d2e; }
	.rd-tbl th { padding:11px 16px; text-align:left; font-size:10.5px; font-weight:700; color:${T2}; text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid ${BORD}; white-space:nowrap; }
	.rd-tbl tbody tr { cursor:pointer; transition:background .1s; }
	.rd-tbl tbody tr:hover { background:${ACG}.07); }
	.rd-tbl tbody tr:hover .rd-tname { text-decoration:underline; }
	.rd-tbl td { padding:12px 16px; color:${T1}; border-bottom:1px solid ${BORD}; max-width:210px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
	.rd-tbl tbody tr:last-child td { border-bottom:none; }
	.rd-tbl .tsno { color:${T2}; font-size:11px; width:40px; text-align:center; }
	.rd-tbl .tid  { font-family:monospace; font-size:11px; color:${T2}; }
	.rd-tname { font-weight:600; color:${AC}; }
	.rd-nodata { padding:60px; text-align:center; color:${T2}; font-size:14px; }
	`;
	document.head.appendChild(S);

	// ── DOM ───────────────────────────────────────────────────────────────────
	$(wrapper).find('.page-content').append(`
		<div class="rd-wrap">
			<div id="rd-front"></div>
			<div class="rd-detail" id="rd-detail"></div>
			<div class="rd-records" id="rd-records"></div>
			<div class="rd-profile" id="rd-profile"></div>
		</div>
	`);

	const $front   = $('#rd-front');
	const $detail  = $('#rd-detail');
	const $records = $('#rd-records');
	const $profile = $('#rd-profile');
	const store    = {};
	let grandTotal = 0, grandOffers = 0;

	function fmtDate() {
		return new Date().toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long', year:'numeric' });
	}

	// ── front page ────────────────────────────────────────────────────────────
	$front.html(`
		<div class="rd-hero">
			<div class="rd-hero-eyebrow">
				<span class="rd-hero-dot"></span>
				Azim Premji Foundation
			</div>
			<div class="rd-hero-title">Recruitment Dashboard</div>
			<div class="rd-hero-sub">Monitor applicants across all recruitment units. Select a unit below to explore.</div>
			<div class="rd-hero-stats">
				<div class="rd-hstat"><span class="rd-hstat-v" id="gs-total">—</span><span class="rd-hstat-k">Total Applicants</span></div>
				<div class="rd-hstat"><span class="rd-hstat-v" id="gs-offers">—</span><span class="rd-hstat-k">Total Offers</span></div>
				<div class="rd-hstat"><span class="rd-hstat-v">4</span><span class="rd-hstat-k">Active Units</span></div>
			</div>
		</div>

		<div class="rd-section-label" style="margin-top:8px">Recruitment Units</div>
		<div class="rd-units">
			${UNITS.map((u, i) => `
				<div class="rd-ucard" data-ui="${i}">
					<div class="rd-ucard-top">
						<div class="rd-ucard-icon">${u.icon}</div>
						<div class="rd-ucard-num" id="unum-${i}">—</div>
					</div>
					<div class="rd-ucard-label">${u.label}</div>
					<div class="rd-ucard-desc">${u.desc}</div>
					<div class="rd-ucard-foot">
						<span class="rd-ucard-pill">View Pipeline</span>
						<span class="rd-ucard-arrow">&#8594;</span>
					</div>
				</div>`).join('')}
		</div>
	`);

	$front.on('click', '.rd-ucard', function () {
		showDetail(parseInt($(this).data('ui')));
	});

	// ── fetch all units ───────────────────────────────────────────────────────
	UNITS.forEach(function (unit, ui) {
		const fields = ['name', unit.status_field].concat(unit.columns.map(c => c.field));
		frappe.call({
			method: 'frappe.client.get_list',
			args: { doctype: unit.doctype, fields, filters: [['name','!=','']], limit_page_length: 0 },
			callback: function (r) {
				const rows = r && r.message ? r.message : [];
				const counts = {};
				rows.forEach(function (row) {
					const s = row[unit.status_field] || 'New Applicant';
					counts[s] = (counts[s] || 0) + 1;
				});
				store[ui] = { rows, counts };
				$('#unum-' + ui).text(rows.length);
				grandTotal  += rows.length;
				grandOffers += unit.offerStatuses.reduce((s, st) => s + (counts[st] || 0), 0);
				$('#gs-total').text(grandTotal);
				$('#gs-offers').text(grandOffers);
			}
		});
	});

	// ── detail page ───────────────────────────────────────────────────────────
	function showDetail(ui) {
		const unit = UNITS[ui];
		const data = store[ui];
		if (!data) { frappe.msgprint('Data still loading, please wait.'); return; }
		const { rows, counts } = data;
		const total   = rows.length;
		const RW      = ['reject','blocklist','regret'];
		const offered = unit.offerStatuses.reduce((s, st) => s + (counts[st] || 0), 0);
		const docColl = counts['Document Collection'] || 0;
		let   rejected = 0;
		Object.keys(counts).forEach(s => { if (RW.some(w => s.toLowerCase().includes(w))) rejected += counts[s]; });
		const pipeline = total - offered - docColl - rejected;

		$front.hide();
		$detail.show().html(`
			<div class="rd-dbar">
				<button class="rd-back" id="rd-back">
					<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
					Dashboard
				</button>
				<span class="rd-dbreadcrumb">Recruitment &rsaquo; <b>${unit.label}</b></span>
				<span class="rd-dbar-sp"></span>
				<span class="rd-dbar-date">${fmtDate()}</span>
			</div>

			<div class="rd-dstats">
				<div class="rd-dstat rd-dstat-clickable" id="rd-dstat-total" style="cursor:pointer">
					<div class="rd-dstat-icon" style="background:${ACG}.1);border:1px solid ${ACG}.2)">
						<svg fill="none" stroke="${AC}" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:${AC};text-shadow:0 0 16px ${ACG}.5)">${total}</div><div class="dsk">Total Applicants</div></div>
				</div>
				<div class="rd-dstat">
					<div class="rd-dstat-icon" style="background:rgba(74,222,128,.1);border:1px solid rgba(74,222,128,.25)">
						<svg fill="none" stroke="#4ade80" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:#4ade80;text-shadow:0 0 16px rgba(74,222,128,.5)">${offered}</div><div class="dsk">Offered</div></div>
				</div>
				<div class="rd-dstat">
					<div class="rd-dstat-icon" style="background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.25)">
						<svg fill="none" stroke="#f87171" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:#f87171;text-shadow:0 0 16px rgba(248,113,113,.5)">${rejected}</div><div class="dsk">Rejected</div></div>
				</div>
				<div class="rd-dstat">
					<div class="rd-dstat-icon" style="background:rgba(103,232,249,.1);border:1px solid rgba(103,232,249,.25)">
						<svg fill="none" stroke="#67e8f9" stroke-width="2" viewBox="0 0 24 24"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:#67e8f9;text-shadow:0 0 16px rgba(103,232,249,.5)">${pipeline}</div><div class="dsk">In Pipeline</div></div>
				</div>
			</div>

			<div class="rd-dchart-wrap">
				<div class="rd-dchart-hdr">
					<div class="rd-dchart-ttl">Applicants by Status</div>
					<div class="rd-dchart-sub">Click a bar to view records for that status</div>
				</div>
				<div id="rd-bar"></div>
			</div>

			<div class="rd-section-label" style="margin-top:0">Status Breakdown — click a card to view records</div>
			<div class="rd-dgrid" id="rd-dgrid">
				${unit.statuses.map(s => `
					<div class="rd-dcard${(counts[s] || 0) === 0 ? ' zero' : ''}" data-status="${s}">
						<div class="dl">${s}</div>
						<div class="dn pop">${counts[s] || 0}</div>
					</div>`).join('')}
			</div>
		`);

		setTimeout(function () { drawCharts(unit, counts, rows); }, 180);
		$detail.find('#rd-back').on('click', function () { $detail.hide(); $front.show(); });
		$detail.find('#rd-dgrid').on('click', '.rd-dcard:not(.zero)', function () {
			showRecords(unit, rows, $(this).data('status'));
		});
		$detail.find('#rd-dstat-total').on('click', function () {
			showRecords(unit, rows, null);
		});
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	// ── records page ──────────────────────────────────────────────────────────
	function showRecords(unit, allRows, status) {
		const isAll    = status === null;
		const filtered = isAll ? allRows : allRows.filter(r => (r[unit.status_field] || 'New Applicant') === status);
		const titleLabel = isAll ? 'All Applicants' : status;
		$detail.hide();
		$records.show().html(`
			<div class="rd-dbar">
				<button class="rd-back" id="rp-back">
					<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
					${unit.short}
				</button>
				<span class="rd-dbreadcrumb">Recruitment &rsaquo; <b>${unit.label}</b> &rsaquo; <b>${titleLabel}</b></span>
				<span class="rd-dbar-sp"></span>
				<span class="rd-dbar-date">${fmtDate()}</span>
			</div>
			<div class="rd-rpage-hero">
				<div class="rd-rpage-unit">${unit.label}</div>
				<div class="rd-rpage-title">${titleLabel}</div>
				<div class="rd-rpage-meta">${filtered.length} applicant${filtered.length !== 1 ? 's' : ''} in this stage</div>
				<div class="rd-rpage-big">${filtered.length}</div>
			</div>
			<div class="rd-rpage-card">
				<div class="rd-rpage-toolbar">
					<span class="rd-rpage-tlabel">${titleLabel} — All Records</span>
					<span class="rd-rpage-tcnt" id="rp-cnt">${filtered.length} applicants</span>
					<input class="rd-rpage-srch" type="text" placeholder="Search name, email, phone…" id="rp-srch" />
				</div>
				<div class="rd-rpage-body" id="rp-body">${buildTable(unit, filtered)}</div>
				<div class="rd-rpage-foot">
					<span id="rp-foot">Showing ${filtered.length} of ${filtered.length} records</span>
					<span>Click any row to open the applicant profile</span>
				</div>
			</div>
		`);
		$records.find('#rp-back').on('click', function () { $records.hide(); $detail.show(); window.scrollTo({ top:0, behavior:'smooth' }); });
		$records.find('#rp-srch').on('input', function () {
			const q = $(this).val().toLowerCase().trim();
			const f = q ? filtered.filter(r => unit.columns.some(c => (r[c.field]||'').toLowerCase().includes(q))) : filtered;
			$records.find('#rp-body').html(buildTable(unit, f));
			$records.find('#rp-cnt').text(f.length + ' applicants');
			$records.find('#rp-foot').text('Showing ' + f.length + ' of ' + filtered.length + ' records');
		});
		$records.off('click', '.rd-tbl tbody tr').on('click', '.rd-tbl tbody tr', function () {
			const name = $(this).data('name');
			if (name) showProfile(unit, name, titleLabel);
		});
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	// ── profile page ──────────────────────────────────────────────────────────
	function showProfile(unit, docName, status) {
		$records.hide();
		$profile.show().html(`
			<div class="rd-dbar">
				<button class="rd-back" id="rpp-back">
					<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
					${status}
				</button>
				<span class="rd-dbreadcrumb">Recruitment &rsaquo; <b>${unit.label}</b> &rsaquo; <b>${status}</b> &rsaquo; <b>${docName}</b></span>
				<span class="rd-dbar-sp"></span>
			</div>
			<div class="rdp-loading">Loading applicant data…</div>
		`);
		$profile.find('#rpp-back').on('click', function () { $profile.hide(); $records.show(); window.scrollTo({ top:0, behavior:'smooth' }); });

		frappe.call({
			method: 'frappe.client.get',
			args: { doctype: unit.doctype, name: docName },
			callback: function (r) {
				if (!r || !r.message) { $profile.find('.rdp-loading').text('Could not load data.'); return; }
				const doc = r.message;
				const displayName = doc[unit.nameField] || docName;
				const initial     = (displayName || '?').trim()[0].toUpperCase();
				const RW          = ['reject','blocklist','regret'];
				const isOffer     = unit.offerStatuses.includes(status);
				const isReject    = RW.some(w => status.toLowerCase().includes(w));
				const isHold      = status.toLowerCase().includes('hold');
				const badgeBg     = isOffer ? 'rgba(74,222,128,.12)'  : isReject ? 'rgba(248,113,113,.12)' : isHold ? 'rgba(251,191,36,.12)' : ACG+'.1)';
				const badgeClr    = isOffer ? '#4ade80' : isReject ? '#f87171' : isHold ? '#fbbf24' : AC;
				const badgeBd     = isOffer ? 'rgba(74,222,128,.3)'   : isReject ? 'rgba(248,113,113,.3)'  : isHold ? 'rgba(251,191,36,.3)'  : ACG+'.25)';

				const sectionsHtml = unit.profileFields.map(sec => {
					const fh = sec.cols.map(f => {
						const v = doc[f.field];
						if (v === null || v === undefined || v === '') return '';
						return `<div class="rdp-field"><div class="rdp-field-label">${f.label}</div><div class="rdp-field-value">${v}</div></div>`;
					}).join('');
					if (!fh) return '';
					return `<div class="rdp-section"><div class="rdp-section-hdr"><div class="rdp-section-dot"></div><div class="rdp-section-ttl">${sec.section}</div></div><div class="rdp-fields">${fh}</div></div>`;
				}).join('');

				$profile.html(`
					<div class="rd-dbar">
						<button class="rd-back" id="rpp-back2">
							<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
							${status}
						</button>
						<span class="rd-dbreadcrumb">Recruitment &rsaquo; <b>${unit.label}</b> &rsaquo; <b>${status}</b> &rsaquo; <b>${displayName}</b></span>
						<span class="rd-dbar-sp"></span>
						<span class="rd-dbar-date">${fmtDate()}</span>
					</div>
					<div class="rdp-hero">
						<div class="rdp-avatar">${initial}</div>
						<div class="rdp-hero-info">
							<div class="rdp-hero-name">${displayName}</div>
							<div class="rdp-hero-id">${docName}</div>
							<div class="rdp-hero-badges">
								<span class="rdp-badge" style="background:${badgeBg};color:${badgeClr};border-color:${badgeBd}">${status}</span>
								<span class="rdp-badge rdp-badge-unit">${unit.label}</span>
							</div>
						</div>
					</div>
					<div class="rdp-body">${sectionsHtml || '<div class="rdp-nodata">No additional data available.</div>'}</div>
				`);
				$profile.find('#rpp-back2').on('click', function () { $profile.hide(); $records.show(); window.scrollTo({ top:0, behavior:'smooth' }); });
				window.scrollTo({ top: 0, behavior: 'smooth' });
			}
		});
	}

	// ── bar chart ─────────────────────────────────────────────────────────────
	function drawCharts(unit, counts, allRows) {
		const labels = unit.statuses.filter(s => (counts[s] || 0) > 0);
		const values = labels.map(s => counts[s]);
		const barEl  = document.getElementById('rd-bar');
		if (!barEl || !labels.length) return;
		try {
			new frappe.Chart(barEl, {
				type: 'bar', height: 240, colors: [AC],
				data: { labels, datasets: [{ name: 'Applicants', values }] },
				barOptions: { spaceRatio: 0.3 },
				tooltipOptions: { formatTooltipY: d => d + ' applicants' }
			});
			barEl.addEventListener('data-select', function (e) {
				const lbl = e.label || (e.detail && e.detail.label);
				if (lbl) showRecords(unit, allRows, lbl);
			});
		} catch(err) {}
	}

	// ── table builder ─────────────────────────────────────────────────────────
	function buildTable(unit, rows) {
		if (!rows.length) return '<div class="rd-nodata">No records found for this status.</div>';
		const thHtml = unit.columns.map(c => `<th>${c.label}</th>`).join('');
		const trs = rows.map(function (r, i) {
			const tds = unit.columns.map(function (c, ci) {
				const v = r[c.field] || '—';
				return ci === 0 ? `<td class="rd-tname" title="${v}">${v}</td>` : `<td title="${v}">${v}</td>`;
			}).join('');
			return `<tr data-name="${r.name||''}"><td class="tsno">${i+1}</td><td class="tid">${r.name||''}</td>${tds}</tr>`;
		}).join('');
		return `<table class="rd-tbl"><thead><tr><th>#</th><th>ID</th>${thHtml}</tr></thead><tbody>${trs}</tbody></table>`;
	}
};
