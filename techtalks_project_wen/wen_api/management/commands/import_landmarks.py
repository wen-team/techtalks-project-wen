"""
Load landmarks from the OSM CSV (made by research/osm_coverage) into the database.

Run:  python manage.py import_landmarks
Safe to run again: it deletes the old OSM rows first, then imports fresh.
"""
import csv
from pathlib import Path

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction

from wen_api.models import Landmark, LandmarkAlias

DEFAULT_CSV = Path(__file__).resolve().parents[2] / "data" / "landmarks.csv"
ALIAS_COLUMNS = ["name", "name_ar", "name_en", "alt_name", "brand"]


def normalize(text):
    # lowercase + collapse extra spaces, so "AUB  Gate" == "aub gate"
    return " ".join(text.lower().split())


class Command(BaseCommand):
    help = "Import landmarks from the OSM coverage CSV"

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(DEFAULT_CSV), help="path to landmarks.csv")

    @transaction.atomic  # all or nothing: if one row fails, nothing is saved
    def handle(self, *args, **options):
        # utf-8-sig skips the invisible BOM that Excel-friendly CSVs start with
        with open(options["csv"], encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        _, per_model = Landmark.objects.filter(source="osm").delete()
        deleted = per_model.get("wen_api.Landmark", 0)  # aliases are deleted with them

        landmarks, alias_rows = [], []
        for row in rows:
            landmark = Landmark(
                name=row["name"],
                name_ar=row["name_ar"],
                name_en=row["name_en"],
                brand=row["brand"],
                category=row["category"],
                area=row["area"],
                location=Point(float(row["lon"]), float(row["lat"]), srid=4326),  # x=lon, y=lat
                source="osm",
            )
            landmarks.append(landmark)

            # collect every way of writing this landmark, without duplicates
            seen = set()
            for column in ALIAS_COLUMNS:
                for value in row[column].split(";"):  # OSM puts several alt names as "a;b"
                    value = value.strip()
                    key = normalize(value)
                    if key and key not in seen:
                        seen.add(key)
                        alias_rows.append((landmark, value, key))

        Landmark.objects.bulk_create(landmarks)  # one fast INSERT instead of 2000
        LandmarkAlias.objects.bulk_create(
            LandmarkAlias(landmark=lm, alias=alias, normalized=key) for lm, alias, key in alias_rows
        )

        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(landmarks)} landmarks and {len(alias_rows)} aliases "
            f"(removed {deleted} old rows)"
        ))