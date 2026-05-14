frappe.pages['recruitment-dashboar'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper, title: 'Recruitment Dashboard', single_column: true });

	// ── palette ────────────────────────────────────────────────────────────────
	const BG   = '#f0f4ff';
	const AC   = '#6366f1';
	const ACG  = 'rgba(99,102,241,';
	const BORD = '#e5e9f0';
	const T1   = '#1e293b';
	const T2   = '#64748b';

	// single two-colour gradient used for all unit cards
	const CARD_G1 = '#4f46e5';   // indigo-600
	const CARD_G2 = '#6366f1';   // indigo-500

	const DATE_FILTERS = [
		{ label:'All',     key:'all' },
		{ label:'Today',   key:'today' },
		{ label:'Week',    key:'week' },
		{ label:'Month',   key:'month' },
		{ label:'Quarter', key:'quarter' },
		{ label:'Year',    key:'year' },
		{ label:'Custom',  key:'custom' },
	];
	let activeFilter = 'all';
	let customFrom = '', customTo = '';

	// ── unit config ────────────────────────────────────────────────────────────
	const UNITS = [
		{
			doctype: 'Field Registration Form1',
			label: 'Field Recruitment', short: 'Field',
			icon: `<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24" width="22" height="22"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
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
			icon: `<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24" width="22" height="22"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>`,
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
			icon: `<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24" width="22" height="22"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
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
			icon: `<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24" width="22" height="22"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
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
	.rd-wrap {
		background:${BG}; min-height:calc(100vh - 60px);
		margin:-15px -15px 0; padding:15px 28px 80px;
	}
	/* sticky nav */
	.rd-dbar {
		display:flex; align-items:center; gap:12px;
		padding:12px 28px; border-bottom:1px solid ${BORD};
		margin:0 -28px 28px; position:sticky; top:0; z-index:50;
		background:#fff; box-shadow:0 2px 12px rgba(0,0,0,.07);
	}
	.rd-back {
		display:inline-flex; align-items:center; gap:7px;
		padding:7px 16px; background:${ACG}.08); border:1px solid ${ACG}.2);
		border-radius:8px; font-size:13px; font-weight:600; color:${AC};
		cursor:pointer; transition:all .18s;
	}
	.rd-back:hover { background:${AC}; color:#fff; border-color:${AC}; }
	.rd-dbreadcrumb { font-size:13px; color:${T2}; }
	.rd-dbreadcrumb b { color:${T1}; }
	.rd-dbar-sp { flex:1; }
	.rd-dbar-date { font-size:12px; color:${T2}; }
	.rd-section-label {
		font-size:11px; font-weight:700; color:${T2};
		text-transform:uppercase; letter-spacing:.08em; margin:28px 0 14px;
	}
	/* ── hero ── */
	.rd-hero {
		margin:20px 0 28px; padding:36px 40px; border-radius:20px;
		background:linear-gradient(135deg,#1e1b4b 0%,#3730a3 50%,#6366f1 100%);
		position:relative; overflow:hidden;
	}
	.rd-hero::before {
		content:''; position:absolute; right:-100px; top:-100px;
		width:360px; height:360px; border-radius:50%;
		background:rgba(255,255,255,.06); pointer-events:none;
	}
	.rd-hero::after {
		content:''; position:absolute; left:-60px; bottom:-100px;
		width:260px; height:260px; border-radius:50%;
		background:rgba(255,255,255,.04); pointer-events:none;
	}
	.rd-hero-eyebrow {
		display:inline-flex; align-items:center; gap:8px;
		background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.2);
		border-radius:20px; padding:5px 14px; font-size:11px; font-weight:700;
		letter-spacing:.07em; text-transform:uppercase; color:#fff; margin-bottom:16px;
	}
	.rd-hero-dot { width:6px; height:6px; background:#fff; border-radius:50%; }
	.rd-hero-title { font-size:30px; font-weight:900; color:#fff; margin-bottom:6px; }
	.rd-hero-sub { font-size:13.5px; color:rgba(255,255,255,.65); margin-bottom:24px; }
	.rd-hero-stats { display:flex; gap:0; margin-bottom:24px; }
	.rd-hstat {
		padding:0 36px 0 0; display:flex; flex-direction:column;
		border-right:1px solid rgba(255,255,255,.15); margin-right:36px;
	}
	.rd-hstat:last-child { border-right:none; margin-right:0; }
	.rd-hstat-v { font-size:34px; font-weight:900; color:#fff; line-height:1; }
	.rd-hstat-k { font-size:11px; color:rgba(255,255,255,.6); text-transform:uppercase; letter-spacing:.07em; margin-top:6px; }
	/* date filter pills */
	.rd-filter-row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
	.rd-filter-btn {
		padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600;
		background:rgba(255,255,255,.1); color:rgba(255,255,255,.8);
		border:1px solid rgba(255,255,255,.18); cursor:pointer; transition:all .15s;
	}
	.rd-filter-btn:hover { background:rgba(255,255,255,.2); color:#fff; }
	.rd-filter-btn.active { background:#fff; color:#3730a3; border-color:#fff; }
	/* custom date range row */
	.rd-custom-row {
		display:none; align-items:center; gap:10px; margin-top:10px;
		background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.2);
		border-radius:12px; padding:10px 16px; flex-wrap:wrap;
	}
	.rd-custom-row.show { display:flex; }
	.rd-custom-label { font-size:11px; font-weight:600; color:rgba(255,255,255,.7); text-transform:uppercase; letter-spacing:.06em; }
	.rd-date-input {
		padding:6px 12px; border-radius:8px; font-size:12px; font-weight:500;
		background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.25);
		color:#fff; outline:none; cursor:pointer;
		transition:border-color .15s, background .15s;
	}
	.rd-date-input::-webkit-calendar-picker-indicator { filter:invert(1); opacity:.7; cursor:pointer; }
	.rd-date-input:focus { background:rgba(255,255,255,.22); border-color:#fff; }
	.rd-apply-btn {
		padding:6px 16px; border-radius:8px; font-size:12px; font-weight:700;
		background:#fff; color:#3730a3; border:none; cursor:pointer; transition:all .15s;
	}
	.rd-apply-btn:hover { background:#e0e7ff; }
	/* unit cards */
	.rd-units { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }
	.rd-ucard {
		border-radius:18px; padding:28px 30px; cursor:pointer;
		position:relative; overflow:hidden; transition:all .22s;
		box-shadow:0 4px 24px rgba(0,0,0,.13);
	}
	.rd-ucard:hover { transform:translateY(-4px); box-shadow:0 16px 48px rgba(0,0,0,.2); }
	.rd-ucard-top { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:14px; }
	.rd-ucard-icon {
		width:46px; height:46px; border-radius:13px;
		display:flex; align-items:center; justify-content:center;
		background:rgba(255,255,255,.2);
	}
	.rd-ucard-num { font-size:42px; font-weight:900; color:#fff; line-height:1; text-shadow:0 2px 12px rgba(0,0,0,.2); }
	.rd-ucard-label { font-size:16px; font-weight:800; color:#fff; margin-bottom:4px; }
	.rd-ucard-desc  { font-size:12.5px; color:rgba(255,255,255,.72); margin-bottom:20px; }
	.rd-ucard-foot  { display:flex; align-items:center; justify-content:space-between; }
	.rd-ucard-pill  { font-size:11px; font-weight:700; padding:5px 14px; border-radius:20px; background:rgba(255,255,255,.2); color:#fff; }
	.rd-ucard-arrow {
		width:32px; height:32px; border-radius:9px;
		background:rgba(255,255,255,.2); color:#fff;
		display:flex; align-items:center; justify-content:center; font-size:15px; transition:all .2s;
	}
	.rd-ucard:hover .rd-ucard-arrow { background:rgba(255,255,255,.35); }
	/* ── detail ── */
	.rd-detail { display:none; }
	.rd-dstats { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:26px; }
	.rd-dstat {
		background:#fff; border:1px solid ${BORD}; border-radius:14px;
		padding:20px 22px; display:flex; align-items:center; gap:16px;
		box-shadow:0 1px 4px rgba(0,0,0,.05); transition:all .2s;
	}
	.rd-dstat:hover { box-shadow:0 6px 24px rgba(0,0,0,.09); transform:translateY(-2px); }
	.rd-dstat-icon { width:46px; height:46px; border-radius:12px; flex-shrink:0; display:flex; align-items:center; justify-content:center; }
	.rd-dstat-icon svg { width:22px; height:22px; }
	.rd-dstat-body { flex:1; min-width:0; }
	.rd-dstat .dsv { font-size:30px; font-weight:900; line-height:1; margin-bottom:4px; }
	.rd-dstat .dsk { font-size:11.5px; font-weight:600; color:${T2}; }
	/* chart */
	.rd-dchart-wrap {
		background:#fff; border:1px solid ${BORD}; border-radius:14px;
		padding:22px 26px 18px; margin-bottom:26px; box-shadow:0 1px 4px rgba(0,0,0,.05);
	}
	.rd-dchart-hdr { display:flex; align-items:baseline; justify-content:space-between; margin-bottom:20px; }
	.rd-dchart-ttl { font-size:14px; font-weight:700; color:${T1}; }
	.rd-dchart-sub { font-size:12px; color:${T2}; }
	.rd-dchart-wrap .chart-container svg { cursor:pointer; }
	.rd-dchart-wrap .chart-container text { fill:${T2} !important; }
	.rd-dchart-wrap .chart-container .x.axis line,
	.rd-dchart-wrap .chart-container .y.axis line { stroke:#e2e8f0 !important; }
	/* status grid */
	.rd-dgrid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:26px; }
	.rd-dcard {
		background:#fff; border:1px solid ${BORD}; border-left:3px solid transparent;
		border-radius:12px; padding:16px 18px 14px; cursor:pointer;
		box-shadow:0 1px 3px rgba(0,0,0,.05); transition:all .18s;
	}
	.rd-dcard:hover { border-left-color:${AC}; box-shadow:0 6px 20px ${ACG}.1); transform:translateY(-2px); }
	.rd-dcard.zero { opacity:.45; cursor:default; }
	.rd-dcard.zero:hover { border-left-color:transparent; box-shadow:0 1px 3px rgba(0,0,0,.05); transform:none; }
	.rd-dcard .dl { font-size:10.5px; font-weight:700; color:${T2}; letter-spacing:.05em; text-transform:uppercase; margin-bottom:10px; line-height:1.4; }
	.rd-dcard .dn { font-size:34px; font-weight:900; color:${AC}; line-height:1; }
	@keyframes dnPop { 0%{transform:scale(.5);opacity:0} 65%{transform:scale(1.15)} 100%{transform:scale(1);opacity:1} }
	.rd-dcard .dn.pop { animation:dnPop .3s cubic-bezier(.34,1.56,.64,1) forwards; }
	/* ── records ── */
	.rd-records { display:none; }
	.rd-rpage-hero {
		border-radius:16px; padding:30px 34px; margin-bottom:24px;
		background:linear-gradient(135deg,#1e1b4b 0%,#3730a3 60%,#6366f1 100%);
		position:relative; overflow:hidden;
	}
	.rd-rpage-hero::before {
		content:''; position:absolute; right:-60px; top:-60px;
		width:220px; height:220px; border-radius:50%;
		background:rgba(255,255,255,.07); pointer-events:none;
	}
	.rd-rpage-unit  { font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:rgba(255,255,255,.65); margin-bottom:8px; }
	.rd-rpage-title { font-size:26px; font-weight:900; color:#fff; margin-bottom:6px; }
	.rd-rpage-meta  { font-size:13px; color:rgba(255,255,255,.65); }
	.rd-rpage-big   { position:absolute; top:14px; right:30px; font-size:80px; font-weight:900; color:rgba(255,255,255,.08); line-height:1; pointer-events:none; }
	.rd-rpage-card  { background:#fff; border:1px solid ${BORD}; border-radius:14px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.05); }
	.rd-rpage-toolbar { display:flex; align-items:center; gap:12px; padding:14px 20px; border-bottom:1px solid ${BORD}; }
	.rd-rpage-tlabel { font-size:14px; font-weight:700; color:${T1}; flex:1; }
	.rd-rpage-tcnt { font-size:12px; font-weight:600; padding:4px 12px; border-radius:20px; background:${ACG}.08); color:${AC}; border:1px solid ${ACG}.2); }
	.rd-rpage-srch {
		padding:8px 14px; border:1px solid ${BORD}; border-radius:8px;
		font-size:13px; width:240px; outline:none; background:#fafbff; color:${T1};
		transition:border-color .18s,box-shadow .18s;
	}
	.rd-rpage-srch::placeholder { color:${T2}; }
	.rd-rpage-srch:focus { border-color:${AC}; box-shadow:0 0 0 3px ${ACG}.1); }
	.rd-rpage-body { overflow-x:auto; max-height:560px; overflow-y:auto; }
	.rd-rpage-foot { display:flex; align-items:center; justify-content:space-between; padding:11px 20px; border-top:1px solid ${BORD}; font-size:12px; color:${T2}; background:#fafbff; }
	/* ── profile ── */
	.rd-profile { display:none; }
	.rdp-hero {
		background:linear-gradient(130deg,#1e1b4b 0%,#3730a3 55%,#6366f1 100%);
		border-radius:18px; padding:32px 36px; margin-bottom:24px;
		display:flex; align-items:center; gap:28px; position:relative; overflow:hidden;
	}
	.rdp-hero::before {
		content:''; position:absolute; right:-60px; top:-60px;
		width:240px; height:240px; border-radius:50%;
		background:rgba(255,255,255,.07); pointer-events:none;
	}
	.rdp-avatar {
		width:72px; height:72px; border-radius:18px; flex-shrink:0;
		background:rgba(255,255,255,.2); border:2px solid rgba(255,255,255,.35);
		color:#fff; display:flex; align-items:center; justify-content:center;
		font-size:28px; font-weight:900;
	}
	.rdp-hero-info { flex:1; min-width:0; }
	.rdp-hero-name { font-size:24px; font-weight:900; color:#fff; margin-bottom:4px; }
	.rdp-hero-id   { font-size:12px; color:rgba(255,255,255,.6); margin-bottom:12px; font-family:monospace; }
	.rdp-hero-badges { display:flex; gap:8px; flex-wrap:wrap; }
	.rdp-badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:12px; font-weight:700; border:1px solid; }
	.rdp-badge-unit { background:rgba(255,255,255,.15); color:#fff; border-color:rgba(255,255,255,.2); font-size:11px; }
	.rdp-body { display:flex; flex-direction:column; gap:14px; }
	.rdp-section { background:#fff; border:1px solid ${BORD}; border-radius:14px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.05); }
	.rdp-section-hdr { padding:13px 22px; background:#fafbff; border-bottom:1px solid ${BORD}; display:flex; align-items:center; gap:10px; }
	.rdp-section-dot { width:8px; height:8px; border-radius:3px; background:${AC}; }
	.rdp-section-ttl { font-size:11.5px; font-weight:700; color:${AC}; text-transform:uppercase; letter-spacing:.07em; }
	.rdp-fields { display:grid; grid-template-columns:repeat(3,1fr); }
	.rdp-field { padding:14px 22px; border-bottom:1px solid ${BORD}; transition:background .12s; }
	.rdp-field:hover { background:#fafbff; }
	.rdp-field-label { font-size:10.5px; font-weight:700; color:${T2}; text-transform:uppercase; letter-spacing:.05em; margin-bottom:5px; }
	.rdp-field-value { font-size:14px; font-weight:600; color:${T1}; word-break:break-word; }
	.rdp-nodata { padding:48px; text-align:center; color:${T2}; font-size:14px; }
	.rdp-loading { padding:60px; text-align:center; color:${T2}; font-size:13px; }
	/* shared table */
	.rd-tbl { width:100%; border-collapse:collapse; font-size:13.5px; }
	.rd-tbl thead tr { position:sticky; top:0; z-index:2; background:#f8faff; }
	.rd-tbl th { padding:11px 16px; text-align:left; font-size:10.5px; font-weight:700; color:${T2}; text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid ${BORD}; white-space:nowrap; }
	.rd-tbl tbody tr { cursor:pointer; transition:background .1s; }
	.rd-tbl tbody tr:hover { background:${ACG}.05); }
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

	function fmtDate() {
		return new Date().toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long', year:'numeric' });
	}

	// ── date filter helpers ───────────────────────────────────────────────────
	function filterByDate(rows, key) {
		if (key === 'all') return rows;
		const now = new Date();
		let start, end;
		if (key === 'custom') {
			if (!customFrom && !customTo) return rows;
			start = customFrom ? new Date(customFrom) : null;
			end   = customTo   ? new Date(customTo + 'T23:59:59') : null;
			return rows.filter(function(r) {
				if (!r.creation) return false;
				const d = new Date(r.creation);
				return (!start || d >= start) && (!end || d <= end);
			});
		}
		if (key === 'today') {
			start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
		} else if (key === 'week') {
			start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay());
		} else if (key === 'month') {
			start = new Date(now.getFullYear(), now.getMonth(), 1);
		} else if (key === 'quarter') {
			start = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
		} else {
			start = new Date(now.getFullYear(), 0, 1);
		}
		return rows.filter(function(r) { return r.creation && new Date(r.creation) >= start; });
	}

	function getFilteredData(ui) {
		if (!store[ui]) return { rows: [], counts: {} };
		const rows = filterByDate(store[ui].rows, activeFilter);
		const counts = {};
		rows.forEach(function(row) {
			const s = row[UNITS[ui].status_field] || 'New Applicant';
			counts[s] = (counts[s] || 0) + 1;
		});
		return { rows, counts };
	}

	function updateFrontStats() {
		let total = 0, offers = 0;
		UNITS.forEach(function(unit, ui) {
			if (!store[ui]) return;
			const { rows, counts } = getFilteredData(ui);
			$('#unum-' + ui).text(rows.length);
			total  += rows.length;
			offers += unit.offerStatuses.reduce(function(s, st) { return s + (counts[st] || 0); }, 0);
		});
		$('#gs-total').text(total);
		$('#gs-offers').text(offers);
	}

	// ── front page ────────────────────────────────────────────────────────────
	$front.html(`
		<div class="rd-hero">
			<div class="rd-hero-eyebrow">
				<span class="rd-hero-dot"></span>
				Azim Premji Foundation
			</div>
			<div class="rd-hero-title">Recruitment Dashboard</div>
			<div class="rd-hero-sub">Monitor applicants across all recruitment units. Filter by date or select a unit to explore.</div>
			<div class="rd-hero-stats">
				<div class="rd-hstat"><span class="rd-hstat-v" id="gs-total">—</span><span class="rd-hstat-k">Total Applicants</span></div>
				<div class="rd-hstat"><span class="rd-hstat-v" id="gs-offers">—</span><span class="rd-hstat-k">Total Offers</span></div>
				<div class="rd-hstat"><span class="rd-hstat-v">4</span><span class="rd-hstat-k">Active Units</span></div>
			</div>
			<div class="rd-filter-row">
				${DATE_FILTERS.map(function(f) {
					return '<button class="rd-filter-btn' + (f.key === 'all' ? ' active' : '') + '" data-key="' + f.key + '">' + f.label + '</button>';
				}).join('')}
			</div>
			<div class="rd-custom-row" id="rd-custom-row">
				<span class="rd-custom-label">From</span>
				<input type="date" class="rd-date-input" id="rd-from-date" />
				<span class="rd-custom-label">To</span>
				<input type="date" class="rd-date-input" id="rd-to-date" />
				<button class="rd-apply-btn" id="rd-apply-custom">Apply</button>
			</div>
		</div>
		<div class="rd-section-label" style="margin-top:8px">Recruitment Units</div>
		<div class="rd-units">
			${UNITS.map(function(u, i) {
				return '<div class="rd-ucard" data-ui="' + i + '" style="background:linear-gradient(135deg,' + CARD_G1 + ' 0%,' + CARD_G2 + ' 100%)">' +
					'<div class="rd-ucard-top"><div class="rd-ucard-icon">' + u.icon + '</div><div class="rd-ucard-num" id="unum-' + i + '">—</div></div>' +
					'<div class="rd-ucard-label">' + u.label + '</div>' +
					'<div class="rd-ucard-desc">' + u.desc + '</div>' +
					'<div class="rd-ucard-foot"><span class="rd-ucard-pill">View Pipeline</span><span class="rd-ucard-arrow">&#8594;</span></div>' +
					'</div>';
			}).join('')}
		</div>
	`);

	$front.on('click', '.rd-ucard', function () {
		showDetail(parseInt($(this).data('ui')));
	});

	$front.on('click', '.rd-filter-btn', function () {
		activeFilter = $(this).data('key');
		$front.find('.rd-filter-btn').removeClass('active');
		$(this).addClass('active');
		if (activeFilter === 'custom') {
			$('#rd-custom-row').addClass('show');
		} else {
			$('#rd-custom-row').removeClass('show');
			customFrom = ''; customTo = '';
			updateFrontStats();
		}
	});

	$front.on('click', '#rd-apply-custom', function () {
		customFrom = $('#rd-from-date').val();
		customTo   = $('#rd-to-date').val();
		updateFrontStats();
	});

	// ── fetch all units (include creation for date filter) ────────────────────
	UNITS.forEach(function (unit, ui) {
		const fields = ['name', 'creation', unit.status_field].concat(unit.columns.map(function(c) { return c.field; }));
		frappe.call({
			method: 'frappe.client.get_list',
			args: { doctype: unit.doctype, fields: fields, filters: [['name','!=','']], limit_page_length: 0 },
			callback: function (r) {
				store[ui] = { rows: r && r.message ? r.message : [] };
				updateFrontStats();
			}
		});
	});

	// ── detail page ───────────────────────────────────────────────────────────
	function showDetail(ui) {
		const unit = UNITS[ui];
		if (!store[ui]) { frappe.msgprint('Data still loading, please wait.'); return; }
		const { rows, counts } = getFilteredData(ui);
		const total    = rows.length;
		const RW       = ['reject','blocklist','regret'];
		const offered  = unit.offerStatuses.reduce(function(s, st) { return s + (counts[st] || 0); }, 0);
		const docColl  = counts['Document Collection'] || 0;
		let   rejected = 0;
		Object.keys(counts).forEach(function(s) { if (RW.some(function(w) { return s.toLowerCase().includes(w); })) rejected += counts[s]; });
		const pipeline = Math.max(0, total - offered - docColl - rejected);

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
				<div class="rd-dstat" id="rd-dstat-total" style="cursor:pointer">
					<div class="rd-dstat-icon" style="background:linear-gradient(135deg,${CARD_G1},${CARD_G2})">
						<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:${CARD_G1}">${total}</div><div class="dsk">Total Applicants</div></div>
				</div>
				<div class="rd-dstat">
					<div class="rd-dstat-icon" style="background:linear-gradient(135deg,#22c55e,#4ade80)">
						<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:#16a34a">${offered}</div><div class="dsk">Offered</div></div>
				</div>
				<div class="rd-dstat">
					<div class="rd-dstat-icon" style="background:linear-gradient(135deg,#ef4444,#f87171)">
						<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:#dc2626">${rejected}</div><div class="dsk">Rejected</div></div>
				</div>
				<div class="rd-dstat">
					<div class="rd-dstat-icon" style="background:linear-gradient(135deg,#06b6d4,#67e8f9)">
						<svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>
					</div>
					<div class="rd-dstat-body"><div class="dsv" style="color:#0891b2">${pipeline}</div><div class="dsk">In Pipeline</div></div>
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
				${unit.statuses.map(function(s) {
					return '<div class="rd-dcard' + ((counts[s] || 0) === 0 ? ' zero' : '') + '" data-status="' + s + '">' +
						'<div class="dl">' + s + '</div>' +
						'<div class="dn pop">' + (counts[s] || 0) + '</div></div>';
				}).join('')}
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
		const isAll      = status === null;
		const filtered   = isAll ? allRows : allRows.filter(function(r) { return (r[unit.status_field] || 'New Applicant') === status; });
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
			const f = q ? filtered.filter(function(r) { return unit.columns.some(function(c) { return (r[c.field]||'').toLowerCase().includes(q); }); }) : filtered;
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
				const doc         = r.message;
				const displayName = doc[unit.nameField] || docName;
				const initial     = (displayName || '?').trim()[0].toUpperCase();
				const RW          = ['reject','blocklist','regret'];
				const isOffer     = unit.offerStatuses.includes(status);
				const isReject    = RW.some(function(w) { return status.toLowerCase().includes(w); });
				const isHold      = status.toLowerCase().includes('hold');
				const badgeBg     = isOffer ? 'rgba(34,197,94,.15)'  : isReject ? 'rgba(239,68,68,.15)'  : isHold ? 'rgba(245,158,11,.15)' : ACG+'.12)';
				const badgeClr    = isOffer ? '#16a34a' : isReject ? '#dc2626' : isHold ? '#d97706' : AC;
				const badgeBd     = isOffer ? 'rgba(34,197,94,.3)'   : isReject ? 'rgba(239,68,68,.3)'   : isHold ? 'rgba(245,158,11,.3)'  : ACG+'.25)';

				const sectionsHtml = unit.profileFields.map(function(sec) {
					const fh = sec.cols.map(function(f) {
						const v = doc[f.field];
						if (v === null || v === undefined || v === '') return '';
						return '<div class="rdp-field"><div class="rdp-field-label">' + f.label + '</div><div class="rdp-field-value">' + v + '</div></div>';
					}).join('');
					if (!fh) return '';
					return '<div class="rdp-section"><div class="rdp-section-hdr"><div class="rdp-section-dot"></div><div class="rdp-section-ttl">' + sec.section + '</div></div><div class="rdp-fields">' + fh + '</div></div>';
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
		const labels = unit.statuses.filter(function(s) { return (counts[s] || 0) > 0; });
		const values = labels.map(function(s) { return counts[s]; });
		const barEl  = document.getElementById('rd-bar');
		if (!barEl || !labels.length) return;
		try {
			new frappe.Chart(barEl, {
				type: 'bar', height: 240, colors: [AC],
				data: { labels: labels, datasets: [{ name: 'Applicants', values: values }] },
				barOptions: { spaceRatio: 0.3 },
				tooltipOptions: { formatTooltipY: function(d) { return d + ' applicants'; } }
			});
			barEl.addEventListener('data-select', function (e) {
				const lbl = e.label || (e.detail && e.detail.label);
				if (lbl) showRecords(unit, allRows, lbl);
			});
		} catch(err) {}
	}

	// ── table builder ─────────────────────────────────────────────────────────
	function buildTable(unit, rows) {
		if (!rows.length) return '<div class="rd-nodata">No records found.</div>';
		const thHtml = unit.columns.map(function(c) { return '<th>' + c.label + '</th>'; }).join('');
		const trs = rows.map(function(r, i) {
			const tds = unit.columns.map(function(c, ci) {
				const v = r[c.field] || '—';
				return ci === 0 ? '<td class="rd-tname" title="' + v + '">' + v + '</td>' : '<td title="' + v + '">' + v + '</td>';
			}).join('');
			return '<tr data-name="' + (r.name||'') + '"><td class="tsno">' + (i+1) + '</td><td class="tid">' + (r.name||'') + '</td>' + tds + '</tr>';
		}).join('');
		return '<table class="rd-tbl"><thead><tr><th>#</th><th>ID</th>' + thHtml + '</tr></thead><tbody>' + trs + '</tbody></table>';
	}
};
