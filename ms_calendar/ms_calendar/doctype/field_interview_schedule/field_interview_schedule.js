// Copyright (c) 2026, Augustin Moses and contributors
// For license information, please see license.txt

// ─────────────────────────────────────────────────────────────────────────────
// Loader helpers
// ─────────────────────────────────────────────────────────────────────────────
function showInterviewLoader(title, subtitle, mode) {
    if ($('#interview-pro-loader').length) {
        $('#interview-pro-loader').remove();
    }

    // ── Build steps based on mode ─────────────────────────────────────────
    var stepsHtml = '';
    if (mode === 'room') {
        // Room availability flow
        var roomSteps = [
            {
                icon: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
                title: 'Connecting to Microsoft Graph',
                desc: 'Authenticating with Microsoft 365 services',
                active: true, done: true, delay: '0s'
            },
            {
                icon: '<div style="width:8px;height:8px;border-radius:50%;background:#2563eb;animation:ld-dot-blink 0.8s ease-in-out infinite;"></div>',
                title: 'Fetching Room Calendars',
                desc: 'Retrieving all available meeting rooms',
                active: true, done: false, delay: '0.4s'
            },
            {
                icon: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
                title: 'Checking Availability Slots',
                desc: 'Comparing room schedules for your time slot',
                active: false, done: false, delay: ''
            }
        ];
        stepsHtml = buildStepsHtml(roomSteps);
    } else {
        // Calendar event creation flow (default)
        var calSteps = [
            {
                icon: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>',
                title: 'Validating Interview Details',
                desc: 'Checking date, time slots and participant info',
                active: true, done: true, delay: '0s'
            },
            {
                icon: '<div style="width:8px;height:8px;border-radius:50%;background:#2563eb;animation:ld-dot-blink 0.8s ease-in-out infinite;"></div>',
                title: 'Creating Calendar Event',
                desc: 'Syncing with Microsoft Calendar & booking rooms',
                active: true, done: false, delay: '0.4s'
            },
            {
                icon: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.17 1.21 2 2 0 012.18 0h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.91 7.16a16 16 0 006.29 6.29l1.42-1.42a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 14.17z"/></svg>',
                title: 'Sending Notifications',
                desc: 'Emailing invites to interviewers & candidate',
                active: false, done: false, delay: ''
            }
        ];
        stepsHtml = buildStepsHtml(calSteps);
    }

    function buildStepsHtml(steps) {
        var html = '';
        steps.forEach(function (step, i) {
            var circleBg = step.active ? '#eff6ff' : '#f8fafc';
            var circleBdr = step.active ? '#2563eb' : '#cbd5e1';
            var pulse = step.active && !step.done
                ? 'animation:ld-step-pulse 2s ease-in-out infinite ' + step.delay + ';' : '';
            var titleColor = step.active ? '#0f172a' : '#94a3b8';
            var descColor = step.active ? '#64748b' : '#cbd5e1';
            var divider = i < steps.length - 1
                ? '<div style="margin-left:13px;width:2px;height:10px;background:'
                + (step.done ? 'linear-gradient(#2563eb,#e2e8f0)' : '#e2e8f0')
                + ';margin-bottom:4px;"></div>'
                : '';
            html += `
                <div style="display:flex;align-items:flex-start;gap:14px;margin-bottom:14px;">
                    <div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;
                        background:${circleBg};border:2px solid ${circleBdr};
                        display:flex;align-items:center;justify-content:center;${pulse}">
                        ${step.icon}
                    </div>
                    <div style="padding-top:4px;">
                        <div style="font-size:13px;font-weight:600;color:${titleColor};">${step.title}</div>
                        <div style="font-size:11px;color:${descColor};margin-top:1px;">${step.desc}</div>
                    </div>
                </div>
                ${divider}`;
        });
        return html;
    }

    $('body').append(`
        <div id="interview-pro-loader" style="
            position:fixed;top:0;left:0;width:100%;height:100%;
            background:rgba(2,8,23,0.72);backdrop-filter:blur(12px);
            display:flex;align-items:center;justify-content:center;
            z-index:99999;font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;">

            <div style="
                background:#ffffff;border-radius:16px;
                width:460px;overflow:hidden;
                box-shadow:0 32px 80px rgba(0,0,0,0.25),0 0 0 1px rgba(0,0,0,0.06);">

                <!-- ── HEADER BAND ── -->
                <div style="
                    background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 60%,#2563eb 100%);
                    padding:28px 32px 24px;position:relative;overflow:hidden;">

                    <!-- background circles -->
                    <div style="position:absolute;top:-30px;right:-30px;width:120px;height:120px;
                        border-radius:50%;background:rgba(255,255,255,0.05);"></div>
                    <div style="position:absolute;bottom:-40px;right:60px;width:90px;height:90px;
                        border-radius:50%;background:rgba(255,255,255,0.04);"></div>

                    <!-- brand row -->
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
                        <div style="
                            width:40px;height:40px;border-radius:10px;
                            background:rgba(255,255,255,0.15);
                            display:flex;align-items:center;justify-content:center;
                            border:1px solid rgba(255,255,255,0.2);">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                                stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="4" width="18" height="18" rx="2"/>
                                <line x1="16" y1="2" x2="16" y2="6"/>
                                <line x1="8" y1="2" x2="8" y2="6"/>
                                <line x1="3" y1="10" x2="21" y2="10"/>
                                <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/>
                            </svg>
                        </div>
                        <div>
                            <div style="font-size:11px;color:rgba(255,255,255,0.6);
                                font-weight:500;letter-spacing:0.08em;text-transform:uppercase;">
                                Interview Management System
                            </div>
                            <div style="font-size:15px;font-weight:700;color:#ffffff;margin-top:1px;">
                                ${title || 'Processing Request'}
                            </div>
                        </div>
                    </div>

                    <!-- spinner + status row -->
                    <div style="display:flex;align-items:center;gap:14px;">
                        <div style="position:relative;width:36px;height:36px;flex-shrink:0;">
                            <div style="position:absolute;inset:0;border-radius:50%;
                                border:2.5px solid rgba(255,255,255,0.15);
                                border-top-color:#ffffff;
                                animation:ld-spin 0.8s linear infinite;"></div>
                            <div style="position:absolute;inset:7px;border-radius:50%;
                                border:2px solid rgba(255,255,255,0.1);
                                border-top-color:rgba(255,255,255,0.6);
                                animation:ld-spin 1.2s linear infinite reverse;"></div>
                        </div>
                        <div style="font-size:13px;color:rgba(255,255,255,0.85);line-height:1.5;">
                            ${subtitle || 'Please wait while we process your request…'}
                        </div>
                    </div>
                </div>

                <!-- ── STEPS SECTION ── -->
                <div style="padding:24px 32px 20px;">
                    <div style="font-size:11px;font-weight:600;color:#94a3b8;
                        letter-spacing:0.07em;text-transform:uppercase;margin-bottom:16px;">
                        Processing Steps
                    </div>
                    ${stepsHtml}
                </div>

                <!-- ── PROGRESS BAR ── -->
                <div style="padding:0 32px 20px;">
                    <div style="display:flex;justify-content:space-between;
                        font-size:10px;color:#94a3b8;font-weight:500;margin-bottom:6px;">
                        <span>Progress</span><span id="ld-pct">0%</span>
                    </div>
                    <div style="height:5px;background:#f1f5f9;border-radius:99px;overflow:hidden;">
                        <div id="ld-bar" style="
                            height:100%;width:0%;border-radius:99px;
                            background:linear-gradient(90deg,#1d4ed8,#3b82f6,#60a5fa);
                            transition:width 0.4s ease;"></div>
                    </div>
                </div>

                <!-- ── FOOTER ── -->
                <div style="
                    padding:12px 32px;
                    background:#f8fafc;border-top:1px solid #f1f5f9;
                    display:flex;align-items:center;justify-content:space-between;">
                    <div style="display:flex;align-items:center;gap:6px;">
                        <div style="width:6px;height:6px;border-radius:50%;background:#22c55e;
                            animation:ld-live 1.5s ease-in-out infinite;"></div>
                        <span style="font-size:11px;color:#64748b;font-weight:500;">Secure Connection</span>
                    </div>
                    <span style="font-size:11px;color:#94a3b8;">Do not close this window</span>
                </div>
            </div>
        </div>

        <style>
            @keyframes ld-spin {
                to { transform:rotate(360deg); }
            }
            @keyframes ld-dot-blink {
                0%,100% { opacity:0.3; transform:scale(0.8); }
                50%      { opacity:1;   transform:scale(1.2); }
            }
            @keyframes ld-step-pulse {
                0%,100% { box-shadow:0 0 0 0 rgba(37,99,235,0.3); }
                50%      { box-shadow:0 0 0 5px rgba(37,99,235,0); }
            }
            @keyframes ld-live {
                0%,100% { opacity:1; transform:scale(1); }
                50%      { opacity:0.4; transform:scale(0.7); }
            }
        </style>
    `);

    // animate progress bar 0 → 85% over ~4 seconds
    var pct = 0;
    var interval = setInterval(function () {
        pct += (pct < 50 ? 3 : pct < 75 ? 1.2 : 0.4);
        if (pct >= 85) { pct = 85; clearInterval(interval); }
        var bar = document.getElementById('ld-bar');
        var lbl = document.getElementById('ld-pct');
        if (bar) bar.style.width = pct.toFixed(0) + '%';
        if (lbl) lbl.textContent = pct.toFixed(0) + '%';
    }, 120);
    window._ldrInterval = interval;
}

function hideInterviewLoader() {
    if (window._ldrInterval) { clearInterval(window._ldrInterval); window._ldrInterval = null; }
    $('#interview-pro-loader').remove();
}
// ─────────────────────────────────────────────────────────────────────────────

frappe.ui.form.on('Field Interview Schedule', {
    refresh: function (frm) {
        frm.toggle_display('available_slots_section', false);
        // Reset scheduling guard on form load/refresh
        frm._scheduling_in_progress = false;
        // Clear application_id on new documents
        if (frm.is_new()) {
            frm.set_value('application_id', '');
        }

        // ── Schedule Another Interview button ────────────────────────────
        frm.add_custom_button('Schedule Another Interview', function () {
            frappe.new_doc('Field Interview Schedule', {
                application_id:       frm.doc.application_id,
                applicants_name:      frm.doc.applicants_name,
                role:                 frm.doc.role,
                department:           frm.doc.department,
                phone_no:             frm.doc.phone_no,
                organizer_email:      frm.doc.organizer_email,
                attendees:            frm.doc.attendees,
                candidate_cv__resume: frm.doc.candidate_cv__resume,
                feedback_form_link:   frm.doc.feedback_form_link,
                interview_mode:       frm.doc.interview_mode,
                google_map:           frm.doc.google_map,
                location:             frm.doc.location,
            });
        });
    },

    application_id: function (frm) {
        if (!frm.doc.application_id) return;
        frappe.db.exists('DocType', 'Field Registration Form').then(function (exists) {
            var _doctype = exists ? 'Field Registration Form' : 'Field Registration Form1';
            frappe.db.get_value(
                _doctype,
                frm.doc.application_id,
                ['email_address', 'phone_number', 'full_name_aadhaar'],
                function (r) {
                    if (!r) return;
                    if (r.email_address) frm.set_value('attendees', r.email_address);
                    if (r.phone_number)  frm.set_value('phone_no', r.phone_number);
                    if (r.full_name_aadhaar) frm.set_value('applicants_name', r.full_name_aadhaar);
                }
            );
        });
    },

    after_save: function (frm) {
        // ── Guard: prevent double-fire ───────────────────────────────────
        if (frm._scheduling_in_progress) return;

        // ── Validate required fields ─────────────────────────────────────
        if (
            !frm.doc.interviewer_email ||
            !frm.doc.attendees ||
            !frm.doc.interview_date ||
            !frm.doc.start_time ||
            !frm.doc.end_time
        ) {
            frappe.msgprint(__('Please fill Interviewer Email, Candidate Email, Date, Start Time and End Time.'));
            return;
        }

        if (!frm.doc.organizer_email) {
            frappe.msgprint({
                title: __('Missing Organizer Email'),
                message: __('Please select an <b>Organizer Email</b> before saving. This is required to create the calendar event.'),
                indicator: 'red'
            });
            return;
        }

        frm._scheduling_in_progress = true;

        // ✅ Explicit format strings — avoids moment.js deprecation on cloud
        const startDateTime = moment(
            frm.doc.interview_date + " " + frm.doc.start_time, "YYYY-MM-DD HH:mm:ss"
        ).format("YYYY-MM-DDTHH:mm:ss");
        const endDateTime = moment(
            frm.doc.interview_date + " " + frm.doc.end_time, "YYYY-MM-DD HH:mm:ss"
        ).format("YYYY-MM-DDTHH:mm:ss");

        // 1️⃣ Get interviewer emails
        const interviewerEmailsArr = (frm.doc.interviewer_email || [])
            .map(function (row) { return row.interviewer_email; })
            .filter(function (email) { return !!email; });
        const interviewerEmailsString = interviewerEmailsArr.join(",");

        // 2️⃣ Build attachments
        var attachments = [];
        if (frm.doc.candidate_cv__resume) {
            attachments.push(frm.doc.candidate_cv__resume);
        }
        if (frm.doc.feedback_form) {
            attachments.push(frm.doc.feedback_form);
        }
        const attachmentPathsStr = JSON.stringify(attachments);

        // 3️⃣ Read conditional fields directly from frm.doc
        const locationValue = frm.doc.location || "";
        const phoneNoValue = frm.doc.phone_no || "";
        const mapLocValue = frm.doc.google_map || "";
        const interviewMode = frm.doc.interview_mode || "Face-to-Face";

        // 4️⃣ Show loader
        showInterviewLoader(
            'Creating Calendar Event',
            'Scheduling interview & sending notifications…'
        );

        // 5️⃣ Use email addresses directly as names (field is now plain Data)
        Promise.resolve(interviewerEmailsArr).then(function (interviewerNamesArray) {
            var interviewerNamesString = interviewerNamesArray.join(", ");

            frappe.call({
                method: "ms_calendar.api.ms_field.create_interview_event",
                args: {
                    event_title: frm.doc.event_title || "Interview",
                    start_datetime: startDateTime,
                    end_datetime: endDateTime,
                    interviewer_emails: interviewerEmailsString,
                    interviewee_email: frm.doc.attendees,
                    room_emails: frm.doc.room_email || "",
                    is_online: frm.doc.interview_type || 0,
                    Organizer_email: frm.doc.organizer_email,
                    Interview_round: frm.doc.interview_round,
                    InterviewersName: interviewerNamesString,
                    Applicants_name: frm.doc.applicants_name,
                    Applicants_Role: frm.doc.role,
                    department: frm.doc.department || "",
                    application_id: frm.doc.application_id || "",

                    interview_mode: interviewMode,
                    candidate_phone: phoneNoValue,
                    Map_location: mapLocValue,
                    address: locationValue,
                    commands_to_candidate: "",
                    commands_to_interviewer: "",
                    attachment_paths: attachmentPathsStr,
                    demo_feed_back_form: frm.doc.demo_feed_back_form || 0,
                    feedback_form_link: frm.doc.feedback_form_link || "",
                    demo_feedback_interviewers_email: (frm.doc.demo_feedback_interviewers_email || [])
                        .map(function (row) { return row.interviewer_email; })
                        .filter(function (e) { return !!e; })
                        .join(",")
                },
                callback: function (r) {
                    frm._scheduling_in_progress = false;
                    hideInterviewLoader();
                    if (r && r.message) {
                        console.log("Interview event result:", r.message);
                        frappe.msgprint({
                            title: __("Success"),
                            message: __("Interview scheduled successfully! Mode: ") + (r.message.mode || ""),
                            indicator: "green"
                        });
                    }
                },
                error: function (err) {
                    frm._scheduling_in_progress = false;
                    hideInterviewLoader();
                    frappe.msgprint({
                        title: __("Error"),
                        message: __("Failed to create calendar event. Please check server logs."),
                        indicator: "red"
                    });
                    console.error("Calendar Event Error:", err);
                }
            });

        }).catch(function (err) {
            frm._scheduling_in_progress = false;
            hideInterviewLoader();
            console.error("Name resolution error:", err);
        });
    },

    interview_date: function (frm) {
        // Past dates are allowed for scheduling and editing
    },

    start_time: function (frm) {
        if (frm.doc.end_time && frm.doc.start_time) {
            const s = moment(frm.doc.interview_date + " " + frm.doc.start_time, "YYYY-MM-DD HH:mm:ss");
            const e = moment(frm.doc.interview_date + " " + frm.doc.end_time, "YYYY-MM-DD HH:mm:ss");
            if (s.isAfter(e)) {
                frappe.msgprint(__('Start Time must be less than End Time.'));
                frm.set_value('start_time', null);
            }
        }
    },

    end_time: function (frm) {
        if (frm.doc.start_time && frm.doc.end_time) {
            const s = moment(frm.doc.interview_date + " " + frm.doc.start_time, "YYYY-MM-DD HH:mm:ss");
            const e = moment(frm.doc.interview_date + " " + frm.doc.end_time, "YYYY-MM-DD HH:mm:ss");
            if (e.isBefore(s)) {
                frappe.msgprint(__('End Time must be greater than Start Time.'));
                frm.set_value('end_time', null);
            }
        }
    },

    check_available_room: function (frm) {
        if (!frm.doc.interview_date || !frm.doc.start_time || !frm.doc.end_time) {
            showCustomDialog(frm, 'Missing Information', 'Please fill Interview Date, Start Time, and End Time.', '#dc2626', 'fa-exclamation-circle');
            return;
        }

        const startDateTime = moment(frm.doc.interview_date + " " + frm.doc.start_time, "YYYY-MM-DD HH:mm:ss");
        const endDateTime = moment(frm.doc.interview_date + " " + frm.doc.end_time, "YYYY-MM-DD HH:mm:ss");

        if (endDateTime.isBefore(startDateTime)) {
            showCustomDialog(frm, 'Invalid Time', 'End Time must be greater than Start Time.', '#dc2626', 'fa-clock-o');
            return;
        }

        if (!frm.fields_dict.meeting_room) {
            showCustomDialog(frm, 'Configuration Error', 'The "meeting_room" field is missing in the form.', '#dc2626', 'fa-cog');
            return;
        }
        if (!frm.fields_dict.room_email) {
            showCustomDialog(frm, 'Configuration Error', 'The "room_email" field is missing in the form.', '#dc2626', 'fa-cog');
            return;
        }

        if (frm.doc.room_email && frm.doc.room_email.trim() !== '') {
            const emails = frm.doc.room_email.split(', ').filter(function (e) { return e; });
            frm.selected_rooms = [];
            if (frm.room_email_map) {
                frm.selected_rooms = Object.keys(frm.room_email_map).filter(function (room) {
                    return emails.includes(frm.room_email_map[room]);
                });
            } else if (frm.doc.meeting_room) {
                frm.selected_rooms = frm.doc.meeting_room.split(', ');
            }

            const dialog = new frappe.ui.Dialog({
                title: __('Select Meeting Rooms'),
                fields: [{ fieldtype: 'HTML', fieldname: 'rooms_display', options: '' }],
                primary_action_label: __('Block Rooms'),
                primary_action: function () {
                    if (frm.selected_rooms.length > 0) {
                        frm.set_value('meeting_room', frm.selected_rooms.join(', '));
                        frm.set_value('room_email', frm.selected_rooms.map(function (room) {
                            return frm.room_email_map[room] || '';
                        }).join(', '));
                        dialog.hide();
                    } else {
                        showCustomDialog(frm, 'No Rooms Selected', 'Please select at least one available room.', '#dc2626', 'fa-exclamation-circle');
                    }
                }
            });

            dialog.fields_dict.rooms_display.$wrapper.html(
                buildRoomsHtml(frm, frm.room_availability_map
                    ? Object.keys(frm.room_availability_map).map(function (name) {
                        return {
                            name: name,
                            email: frm.room_email_map[name] || '',
                            capacity: frm.room_capacity_map ? (frm.room_capacity_map[name] || 'N/A') : 'N/A',
                            is_available: frm.room_availability_map[name] || false
                        };
                    })
                    : [])
            );

            attachRoomEvents(dialog, frm);
            styleDialog(dialog);
            dialog.show();

        } else {
            showInterviewLoader('Fetching Meeting Rooms', 'Checking availability across all rooms…', 'room');

            frappe.call({
                method: 'ms_calendar.api.ms_field.get_org_rooms_and_availability',
                args: {
                    interview_date: frm.doc.interview_date,
                    start_time: frm.doc.start_time,
                    end_time: frm.doc.end_time
                },
                callback: function (r) {
                    hideInterviewLoader();
                    if (r && r.message && r.message.rooms) {
                        const rooms = r.message.rooms;
                        frm.room_email_map = {};
                        frm.room_availability_map = {};
                        frm.room_capacity_map = {};
                        rooms.forEach(function (room) {
                            frm.room_email_map[room.name] = room.email;
                            frm.room_availability_map[room.name] = room.is_available;
                            frm.room_capacity_map[room.name] = room.capacity;
                        });
                        frm.selected_rooms = [];

                        const dialog = new frappe.ui.Dialog({
                            title: __('Select Meeting Rooms'),
                            fields: [{ fieldtype: 'HTML', fieldname: 'rooms_display', options: '' }],
                            primary_action_label: __('Block Rooms'),
                            primary_action: function () {
                                if (frm.selected_rooms.length > 0) {
                                    frm.set_value('meeting_room', frm.selected_rooms.join(', '));
                                    frm.set_value('room_email', frm.selected_rooms.map(function (room) {
                                        return frm.room_email_map[room];
                                    }).join(', '));
                                    dialog.hide();
                                } else {
                                    showCustomDialog(frm, 'No Rooms Selected', 'Please select at least one available room.', '#dc2626', 'fa-exclamation-circle');
                                }
                            }
                        });

                        dialog.fields_dict.rooms_display.$wrapper.html(buildRoomsHtml(frm, rooms));
                        attachRoomEvents(dialog, frm);
                        styleDialog(dialog);
                        dialog.show();

                        if (rooms.filter(function (room) { return room.is_available; }).length === 0) {
                            showCustomDialog(frm, 'No Rooms Available', 'No rooms are available for the selected time slot.', '#f59e0b', 'fa-exclamation-triangle');
                        }
                    } else {
                        showCustomDialog(frm, 'Error', 'Failed to fetch room availability. Please try again.', '#dc2626', 'fa-exclamation-circle');
                    }
                },
                error: function (err) {
                    hideInterviewLoader();
                    showCustomDialog(frm, 'Error', 'Failed to fetch room availability.', '#dc2626', 'fa-exclamation-circle');
                    console.error("Room Availability Error:", err);
                }
            });
        }
    },

    meeting_room: function (frm) {
        const selected_rooms = frm.doc.meeting_room ? frm.doc.meeting_room.split(', ') : [];
        if (selected_rooms.length > 0 && frm.room_email_map) {
            const emails = selected_rooms.map(function (room) {
                return frm.room_email_map[room] || '';
            }).filter(function (e) { return e; });
            frm.set_value('room_email', emails.join(', '));
            const hasBusyRoom = selected_rooms.some(function (room) {
                return !frm.room_availability_map[room];
            });
            if (hasBusyRoom) {
                showCustomDialog(frm, 'Room Unavailable', 'One or more selected rooms are busy for the chosen time slot.', '#f59e0b', 'fa-exclamation-triangle');
            }
        } else {
            frm.set_value('room_email', '');
        }
    },

    check_availability: function (frm) {
        var selected_emails = (frm.doc.interviewer_email || []).map(function (row) {
            return row.interviewer_email;
        });

        if (!selected_emails.length || !frm.doc.interview_date) {
            frappe.msgprint({
                title: __('Missing Information'),
                indicator: 'red',
                message: __('Please enter at least one interviewer email and the interview date.')
            });
            return;
        }

        frm.get_field('available_slots').$wrapper.html(`
            <div class="text-center p-5">
                <div class="spinner-border text-primary mb-3" style="width:3rem;height:3rem;" role="status"></div>
                <h5 class="fw-bold">Checking Availability...</h5>
                <p class="text-muted">Please wait while we fetch available slots.</p>
            </div>
        `);
        frm.toggle_display('available_slots_section', true);

        frappe.call({
            method: 'ms_calendar.api.ms_field.get_schedule_free_slots',
            args: {
                interviewer_emails: selected_emails,
                interview_date: frm.doc.interview_date
            },
            callback: function (r) {
                if (r && r.message) {
                    var allSchedulesHtml = '';
                    Object.keys(r.message).forEach(function (email) {
                        var intervals = r.message[email];
                        var processedEvents = intervals.map(function (interval) {
                            var startUtc = moment.utc(interval.start.dateTime);
                            var endUtc = moment.utc(interval.end.dateTime);
                            var start = startUtc.local();
                            var end = endUtc.local();
                            return {
                                title: "Busy",
                                type: (interval.location && interval.location.displayName)
                                    ? interval.location.displayName : "Meeting",
                                startHour: start.hours() + start.minutes() / 60,
                                endHour: end.hours() + end.minutes() / 60,
                                displayStartTime: start.format("h:mm A"),
                                displayEndTime: end.format("h:mm A"),
                                color: '#e74c3c'
                            };
                        });
                        allSchedulesHtml += frm.events.generate_schedule_html(frm, processedEvents, email);
                    });
                    frm.get_field('available_slots').$wrapper.html(allSchedulesHtml);
                } else {
                    frm.get_field('available_slots').$wrapper.html(
                        '<div class="alert alert-danger">An error occurred while fetching availability.</div>'
                    );
                }
            },
            error: function (err) {
                frappe.msgprint({ title: __("Error"), message: __("Failed to fetch schedule."), indicator: "red" });
                console.error("Schedule Fetch Error:", err);
            }
        });
    },

    generate_schedule_html: function (frm, events, email) {
        const day_start_hour = 8;
        const day_end_hour = 18;
        const total_hours = day_end_hour - day_start_hour;
        const SLOT_WIDTH_PX = 80;

        var timeSlotsHtml = '';
        for (var i = day_start_hour; i < day_end_hour; i++) {
            var hour = i % 12 === 0 ? 12 : i % 12;
            var ampm = i < 12 ? 'AM' : 'PM';
            timeSlotsHtml += `
                <div class="time-slot-group" style="width:${SLOT_WIDTH_PX * 2}px;">
                    <div class="time-slot-hour">
                        <div class="hour-label major">${hour}:00 ${ampm}</div>
                        <div class="hour-line major"></div>
                    </div>
                    <div class="time-slot-half">
                        <div class="hour-label minor">${hour}:30</div>
                        <div class="hour-line minor"></div>
                    </div>
                </div>`;
        }
        var finalHour = day_end_hour % 12 === 0 ? 12 : day_end_hour % 12;
        var finalAmpm = day_end_hour < 12 ? 'AM' : 'PM';
        timeSlotsHtml += `<div class="time-slot-final" style="width:${SLOT_WIDTH_PX}px;">
            <div class="hour-label major">${finalHour}:00 ${finalAmpm}</div>
            <div class="hour-line major"></div></div>`;

        var eventsHtml = '';
        events.forEach(function (event) {
            if (event.endHour <= day_start_hour || event.startHour >= day_end_hour) return;
            var startHour = Math.max(event.startHour, day_start_hour);
            var endHour = Math.min(event.endHour, day_end_hour);
            var leftPct = ((startHour - day_start_hour) / total_hours) * 100;
            var widthPct = ((endHour - startHour) / total_hours) * 100;
            eventsHtml += `
                <div class="schedule-event event-busy"
                     data-start="${event.displayStartTime}" data-end="${event.displayEndTime}"
                     data-title="Busy" data-type="${event.type}"
                     style="left:${leftPct}%;width:${widthPct}%;">
                    <div class="event-content">
                        <div class="event-title">Busy</div>
                        <div class="event-time">${event.displayStartTime} - ${event.displayEndTime}</div>
                    </div>
                    <div class="event-tooltip"><strong>Busy</strong><br>
                        ${event.displayStartTime} - ${event.displayEndTime}</div>
                </div>`;
        });

        var freeSlots = frm.events.calculate_free_slots(events, day_start_hour, day_end_hour);
        freeSlots.forEach(function (slot) {
            var leftPct = ((slot.start - day_start_hour) / total_hours) * 100;
            var widthPct = ((slot.end - slot.start) / total_hours) * 100;
            if (widthPct > 0) {
                var sf = moment().hour(Math.floor(slot.start)).minute((slot.start % 1) * 60).format("h:mm A");
                var ef = moment().hour(Math.floor(slot.end)).minute((slot.end % 1) * 60).format("h:mm A");
                eventsHtml += `
                    <div class="schedule-event event-free"
                         data-start="${sf}" data-end="${ef}" data-title="Free"
                         style="left:${leftPct}%;width:${widthPct}%;">
                        <div class="event-content">
                            <div class="event-title">Free</div>
                            <div class="event-time">${sf} - ${ef}</div>
                        </div>
                        <div class="event-tooltip"><strong>Free</strong><br>${sf} - ${ef}</div>
                    </div>`;
            }
        });

        return `
            <div class="schedule-container">
                <div class="schedule-header">
                    <div class="header-content">
                        <div class="date-section">
                            <h5 class="schedule-date">${moment(frm.doc.interview_date, "YYYY-MM-DD").format('dddd, MMMM DD, YYYY')}</h5>
                        </div>
                        <div class="email-info">
                            <span class="email-label">Calendar Events for</span>
                            <span class="email-address">${email}</span>
                        </div>
                    </div>
                </div>
                <div class="schedule-legend">
                    <div class="legend-items">
                        <div class="legend-item"><div class="legend-dot busy"></div><span>Busy</span></div>
                        <div class="legend-item"><div class="legend-dot available"></div><span>Free</span></div>
                    </div>
                </div>
                <div class="timeline-section">
                    <div class="time-labels">${timeSlotsHtml}</div>
                    <div class="timeline-grid">
                        <div class="timeline-track"></div>
                        ${eventsHtml}
                    </div>
                </div>
                <div class="schedule-footer"><div class="footer-stats"></div></div>
            </div>
            <style>
                .schedule-container{max-width:1200px;margin:20px auto;background:white;border-radius:8px;box-shadow:0 2px 4px -1px rgba(0,0,0,0.1);border:1px solid #e2e8f0;overflow:hidden;font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;}
                .schedule-header{padding:0.75rem;border-bottom:1px solid #e2e8f0;background:linear-gradient(135deg,#f8fafc 0%,#f1f5f9 100%);}
                .header-content{display:flex;justify-content:space-between;align-items:flex-start;}
                .schedule-date{font-size:0.8rem;font-weight:700;color:#1e293b;margin:0 0 0.25rem 0;}
                .email-info{display:flex;flex-direction:column;gap:0.1rem;}
                .email-label{color:#64748b;font-size:0.65rem;font-weight:500;text-transform:uppercase;}
                .email-address{color:#374151;font-size:0.75rem;font-weight:600;font-family:monospace;}
                .schedule-legend{display:flex;justify-content:space-between;align-items:center;padding:0.4rem 0.75rem;background:#f8fafc;border-bottom:1px solid #e2e8f0;}
                .legend-items{display:flex;gap:1rem;}
                .legend-item{display:flex;align-items:center;gap:0.3rem;font-size:0.65rem;color:#475569;}
                .legend-dot{width:10px;height:10px;border-radius:3px;}
                .legend-dot.busy{background:#f87171;}
                .legend-dot.available{background:#6ee7b7;}
                .timeline-section{padding:0.75rem;overflow-x:auto;}
                .time-labels{display:flex;margin-bottom:0.2rem;min-width:800px;}
                .time-slot-group,.time-slot-final{display:flex;flex-direction:column;position:relative;}
                .time-slot-group{justify-content:space-between;}
                .time-slot-hour,.time-slot-half{display:flex;flex-direction:column;align-items:center;flex:1;gap:0.15rem;}
                .time-slot-final{align-items:center;gap:0.15rem;}
                .hour-label{font-size:0.55rem;color:#64748b;text-align:center;}
                .hour-label.major{font-weight:600;color:#374151;font-size:0.6rem;}
                .hour-label.minor{font-weight:500;color:#6b7280;font-size:0.5rem;}
                .hour-line{width:1px;height:6px;}
                .hour-line.major{background:#374151;height:10px;width:1.5px;}
                .hour-line.minor{background:#6b7280;height:4px;}
                .timeline-grid{position:relative;height:40px;border:1px solid #e2e8f0;border-radius:6px;background:#fff;min-width:800px;}
                .timeline-track{position:absolute;top:0;left:0;right:0;bottom:0;background:repeating-linear-gradient(to right,transparent 0%,transparent 4.9%,rgba(107,114,128,0.3) 4.9%,rgba(107,114,128,0.3) 5%,transparent 5%,transparent 9.9%,rgba(55,65,81,0.4) 9.9%,rgba(55,65,81,0.4) 10%);}
                .schedule-event{position:absolute;top:2px;bottom:2px;border-radius:4px;padding:0.15rem;cursor:pointer;transition:all 0.3s ease;display:flex;flex-direction:column;justify-content:center;min-width:40px;z-index:2;box-shadow:0 1px 4px rgba(0,0,0,0.1);overflow:hidden;}
                .schedule-event:hover{transform:translateY(-1px);box-shadow:0 4px 10px rgba(0,0,0,0.15);z-index:10;}
                .event-busy{background:linear-gradient(135deg,#f87171,#fb7185)!important;color:white!important;border:1px solid #f87171!important;}
                .event-free{background:linear-gradient(135deg,#6ee7b7,#34d399)!important;color:white!important;border:1px solid #6ee7b7!important;}
                .event-content{text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
                .event-title{font-weight:600;font-size:0.55rem;line-height:1;margin-bottom:0.05rem;}
                .event-time{font-size:0.5rem;opacity:0.9;line-height:1;}
                .event-tooltip{visibility:hidden;position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);background:#1f2937;color:white;padding:0.3rem 0.5rem;border-radius:4px;font-size:0.55rem;z-index:1000;white-space:nowrap;opacity:0;transition:all 0.3s ease;}
                .event-tooltip::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);border:4px solid transparent;border-top-color:#1f2937;}
                .schedule-event:hover .event-tooltip{visibility:visible;opacity:1;}
                .schedule-footer{padding:0.75rem;background:#f8fafc;border-top:1px solid #e2e8f0;}
            </style>`;
    },

    calculate_free_slots: function (events, day_start_hour, day_end_hour) {
        var slots = [];
        var currentHour = day_start_hour;
        var sortedEvents = events
            .filter(function (e) { return e.endHour > day_start_hour && e.startHour < day_end_hour; })
            .sort(function (a, b) { return a.startHour - b.startHour; });

        sortedEvents.forEach(function (event) {
            var start = Math.max(event.startHour, day_start_hour);
            if (currentHour < start) slots.push({ start: currentHour, end: start });
            currentHour = Math.max(currentHour, event.endHour);
        });

        if (currentHour < day_end_hour) slots.push({ start: currentHour, end: day_end_hour });
        return slots;
    }
});


// ── ROOM DIALOG HELPERS ──────────────────────────────────────────────────────

function buildRoomsHtml(frm, rooms) {
    var timeLabel = moment(frm.doc.interview_date + " " + frm.doc.start_time, "YYYY-MM-DD HH:mm:ss").format('h:mm A')
        + " - " + moment(frm.doc.interview_date + " " + frm.doc.end_time, "YYYY-MM-DD HH:mm:ss").format('h:mm A');
    var html = `
        <style>
            .room-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:8px;max-height:300px;overflow-y:auto;}
            .room-item{min-height:80px;position:relative;padding:8px;border:1px solid #e5e7eb;border-radius:4px;color:white;text-align:center;transition:all 0.2s ease;}
            .room-name{font-weight:600;font-size:11px;margin-top:4px;margin-bottom:3px;word-wrap:break-word;}
            .room-capacity{font-size:9px;opacity:0.9;margin-bottom:3px;}
            .room-status{font-size:9px;opacity:0.9;}
        </style>
        <div style="padding:12px;background:#f9fafb;border-radius:6px;font-family:-apple-system,sans-serif;">
            <div style="margin-bottom:8px;text-align:center;font-size:12px;font-weight:600;color:#1e3a8a;background:#e0e7ff;padding:6px;border-radius:3px;">
                <i class="fa fa-calendar" style="margin-right:4px;"></i>Time Slot: ${timeLabel}
            </div>
            <div style="display:flex;justify-content:center;gap:10px;margin-bottom:10px;font-size:10px;background:#f1f5f9;padding:4px;border-radius:3px;">
                <div><span style="color:#10b981;">●</span> Available</div>
                <div><span style="color:#ef4444;">●</span> Busy</div>
                <div><span style="color:#3b82f6;">●</span> Selected</div>
            </div>
            <div class="room-grid">`;

    rooms.forEach(function (room) {
        var isAvailable = room.is_available;
        var bgColor = isAvailable ? '#10b981' : '#ef4444';
        var statusText = isAvailable ? 'Available' : 'Busy';
        var icon = isAvailable
            ? '<i class="fa fa-check-circle" style="font-size:10px;"></i>'
            : '<i class="fa fa-times-circle" style="font-size:10px;"></i>';
        var isSelected = frm.selected_rooms && frm.selected_rooms.includes(room.name);

        html += `
            <div class="room-item ${isAvailable ? '' : 'disabled'} ${isSelected ? 'selected' : ''}"
                 data-room="${room.name}" data-available="${isAvailable}"
                 style="background:${isSelected ? '#3b82f6' : bgColor};
                        ${isAvailable ? 'cursor:pointer;' : 'cursor:not-allowed;opacity:0.7;'}
                        ${isSelected ? 'border:2px solid #3b82f6;' : ''}">
                <div style="position:absolute;top:-4px;left:-4px;width:18px;height:18px;background:white;border-radius:50%;display:flex;align-items:center;justify-content:center;">${icon}</div>
                <div class="room-name">${room.name}</div>
                <div class="room-capacity">Capacity: ${room.capacity}</div>
                <div class="room-status">${isSelected ? 'Selected' : statusText}</div>
            </div>`;
    });

    html += '</div></div>';
    return html;
}

function attachRoomEvents(dialog, frm) {
    dialog.$wrapper.find('.room-item[data-available="true"]').on('click', function () {
        var roomName = $(this).data('room');
        var isSelected = frm.selected_rooms.includes(roomName);
        if (isSelected) {
            frm.selected_rooms = frm.selected_rooms.filter(function (r) { return r !== roomName; });
            $(this).css({ 'background': '#10b981', 'border': '1px solid #e5e7eb', 'transform': 'scale(1)', 'box-shadow': 'none' }).removeClass('selected');
            $(this).find('.room-status').text('Available');
        } else {
            frm.selected_rooms.push(roomName);
            $(this).css({ 'background': '#3b82f6', 'border': '2px solid #1e3a8a', 'transform': 'scale(1.03)', 'box-shadow': '0 2px 6px rgba(0,0,0,0.15)' }).addClass('selected');
            $(this).find('.room-status').text('Selected');
        }
    });
    dialog.$wrapper.find('.room-item[data-available="true"]').hover(
        function () { if (!$(this).hasClass('selected')) $(this).css({ 'transform': 'scale(1.05)', 'box-shadow': '0 2px 4px rgba(0,0,0,0.15)' }); },
        function () { if (!$(this).hasClass('selected')) $(this).css({ 'transform': 'scale(1)', 'box-shadow': 'none' }); }
    );
}

function styleDialog(dialog) {
    dialog.$wrapper.find('.btn-primary').css({
        'background': 'linear-gradient(135deg, #1e40af, #3b82f6)',
        'border': 'none', 'border-radius': '4px', 'padding': '6px 12px', 'font-weight': '500'
    });
    dialog.$wrapper.find('.modal-content').css({ 'border-radius': '6px', 'max-width': '700px' });
}

function showCustomDialog(frm, title, message, color, icon) {
    var dialog = new frappe.ui.Dialog({
        title: __(title),
        fields: [{
            fieldtype: 'HTML',
            options: `<div style="padding:8px;font-size:11px;color:${color};"><i class="fa ${icon}" style="margin-right:4px;"></i>${message}</div>`
        }],
        primary_action_label: __('OK'),
        primary_action: function () { dialog.hide(); }
    });
    dialog.show();
    dialog.$wrapper.find('.modal-content').css({ 'border-radius': '6px', 'box-shadow': '0 3px 8px rgba(0,0,0,0.1)' });
    dialog.$wrapper.find('.btn-primary').css({ 'background': color, 'border': 'none', 'border-radius': '4px', 'padding': '6px 12px' });
    return dialog;
}
