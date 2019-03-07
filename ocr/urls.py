#21.02.2019 shmakovpn
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

#importing views
from .views import *


app_name = 'ocr'
urlpatterns = [
    path('', main_page, name='main_page'),
]

if settings.DEBUG:
    urlpatterns += static('upload', document_root=settings.BASE_DIR+'/'+app_name+'/upload/')
    urlpatterns += static('pdf', document_root=settings.BASE_DIR + '/' + app_name + '/pdf/')
