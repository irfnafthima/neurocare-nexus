from rest_framework import serializers
from prescriptions.models import Prescription, MedicationSchedule, MedicationDoseLog

class MedicationScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationSchedule
        fields = [
            'id', 'prescription', 'scheduled_time', 'time_label',
            'start_date', 'end_date', 'is_active', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError('start_date must be before or equal to end_date.')
        return data

class MedicationDoseLogSerializer(serializers.ModelSerializer):
    marked_by_name = serializers.CharField(source='marked_by.full_name', read_only=True)
    marked_by_role = serializers.CharField(source='marked_by.role', read_only=True)

    class Meta:
        model = MedicationDoseLog
        fields = [
            'id', 'schedule', 'scheduled_date', 'status',
            'action_at', 'marked_by', 'marked_by_name', 'marked_by_role',
            'notes', 'created_at', 'updated_at'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    prescribing_doctor_email = serializers.CharField(source='prescribing_doctor.email', read_only=True)
    schedules = MedicationScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'prescribing_doctor', 'prescribing_doctor_email',
            'prescribing_doctor_name', 'prescription_date', 'medicines',
            'dosage', 'frequency', 'duration', 'instructions', 'document',
            'status', 'schedules'
        ]
