from django.contrib import admin
from .models import DisasterReport, LandslideEvent, HurricaneData, LocationPoint, UploadedDataset

admin.site.register(DisasterReport)
admin.site.register(LandslideEvent)
admin.site.register(HurricaneData)
admin.site.register(LocationPoint)
admin.site.register(UploadedDataset)

