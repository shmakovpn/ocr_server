"""
apiviews.py
This file contains views for OCR Server based on Django REST API
"""
__author__ = "shmakovpn <shmakovpn@yandex.ru>"
__date__ = "2019-03-19"

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, MultiPartParser
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import *
from .serializers import *
from .exceptions import *


class UploadFile(APIView):
    """
    Returns the information of the uploaded file 2019-03-19
    """

    parser_classes = (MultiPartParser,)

    def post(self, request,):
        """
        Returns information of uploaded file2019-03-19
        :param request: rest framework request
        :return: rest framework response with the information of the authenticated user
        """
        if 'file' not in request.FILES:
            return Response({
                'error': True,
                'message': 'A file does not present',
            }, status=status.HTTP_400_BAD_REQUEST)
        ocred_file_serializer = OCRedFileSerializer(data={'file': request.FILES['file']})
        try:
            ocred_file_serializer.is_valid(raise_exception=True)
        except (Md5DuplicationError, Md5PdfDuplicationError) as e:
            ocred_file = OCRedFile.objects.get(Q(md5=e.md5) | Q(ocred_pdf_md5=e.md5))
            ocred_file_serializer = OCRedFileSerializer(ocred_file, many=False)
            return Response({
                'error': False,
                'created': False,
                'code': e.code,
                'data': ocred_file_serializer.data
            }, status.HTTP_200_OK)
        except FileTypeError as e:
            return Response({
                'error': True,
                'code': e.code,
                'message': e.message,
                'file_type': e.file_type,
            }, status=status.HTTP_400_BAD_REQUEST)
        ocred_file_serializer.save()
        data = ocred_file_serializer.data
        return Response({
            'error': False,
            'created': True,
            'data': data
        }, status=status.HTTP_201_CREATED)


class OCRedFileList(APIView):
    """
    Returns list of OCRedFile instances in JSON format 2019-03-20
    """
    def get(self, request, ):
        ocred_files = OCRedFile.objects.all()[:20]
        data = OCRedFileSerializer(ocred_files, many=True).data
        return Response(data, status=status.HTTP_200_OK)
