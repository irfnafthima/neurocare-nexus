import os
from datetime import datetime, date, time, timedelta
import zoneinfo
from django.db import transaction, models
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from patients.models import Patient
from doctors.models import DoctorPatientLink
from caregivers.models import CaregiverPatientLink
from prescriptions.models import Prescription, MedicationSchedule, MedicationDoseLog
from prescriptions.serializers import (
    PrescriptionSerializer, MedicationScheduleSerializer, MedicationDoseLogSerializer
)
from medical_records.views import get_authorized_patient_id, is_user_authorized_for_patient
from accounts.utils import log_audit_trail

APP_TIMEZONE = zoneinfo.ZoneInfo('Asia/Kolkata')

# Configurable software tracking grace period in minutes.
# Note: This is a software tracking/classification grace window, NOT a clinical medical instruction.
MEDICATION_GRACE_PERIOD_MINUTES = 120

class PrescriptionSerializer(PrescriptionSerializer):
    pass

class PrescriptionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not patient_id:
            return Response([], status=status.HTTP_200_OK)

        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to view patient prescriptions.", status=status.HTTP_403_FORBIDDEN)

        rx_list = Prescription.objects.filter(patient_id=patient_id).prefetch_related('schedules').order_by('-id')
        log_audit_trail(request, 'Accessed Patient Prescriptions', f"Prescriptions for Patient {patient_id}", 'Success')
        return Response(PrescriptionSerializer(rx_list, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Only licensed doctors can issue prescriptions.", status=status.HTTP_403_FORBIDDEN)

        raw_pid = request.data.get('patientId')
        if not raw_pid:
            return Response("Target patientId is required to issue a prescription.", status=status.HTTP_400_BAD_REQUEST)

        from patients.views import find_patient_by_identifier
        patient = find_patient_by_identifier(raw_pid)
        if not patient:
            return Response("Target patient not found.", status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, patient.id):
            return Response(f"Unauthorized: Doctor must be linked to patient {patient.id} to issue a prescription.", status=status.HTTP_403_FORBIDDEN)

        rx = Prescription.objects.create(
            patient=patient,
            prescribing_doctor=request.user,
            prescribing_doctor_name=request.user.full_name,
            prescription_date=request.data.get('prescriptionDate') or request.data.get('prescription_date') or timezone.now().date(),
            medicines=request.data.get('medicines', 'Paracetamol 500mg'),
            dosage=request.data.get('dosage', '1 tablet'),
            frequency=request.data.get('frequency', 'Twice daily'),
            duration=request.data.get('duration', '7 days'),
            instructions=request.data.get('instructions', 'Take after meals with water.')
        )

        schedule_times = request.data.get('schedule_times') or request.data.get('scheduleTimes')
        if isinstance(schedule_times, list):
            for t_str in schedule_times:
                try:
                    s_clean = str(t_str).strip()
                    t_val = datetime.strptime(s_clean, '%H:%M').time() if len(s_clean) == 5 else datetime.strptime(s_clean, '%H:%M:%S').time()
                    MedicationSchedule.objects.create(
                        prescription=rx,
                        scheduled_time=t_val,
                        start_date=rx.prescription_date or timezone.now().date(),
                        is_active=True
                    )
                except Exception:
                    pass

        log_audit_trail(
            request=request,
            action='Issued Prescription',
            target=f"Prescription: {rx.medicines} for Patient {patient.id} ({patient.name})",
            result='Success'
        )

        from notifications.notification_service import dispatch_event_notification
        dispatch_event_notification(
            event_type='PRESCRIPTION_CREATED',
            patient_or_id=patient,
            title="New Prescription",
            message="Your doctor added a new prescription.",
            category="prescription",
            target_id=rx.id,
            actor=request.user,
            context_data={
                'doctor_name': request.user.full_name,
                'patient_name': patient.name,
                'prescription_date': str(rx.prescription_date or timezone.now().date()),
                'medicines': rx.medicines
            }
        )

        return Response(PrescriptionSerializer(rx).data, status=status.HTTP_201_CREATED)

class PrescriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Patients, caregivers, and family members cannot modify doctor prescriptions.", status=status.HTTP_403_FORBIDDEN)
        
        rx = Prescription.objects.filter(id=id).first()
        if not rx:
            return Response("Prescription not found.", status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, rx.patient_id):
            return Response("Unauthorized: Doctor must be linked to patient to update prescription.", status=status.HTTP_403_FORBIDDEN)

        serializer = PrescriptionSerializer(rx, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_audit_trail(request, 'Updated Prescription', f"Prescription ID {rx.id} for Patient {rx.patient_id}", 'Success')
            
            from notifications.notification_service import dispatch_event_notification
            dispatch_event_notification(
                event_type='PRESCRIPTION_UPDATED',
                patient_or_id=rx.patient,
                title="Prescription Updated",
                message="Your doctor updated a prescription.",
                category="prescription",
                target_id=rx.id,
                actor=request.user,
                context_data={
                    'doctor_name': request.user.full_name,
                    'patient_name': rx.patient.name,
                    'prescription_date': str(rx.prescription_date or timezone.now().date()),
                    'medicines': rx.medicines
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Patients, caregivers, and family members cannot discontinue doctor prescriptions.", status=status.HTTP_403_FORBIDDEN)

        rx = Prescription.objects.filter(id=id).first()
        if not rx:
            return Response("Prescription not found.", status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, rx.patient_id):
            return Response("Unauthorized: Doctor must be linked to patient to discontinue prescription.", status=status.HTTP_403_FORBIDDEN)

        patient = rx.patient
        medicines = rx.medicines
        pid = rx.patient_id
        previous_status = rx.status

        # Soft Discontinuation: Preserve prescription and adherence history
        rx.status = 'Discontinued'
        rx.save()
        # Deactivate active schedules so future occurrences no longer appear
        rx.schedules.filter(is_active=True).update(is_active=False)

        log_audit_trail(request, 'Discontinued Prescription', f"Prescription ID {id} for Patient {pid}", 'Success')

        # Dispatch Stage 2 notification only if status was not already discontinued
        if previous_status != 'Discontinued':
            from notifications.notification_service import dispatch_event_notification
            dispatch_event_notification(
                event_type='PRESCRIPTION_DISCONTINUED',
                patient_or_id=patient,
                title="Prescription Discontinued",
                message="A prescription has been discontinued by your doctor.",
                category="prescription",
                target_id=id,
                actor=request.user,
                context_data={
                    'doctor_name': request.user.full_name,
                    'patient_name': patient.name,
                    'medicines': medicines
                }
            )
        return Response({"detail": "Prescription discontinued successfully.", "status": "Discontinued"}, status=status.HTTP_200_OK)

class MedicationScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not patient_id:
            return Response("Patient context required.", status=status.HTTP_400_BAD_REQUEST)

        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized access to patient medication schedules.", status=status.HTTP_403_FORBIDDEN)

        prescription_id = request.query_params.get('prescriptionId') or request.query_params.get('prescription_id')
        schedules = MedicationSchedule.objects.filter(
            prescription__patient_id=patient_id,
            is_active=True
        ).select_related('prescription')

        if prescription_id:
            schedules = schedules.filter(prescription_id=prescription_id)

        return Response(MedicationScheduleSerializer(schedules, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Only licensed doctors can configure medication schedules.", status=status.HTTP_403_FORBIDDEN)

        rx_id = request.data.get('prescriptionId') or request.data.get('prescription_id')
        if not rx_id:
            return Response("prescription_id is required.", status=status.HTTP_400_BAD_REQUEST)

        rx = Prescription.objects.filter(id=rx_id).first()
        if not rx:
            return Response("Prescription not found.", status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, rx.patient_id):
            return Response("Unauthorized: Doctor must be authorized for this patient.", status=status.HTTP_403_FORBIDDEN)

        if rx.status != 'Active':
            return Response("Cannot configure schedule on a non-active prescription.", status=status.HTTP_400_BAD_REQUEST)

        times_list = request.data.get('times')
        if times_list is not None and isinstance(times_list, list):
            if len(times_list) == 0:
                return Response("At least one scheduled time must be provided.", status=status.HTTP_400_BAD_REQUEST)
            
            parsed_times = []
            for t_item in times_list:
                t_str = str(t_item).strip()
                try:
                    if len(t_str) == 5:
                        parsed_times.append(datetime.strptime(t_str, '%H:%M').time())
                    else:
                        parsed_times.append(datetime.strptime(t_str, '%H:%M:%S').time())
                except ValueError:
                    return Response(f"Invalid time format: '{t_str}'. Expected HH:MM.", status=status.HTTP_400_BAD_REQUEST)

            if len(parsed_times) != len(set(parsed_times)):
                return Response("Duplicate scheduled times provided in request.", status=status.HTTP_400_BAD_REQUEST)

            local_today = timezone.now().astimezone(APP_TIMEZONE).date()

            with transaction.atomic():
                # Schedule Versioning: Deactivate existing active schedules to preserve past dose logs
                rx.schedules.filter(is_active=True).update(is_active=False, end_date=local_today)
                
                created_schedules = []
                for p_time in sorted(parsed_times):
                    sch = MedicationSchedule.objects.create(
                        prescription=rx,
                        scheduled_time=p_time,
                        start_date=local_today,
                        is_active=True
                    )
                    created_schedules.append(sch)

            log_audit_trail(request, 'Configured Medication Schedule', f"Configured {len(created_schedules)} schedule times for Rx #{rx.id}", 'Success')
            return Response(MedicationScheduleSerializer(created_schedules, many=True).data, status=status.HTTP_201_CREATED)

        # Single schedule item creation
        scheduled_time_str = request.data.get('scheduled_time') or request.data.get('scheduledTime')
        if not scheduled_time_str:
            return Response("scheduled_time or times list is required.", status=status.HTTP_400_BAD_REQUEST)

        try:
            t_str = str(scheduled_time_str).strip()
            parsed_time = datetime.strptime(t_str, '%H:%M').time() if len(t_str) == 5 else datetime.strptime(t_str, '%H:%M:%S').time()
        except ValueError:
            return Response("Invalid time format. Expected HH:MM.", status=status.HTTP_400_BAD_REQUEST)

        start_date = request.data.get('start_date') or timezone.now().astimezone(APP_TIMEZONE).date()
        end_date = request.data.get('end_date')

        if start_date and end_date and start_date > end_date:
            return Response("start_date must be before or equal to end_date.", status=status.HTTP_400_BAD_REQUEST)

        if MedicationSchedule.objects.filter(prescription=rx, scheduled_time=parsed_time, is_active=True).exists():
            return Response("An active schedule at this time already exists for this prescription.", status=status.HTTP_400_BAD_REQUEST)

        sch = MedicationSchedule.objects.create(
            prescription=rx,
            scheduled_time=parsed_time,
            time_label=request.data.get('time_label', ''),
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        return Response(MedicationScheduleSerializer(sch).data, status=status.HTTP_201_CREATED)

class MedicationTodayTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not patient_id:
            return Response("Patient context required.", status=status.HTTP_400_BAD_REQUEST)

        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to view patient medication timeline.", status=status.HTTP_403_FORBIDDEN)

        current_local_dt = timezone.now().astimezone(APP_TIMEZONE)
        current_local_date = current_local_dt.date()

        active_schedules = MedicationSchedule.objects.filter(
            prescription__patient_id=patient_id,
            prescription__status='Active',
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=current_local_date)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=current_local_date)
        ).select_related('prescription', 'prescription__prescribing_doctor').order_by('scheduled_time')

        today_logs = {
            log.schedule_id: log 
            for log in MedicationDoseLog.objects.filter(
                schedule__in=active_schedules,
                scheduled_date=current_local_date
            ).select_related('marked_by')
        }

        doses = []
        taken_count = 0
        skipped_count = 0
        missed_count = 0
        due_count = 0
        upcoming_count = 0

        user_role = request.user.role
        can_mark = (user_role == 'patient') or (user_role == 'caregiver')

        for sch in active_schedules:
            log = today_logs.get(sch.id)
            scheduled_dt = datetime.combine(current_local_date, sch.scheduled_time, tzinfo=APP_TIMEZONE)
            diff_seconds = (current_local_dt - scheduled_dt).total_seconds()
            grace_seconds = MEDICATION_GRACE_PERIOD_MINUTES * 60

            if log:
                derived_status = log.status
                if log.status == 'TAKEN':
                    taken_count += 1
                elif log.status == 'SKIPPED':
                    skipped_count += 1
            else:
                if diff_seconds > grace_seconds:
                    derived_status = 'MISSED'
                    missed_count += 1
                elif diff_seconds >= -1800:
                    derived_status = 'DUE'
                    due_count += 1
                else:
                    derived_status = 'UPCOMING'
                    upcoming_count += 1

            doses.append({
                'schedule_id': sch.id,
                'prescription_id': sch.prescription_id,
                'medicine_name': sch.prescription.medicines,
                'dosage': sch.prescription.dosage,
                'instructions': sch.prescription.instructions,
                'prescribing_doctor_name': sch.prescription.prescribing_doctor_name,
                'scheduled_time': sch.scheduled_time.strftime('%H:%M'),
                'scheduled_time_formatted': sch.scheduled_time.strftime('%I:%M %p'),
                'time_label': sch.time_label,
                'scheduled_date': str(current_local_date),
                'derived_status': derived_status,
                'log_id': log.id if log else None,
                'action_at': log.action_at if log else None,
                'marked_by_name': log.marked_by.full_name if (log and log.marked_by) else (log.marked_by.email if log and log.marked_by else None),
                'notes': log.notes if log else '',
                'is_actionable': can_mark and (log is None)
            })

        prescriptions_without_schedules = Prescription.objects.filter(
            patient_id=patient_id,
            status='Active'
        ).exclude(
            schedules__is_active=True
        ).values('id', 'medicines', 'dosage', 'frequency', 'instructions')

        return Response({
            'date': str(current_local_date),
            'timezone': 'Asia/Kolkata',
            'doses': doses,
            'unconfigured_prescriptions': list(prescriptions_without_schedules),
            'summary': {
                'total_scheduled_today': len(doses),
                'taken_count': taken_count,
                'skipped_count': skipped_count,
                'missed_count': missed_count,
                'due_count': due_count,
                'upcoming_count': upcoming_count,
            }
        }, status=status.HTTP_200_OK)

class MedicationDoseActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, schedule_id, action_type):
        action_upper = action_type.strip().upper()
        if action_upper not in ['TAKE', 'SKIP', 'TAKEN', 'SKIPPED']:
            return Response("Invalid dose action. Expected 'take' or 'skip'.", status=status.HTTP_400_BAD_REQUEST)

        target_status = 'TAKEN' if action_upper in ['TAKE', 'TAKEN'] else 'SKIPPED'

        sch = MedicationSchedule.objects.filter(id=schedule_id).select_related('prescription', 'prescription__patient').first()
        if not sch:
            return Response("Medication schedule not found.", status=status.HTTP_404_NOT_FOUND)

        rx = sch.prescription
        patient = rx.patient
        user = request.user

        if user.role == 'doctor':
            return Response("Unauthorized: Doctors cannot manually record patient dose adherence actions.", status=status.HTTP_403_FORBIDDEN)
        if user.role == 'family':
            return Response("Unauthorized: Family members have read-only access to medication tracking.", status=status.HTTP_403_FORBIDDEN)
        if user.role == 'caregiver':
            if not CaregiverPatientLink.objects.filter(caregiver=user, patient=patient, is_approved=True).exists():
                return Response("Unauthorized: Caregiver must have an approved link with this patient to record doses.", status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'patient':
            if not is_user_authorized_for_patient(user, patient.id):
                return Response("Unauthorized: Patients can only record their own medication doses.", status=status.HTTP_403_FORBIDDEN)
        else:
            return Response("Unauthorized action role.", status=status.HTTP_403_FORBIDDEN)

        req_date_str = request.data.get('scheduled_date') or request.data.get('scheduledDate')
        if req_date_str:
            try:
                target_date = datetime.strptime(str(req_date_str).strip(), '%Y-%m-%d').date()
            except ValueError:
                return Response("Invalid scheduled_date format. Expected YYYY-MM-DD.", status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = timezone.now().astimezone(APP_TIMEZONE).date()

        notes = request.data.get('notes') or request.data.get('reason') or ''

        with transaction.atomic():
            existing_log = MedicationDoseLog.objects.select_for_update().filter(
                schedule=sch,
                scheduled_date=target_date
            ).first()

            if existing_log:
                if existing_log.status == target_status:
                    return Response(MedicationDoseLogSerializer(existing_log).data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"detail": f"Dose on {target_date} has already been recorded as {existing_log.status} and cannot be modified."},
                        status=status.HTTP_409_CONFLICT
                    )

            dose_log = MedicationDoseLog.objects.create(
                schedule=sch,
                scheduled_date=target_date,
                status=target_status,
                action_at=timezone.now(),
                marked_by=user,
                notes=str(notes).strip()
            )

        log_audit_trail(
            request=request,
            action=f"Marked Dose {target_status}",
            target=f"Dose for Rx #{rx.id} ({rx.medicines}) on {target_date}",
            result='Success'
        )

        return Response(MedicationDoseLogSerializer(dose_log).data, status=status.HTTP_201_CREATED)

class MedicationAdherenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not patient_id:
            return Response("Patient context required.", status=status.HTTP_400_BAD_REQUEST)

        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to view patient adherence.", status=status.HTTP_403_FORBIDDEN)

        try:
            days = int(request.query_params.get('days', 7))
        except ValueError:
            days = 7

        current_local_dt = timezone.now().astimezone(APP_TIMEZONE)
        current_local_date = current_local_dt.date()
        start_date = current_local_date - timedelta(days=days - 1)

        schedules = MedicationSchedule.objects.filter(
            prescription__patient_id=patient_id
        ).select_related('prescription')

        logs = MedicationDoseLog.objects.filter(
            schedule__prescription__patient_id=patient_id,
            scheduled_date__gte=start_date,
            scheduled_date__lte=current_local_date
        )

        logs_by_key = {(l.schedule_id, l.scheduled_date): l for l in logs}

        total_taken = 0
        total_skipped = 0
        total_missed = 0
        daily_breakdown = []

        grace_seconds = MEDICATION_GRACE_PERIOD_MINUTES * 60

        for day_offset in range(days):
            eval_date = start_date + timedelta(days=day_offset)
            is_today = (eval_date == current_local_date)

            day_taken = 0
            day_skipped = 0
            day_missed = 0

            for sch in schedules:
                if sch.start_date and sch.start_date > eval_date:
                    continue
                if sch.end_date and sch.end_date < eval_date:
                    continue
                if not sch.is_active:
                    if sch.end_date and eval_date > sch.end_date:
                        continue
                    elif not sch.end_date and (sch.id, eval_date) not in logs_by_key:
                        continue


                log_entry = logs_by_key.get((sch.id, eval_date))

                if log_entry:
                    if log_entry.status == 'TAKEN':
                        day_taken += 1
                    elif log_entry.status == 'SKIPPED':
                        day_skipped += 1
                else:
                    if not is_today:
                        day_missed += 1
                    else:
                        scheduled_dt = datetime.combine(eval_date, sch.scheduled_time, tzinfo=APP_TIMEZONE)
                        diff_seconds = (current_local_dt - scheduled_dt).total_seconds()
                        if diff_seconds > grace_seconds:
                            day_missed += 1

            day_eligible = day_taken + day_skipped + day_missed
            day_rate = round((day_taken / day_eligible) * 100.0, 1) if day_eligible > 0 else None

            daily_breakdown.append({
                'date': str(eval_date),
                'taken': day_taken,
                'skipped': day_skipped,
                'missed': day_missed,
                'eligible': day_eligible,
                'adherence_rate': day_rate
            })

            total_taken += day_taken
            total_skipped += day_skipped
            total_missed += day_missed

        total_eligible = total_taken + total_skipped + total_missed
        adherence_rate = round((total_taken / total_eligible) * 100.0, 1) if total_eligible > 0 else None

        return Response({
            'patient_id': patient_id,
            'window_days': days,
            'start_date': str(start_date),
            'end_date': str(current_local_date),
            'eligible_doses': total_eligible,
            'taken_count': total_taken,
            'skipped_count': total_skipped,
            'missed_count': total_missed,
            'adherence_rate': adherence_rate,
            'daily_breakdown': daily_breakdown
        }, status=status.HTTP_200_OK)

class MedicationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not patient_id:
            return Response("Patient context required.", status=status.HTTP_400_BAD_REQUEST)

        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to view patient medication history.", status=status.HTTP_403_FORBIDDEN)

        logs = MedicationDoseLog.objects.filter(
            schedule__prescription__patient_id=patient_id
        ).select_related(
            'schedule', 'schedule__prescription', 'marked_by'
        ).order_by('-scheduled_date', '-action_at')

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            logs = logs.filter(scheduled_date__gte=start_date)
        if end_date:
            logs = logs.filter(scheduled_date__lte=end_date)

        return Response(MedicationDoseLogSerializer(logs[:100], many=True).data, status=status.HTTP_200_OK)
