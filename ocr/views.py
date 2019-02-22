from django.shortcuts import render
from .settings import *

# Create your views here.
def main_page(request):
    params = {}
    params["package"] = __package__
    params["STORE_FILES"] = STORE_FILES
    params["STORE_PDF"] = STORE_PDF
    return render(request, __package__+'/main_page.html', params)