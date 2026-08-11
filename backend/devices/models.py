from django.db import models

class SyntheticDevice(models.Model):
    serial = models.CharField(max_length=20, primary_key=True)
    mac = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=50, default='Unassigned')

    def __str__(self):
        return f"{self.serial} ({self.mac})"

class WearableDevice(models.Model):
    serial = models.CharField(max_length=20, primary_key=True)
    mac = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=50, default='Active')

    def __str__(self):
        return f"{self.serial} - {self.status}"

class DeviceAssignment(models.Model):
    patient = models.OneToOneField('patients.Patient', on_delete=models.CASCADE, related_name='device_assignment')
    device = models.OneToOneField(WearableDevice, on_delete=models.CASCADE, related_name='assignment')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment: {self.patient_id} <-> {self.device.serial}"
