import base64
import hashlib
import hmac
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

def string_to_sign(method, ts, web_id=''):
    web_id = '' if None else web_id
    return "%s%s%s%d" % (method, web_id, settings.VUZIT_PUBLIC_KEY, ts)

def sign_msg(msg):
    return base64.b64encode(hmac.new(settings.VUZIT_PRIVATE_KEY, msg, hashlib.sha1).digest())

class PictureCreateView(CreateView):
    model = Picture

    def form_valid(self, form):
        self.object = form.save()
        f = self.request.FILES.get('file')

        # upload to vuzit
        register_openers()

        ts = int(time.time())
        datagen, headers = multipart_encode({
            "method": "create",
            "upload": open(settings.MEDIA_ROOT + "pictures/" + f.name.replace(" ", "_")),
            "secure": "1",
            "download_document": "1",
            "download_pdf": "1",
            "key": settings.VUZIT_PUBLIC_KEY,
            "signature": sign_msg(string_to_sign("create", ts)),
            "timestamp": str(ts),
        })
        request = urllib2.Request("http://vuzit.com/documents.json", datagen, headers)
        response_json = urllib2.urlopen(request).read()
        uuid = simplejson.loads(response_json)['document']['web_id']
        self.object.uuid = uuid
        self.object.save()
        print uuid

        # wait for the document to be processed
        time.sleep(30)

        # get the thumbnail
        ts = int(time.time())
        params = {
            't': 'thumb',
            'key': settings.VUZIT_PUBLIC_KEY,
            'signature': sign_msg(string_to_sign("show", ts, uuid)),
            'timestamp': str(ts),
        }
        request = urllib2.Request("http://vuzit.com/documents/%s/pages/0.jpg?%s" % (uuid, urllib.urlencode(params)))
        try:
            response_file = urllib2.urlopen(request)
        except Exception, e:
            print e.fp.read()
            raise e
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

        ts = int(time.time())
        retval = [{
            'uuid': self.object.uuid,
            'signature': urllib.quote_plus(sign_msg(string_to_sign("show", ts, self.object.uuid))),
            'timestamp': str(ts),
        }]
        response = JSONResponse(retval, {}, response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

class JSONResponse(HttpResponse):
    """JSON response class."""
    def __init__(self,obj='',json_opts={},mimetype="application/json",*args,**kwargs):
        content = simplejson.dumps(obj,**json_opts)
        super(JSONResponse,self).__init__(content,mimetype,*args,**kwargs)