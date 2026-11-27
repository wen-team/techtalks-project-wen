#from django.contrib import admin

# Register your models here.

from django.contrib.gis import admin

from .models import Landmark, LandmarkAlias


class AliasInline(admin.TabularInline):
    model = LandmarkAlias
    extra = 0


@admin.register(Landmark)
class LandmarkAdmin(admin.GISModelAdmin):  # GISModelAdmin shows the point on a map
    list_display = ("name", "name_ar", "brand", "category", "area")
    list_filter = ("area", "source")
    search_fields = ("name", "name_ar", "name_en", "brand", "aliases__normalized")
    inlines = [AliasInline]