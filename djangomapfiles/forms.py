from django import forms
from .models import DataFile


class DataFileUploadForm(forms.ModelForm):
    class Meta:
        model = DataFile
        fields = ['name',
                  'file_type',
                  'encoding',
                  'stored_file']

    
class DataFileEditForm(forms.ModelForm):
    class Meta:
        model = DataFile
