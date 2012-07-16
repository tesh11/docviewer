import httplib
import urllib
import urllib2
from django.views.generic.detail import BaseDetailView
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import time
from core.models import Picture
from django.views.generic import CreateView, DeleteView

from django.http import HttpResponse
from django.utils import simplejson
from django.core.urlresolvers import reverse

from django.conf import settings

def response_mimetype(request):
    if "application/json" in request.META['HTTP_ACCEPT']:
        return "application/json"
    else:
        return "text/plain"

class PictureCreateView(CreateView):
    model = Picture

    def form_valid(self, form):
        self.object = form.save()
        f = self.request.FILES.get('file')

        # upload to crocodoc
        register_openers()
        datagen, headers = multipart_encode({"file": open(settings.MEDIA_ROOT + "pictures/" + f.name.replace(" ", "_")), "token": settings.CROCODOC_API_KEY})
        request = urllib2.Request("https://crocodoc.com/api/v2/document/upload", datagen, headers)
        response_json = urllib2.urlopen(request).read()
        uuid = simplejson.loads(response_json)['uuid']
        self.object.uuid = uuid
        self.object.save()
        print uuid

        # wait for the document to be processed
        time.sleep(10)

        # get the thumbnail
        request = urllib2.Request("https://crocodoc.com/api/v2/download/thumbnail?token=%s&uuid=%s&size=300x300" % (settings.CROCODOC_API_KEY, uuid))
        response_file = urllib2.urlopen(request)
        t = open(settings.MEDIA_ROOT + "pictures/" + uuid + "_thumbnail.png", "wb")
        t.write(response_file.read())
        t.close()

        data = [{
            'name': f.name,
            'url': settings.MEDIA_URL + "pictures/" + f.name.replace(" ", "_"),
            'thumbnail_url': settings.MEDIA_URL + "pictures/" + uuid + "_thumbnail.png",
            'delete_url': reverse('upload-delete', args=[self.object.id]),
            'delete_type': "DELETE",
            'view_url': reverse('upload-view', args=[self.object.id]),
        }]
        response = JSONResponse(data, {}, response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response


class PictureDeleteView(DeleteView):
    model = Picture

    def delete(self, request, *args, **kwargs):
        """
        This does not actually delete the file, only the database record.  But
        that is easy to implement.
        """
        self.object = self.get_object()
        self.object.delete()
        response = JSONResponse(True, {}, response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

class PictureViewerView(BaseDetailView):
    model = Picture

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # create a viewing session and return the session id
        data = urllib.urlencode({
            'token': settings.CROCODOC_API_KEY,
            'uuid': self.object.uuid,
            'downloadable': 'true'
        })
        request = urllib2.Request("https://crocodoc.com/api/v2/session/create", data)
        response_json = urllib2.urlopen(request).read()
        session_id = simplejson.loads(response_json)['session']
        print session_id

        retval = [{'session_id': session_id}]
        response = JSONResponse(retval, {}, response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

class JSONResponse(HttpResponse):
    """JSON response class."""
    def __init__(self,obj='',json_opts={},mimetype="application/json",*args,**kwargs):
        content = simplejson.dumps(obj,**json_opts)
        super(JSONResponse,self).__init__(content,mimetype,*args,**kwargs)