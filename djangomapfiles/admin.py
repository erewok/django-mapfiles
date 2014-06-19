from django.contrib.gis import admin

from .models import DataFile
from .tasks import process_files

class DataFileAdmin(admin.ModelAdmin):

    list_display = ('name', 'file_type', 'description', 
                    'view_map', 'first_uploaded', 'updated')
    readonly_fields = ('processed', 'process_note', 'geom_type')
    exclude = ('default_center', 'srs_wkt')

    def save_model(self, request, obj, form, change):
        if not change:
            super(DataFileAdmin, self).save_model(request, obj, form, change)
            process_files.delay(obj.id, obj.file_type)
        elif 'stored_file' in form.changed_data:
            super(DataFileAdmin, self).save_model(request, obj, form, change)
            process_files.delay(obj.id, obj.file_type)
        else:
            super(DataFileAdmin, self).save_model(request, obj, form, change)

    def view_map(self, obj):
        link = """<a href="{}">View map</a>""".format(obj.get_absolute_url())
        return link
    view_map.allow_tags = True

admin.site.register(DataFile, DataFileAdmin)
