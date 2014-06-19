from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.core import serializers
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.gis.shortcuts import render_to_kml

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.clickjacking import xframe_options_exempt

from .models import DataFile, Feature, Attribute
from .forms import DataFileUploadForm, DataFileEditForm
from .tasks import process_files


ONE_MINUTE = 60
ONE_HOUR = 60 * ONE_MINUTE
ONE_DAY = ONE_HOUR * 24
ONE_WEEK = ONE_DAY * 7
ONE_MONTH = ONE_WEEK * 4

def datafiles_main(request):
    return HttpResponse("YES")


def list_datafiles(request, 
               template_file = 'listdatafiles.html'):
    datafiles = DataFile.objects.all().order_by('-updated')
    temp_vars = { 'datafiles' : datafiles }
    return render(request, template_file, temp_vars)

####### ---------------------------- #######
###       Generic File Uploading     ###
####### ---------------------------- #######

@staff_member_required
def upload_datafile(request,
                    template_file='importdatafile.html'):
    if request.method == 'POST':
        form = DataFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            datafile_object = form.save()
            file_type = datafile_object.file_type
            process_files.delay(datafile_object.id, file_type)
            return redirect('list_datafiles')
    else:
        form = DataFileUploadForm()
    return render(request, template_file, {'form': form})

@cache_page(ONE_MINUTE)
def view_datafile(request, file_id,
                  template_file = 'viewdatafile.html'):
    all_features = Feature.objects.filter(
        datafile__id=file_id)
    datafile = DataFile.objects.get(id=file_id)
    lat, lon = datafile.default_center.tuple
    zoom = datafile.default_zoom
    if not zoom:
        zoom = 10
    temp_vars = {'features' : all_features,
                 'datafile': datafile,
                 'lat': lat,
                 'lon': lon,
                 'zoom': zoom}
    return render(request, template_file, temp_vars)
 

@staff_member_required
def edit_datafile(request, file_id,
                  template_file = 'editdatafile.html'):
    ### What if someone uploads a new version of that file??
    ### needs to be reprocessed AND the old file needs to be
    ### deleted
    datafile = get_object_or_404(DataFile, id=file_id)
    form = DataFileEditForm(request.POST or None, 
                            instance=datafile)
    if form.is_valid():
        form.save()
        return redirect('list_datafiles')
    return render(request, template_file, {'form':form})


@staff_member_required
def delete_datafile(request, file_id,
                    template_file = 'deletedatafile.html'):
    datafile_to_del = get_object_or_404(DataFile, id=file_id)
    temp_vars = {'datafile' : datafile_to_del}
    if request.method == "POST":
        datafile_to_del.stored_file.delete()
        datafile_to_del.delete()
        return redirect('list_datafiles')
            
    return render(request, template_file, temp_vars)


###################################################
### Feature viewers have been lifted totally from main ###
###################################################

@cache_page(ONE_MINUTE)
def view_feature(request, feat_id):
    attributes = Attribute.objects.filter(feature__id=feat_id)
    json_values = serializers.serialize('json', 
                                        attributes,
                                        fields=('field_name', 'field_value'))
    return HttpResponse(json_values, content_type="application/json")

@cache_page(ONE_MINUTE)
def feature_detail_by_loc(request):
    if request.GET:
        if request.GET['longitude'] and request.GET['latitude']:
            lat = float(request.GET.get('latitude', ''))
            lon = float(request.GET.get('longitude', ''))
            detail_pt = Point(lon, lat)
            feature = Feature.objects.filter(geometry__contains=detail_pt)
            edata = serializers.serialize("json", feature)
            return HttpResponse(edata, mimetype='application/json')
        else:
            raise Http404
    else:
        raise Http404


