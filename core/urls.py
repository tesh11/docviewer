from django.conf.urls.defaults import *
from core.views import PictureCreateView, PictureDeleteView, PictureViewerView

urlpatterns = patterns('',
    (r'^new/$', PictureCreateView.as_view(), {}, 'upload-new'),
    (r'^delete/(?P<pk>\d+)$', PictureDeleteView.as_view(), {}, 'upload-delete'),
    (r'^view/(?P<pk>\d+)$', PictureViewerView.as_view(), {}, 'upload-view'),
)
