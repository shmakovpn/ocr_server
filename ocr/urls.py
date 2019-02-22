#21.02.2019 shmakovpn
from django.urls import path

#importing views
from .views import *


app_name = 'ocr'
urlpatterns = [
    # path('', Index.as_view(), name='index'),
    # path('', main_page, name='main_page'),
    path('', main_page, name='main_page'),
]