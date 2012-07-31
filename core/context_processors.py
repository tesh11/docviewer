from django.conf import settings

def vuzit(request):
    return {'VUZIT_PUBLIC_KEY': settings.VUZIT_PUBLIC_KEY}