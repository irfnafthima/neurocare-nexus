from django.db import models

class SensorReading(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='telemetry')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # MAX30102
    heart_rate = models.IntegerField(null=True, blank=True)
    spo2 = models.IntegerField(null=True, blank=True)
    
    # DS18B20
    temperature = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    # MPU6050
    accel_x = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accel_y = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    accel_z = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gyro_x = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gyro_y = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gyro_z = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fall_detected = models.BooleanField(default=False)
    
    # ESP32 Status
    esp32_connected = models.BooleanField(default=True)
    esp32_battery = models.IntegerField(null=True, blank=True)
    esp32_rssi = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Reading: {self.patient_id} at {self.timestamp}"
