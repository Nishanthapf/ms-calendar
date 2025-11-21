frappe.ui.form.on('Schedule interview', {
    refresh: function(frm) {
        frm.toggle_display('available_slots_section', false);
    },

 
 async after_save(frm) {

    if (
        !frm.doc.interviewer_email ||
        !frm.doc.attendees ||
        !frm.doc.interview_date ||
        !frm.doc.start_time ||
        !frm.doc.end_time
    ) {
        frappe.msgprint(__('Please fill Interviewer Email, Interviewee Email, Date, Start Time and End Time.'));
        return;
    }

    const startDateTime = moment(`${frm.doc.interview_date} ${frm.doc.start_time}`)
        .format("YYYY-MM-DDTHH:mm:ss");

    const endDateTime = moment(`${frm.doc.interview_date} ${frm.doc.end_time}`)
        .format("YYYY-MM-DDTHH:mm:ss");

    // 1️⃣ Get interviewer emails
    const interviewerEmailsArr = (frm.doc.interviewer_email || [])
        .map(row => row.interviewer_email)
        .filter(email => !!email);

    const interviewerEmailsString = interviewerEmailsArr.join(",");

    // 2️⃣ Fetch interviewer names (SAFE)
    async function get_interviewer_names(emailArray) {
        let names = [];

        for (let email of emailArray) {
            let r = await frappe.db.get_value(
                "Interviewer Email List",
                email,    // PRIMARY KEY = name
                "interviewer_name"
            );

            if (r && r.message && r.message.interviewer_name) {
                names.push(r.message.interviewer_name);
            } else {
                names.push(email);
            }
        }

        return names;
    }

    let interviewerNamesArray = await get_interviewer_names(interviewerEmailsArr);
    let interviewerNamesString = interviewerNamesArray.join(", ");

    let attachments = [];
    if (frm.doc.candidate_cv__resume) {
        attachments.push(frm.doc.candidate_cv__resume);
        attachments.push(frm.doc.feedback_form);

    }

    frappe.call({
        method: "ms_calendar.api.msgraph.create_interview_event",
        args: {
            event_title: frm.doc.event_title || "Interview",
            start_datetime: startDateTime,
            end_datetime: endDateTime,
            interviewer_emails: interviewerEmailsString,
            interviewee_email: frm.doc.attendees,
            room_emails: frm.doc.room_email || "",
            is_online: frm.doc.interview_type,
            Organizer_email: frm.doc.organizer_email,
            Interview_round: frm.doc.interview_round,
            InterviewersName: interviewerNamesString,
            Applicants_name: frm.doc.applicants_name,
            application_id:"APF-001",
            attachment_paths: attachments  
        },
        freeze: true,
        freeze_message: __("Creating calendar event..."),
        callback: function(r) {
            if (r.message) {
                frappe.msgprint({
                    title: __("Success"),
                    message: __("Interview scheduled successfully! Event ID: ") + r.message.master_event_id,
                    indicator: "green"
                });
            }
        },
        error: function(err) {
            frappe.msgprint({
                title: __("Error"),
                message: __("Failed to create calendar event. See console."),
                indicator: "red"
            });
            console.error("Calendar Event Error:", err);
        }
    });
},
    interview_date: function(frm) {
        const today = moment().startOf('day');
        const interviewDate = moment(frm.doc.interview_date, "YYYY-MM-DD");

        if (interviewDate.isBefore(today)) {
            frappe.msgprint(__('Interview Date cannot be in the past.'));
            frm.set_value('interview_date', null);
        }
    },

    start_time: function(frm) {
        if (frm.doc.end_time && frm.doc.start_time) {
            const startDateTime = moment(frm.doc.interview_date + " " + frm.doc.start_time);
            const endDateTime = moment(frm.doc.interview_date + " " + frm.doc.end_time);

            if (startDateTime.isAfter(endDateTime)) {
                frappe.msgprint(__('Start Time must be less than End Time.'));
                frm.set_value('start_time', null);
            }
        }
    },

    end_time: function(frm) {
        if (frm.doc.start_time && frm.doc.end_time) {
            const startDateTime = moment(frm.doc.interview_date + " " + frm.doc.start_time);
            const endDateTime = moment(frm.doc.interview_date + " " + frm.doc.end_time);
            if (endDateTime.isBefore(startDateTime)) {
                frappe.msgprint(__('End Time must be greater than Start Time.'));
                frm.set_value('end_time', null);
            }
        }
    },

    check_available_room: function(frm) {
        // Validate required fields
        if (!frm.doc.interview_date || !frm.doc.start_time || !frm.doc.end_time) {
            showCustomDialog(frm, 'Missing Information', 'Please fill Interview Date, Start Time, and End Time.', '#dc2626', 'fa-exclamation-circle');
            return;
        }

        const startDateTime = moment(frm.doc.interview_date + " " + frm.doc.start_time);
        const endDateTime = moment(frm.doc.interview_date + " " + frm.doc.end_time);

        if (endDateTime.isBefore(startDateTime)) {
            showCustomDialog(frm, 'Invalid Time', 'End Time must be greater than Start Time.', '#dc2626', 'fa-clock-o');
            return;
        }

        // Check if required fields exist
        if (!frm.fields_dict.meeting_room) {
            showCustomDialog(frm, 'Configuration Error', 'The "meeting_room" field is missing in the form. Please add it via Customize Form.', '#dc2626', 'fa-cog');
            return;
        }
        if (!frm.fields_dict.room_email) {
            showCustomDialog(frm, 'Configuration Error', 'The "room_email" field is missing in the form. Please add it via Customize Form.', '#dc2626', 'fa-cog');
            return;
        }

        // Check if room_email has a value to avoid API call
        if (frm.doc.room_email && frm.doc.room_email.trim() !== '') {
            const emails = frm.doc.room_email.split(', ').filter(email => email);
            frm.selected_rooms = [];
            if (frm.room_email_map) {
                frm.selected_rooms = Object.keys(frm.room_email_map).filter(room => emails.includes(frm.room_email_map[room]));
            } else if (frm.doc.meeting_room) {
                frm.selected_rooms = frm.doc.meeting_room.split(', ');
            }

            // Create popup dialog without API call
            const dialog = new frappe.ui.Dialog({
                title: __('Select Meeting Rooms'),
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'rooms_display',
                    options: ''
                }],
                primary_action_label: __('Block Rooms'),
                primary_action: function() {
                    if (frm.selected_rooms.length > 0) {
                        frm.set_value('meeting_room', frm.selected_rooms.join(', '));
                        frm.set_value('room_email', frm.selected_rooms.map(room => frm.room_email_map[room] || '').join(', '));
                        dialog.hide();
                    } else {
                        showCustomDialog(frm, 'No Rooms Selected', 'Please select at least one available room before confirming.', '#dc2626', 'fa-exclamation-circle');
                    }
                }
            });

            // Generate HTML for room selection with pre-selected rooms
            let rooms_html = `
                <style>
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(-10px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    .room-item:hover[data-available="true"]:not(.selected) {
                        transform: scale(1.05);
                    }
                    .room-grid {
                        display: grid;
                        grid-template-columns: repeat(4, 1fr);
                        gap: 8px;
                        padding: 8px;
                        justify-items: center;
                        max-height: 300px;
                        overflow-y: auto;
                        overflow-x: hidden;
                    }
                    .room-item {
                        width: 100%;
                        box-sizing: border-box;
                        min-width: 0;
                        min-height: 80px;
                        position: relative;
                        padding: 8px;
                        border: 1px solid #e5e7eb;
                        border-radius: 4px;
                        color: white;
                        text-align: center;
                        transition: all 0.2s ease;
                    }
                    .room-name {
                        font-weight: 600;
                        font-size: 11px;
                        margin-top: 4px;
                        margin-bottom: 3px;
                        word-wrap: break-word;
                        line-height: 1.3;
                    }
                    .room-capacity {
                        font-size: 9px;
                        opacity: 0.9;
                        margin-bottom: 3px;
                    }
                    .room-status {
                        font-size: 9px;
                        opacity: 0.9;
                    }
                    @media (max-width: 600px) {
                        .room-grid {
                            grid-template-columns: repeat(3, 1fr);
                        }
                    }
                    @media (max-width: 400px) {
                        .room-grid {
                            grid-template-columns: repeat(2, 1fr);
                        }
                    }
                </style>
                <div style="padding: 12px; background: #f9fafb; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;">
                    <div style="margin-bottom: 8px; text-align: center; font-size: 12px; font-weight: 600; color: #1e3a8a; background: #e0e7ff; padding: 6px; border-radius: 3px;">
                        <i class="fa fa-calendar" style="margin-right: 4px;"></i>Time Slot: ${moment(frm.doc.interview_date + " " + frm.doc.start_time).format('h:mm A')} - ${moment(frm.doc.interview_date + " " + frm.doc.end_time).format('h:mm A')}
                    </div>
                    <div class="legend" style="display: flex; justify-content: center; gap: 10px; margin-bottom: 10px; font-size: 10px; color: #1f2937; background: #f1f5f9; padding: 4px; border-radius: 3px;">
                        <div><span style="color: #10b981; font-size: 10px; margin-right: 2px;">●</span>Available</div>
                        <div><span style="color: #ef4444; font-size: 10px; margin-right: 2px;">●</span>Busy</div>
                        <div><span style="color: #3b82f6; font-size: 10px; margin-right: 2px;">●</span>Selected</div>
                    </div>
                    <div class="room-grid" style="animation: fadeIn 0.3s ease-in;">
            `;

            // Use existing room data or mock it if not available
            const roomData = frm.room_availability_map ? Object.keys(frm.room_availability_map).map(name => ({
                name,
                email: frm.room_email_map[name] || '',
                capacity: frm.room_capacity_map ? frm.room_capacity_map[name] || 'N/A' : 'N/A',
                is_available: frm.room_availability_map[name] || false
            })) : [];

            roomData.forEach(room => {
                const isAvailable = room.is_available;
                const bgColor = isAvailable ? '#10b981' : '#ef4444';
                const statusText = isAvailable ? 'Available' : 'Busy';
                const icon = isAvailable ? '<i class="fa fa-check-circle" style="font-size: 10px;"></i>' : '<i class="fa fa-times-circle" style="font-size: 10px;"></i>';
                const isSelected = frm.selected_rooms.includes(room.name);
                const selectedStyle = isSelected ? 'border: 2px solid #3b82f6; transform: scale(1.03); box-shadow: 0 2px 6px rgba(0,0,0,0.15); background: #3b82f6;' : '';
                rooms_html += `
                    <div class="room-item ${isAvailable ? '' : 'disabled'} ${isSelected ? 'selected' : ''}" data-room="${room.name}" data-available="${isAvailable}"
                        style="background: ${isSelected ? '#3b82f6' : bgColor}; ${isAvailable ? 'cursor: pointer;' : 'cursor: not-allowed; opacity: 0.7;'} ${selectedStyle}">
                        <div style="position: absolute; top: -4px; left: -4px; width: 18px; height: 18px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 1px rgba(0,0,0,0.1);">${icon}</div>
                        <div class="room-name">${room.name}</div>
                        <div class="room-capacity">Capacity: ${room.capacity}</div>
                        <div class="room-status">${isSelected ? 'Selected' : statusText}</div>
                    </div>
                `;
            });
            rooms_html += '</div></div>';

            // Set HTML in dialog
            dialog.fields_dict.rooms_display.$wrapper.html(rooms_html);

            // Add click event for room selection
            dialog.$wrapper.find('.room-item[data-available="true"]').on('click', function() {
                const roomName = $(this).data('room');
                const isSelected = frm.selected_rooms.includes(roomName);

                if (isSelected) {
                    frm.selected_rooms = frm.selected_rooms.filter(r => r !== roomName);
                    $(this).css({
                        'background': '#10b981',
                        'border': '1px solid #e5e7eb',
                        'transform': 'scale(1)',
                        'box-shadow': 'none'
                    }).removeClass('selected');
                    $(this).find('.room-status').text('Available');
                } else {
                    frm.selected_rooms.push(roomName);
                    $(this).css({
                        'background': '#3b82f6',
                        'border': '2px solid #1e3a8a',
                        'transform': 'scale(1.03)',
                        'box-shadow': '0 2px 6px rgba(0,0,0,0.15)'
                    }).addClass('selected');
                    $(this).find('.room-status').text('Selected');
                }
            });

            // Add hover effects for available rooms
            dialog.$wrapper.find('.room-item[data-available="true"]').hover(
                function() {
                    if (!$(this).hasClass('selected')) {
                        $(this).css({
                            'transform': 'scale(1.05)',
                            'box-shadow': '0 2px 4px rgba(0,0,0,0.15)'
                        });
                    }
                },
                function() {
                    if (!$(this).hasClass('selected')) {
                        $(this).css({
                            'transform': 'scale(1)',
                            'box-shadow': 'none'
                        });
                    }
                }
            );

            // Style dialog buttons
            dialog.$wrapper.find('.btn-primary').css({
                'background': 'linear-gradient(135deg, #1e40af, #3b82f6)',
                'border': 'none',
                'border-radius': '4px',
                'padding': '6px 12px',
                'font-weight': '500',
                'transition': 'all 0.2s ease',
                'box-shadow': '0 1px 3px rgba(0,0,0,0.1)'
            }).hover(
                function() { $(this).css('background', 'linear-gradient(135deg, #2b6cb0, #60a5fa)'); },
                function() { $(this).css('background', 'linear-gradient(135deg, #1e40af, #3b82f6)'); }
            );

            // Show dialog with animation
            dialog.show();
            dialog.$wrapper.find('.modal-content').css({
                'animation': 'fadeIn 0.3s ease-in',
                'border-radius': '6px',
                'max-width': '700px',
                'padding': '8px'
            });
        } else {
            frappe.call({
                method: 'ms_calendar.api.msgraph.get_org_rooms_and_availability',
                args: {
                    interview_date: frm.doc.interview_date,
                    start_time: frm.doc.start_time,
                    end_time: frm.doc.end_time
                },
                freeze: true,
                freeze_message: __("Fetching available rooms..."),
                callback: function(r) {
                    if (r.message && r.message.rooms) {
                        const rooms = r.message.rooms;
                        // Store room data for reuse
                        frm.room_email_map = {};
                        frm.room_availability_map = {};
                        frm.room_capacity_map = {};
                        rooms.forEach(room => {
                            frm.room_email_map[room.name] = room.email;
                            frm.room_availability_map[room.name] = room.is_available;
                            frm.room_capacity_map[room.name] = room.capacity;
                        });

                        // Initialize selected rooms array
                        frm.selected_rooms = [];

                        // Create popup dialog
                        const dialog = new frappe.ui.Dialog({
                            title: __('Select Meeting Rooms'),
                            fields: [{
                                fieldtype: 'HTML',
                                fieldname: 'rooms_display',
                                options: ''
                            }],
                            primary_action_label: __('Block Rooms'),
                            primary_action: function() {
                                if (frm.selected_rooms.length > 0) {
                                    frm.set_value('meeting_room', frm.selected_rooms.join(', '));
                                    frm.set_value('room_email', frm.selected_rooms.map(room => frm.room_email_map[room]).join(', '));
                                    dialog.hide();
                                } else {
                                    showCustomDialog(frm, 'No Rooms Selected', 'Please select at least one available room before confirming.', '#dc2626', 'fa-exclamation-circle');
                                }
                            }
                        });

                        // Generate HTML for room selection
                        let rooms_html = `
                            <style>
                                @keyframes fadeIn {
                                    from { opacity: 0; transform: translateY(-10px); }
                                    to { opacity: 1; transform: translateY(0); }
                                }
                                .room-item:hover[data-available="true"]:not(.selected) {
                                    transform: scale(1.05);
                                }
                                .room-grid {
                                    display: grid;
                                    grid-template-columns: repeat(4, 1fr);
                                    gap: 8px;
                                    padding: 8px;
                                    justify-items: center;
                                    max-height: 300px;
                                    overflow-y: auto;
                                    overflow-x: hidden;
                                }
                                .room-item {
                                    width: 100%;
                                    box-sizing: border-box;
                                    min-width: 0;
                                    min-height: 80px;
                                    position: relative;
                                    padding: 8px;
                                    border: 1px solid #e5e7eb;
                                    border-radius: 4px;
                                    color: white;
                                    text-align: center;
                                    transition: all 0.2s ease;
                                }
                                .room-name {
                                    font-weight: 600;
                                    font-size: 11px;
                                    margin-top: 4px;
                                    margin-bottom: 3px;
                                    word-wrap: break-word;
                                    line-height: 1.3;
                                }
                                .room-capacity {
                                    font-size: 9px;
                                    opacity: 0.9;
                                    margin-bottom: 3px;
                                }
                                .room-status {
                                    font-size: 9px;
                                    opacity: 0.9;
                                }
                                @media (max-width: 600px) {
                                    .room-grid {
                                        grid-template-columns: repeat(3, 1fr);
                                    }
                                }
                                @media (max-width: 400px) {
                                    .room-grid {
                                        grid-template-columns: repeat(2, 1fr);
                                    }
                                }
                            </style>
                            <div style="padding: 12px; background: #f9fafb; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;">
                                <div style="margin-bottom: 8px; text-align: center; font-size: 12px; font-weight: 600; color: #1e3a8a; background: #e0e7ff; padding: 6px; border-radius: 3px;">
                                    <i class="fa fa-calendar" style="margin-right: 4px;"></i>Time Slot: ${moment(frm.doc.interview_date + " " + frm.doc.start_time).format('h:mm A')} - ${moment(frm.doc.interview_date + " " + frm.doc.end_time).format('h:mm A')}
                                </div>
                                <div class="legend" style="display: flex; justify-content: center; gap: 10px; margin-bottom: 10px; font-size: 10px; color: #1f2937; background: #f1f5f9; padding: 4px; border-radius: 3px;">
                                    <div><span style="color: #10b981; font-size: 10px; margin-right: 2px;">●</span>Available</div>
                                    <div><span style="color: #ef4444; font-size: 10px; margin-right: 2px;">●</span>Busy</div>
                                    <div><span style="color: #3b82f6; font-size: 10px; margin-right: 2px;">●</span>Selected</div>
                                </div>
                                <div class="room-grid" style="animation: fadeIn 0.3s ease-in;">
                        `;
                        rooms.forEach(room => {
                            const isAvailable = room.is_available;
                            const bgColor = isAvailable ? '#10b981' : '#ef4444';
                            const statusText = isAvailable ? 'Available' : 'Busy';
                            const icon = isAvailable ? '<i class="fa fa-check-circle" style="font-size: 10px;"></i>' : '<i class="fa fa-times-circle" style="font-size: 10px;"></i>';
                            const isSelected = frm.selected_rooms.includes(room.name);
                            const selectedStyle = isSelected ? 'border: 2px solid #3b82f6; transform: scale(1.03); box-shadow: 0 2px 6px rgba(0,0,0,0.15); background: #3b82f6;' : '';
                            rooms_html += `
                                <div class="room-item ${isAvailable ? '' : 'disabled'} ${isSelected ? 'selected' : ''}" data-room="${room.name}" data-available="${isAvailable}"
                                    style="background: ${isSelected ? '#3b82f6' : bgColor}; ${isAvailable ? 'cursor: pointer;' : 'cursor: not-allowed; opacity: 0.7;'} ${selectedStyle}">
                                    <div style="position: absolute; top: -4px; left: -4px; width: 18px; height: 18px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 1px rgba(0,0,0,0.1);">${icon}</div>
                                    <div class="room-name">${room.name}</div>
                                    <div class="room-capacity">Capacity: ${room.capacity}</div>
                                    <div class="room-status">${isSelected ? 'Selected' : statusText}</div>
                                </div>
                            `;
                        });
                        rooms_html += '</div></div>';

                        // Set HTML in dialog
                        dialog.fields_dict.rooms_display.$wrapper.html(rooms_html);

                        // Add click event for room selection
                        dialog.$wrapper.find('.room-item[data-available="true"]').on('click', function() {
                            const roomName = $(this).data('room');
                            const isSelected = frm.selected_rooms.includes(roomName);

                            if (isSelected) {
                                frm.selected_rooms = frm.selected_rooms.filter(r => r !== roomName);
                                $(this).css({
                                    'background': '#10b981',
                                    'border': '1px solid #e5e7eb',
                                    'transform': 'scale(1)',
                                    'box-shadow': 'none'
                                }).removeClass('selected');
                                $(this).find('.room-status').text('Available');
                            } else {
                                frm.selected_rooms.push(roomName);
                                $(this).css({
                                    'background': '#3b82f6',
                                    'border': '2px solid #1e3a8a',
                                    'transform': 'scale(1.03)',
                                    'box-shadow': '0 2px 6px rgba(0,0,0,0.15)'
                                }).addClass('selected');
                                $(this).find('.room-status').text('Selected');
                            }
                        });

                        // Add hover effects for available rooms
                        dialog.$wrapper.find('.room-item[data-available="true"]').hover(
                            function() {
                                if (!$(this).hasClass('selected')) {
                                    $(this).css({
                                        'transform': 'scale(1.05)',
                                        'box-shadow': '0 2px 4px rgba(0,0,0,0.15)'
                                    });
                                }
                            },
                            function() {
                                if (!$(this).hasClass('selected')) {
                                    $(this).css({
                                        'transform': 'scale(1)',
                                        'box-shadow': 'none'
                                    });
                                }
                            }
                        );

                        // Style dialog buttons
                        dialog.$wrapper.find('.btn-primary').css({
                            'background': 'linear-gradient(135deg, #1e40af, #3b82f6)',
                            'border': 'none',
                            'border-radius': '4px',
                            'padding': '6px 12px',
                            'font-weight': '500',
                            'transition': 'all 0.2s ease',
                            'box-shadow': '0 1px 3px rgba(0,0,0,0.1)'
                        }).hover(
                            function() { $(this).css('background', 'linear-gradient(135deg, #2b6cb0, #60a5fa)'); },
                            function() { $(this).css('background', 'linear-gradient(135deg, #1e40af, #3b82f6)'); }
                        );

                        // Show dialog with animation
                        dialog.show();
                        dialog.$wrapper.find('.modal-content').css({
                            'animation': 'fadeIn 0.3s ease-in',
                            'border-radius': '6px',
                            'max-width': '700px',
                            'padding': '8px'
                        });

                        // Show message if no rooms are available
                        const available_rooms = rooms.filter(room => room.is_available);
                        if (available_rooms.length === 0) {
                            showCustomDialog(frm, 'No Rooms Available', 'No rooms are available for the selected time slot.', '#f59e0b', 'fa-exclamation-triangle');
                        }
                    } else {
                        showCustomDialog(frm, 'Error', 'Failed to fetch room availability. Please try again.', '#dc2626', 'fa-exclamation-circle');
                    }
                },
                error: function(err) {
                    showCustomDialog(frm, 'Error', 'Failed to fetch room availability. Please check the console.', '#dc2626', 'fa-exclamation-circle');
                    console.error("Room Availability Error:", err);
                }
            });
        }
    },

    meeting_room: function(frm) {
        const selected_rooms = frm.doc.meeting_room ? frm.doc.meeting_room.split(', ') : [];
        if (selected_rooms.length > 0 && frm.room_email_map) {
            const emails = selected_rooms.map(room => frm.room_email_map[room] || '').filter(email => email);
            frm.set_value('room_email', emails.join(', '));
            console.log(frm.doc.room_email,"room email");
            // Check if any selected room is busy
            const hasBusyRoom = selected_rooms.some(room => !frm.room_availability_map[room]);
            if (hasBusyRoom) {
                showCustomDialog(frm, 'Room Unavailable', 'One or more selected rooms are busy for the chosen time slot.', '#f59e0b', 'fa-exclamation-triangle');
            }
        } else {
            frm.set_value('room_email', '');
        }
    },
 
    check_availability: function(frm) {
        console.log("working")
        let selected_emails = (frm.doc.interviewer_email || []).map(row => row.interviewer_email);
        console.log("Selected emails:", selected_emails);

        if (!selected_emails.length || !frm.doc.interview_date) {
            frappe.msgprint({
                title: __('Missing Information'),
                indicator: 'red',
                message: __('Please enter at least one interviewer email and the interview date.')
            });
            return;
        }

        frm.get_field('available_slots').$wrapper.html(`
            <div class="availability-loader text-center p-5">
                <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
                <h5 class="fw-bold">Checking Availability...</h5>
                <p class="text-muted">Please wait while we fetch available slots.</p>
            </div>
        `);

        frm.toggle_display('available_slots_section', true);

        frappe.call({
            method: 'ms_calendar.api.msgraph.get_schedule_free_slots',
            args: {
                interviewer_emails: selected_emails,
                interview_date: frm.doc.interview_date
            },
            callback: function(r) {
                if (r.message) {
                    let allSchedulesHtml = '';

                    Object.keys(r.message).forEach(email => {
                        const intervals = r.message[email];
                        const processedEvents = intervals.map(interval => {
                            const startUtc = moment.utc(interval.start.dateTime);
                            const endUtc = moment.utc(interval.end.dateTime);

                            const start = startUtc.local();
                            const end = endUtc.local();

                            return {
                                title: "Busy",
                                type: interval.location?.displayName || "Meeting",
                                attendee: interval.organizer?.emailAddress?.name || "Unknown",
                                startHour: start.hours() + start.minutes() / 60,
                                endHour: end.hours() + end.minutes() / 60,
                                displayStartTime: start.format("h:mm A"),
                                displayEndTime: end.format("h:mm A"),
                                color: '#e74c3c'
                            };
                        });

                        const scheduleHtml = frm.events.generate_schedule_html(frm, processedEvents, email);
                        allSchedulesHtml += scheduleHtml;
                    });

                    frm.get_field('available_slots').$wrapper.html(allSchedulesHtml);

                    setTimeout(() => {
                        $('.schedule-event').on('click', function() {
                            const startTime = $(this).data('start');
                            const endTime = $(this).data('end');
                            const title = $(this).data('title');
                            const type = $(this).data('type');

                            frappe.msgprint({
                                title: title === 'Busy' ? 'Busy Slot' : 'Available Time Slot',
                                message: `
                                    <div class="event-details">
                                        <p><strong>${title}</strong></p>
                                        <p><strong>Time:</strong> ${startTime} - ${endTime}</p>
                                        ${title === 'Busy' ? `<p><strong>Type:</strong> ${type}</p>` : ""}
                                    </div>
                                `
                            });
                        });
                    }, 100);
                } else {
                    frm.get_field('available_slots').$wrapper.html(`
                        <div class="alert alert-danger d-flex align-items-center" role="alert">
                            <svg class="bi shrink-0 me-2" width="24" height="24" role="img" aria-label="Danger:">
                                <use xlink:href="#exclamation-triangle-fill"/>
                            </svg>
                            <div>An error occurred while fetching availability.</div>
                        </div>
                    `);
                }
            },
            error: function(err) {
                frappe.msgprint({
                    title: __("Error"),
                    message: __("Failed to fetch schedule. Please check the console."),
                    indicator: "red"
                });
                console.error("Schedule Fetch Error:", err);
            }
        });
    },

    generate_schedule_html: function(frm, events, email) {
        const day_start_hour = 8;
        const day_end_hour = 18;
        const total_hours = day_end_hour - day_start_hour;
        const SLOT_WIDTH_PX = 80;

        let timeSlotsHtml = '';
        for (let i = day_start_hour; i < day_end_hour; i++) {
            const hour = i % 12 === 0 ? 12 : i % 12;
            const ampm = i < 12 ? 'AM' : 'PM';

            timeSlotsHtml += `
                <div class="time-slot-group" style="width: ${SLOT_WIDTH_PX * 2}px;">
                    <div class="time-slot-hour">
                        <div class="hour-label major">${hour}:00 ${ampm}</div>
                        <div class="hour-line major"></div>
                    </div>
                    <div class="time-slot-half">
                        <div class="hour-label minor">${hour}:30</div>
                        <div class="hour-line minor"></div>
                    </div>
                </div>
            `;
        }

        const finalHour = day_end_hour % 12 === 0 ? 12 : day_end_hour % 12;
        const finalAmpm = day_end_hour < 12 ? 'AM' : 'PM';
        timeSlotsHtml += `
            <div class="time-slot-final" style="width: ${SLOT_WIDTH_PX}px;">
                <div class="hour-label major">${finalHour}:00 ${finalAmpm}</div>
                <div class="hour-line major"></div>
            </div>
        `;

        let eventsHtml = '';
        events.forEach((event, index) => {
            if (event.endHour <= day_start_hour || event.startHour >= day_end_hour) {
                return;
            }

            const startHour = Math.max(event.startHour, day_start_hour);
            const endHour = Math.min(event.endHour, day_end_hour);

            const leftPercentage = ((startHour - day_start_hour) / total_hours) * 100;
            const widthPercentage = ((endHour - startHour) / total_hours) * 100;

            eventsHtml += `
                <div class="schedule-event event-busy" 
                     data-start="${event.displayStartTime}"
                     data-end="${event.displayEndTime}"
                     data-title="Busy"
                     data-type="${event.type}"
                     style="left: ${leftPercentage}%; width: ${widthPercentage}%;">
                    <div class="event-content">
                        <div class="event-title">Busy</div>
                        <div class="event-time">${event.displayStartTime} - ${event.displayEndTime}</div>
                    </div>
                    <div class="event-tooltip">
                        <strong>Busy</strong><br>
                        ${event.displayStartTime} - ${event.displayEndTime}<br>
                        <em>(${event.type})</em>
                    </div>
                </div>
            `;
        });

        const freeSlots = frm.events.calculate_free_slots(events, day_start_hour, day_end_hour);
        freeSlots.forEach(slot => {
            const leftPercentage = ((slot.start - day_start_hour) / total_hours) * 100;
            const widthPercentage = ((slot.end - slot.start) / total_hours) * 100;

            if (widthPercentage > 0) {
                const startFormatted = moment().hour(Math.floor(slot.start)).minute((slot.start % 1) * 60).format("h:mm A");
                const endFormatted = moment().hour(Math.floor(slot.end)).minute((slot.end % 1) * 60).format("h:mm A");

                eventsHtml += `
                    <div class="schedule-event event-free" 
                         data-start="${startFormatted}"
                         data-end="${endFormatted}"
                         data-title="Free"
                         style="left: ${leftPercentage}%; width: ${widthPercentage}%;">
                        <div class="event-content">
                            <div class="event-title">Free</div>
                            <div class="event-time">${startFormatted} - ${endFormatted}</div>
                        </div>
                        <div class="event-tooltip">
                            <strong>Free</strong><br>
                            ${startFormatted} - ${endFormatted}
                        </div>
                    </div>
                `;
            }
        });

        return `
            <div class="schedule-container">
                <div class="schedule-header">
                    <div class="header-content">
                        <div class="date-section">
                            <h5 class="schedule-date">${moment(frm.doc.interview_date).format('dddd, MMMM DD, YYYY')}</h5>
                        </div>
                        <div class="email-info">
                            <span class="email-label">Calendar Events for</span>
                            <span class="email-address">${email}</span>
                        </div>
                    </div>
                </div>

                <div class="schedule-legend">
                    <div class="legend-items">
                        <div class="legend-item">
                            <div class="legend-dot busy"></div>
                            <span>Busy</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-dot available"></div>
                            <span>Free</span>
                        </div>
                    </div>
                </div>

                <div class="timeline-section">
                    <div class="time-labels">
                        ${timeSlotsHtml}
                    </div>

                    <div class="timeline-grid">
                        <div class="timeline-track"></div>
                        ${eventsHtml}
                    </div>
                </div>

                <div class="schedule-footer">
                    <div class="footer-stats"></div>
                </div>
            </div>

            <style>
                .schedule-container {
                    max-width: 1200px;
                    margin: 20px auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.1);
                    border: 1px solid #e2e8f0;
                    overflow: hidden;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                }

                .schedule-header {
                    padding: 0.75rem;
                    border-bottom: 1px solid #e2e8f0;
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                }

                .header-content {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                }

                .date-section {
                    flex: 1;
                }

                .schedule-date {
                    font-size: 0.8rem;
                    font-weight: 700;
                    color: #1e293b;
                    margin: 0 0 0.25rem 0;
                    letter-spacing: -0.025em;
                }

                .email-info {
                    display: flex;
                    flex-direction: column;
                    gap: 0.1rem;
                }

                .email-label {
                    color: #64748b;
                    font-size: 0.65rem;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                .email-address {
                    color: #374151;
                    font-size: 0.75rem;
                    font-weight: 600;
                    font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
                }

                .schedule-legend {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.4rem 0.75rem;
                    background: #f8fafc;
                    border-bottom: 1px solid #e2e8f0;
                }

                .legend-items {
                    display: flex;
                    gap: 1rem;
                }

                .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 0.3rem;
                    font-size: 0.65rem;
                    color: #475569;
                }

                .legend-dot {
                    width: 10px;
                    height: 10px;
                    border-radius: 3px;
                }

                .legend-dot.busy {
                    background: #f87171;
                    border: 1px solid #f87171;
                }

                .legend-dot.available {
                    background: #6ee7b7;
                    border: 1px solid #6ee7b7;
                }

                .timeline-section {
                    padding: 0.75rem;
                    overflow-x: auto;
                }

                .time-labels {
                    display: flex;
                    margin-bottom: 0.2rem;
                    min-width: 800px;
                }

                .time-slot-group, .time-slot-final {
                    display: flex;
                    flex-direction: column;
                    position: relative;
                }

                .time-slot-group {
                    justify-content: space-between;
                }

                .time-slot-hour, .time-slot-half {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    flex: 1;
                    gap: 0.15rem;
                }

                .time-slot-final {
                    align-items: center;
                    gap: 0.15rem;
                }

                .hour-label {
                    font-size: 0.55rem;
                    color: #64748b;
                    text-align: center;
                }

                .hour-label.major {
                    font-weight: 600;
                    color: #374151;
                    font-size: 0.6rem;
                }

                .hour-label.minor {
                    font-weight: 500;
                    color: #6b7280;
                    font-size: 0.5rem;
                }

                .hour-line {
                    width: 1px;
                    height: 6px;
                }

                .hour-line.major {
                    background: #374151;
                    height: 10px;
                    width: 1.5px;
                }

                .hour-line.minor {
                    background: #6b7280;
                    height: 4px;
                    width: 1px;
                }

                .timeline-grid {
                    position: relative;
                    height: 40px;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    background: #ffffff;
                    min-width: 800px;
                }

                .timeline-track {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: repeating-linear-gradient(
                        to right,
                        transparent 0%,
                        transparent 4.9%,
                        rgba(107, 114, 128, 0.3) 4.9%,
                        rgba(107, 114, 128, 0.3) 5%,
                        transparent 5%,
                        transparent 9.9%,
                        rgba(55, 65, 81, 0.4) 9.9%,
                        rgba(55, 65, 81, 0.4) 10%
                    );
                }

                .schedule-event {
                    position: absolute;
                    top: 2px;
                    bottom: 2px;
                    border-radius: 4px;
                    padding: 0.15rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    min-width: 40px;
                    z-index: 2;
                    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }

                .schedule-event:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
                    z-index: 10;
                }

                .event-busy {
                    background: linear-gradient(135deg, #f87171, #fb7185) !important;
                    color: white !important;
                    border: 1px solid #f87171 !important;
                }

                .event-busy:hover {
                    background: linear-gradient(135deg, #fb7185, #f87171) !important;
                }

                .event-free {
                    background: linear-gradient(135deg, #6ee7b7, #34d399) !important;
                    color: white !important;
                    border: 1px solid #6ee7b7 !important;
                }

                .event-free:hover {
                    background: linear-gradient(135deg, #34d399, #6ee7b7) !important;
                }

                .event-content {
                    text-align: center;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .event-title {
                    font-weight: 600;
                    font-size: 0.55rem;
                    line-height: 1;
                    margin-bottom: 0.05rem;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .event-time {
                    font-size: 0.5rem;
                    opacity: 0.9;
                    line-height: 1;
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .event-tooltip {
                    visibility: hidden;
                    position: absolute;
                    bottom: calc(100% + 6px);
                    left: 50%;
                    transform: translateX(-50%);
                    background: #1f2937;
                    color: white;
                    padding: 0.3rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.55rem;
                    z-index: 1000;
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
                    white-space: nowrap;
                    opacity: 0;
                    transition: all 0.3s ease;
                }

                .event-tooltip::after {
                    content: '';
                    position: absolute;
                    top: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    border: 4px solid transparent;
                    border-top-color: #1f2937;
                }

                .schedule-event:hover .event-tooltip {
                    visibility: visible;
                    opacity: 1;
                }

                .schedule-footer {
                    padding: 0.75rem;
                    background: #f8fafc;
                    border-top: 1px solid #e2e8f0;
                }

                .footer-stats {
                    display: flex;
                    gap: 1.5rem;
                }

                @media (max-width: 768px) {
                    .schedule-container {
                        border-radius: 6px;
                    }

                    .schedule-header {
                        padding: 0.5rem;
                    }

                    .header-content {
                        flex-direction: column;
                        gap: 0.75rem;
                        align-items: flex-start;
                    }

                    .schedule-date {
                        font-size: 1rem;
                    }

                    .email-address {
                        font-size: 0.7rem;
                        word-break: break-all;
                    }

                    .schedule-legend {
                        padding: 0.3rem 0.5rem;
                        flex-direction: column;
                        gap: 0.5rem;
                        align-items: flex-start;
                    }

                    .timeline-section {
                        padding: 0.5rem;
                    }

                    .hour-label.major {
                        font-size: 0.55rem;
                    }

                    .hour-label.minor {
                        font-size: 0.5rem;
                    }

                    .schedule-event {
                        padding: 0.15rem;
                    }

                    .event-title {
                        font-size: 0.55rem;
                        margin-bottom: 0.05rem;
                    }

                    .event-time {
                        font-size: 0.5rem;
                    }

                    .footer-stats {
                        gap: 1rem;
                        justify-content: center;
                    }
                }

                @media (max-width: 480px) {
                    .hour-label.minor {
                        display: none;
                    }

                    .event-title {
                        font-size: 0.5rem;
                    }

                    .event-time {
                        font-size: 0.45rem;
                    }

                    .footer-stats {
                        gap: 0.75rem;
                    }
                }
            </style>
        `;
    },
    calculate_free_slots: function(events, day_start_hour, day_end_hour) {
        const slots = [];
        let currentHour = day_start_hour;

        const sortedEvents = events
            .filter(e => e.endHour > day_start_hour && e.startHour < day_end_hour)
            .sort((a, b) => a.startHour - b.startHour);

        sortedEvents.forEach(event => {
            const start = Math.max(event.startHour, day_start_hour);
            if (currentHour < start) {
                slots.push({ start: currentHour, end: start });
            }
            currentHour = Math.max(currentHour, event.endHour);
        });

        if (currentHour < day_end_hour) {
            slots.push({ start: currentHour, end: day_end_hour });
        }

        return slots;
    }
});


// Utility function to show styled dialogs
function showCustomDialog(frm, title, message, color, icon) {
    const dialog = new frappe.ui.Dialog({
        title: __(title),
        fields: [{
            fieldtype: 'HTML',
            options: `<div style="padding: 8px; font-size: 11px; color: ${color};"><i class="fa ${icon}" style="margin-right: 4px;"></i>${message}</div>`
        }],
        primary_action_label: __('OK'),
        primary_action: function() { dialog.hide(); }
    });
    dialog.show();
    dialog.$wrapper.find('.modal-content').css({
        'border-radius': '6px',
        'box-shadow': '0 3px 8px rgba(0,0,0,0.1)'
    });
    dialog.$wrapper.find('.btn-primary').css({
        'background': color,
        'border': 'none',
        'border-radius': '4px',
        'padding': '6px 12px'
    });
    return dialog;
}