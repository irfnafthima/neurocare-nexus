from rest_framework import serializers
from alerts.models import Alert

class AlertSerializer(serializers.ModelSerializer):
    patient_id = serializers.CharField(source='patient.id', read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'patient', 'patient_id', 'patient_name', 
            'timestamp', 'type', 'severity', 'message', 
            'status', 'source'
        ]
        read_only_fields = ['id', 'patient', 'timestamp']
