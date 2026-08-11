from django.db import models

class Alert(models.Model):
    SEVERITY_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    )
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='alerts')
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50) # e.g. 'Heart Rate', 'SpO2', 'Fall', 'Emergency'
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, default='Active') # e.g. 'Active', 'Resolved'
    source = models.CharField(max_length=50, default='System') # e.g. 'System', 'AI', 'Wearable'

    def __str__(self):
        return f"{self.severity} Alert for {self.patient_id} - {self.type}"
