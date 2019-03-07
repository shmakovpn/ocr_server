"""ocr_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'OCR Server Administration'
# admin.site.index_title = 'Features area'                 # default: "Site administration"
admin.site.site_title = 'Welcome to OCR Server Administration Portal' # default: "Django site admin"

urlpatterns = [
    #re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico', permanent=False)),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=False) ),
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/ocr/', permanent=False)),  # switch to ocr.urls
    path('ocr/', include('ocr.urls')),
]


#if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
