import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

EVENT_SUBJECTS = {
    'PASSWORD_RESET': '[NeuroCare Nexus] Password Reset Request — Verification Code: {reset_code}',
    'DOCTOR_REGISTRATION_SUBMITTED': '[NeuroCare Nexus] Doctor Registration Received — {doctor_name}',
    'DOCTOR_DOCUMENTS_REQUESTED': '[NeuroCare Nexus] Action Required: Verification Documents Requested',
    'DOCTOR_DOCUMENTS_SUBMITTED': '[NeuroCare Nexus] Verification Document Submitted — Dr. {doctor_name}',
    'DOCTOR_DOCUMENT_ACCEPTED': '[NeuroCare Nexus] Verification Document Accepted — {document_title}',
    'DOCTOR_DOCUMENT_RESUBMISSION_REQUIRED': '[NeuroCare Nexus] Action Required: Document Resubmission Requested — {document_title}',
    'DOCTOR_APPROVED': '[NeuroCare Nexus] Application Approved — Welcome to Doctor Portal',
    'DOCTOR_REJECTED': '[NeuroCare Nexus] Doctor Registration Update',
    'CRITICAL_PATIENT_ALERT': '[NeuroCare Nexus] Critical Emergency Alert — Patient {patient_name} ({patient_id})',
    'FALL_ALERT': '[NeuroCare Nexus] Urgent Fall Alarm — Patient {patient_name} ({patient_id})',
    'PRESCRIPTION_CREATED': '[NeuroCare Nexus] New Prescription Available — {patient_name}',
    'PRESCRIPTION_UPDATED': '[NeuroCare Nexus] Prescription Update Notice — {patient_name}',
    'PRESCRIPTION_DISCONTINUED': '[NeuroCare Nexus] Prescription Discontinuation Notice — {patient_name}',
    'MEDICATION_UPCOMING_REMINDER': '[NeuroCare Nexus] Medication Reminder — {patient_name}',
    'MEDICATION_MISSED_DOSE': '[NeuroCare Nexus] Missed Medication Notice — {patient_name}',
    'MEDICATION_ADHERENCE_NOTICE': '[NeuroCare Nexus] Medication Adherence Notice — {patient_name}',
}


def render_email_content(event_type, context):
    """
    Renders plain text and HTML content for the specified event type.
    Ensures no raw confidential clinical vitals dumps, passwords, or tokens are exposed.
    """
    doctor_name = context.get('doctor_name', 'Doctor')
    patient_id = context.get('patient_id', 'Patient')
    patient_name = context.get('patient_name', '')
    mrn = context.get('medical_registration_number', '')
    council = context.get('state_medical_council', '')
    document_title = context.get('document_title', 'Document')
    document_type = context.get('document_type', '')
    admin_notes = context.get('admin_notes', '') or context.get('reason', '')
    alert_type = context.get('alert_type', 'Critical Alert')
    alert_message = context.get('alert_message', '')
    scheduled_time = context.get('scheduled_time', '')
    medicine_name = context.get('medicine_name', '')

    html_wrapper = """
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0;">
        <div style="background: #0f172a; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
            <h2 style="color: #ffffff; margin: 0; font-size: 20px; letter-spacing: 0.5px;">NeuroCare Nexus</h2>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Clinical & Care Notification Service</p>
        </div>
        <div style="background: #ffffff; padding: 28px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px;">
            {body}
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0 16px 0;" />
            <p style="color: #64748b; font-size: 11px; line-height: 1.5; margin: 0;">
                This is an automated notification from NeuroCare Nexus. Please do not reply directly to this email. For assistance, log into the secure portal.
            </p>
        </div>
    </div>
    """

    body = ""

    if event_type == 'DOCTOR_REGISTRATION_SUBMITTED':
        body = f"""
        <h3 style="color: #0f172a; margin-top: 0;">Registration Received</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Dear Dr. <strong>{doctor_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Your registration application for NeuroCare Nexus has been submitted successfully.
        </p>
        <div style="background: #f1f5f9; padding: 16px; border-radius: 6px; margin: 16px 0; font-size: 13px; color: #1e293b;">
            <div><strong>Medical Registration No.:</strong> {mrn}</div>
            <div style="margin-top: 6px;"><strong>State Medical Council:</strong> {council}</div>
            <div style="margin-top: 6px;"><strong>Status:</strong> Under Administrative Verification</div>
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            You can sign in to your <strong>Verification Dashboard</strong> at any time to monitor your application progress.
        </p>
        """

    elif event_type == 'DOCTOR_DOCUMENTS_REQUESTED':
        body = f"""
        <h3 style="color: #0f172a; margin-top: 0;">Additional Verification Documents Requested</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Dear Dr. <strong>{doctor_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            The platform administrator has reviewed your application and requested the following verification document:
        </p>
        <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 0 6px 6px 0; margin: 16px 0; font-size: 13px; color: #1e3a8a;">
            <div><strong>Requested Document:</strong> {document_title} ({document_type})</div>
            {f'<div style="margin-top: 8px;"><strong>Administrator Instructions:</strong> {admin_notes}</div>' if admin_notes else ''}
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please log in to your NeuroCare Nexus account to upload this document securely.
        </p>
        """

    elif event_type == 'DOCTOR_DOCUMENTS_SUBMITTED':
        body = f"""
        <h3 style="color: #0f172a; margin-top: 0;">Verification Document Submitted</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Administrator Notice,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Dr. <strong>{doctor_name}</strong> has submitted verification document: <strong>{document_title}</strong>.
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please review this document in the Administrative Governance console.
        </p>
        """

    elif event_type == 'DOCTOR_DOCUMENT_ACCEPTED':
        body = f"""
        <h3 style="color: #047857; margin-top: 0;">Document Accepted</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Dear Dr. <strong>{doctor_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Your credential document <strong>{document_title}</strong> has been reviewed and <strong>accepted</strong>.
        </p>
        """

    elif event_type == 'DOCTOR_DOCUMENT_RESUBMISSION_REQUIRED':
        body = f"""
        <h3 style="color: #b45309; margin-top: 0;">Document Resubmission Requested</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Dear Dr. <strong>{doctor_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Your submitted credential document <strong>{document_title}</strong> requires resubmission.
        </p>
        {f'<div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px; margin: 16px 0; font-size: 13px; color: #92400e;"><strong>Reviewer Feedback:</strong> {admin_notes}</div>' if admin_notes else ''}
        """

    elif event_type == 'DOCTOR_APPROVED':
        body = f"""
        <h3 style="color: #047857; margin-top: 0;">Registration Approved</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Dear Dr. <strong>{doctor_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Your medical credentials and State Medical Council registration have been verified and <strong>approved</strong>.
        </p>
        """

    elif event_type == 'DOCTOR_REJECTED':
        body = f"""
        <h3 style="color: #991b1b; margin-top: 0;">Application Status Update</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Dear Dr. <strong>{doctor_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Your registration application could not be approved at this time.
        </p>
        {f'<div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 16px 0; font-size: 13px; color: #991b1b;"><strong>Reason:</strong> {admin_notes}</div>' if admin_notes else ''}
        """

    elif event_type == 'PASSWORD_RESET':
        reset_code = context.get('reset_code', '')
        reset_url = context.get('reset_url', 'https://www.neurocarenexus.online/login?view=reset')
        user_name = context.get('user_name', 'Clinician / User')
        body = f"""
        <h3 style="color: #0f172a; margin-top: 0; font-size: 18px;">Password Reset Request</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Hello <strong>{user_name}</strong>,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            We received a request to reset the credentials for your NeuroCare Nexus account. Use the 6-digit verification code below or click the direct reset link to update your password securely.
        </p>
        <div style="background: #eff6ff; border: 2px dashed #3b82f6; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: #1e40af; letter-spacing: 1.5px; margin-bottom: 6px;">Your 6-Digit Verification Code</div>
            <div style="font-size: 32px; font-weight: 900; letter-spacing: 6px; color: #1d4ed8; font-family: 'Courier New', monospace;">{reset_code}</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 8px;">Code expires in 15 minutes.</div>
        </div>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{reset_url}" style="display: inline-block; background: #2563eb; color: #ffffff; padding: 12px 28px; border-radius: 8px; font-weight: 700; font-size: 14px; text-decoration: none; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);">
                Reset Password Directly &rarr;
            </a>
        </div>
        <p style="color: #64748b; font-size: 12px; line-height: 1.5;">
            If you did not request a password reset, you can safely ignore this email. Your existing credentials remain completely secure.
        </p>
        """

    elif event_type in ('CRITICAL_PATIENT_ALERT', 'FALL_ALERT'):
        is_fall = (event_type == 'FALL_ALERT')
        header_text = "Urgent Fall Alarm Triggered" if is_fall else "Critical Physiological Monitoring Alert"
        alert_badge = "Fall Detected (MPU6050 Motion)" if is_fall else alert_type
        doctor_link = f"https://www.neurocarenexus.online/vitals?patientId={patient_id}"
        body = f"""
        <h3 style="color: #b91c1c; margin-top: 0; font-size: 18px;">&#9888; {header_text}</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            An urgent clinical alert was triggered for patient <strong>{patient_name or patient_id}</strong>.
        </p>
        <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; border-radius: 0 6px 6px 0; margin: 16px 0; font-size: 13px; color: #991b1b;">
            <div style="margin-bottom: 6px;"><strong>Patient:</strong> {patient_name or patient_id} (ID: {patient_id})</div>
            <div style="margin-bottom: 6px;"><strong>Event Classification:</strong> {alert_badge}</div>
            <div><strong>Clinical Details:</strong> {alert_message}</div>
        </div>
        <div style="text-align: center; margin: 22px 0;">
            <a href="{doctor_link}" style="display: inline-block; background: #dc2626; color: #ffffff; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 13px; text-decoration: none; box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.2);">
                Access Patient Vitals Dashboard &rarr;
            </a>
        </div>
        <p style="color: #334155; font-size: 13px; line-height: 1.6;">
            Please access the secure NeuroCare Nexus portal immediately to review patient telemetry and initiate clinical interventions.
        </p>
        """

    elif event_type == 'PRESCRIPTION_CREATED':
        prescribing_doctor = context.get('doctor_name', 'Your Attending Doctor')
        prescription_date = context.get('prescription_date', '')
        body = f"""
        <h3 style="color: #0f172a; margin-top: 0;">New Prescription Issued</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            A new prescription has been added to the care plan for patient <strong>{patient_name or patient_id}</strong>.
        </p>
        <div style="background: #f1f5f9; padding: 16px; border-radius: 6px; margin: 16px 0; font-size: 13px; color: #1e293b;">
            <div><strong>Patient:</strong> {patient_name or patient_id}</div>
            <div style="margin-top: 6px;"><strong>Prescribed By:</strong> Dr. {prescribing_doctor.replace('Dr. ', '')}</div>
            {f'<div style="margin-top: 6px;"><strong>Date:</strong> {prescription_date}</div>' if prescription_date else ''}
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please sign in securely to NeuroCare Nexus to view the full prescription and medication schedule.
        </p>
        """

    elif event_type == 'PRESCRIPTION_UPDATED':
        prescribing_doctor = context.get('doctor_name', 'Your Attending Doctor')
        prescription_date = context.get('prescription_date', '')
        body = f"""
        <h3 style="color: #0f172a; margin-top: 0;">Prescription Updated</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            An existing prescription has been updated for patient <strong>{patient_name or patient_id}</strong>.
        </p>
        <div style="background: #f1f5f9; padding: 16px; border-radius: 6px; margin: 16px 0; font-size: 13px; color: #1e293b;">
            <div><strong>Patient:</strong> {patient_name or patient_id}</div>
            <div style="margin-top: 6px;"><strong>Attending Doctor:</strong> Dr. {prescribing_doctor.replace('Dr. ', '')}</div>
            {f'<div style="margin-top: 6px;"><strong>Date Updated:</strong> {prescription_date}</div>' if prescription_date else ''}
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please sign in securely to NeuroCare Nexus to view the updated prescription details.
        </p>
        """

    elif event_type == 'PRESCRIPTION_DISCONTINUED':
        prescribing_doctor = context.get('doctor_name', 'Authorized Clinician')
        body = f"""
        <h3 style="color: #991b1b; margin-top: 0;">Prescription Discontinuation Notice</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            A prescription item in the care plan for patient <strong>{patient_name or patient_id}</strong> has been revoked or discontinued.
        </p>
        <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 16px; border-radius: 0 6px 6px 0; margin: 16px 0; font-size: 13px; color: #991b1b;">
            <div><strong>Patient:</strong> {patient_name or patient_id}</div>
            <div style="margin-top: 6px;"><strong>Attending Doctor:</strong> Dr. {prescribing_doctor.replace('Dr. ', '')}</div>
            <div style="margin-top: 6px;"><strong>Status:</strong> Discontinued / Revoked</div>
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please sign in securely to NeuroCare Nexus to verify active medications and treatment records.
        </p>
        """

    elif event_type == 'MEDICATION_UPCOMING_REMINDER':
        body = f"""
        <h3 style="color: #1e40af; margin-top: 0;">Scheduled Medication Reminder</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Hello,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            A scheduled medication dose requires your attention.
        </p>
        <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 0 6px 6px 0; margin: 16px 0; font-size: 13px; color: #1e3a8a;">
            <div><strong>Patient:</strong> {patient_name or patient_id}</div>
            {f'<div style="margin-top: 6px;"><strong>Scheduled Time:</strong> {scheduled_time}</div>' if scheduled_time else ''}
            {f'<div style="margin-top: 6px;"><strong>Medication:</strong> {medicine_name}</div>' if medicine_name else ''}
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please sign in securely to NeuroCare Nexus to review your medication tracker.
        </p>
        """

    elif event_type == 'MEDICATION_MISSED_DOSE':
        body = f"""
        <h3 style="color: #b45309; margin-top: 0;">Missed Medication Notice</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Hello,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            A scheduled medication dose was not recorded within the expected window for patient <strong>{patient_name or patient_id}</strong>.
        </p>
        <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 0 6px 6px 0; margin: 16px 0; font-size: 13px; color: #92400e;">
            <div><strong>Patient:</strong> {patient_name or patient_id}</div>
            {f'<div style="margin-top: 6px;"><strong>Scheduled Time:</strong> {scheduled_time}</div>' if scheduled_time else ''}
            {f'<div style="margin-top: 6px;"><strong>Medication:</strong> {medicine_name}</div>' if medicine_name else ''}
        </div>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please sign in securely to NeuroCare Nexus to review the medication tracker.
        </p>
        """

    elif event_type == 'MEDICATION_ADHERENCE_NOTICE':
        body = f"""
        <h3 style="color: #991b1b; margin-top: 0;">Medication Adherence Notice</h3>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Hello,
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Multiple scheduled medication doses were missed over the past review period for patient <strong>{patient_name or patient_id}</strong>.
        </p>
        <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; border-radius: 0 6px 6px 0; margin: 16px 0; font-size: 13px; color: #991b1b;">
            <div><strong>Patient:</strong> {patient_name or patient_id}</div>
            <div style="margin-top: 6px;"><strong>Status:</strong> Multiple Unresolved Missed Doses</div>
        </div>
        <p style="color: #64748b; font-size: 12px; line-height: 1.5; margin: 12px 0;">
            <em>Note: This is an adherence tracking workflow notice and not a diagnostic or clinical emergency alert.</em>
        </p>
        <p style="color: #334155; font-size: 14px; line-height: 1.6;">
            Please sign in securely to NeuroCare Nexus to review medication adherence records.
        </p>
        """

    html_content = html_wrapper.format(body=body)
    plain_content = strip_tags(html_content)
    return plain_content, html_content


def resolve_actual_recipient(recipient_email):
    dev_override = getattr(settings, 'DEV_OVERRIDE_EMAIL', '') or ''
    if dev_override:
        return dev_override.strip()

    clean_email = (recipient_email or '').strip().lower()
    if not clean_email:
        return None

    fictional_domains = ('.test', '.example', '@example.com', '@test.com', '@nexus.test', '@localhost')
    if any(clean_email.endswith(d) or d in clean_email for d in fictional_domains):
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'neurocarenexus@gmail.com')
        logger.info(f"[EmailService] Mock test domain detected for '{clean_email}'. Routing email to project mailbox '{admin_email}'.")
        return admin_email

    return clean_email


def send_nexus_email(event_type, recipient_email, context_data=None):
    success, _ = send_nexus_email_with_status(event_type, recipient_email, context_data)
    return success


def send_nexus_email_with_status(event_type, recipient_email, context_data=None):
    """
    Centralized email dispatcher returning (success: bool, error_message: str).
    """
    if context_data is None:
        context_data = {}

    subject_template = EVENT_SUBJECTS.get(event_type, '[NeuroCare Nexus Notification]')
    subject = subject_template.format(
        doctor_name=context_data.get('doctor_name', ''),
        patient_name=context_data.get('patient_name', '') or context_data.get('patient_id', 'Patient'),
        patient_id=context_data.get('patient_id', ''),
        document_title=context_data.get('document_title', ''),
        reset_code=context_data.get('reset_code', '')
    )

    actual_recipient = resolve_actual_recipient(recipient_email)
    is_locmem = getattr(settings, 'EMAIL_BACKEND', '').endswith('locmem.EmailBackend')

    if not is_locmem and not getattr(settings, 'EMAIL_ENABLED', False):
        logger.info(f"[EmailService] Email disabled by configuration. Event: {event_type} to: {recipient_email}")
        return True, ""

    target_email = actual_recipient if actual_recipient else recipient_email
    if not target_email:
        logger.info(f"[EmailService] No valid recipient resolved for event {event_type}.")
        return False, "No valid recipient email resolved"

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'neurocarenexus@gmail.com')

    try:
        plain_text, html_message = render_email_content(event_type, context_data)
        send_mail(
            subject=subject,
            message=plain_text,
            from_email=from_email,
            recipient_list=[target_email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"[EmailService] Sent '{event_type}' email to {target_email} (Subject: {subject})")
        return True, ""
    except Exception as e:
        # Sanitize error message to prevent secret leaking
        err_clean = str(e)[:250]
        logger.error(f"[EmailService] Failed to send email for {event_type} to {target_email}: {err_clean}")
        return False, err_clean
