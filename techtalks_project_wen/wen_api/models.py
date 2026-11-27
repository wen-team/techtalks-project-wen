#from django.db import models

# Create your models here.

# GeoDjango models: same as django.db.models, plus map fields like PointField
from django.contrib.gis.db import models


class Landmark(models.Model):
    """A known place (shop, church, school...) that people use in directions."""

    name = models.CharField(max_length=255)                  # main name from OSM
    name_ar = models.CharField(max_length=255, blank=True)   # Arabic name, if any
    name_en = models.CharField(max_length=255, blank=True)   # English name, if any
    brand = models.CharField(max_length=255, blank=True)     # e.g. "Spinneys", "Total"
    category = models.CharField(max_length=100, blank=True)  # e.g. "amenity=pharmacy"
    area = models.CharField(max_length=100, blank=True)      # e.g. "Hamra"
    location = models.PointField(srid=4326)                  # lon/lat on the map (GPS)
    source = models.CharField(max_length=20, default="osm")  # where the row came from
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["area"])]

    def __str__(self):
        return f"{self.name} ({self.area})"


class LandmarkAlias(models.Model):
    """Every other way people write the same landmark (Arabic, English, brand, Arabizi...)."""

    landmark = models.ForeignKey(Landmark, on_delete=models.CASCADE, related_name="aliases")
    alias = models.CharField(max_length=255)                   # as written
    normalized = models.CharField(max_length=255, db_index=True)  # lowercase, for searching

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["landmark", "normalized"], name="unique_alias_per_landmark")
        ]

    def __str__(self):
        return self.alias