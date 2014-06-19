from django.conf.urls import patterns, include, url
from mapfiles import views

## File manager: CRUD patterns
urlpatterns = patterns('',
                       url(r'^$', views.datafiles_main, name='home'),
                       url(r'^list/$', views.list_datafiles, name='list_datafiles'),
                       url(r'^import$', 
                            views.upload_datafile, name='upload_datafile'),
                        url(r'^view/(?P<file_id>\d+)$', 
                            views.view_datafile, name='view_datafile'),
                        url(r'^edit/(?P<file_id>\d+)$', 
                            views.edit_datafile, name='edit_datafile'),
                        url(r'^delete/(?P<file_id>\d+)$', 
                            views.delete_datafile, name='delete_datafile'),
)

## Feature patterns
urlpatterns += patterns('',
                        url(r'^feature/view/(?P<feat_id>\d+)$', 
                            views.view_feature, name='view_feature'),
                        url(r'^feature/locfind/$', 
                            views.feature_detail_by_loc, name='feature_detail_by_loc'),
)
