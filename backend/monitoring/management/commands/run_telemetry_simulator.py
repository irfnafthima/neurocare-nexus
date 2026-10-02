import sys
import time
from django.core.management.base import BaseCommand
from patients.models import Patient
from monitoring.telemetry_simulator import RealTimeTelemetrySimulator


class Command(BaseCommand):
    help = 'Runs continuous multi-patient telemetry simulator for development & research'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=5,
            help='Number of patients to simulate simultaneously (default: 5)'
        )
        parser.add_argument(
            '--patient-ids',
            nargs='+',
            type=str,
            help='Explicit list of Patient IDs to simulate (e.g. --patient-ids P-101 P-102)'
        )
        parser.add_argument(
            '--interval',
            type=float,
            default=2.0,
            help='Telemetry packet interval in seconds per patient (default: 2.0)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=None,
            help='Simulation duration in seconds (default: infinite until Ctrl+C)'
        )
        parser.add_argument(
            '--no-persist',
            action='store_true',
            help='Run in memory only without persisting SensorReading to database'
        )

    def handle(self, *args, **options):
        patient_count = options['patients']
        explicit_ids = options.get('patient_ids')
        interval = options['interval']
        duration = options.get('duration')
        persist = not options['no_persist']

        # 1. Resolve Patient IDs
        if explicit_ids:
            target_ids = explicit_ids
            # Validate existence
            found_ids = list(Patient.objects.filter(id__in=target_ids).values_list('id', flat=True))
            if not found_ids:
                self.stderr.write(self.style.ERROR(f"None of the specified patient IDs exist: {target_ids}"))
                return
            target_ids = [str(pid) for pid in found_ids]
        else:
            db_patients = list(Patient.objects.all().values_list('id', flat=True)[:patient_count])
            if not db_patients:
                self.stderr.write(self.style.ERROR("No Patient records found in database."))
                return
            target_ids = [str(pid) for pid in db_patients]

        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(self.style.SUCCESS("  NEUROCARE NEXUS — MULTI-PATIENT TELEMETRY SIMULATOR"))
        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(f"Target Patients ({len(target_ids)}): {', '.join(target_ids)}")
        self.stdout.write(f"Packet Interval: {interval}s per patient")
        self.stdout.write(f"Duration: {duration}s" if duration else "Duration: Continuous (Press Ctrl+C to stop)")
        self.stdout.write(f"Database Persistence: {'ENABLED (SensorReading)' if persist else 'DISABLED'}")
        self.stdout.write("-" * 65)

        def packet_callback(packet, reading, alerts):
            alert_str = f" [ALERT: {len(alerts)}]" if alerts else ""
            self.stdout.write(
                f"[{packet.timestamp.strftime('%H:%M:%S')}] Patient {packet.patient_id} | "
                f"HR: {packet.heart_rate} bpm | SpO2: {packet.spo2}% | Temp: {packet.temperature}°C | "
                f"Acc: ({packet.accel_x},{packet.accel_y},{packet.accel_z}) | Bat: {packet.esp32_battery}%{alert_str}"
            )

        simulator = RealTimeTelemetrySimulator(
            patient_ids=target_ids,
            interval_seconds=interval,
            duration_seconds=duration,
            persist=persist,
            on_packet_callback=packet_callback
        )

        try:
            simulator.start(async_mode=False)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nInterrupt received. Stopping simulation gracefully..."))
            simulator.stop()

        self.stdout.write("-" * 65)
        self.stdout.write(self.style.SUCCESS(
            f"Simulation finished cleanly.\n"
            f"Total Packets Emitted: {simulator.total_packets_emitted}\n"
            f"Total Alerts Generated: {simulator.total_alerts_emitted}"
        ))
