from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from alerts.models import Alert
from alerts.serializers import AlertSerializer
from patients.views import get_authorized_patients, find_patient_by_identifier
from medical_records.views import is_user_authorized_for_patient
from accounts.utils import log_audit_trail

class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        patient_id = request.query_params.get('patientId')
        severity = request.query_params.get('severity')
        alert_status = request.query_params.get('status')
        alert_type = request.query_params.get('type')

        # Role-based authorized patient base queryset
        authorized_patients = get_authorized_patients(user)

        if patient_id:
            # Check specific patient authorization
            p_obj = find_patient_by_identifier(patient_id)
            if not p_obj:
                return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)
            if not is_user_authorized_for_patient(user, p_obj.id):
                return Response({'error': 'Unauthorized to view alerts for this patient.'}, status=status.HTTP_403_FORBIDDEN)
            alerts_qs = Alert.objects.filter(patient=p_obj)
        else:
            if user.role == 'admin':
                alerts_qs = Alert.objects.all()
            else:
                alerts_qs = Alert.objects.filter(patient__in=authorized_patients)

        if severity and severity.upper() != 'ALL':
            alerts_qs = alerts_qs.filter(severity__iexact=severity)

        if alert_status and alert_status.upper() != 'ALL':
            alerts_qs = alerts_qs.filter(status__iexact=alert_status)

        if alert_type and alert_type.upper() != 'ALL':
            alerts_qs = alerts_qs.filter(type__iexact=alert_type)

        alerts_qs = alerts_qs.select_related('patient').order_by('-timestamp')
        serializer = AlertSerializer(alerts_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AlertResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return self._resolve(request, pk)

    def patch(self, request, pk):
        return self._resolve(request, pk)

    def _resolve(self, request, pk):
        try:
            alert = Alert.objects.select_related('patient').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'error': 'Alert not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, alert.patient.id):
            return Response({'error': 'Unauthorized to update this alert.'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status', 'Resolved')
        alert.status = new_status
        alert.save()

        log_audit_trail(
            request=request,
            action=f"Updated Alert Status to {new_status}",
            target=f"Alert #{alert.id} ({alert.type}) for Patient {alert.patient.id} ({alert.patient.name})",
            result="Success"
        )

        serializer = AlertSerializer(alert)
        return Response(serializer.data, status=status.HTTP_200_OK)

