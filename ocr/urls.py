"""
ocr/urls.py
OCR Server URL dispatcher
"""
__author__ = 'shmakopvn <shmakovpn@yandex.ru>'
__date__ = '2019-03-19'

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from rest_framework.authtoken import views
from rest_framework_swagger.views import get_swagger_view

#importing views
from .views import *
from .apiviews import *


schema_view = get_swagger_view(title='OCR Server API')
app_name = 'ocr'
urlpatterns = [
    path('', RedirectView.as_view(url='/admin', permanent=False)),
    path('login/', views.obtain_auth_token, name='login_view'),
    path('upload/', UploadFile.as_view(), name='upload_file_view'),
    path('list/', OCRedFileList.as_view(), name='ocredfile_list_view'),
    path('swagger/', schema_view),
]

if settings.DEBUG:
    urlpatterns += static('upload', document_root=settings.BASE_DIR+'/'+app_name+'/upload/')
    urlpatterns += static('pdf', document_root=settings.BASE_DIR + '/' + app_name + '/pdf/')
