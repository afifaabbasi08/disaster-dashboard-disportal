# disaster_data/models.py
from django.db import models

# 1. General Disaster Report Model
class DisasterReport(models.Model):
    DISASTER_TYPES = [
        ('Flood', 'Flood'),
        ('Earthquake', 'Earthquake'),
        ('Fire', 'Fire'),
        ('Hurricanes', 'Hurricanes'),
        ('Landslides', 'Landslides'),
    ]

    title = models.CharField(max_length=100)
    disaster_type = models.CharField(max_length=50, choices=DISASTER_TYPES)
    location = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return f"{self.title} ({self.disaster_type})"

class EarthquakeData(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    time = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    mag = models.FloatField()
    place = models.TextField()

    class Meta:
        managed = False  # ✅ Tell Django not to touch this table
        db_table = 'earthquake_data'


    def __str__(self):
        return f"{self.place} | Mag: {self.mag}"

# 3. Landslide Data Model
from django.db import models

class LandslideEvent(models.Model):
    event_id = models.IntegerField(primary_key=True)
    event_title = models.CharField(max_length=255, blank=True, null=True)
    event_description = models.TextField(blank=True, null=True)
    location_description = models.TextField(blank=True, null=True)
    location_accuracy = models.CharField(max_length=100, blank=True, null=True)
    landslide_category = models.CharField(max_length=100, blank=True, null=True)
    landslide_trigger = models.CharField(max_length=100, blank=True, null=True)
    landslide_size = models.CharField(max_length=100, blank=True, null=True)
    fatality_count = models.IntegerField(blank=True, null=True)
    injury_count = models.IntegerField(blank=True, null=True)
    event_import_id = models.CharField(max_length=100, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    longitude = models.FloatField()
    latitude = models.FloatField()
    event_date = models.DateField()


    class Meta:
        managed = False  # 🚫 Django won't try to create/delete the table
        db_table = 'disaster_landslide'  # ✅ match your actual table name

    def __str__(self):
        return f"{self.country_name or 'Unknown Country'} | Trigger: {self.landslide_trigger or 'Unknown'}"


#hurricane data model

class HurricaneData(models.Model):
    sid = models.CharField(max_length=50, primary_key=True)  # 👈 Set this as primary key
    number = models.IntegerField(null=True)
    basin = models.CharField(max_length=50, null=True)
    subbasin = models.CharField(max_length=50, null=True)
    iso_time = models.DateTimeField(null=True)
    nature = models.CharField(max_length=50, null=True)
    lat = models.FloatField(null=True)
    lon = models.FloatField(null=True)

    class Meta:
        managed = False
        db_table = 'hurricane_data'

    def __str__(self):
        return f"{self.sid} ({self.iso_time})"
    

#upload csv interface 

class LocationPoint(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.name or 'Point'} ({self.latitude}, {self.longitude})"


class UploadedDataset(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)  # e.g., earthquake, volcano, custom
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} ({self.name})"


    # Add cascade deletion if necessary for related models
    # For example, if each Dataset has related LocationPoints:
    # location_points = models.ForeignKey(LocationPoint, on_delete=models.CASCADE)

class CustomDisasterType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g. volcano, oilspill
    display_name = models.CharField(max_length=150)       # Shown on homepage card
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True, null=True)  # Emoji/icon
    color = models.CharField(max_length=10, default='#007BFF')     # Card color
    table_name = models.CharField(max_length=100)  # e.g. custom_volcano_data
    is_active = models.BooleanField(default=True)  # Whether this disaster type is active

    def __str__(self):
        return self.display_name or self.name

class LandslideYear(models.Model):
    year = models.IntegerField(unique=True)

    def __str__(self):
        return str(self.year)
