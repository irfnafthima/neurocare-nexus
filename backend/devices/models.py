from django.db import models

class SyntheticDevice(models.Model):
    serial = models.CharField(max_length=20, primary_key=True)
    mac = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=50, default='Unassigned')

    def __str__(self):
        return f"{self.serial} ({self.mac})"

class WearableDevice(models.Model):
    serial = models.CharField(max_length=50, primary_key=True)
    mac = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100, default='Physical ESP32 Wearable Node')
    device_type = models.CharField(max_length=50, default='ESP32_WEARABLE')
    device_key_hash = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=50, default='Active')
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def set_device_key(self, raw_key: str):
        import hashlib
        self.device_key_hash = hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()

    def check_device_key(self, raw_key: str) -> bool:
        import hashlib
        import secrets
        if not self.device_key_hash or not raw_key:
            return False
        computed_hash = hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()
        return secrets.compare_digest(self.device_key_hash, computed_hash)

    @property
    def assigned_patient(self):
        assignment = getattr(self, 'assignment', None)
        return assignment.patient if assignment else None

    def __str__(self):
        return f"{self.serial} - {self.status}"

class DeviceAssignment(models.Model):
    patient = models.OneToOneField('patients.Patient', on_delete=models.CASCADE, related_name='device_assignment')
    device = models.OneToOneField(WearableDevice, on_delete=models.CASCADE, related_name='assignment')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment: {self.patient_id} <-> {self.device.serial}"
