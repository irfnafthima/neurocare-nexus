"""
Django Management Command: import_reference_data
================================================

Imports the synthetic reference CSV files into the Django database.

Usage:
    python manage.py import_reference_data [--dry-run] [--clear] [--only doctors facilities affiliations disciplinary]

Options:
    --dry-run   Validate and parse the CSV files but do not write to the database
    --clear     Clear existing reference data before importing (CAUTION: destructive)
    --only      Import only specific datasets: doctors, facilities, affiliations, disciplinary

Safety notes:
    - Does NOT modify DoctorProfile, Patient, or any authenticated user data
    - Only imports into reference tables: ReferenceDoctorRegistry, HealthFacility,
      ReferenceDoctorAffiliation, DoctorDisciplinaryRecord

Author: NeuroCare Nexus Academic Team
"""

import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


def parse_date(val):
    if not val or not val.strip():
        return None
    try:
        return datetime.strptime(val.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


class Command(BaseCommand):
    help = (
        'Imports synthetic reference data CSVs into NeuroCare Nexus Django database. '
        'Only writes to reference tables. Does not touch authenticated user data.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and validate CSVs without writing to the database.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing reference data before importing (CAUTION: destructive).',
        )
        parser.add_argument(
            '--only',
            nargs='+',
            choices=['doctors', 'facilities', 'affiliations', 'disciplinary'],
            help='Import only specified datasets.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear = options['clear']
        only = options.get('only') or ['doctors', 'facilities', 'affiliations', 'disciplinary']

        data_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'reference_data'
        )
        data_dir = os.path.abspath(data_dir)

        if not os.path.exists(data_dir):
            raise CommandError(
                f"Reference data directory not found: {data_dir}\n"
                "Run: python data_generation/generate_reference_data.py first."
            )

        self.stdout.write(self.style.NOTICE(
            f"{'[DRY RUN] ' if dry_run else ''}Importing synthetic reference data from:\n  {data_dir}"
        ))
        self.stdout.write(self.style.WARNING(
            "REMINDER: This data is SYNTHETIC and for academic use only."
        ))

        if dry_run:
            self.stdout.write(self.style.NOTICE("DRY RUN — no database writes will occur."))

        with transaction.atomic():
            if 'doctors' in only:
                self._import_doctors(data_dir, dry_run, clear)
            if 'facilities' in only:
                self._import_facilities(data_dir, dry_run, clear)
            if 'affiliations' in only:
                self._import_affiliations(data_dir, dry_run, clear)
            if 'disciplinary' in only:
                self._import_disciplinary(data_dir, dry_run, clear)

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.SUCCESS("\nDRY RUN complete — all changes rolled back."))
            else:
                self.stdout.write(self.style.SUCCESS("\nImport complete."))

    # ──────────────────────────────────────────────────────────
    # IMPORT: REFERENCE DOCTORS → ReferenceDoctorRegistry
    # ──────────────────────────────────────────────────────────

    def _import_doctors(self, data_dir, dry_run, clear):
        from doctors.models import ReferenceDoctorRegistry

        csv_path = os.path.join(data_dir, 'reference_doctors.csv')
        if not os.path.exists(csv_path):
            raise CommandError(f"File not found: {csv_path}")

        self.stdout.write(f"\n[doctors] Reading {csv_path} ...")

        if clear and not dry_run:
            count_before = ReferenceDoctorRegistry.objects.count()
            ReferenceDoctorRegistry.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  Cleared {count_before} existing ReferenceDoctorRegistry records."
            ))

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"  Parsed {len(rows)} rows from CSV.")

        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            reg_num = row.get('registration_number', '').strip()
            if not reg_num:
                skipped += 1
                continue

            defaults = {
                'reference_id': row.get('reference_id', '').strip() or None,
                'doctor_name': row.get('doctor_name', '').strip(),
                'normalized_name': row.get('normalized_name', '').strip(),
                'council': row.get('state_medical_council', '').strip(),
                'qualification': row.get('qualification', '').strip(),
                'registration_year': int(row.get('registration_year', 0) or 0),
                'registration_date': parse_date(row.get('registration_date')),
                'specialization': row.get('specialization', '').strip() or None,
                'registration_status': row.get('registration_status', 'ACTIVE').strip(),
                'source_type': row.get('source_type', 'SYNTHETIC_REFERENCE').strip(),
                'source_reference': row.get('source_reference', '').strip() or None,
                'source_year': int(row.get('source_year', 0) or 0) if row.get('source_year') else None,
            }

            if not dry_run:
                obj, was_created = ReferenceDoctorRegistry.objects.update_or_create(
                    registration_number=reg_num,
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"  [doctors] Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))

    # ──────────────────────────────────────────────────────────
    # IMPORT: REFERENCE FACILITIES → HealthFacility
    # ──────────────────────────────────────────────────────────

    def _import_facilities(self, data_dir, dry_run, clear):
        from doctors.models import HealthFacility

        csv_path = os.path.join(data_dir, 'reference_facilities.csv')
        if not os.path.exists(csv_path):
            raise CommandError(f"File not found: {csv_path}")

        self.stdout.write(f"\n[facilities] Reading {csv_path} ...")

        if clear and not dry_run:
            count_before = HealthFacility.objects.count()
            HealthFacility.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  Cleared {count_before} existing HealthFacility records."
            ))

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"  Parsed {len(rows)} rows from CSV.")

        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            fac_id = row.get('facility_id', '').strip()
            fac_identifier = row.get('facility_identifier', fac_id).strip()
            if not fac_identifier:
                skipped += 1
                continue

            ver_status_raw = row.get('verification_status', 'PENDING').strip()
            ver_status = ver_status_raw if ver_status_raw in ('PENDING', 'VERIFIED', 'REJECTED') else 'PENDING'

            defaults = {
                'facility_id': fac_id,
                'name': row.get('facility_name', '').strip(),
                'facility_type': row.get('facility_type', '').strip(),
                'address': f"{row.get('city', '')}, {row.get('district', '')}, {row.get('state', '')}".strip(', '),
                'city': row.get('city', '').strip(),
                'district': row.get('district', '').strip(),
                'state': row.get('state', '').strip(),
                'verification_status': ver_status,
                'source_type': row.get('source_type', 'SYNTHETIC_REFERENCE').strip(),
            }

            if not dry_run:
                obj, was_created = HealthFacility.objects.update_or_create(
                    registration_identifier=fac_identifier,
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"  [facilities] Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))

    # ──────────────────────────────────────────────────────────
    # IMPORT: REFERENCE AFFILIATIONS → ReferenceDoctorAffiliation
    # ──────────────────────────────────────────────────────────

    def _import_affiliations(self, data_dir, dry_run, clear):
        from doctors.models import ReferenceDoctorRegistry, HealthFacility, ReferenceDoctorAffiliation

        csv_path = os.path.join(data_dir, 'doctor_facility_affiliations.csv')
        if not os.path.exists(csv_path):
            raise CommandError(f"File not found: {csv_path}")

        self.stdout.write(f"\n[affiliations] Reading {csv_path} ...")

        if clear and not dry_run:
            count_before = ReferenceDoctorAffiliation.objects.count()
            ReferenceDoctorAffiliation.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  Cleared {count_before} existing ReferenceDoctorAffiliation records."
            ))

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"  Parsed {len(rows)} rows from CSV.")

        # Cache reference doctor and facility mappings for speed
        doc_map = {d.reference_id: d for d in ReferenceDoctorRegistry.objects.filter(reference_id__isnull=False)}
        fac_map = {f.facility_id: f for f in HealthFacility.objects.filter(facility_id__isnull=False)}

        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            aff_id = row.get('affiliation_id', '').strip()
            doc_ref = row.get('reference_doctor_id', '').strip()
            fac_ref = row.get('facility_id', '').strip()

            doc = doc_map.get(doc_ref)
            fac = fac_map.get(fac_ref)

            if not doc or not fac:
                skipped += 1
                continue

            defaults = {
                'reference_doctor': doc,
                'facility': fac,
                'department': row.get('department', '').strip(),
                'designation': row.get('designation', '').strip(),
                'employment_type': row.get('employment_type', 'FULL_TIME').strip(),
                'status': row.get('status', 'CURRENT').strip(),
                'start_date': parse_date(row.get('start_date')),
                'end_date': parse_date(row.get('end_date')),
                'verification_status': row.get('verification_status', 'PENDING').strip(),
                'source_type': row.get('source_type', 'SYNTHETIC_REFERENCE').strip(),
            }

            if not dry_run:
                obj, was_created = ReferenceDoctorAffiliation.objects.update_or_create(
                    affiliation_id=aff_id,
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"  [affiliations] Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))

    # ──────────────────────────────────────────────────────────
    # IMPORT: DISCIPLINARY RECORDS → DoctorDisciplinaryRecord
    # ──────────────────────────────────────────────────────────

    def _import_disciplinary(self, data_dir, dry_run, clear):
        from doctors.models import ReferenceDoctorRegistry, DoctorDisciplinaryRecord

        csv_path = os.path.join(data_dir, 'disciplinary_records.csv')
        if not os.path.exists(csv_path):
            raise CommandError(f"File not found: {csv_path}")

        self.stdout.write(f"\n[disciplinary] Reading {csv_path} ...")

        if clear and not dry_run:
            count_before = DoctorDisciplinaryRecord.objects.count()
            DoctorDisciplinaryRecord.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  Cleared {count_before} existing DoctorDisciplinaryRecord records."
            ))

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"  Parsed {len(rows)} rows from CSV.")

        # Cache reference doctor mappings by registration_number
        doc_map = {d.registration_number: d for d in ReferenceDoctorRegistry.objects.all()}

        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            disc_id = row.get('disciplinary_id', '').strip()
            reg_num = row.get('registration_number', '').strip()
            doc = doc_map.get(reg_num)

            if not doc:
                skipped += 1
                continue

            defaults = {
                'doctor': doc,
                'registration_number': reg_num,
                'doctor_name': row.get('doctor_name', doc.doctor_name).strip(),
                'state_medical_council': row.get('state_medical_council', doc.council).strip(),
                'action_type': row.get('action_type', 'SUSPENSION').strip(),
                'status': row.get('status', 'ACTIVE').strip(),
                'suspended_date': parse_date(row.get('suspended_date')),
                'restored_date': parse_date(row.get('restored_date')),
                'source_type': row.get('source_type', 'SYNTHETIC_TEST_REFERENCE').strip(),
                'source_reference': row.get('source_reference', '').strip() or None,
                'remarks': row.get('remarks', '').strip() or None,
            }

            if not dry_run:
                obj, was_created = DoctorDisciplinaryRecord.objects.update_or_create(
                    disciplinary_id=disc_id,
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"  [disciplinary] Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))

