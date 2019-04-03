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
    Uploads the 'file' to OCR Server,
    If 'file' already was uploaded to OCR Server,
    the view returns the information of the uploaded file
    and status_code 200.
    Unless OCR Server processing 'file' and returns
    information about the new OCRedFile 2019-03-19.
    """

    parser_classes = (MultiPartParser,)

    def post(self, request,):
        """
        Uploads the 'file' to OCR Server, \
        If 'file' already was uploaded to OCR Server, \
        the view returns the information of the uploaded file \
        and status_code 200. \
        Unless OCR Server processing 'file' and returns \
        information about the new OCRedFile 2019-03-19.
        :param request: rest framework request
        :return: rest framework response
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
        """
        Returns a list of OCRedFile instances in JSON format 2019-03-24
        :param request: rest framework request
        :return: rest framework response
        """
        ocred_files = OCRedFile.objects.all()[:20]
        data = OCRedFileSerializer(ocred_files, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class Md5(APIView):
    """
    Returns information about an already uploaded file, \
    or message that a file with md5=md5 or ocred_pdf_md5=md5 not found 2019-03-24
    """
    def get(self, request, md5=md5):
        """
        Returns information about an already uploaded file, \
        or message that a file with md5=md5 or ocred_pdf_md5=md5 not found 2019-03-24
        :param request: rest framework request
        :return: rest framework response
        """
        try:
            ocred_file = OCRedFile.objects.get(Q(md5=md5) | Q(ocred_pdf_md5=md5))
        except OCRedFile.DoesNotExist:
            return Response({
                'error': False,
                'exists': False,
            }, status=status.HTTP_204_NO_CONTENT)
        data = OCRedFileSerializer(ocred_file).data
        return Response({
            'error': False,
            'exists': True,
            'data': data,
        }, status=status.HTTP_200_OK)


class RemoveMd5(APIView):
    """
    Removes an OCRedFile if it exists with md5=md5 or ocred_pdf_md5=md5, \
    or returns message that an OCRedFile with md5=md5 or ocred_pdf_md5 not found. 2019-03-24
    """
    def delete(self, request, md5=md5):
        """
        Removes an OCRedFile if it exists with md5=md5 or ocred_pdf_md5=md5, \
        or returns message that an OCRedFile with md5=md5 or ocred_pdf_md5 not found. 2019-03-24
        :param request: rest api framework request
        :param md5: The md5 of OCRedFile which will be deleted
        :return: rest framework response
        """
        try:
            ocred_file = OCRedFile.objects.get(Q(md5=md5) | Q(ocred_pdf_md5=md5))
        except OCRedFile.DoesNotExist:
            return Response({
                'error': False,
                'exists': False,
                'removed': False,
            }, status=status.HTTP_204_NO_CONTENT)
        ocred_file.delete()
        return Response({
            'error': False,
            'exists': True,
            'removed': True,
        }, status=status.HTTP_200_OK)


class RemoveAll(APIView):
    """
    Removes all OCRedFiles 2019-03-24
    """
    def delete(self, request):
        """
        Removes all OCRedFiles 2019-03-24
        :param request: rest framework request
        :return: rest framework response
        """
        ocred_files = OCRedFile.objects.all()
        num_ocred_files = ocred_files.count()
        for ocred_file in ocred_files:
            ocred_file.delete()
        return Response({
            'error': False,
            'removed': True,
            'count': num_ocred_files,
        }, status=status.HTTP_200_OK)


class RemoveFileMd5(APIView):
    """
    Removes the file from the instance of OCRedFile which has md5=md5 or ocred_pdf_md5=md5 2019-03-25
    """
    def delete(self, request, md5=md5):
        """
        Removes the file from the instance of OCRedFile which has md5=md5 or ocred_pdf_md5=md5 2019-03-25
        :param request: rest framework request
        :param md5: The md5 of OCRedFile whose file will be deleted
        :return: rest framework response
        """
        try:
            ocred_file = OCRedFile.objects.get(Q(md5=md5) | Q(ocred_pdf_md5=md5))
        except OCRedFile.DoesNotExist:
            return Response({
                'error': False,
                'exists': False,
                'removed': False,
            }, status=status.HTTP_204_NO_CONTENT)
        if not ocred_file.can_remove_file:
            return Response({
                'error': False,
                'exists': True,
                'can_remove_file': False,
                'removed': False,
            }, status=status.HTTP_204_NO_CONTENT)
        ocred_file.remove_file()
        return Response({
            'error': False,
            'exists': True,
            'removed': True,
        }, status=status.HTTP_200_OK)


class RemoveFileAll(APIView):
    """
    Removes files from all of instances of OCRedFile 2019-03-25
    """
    def delete(self, request, ):
        """
        Removes files from all of instances of OCRedFile 2019-03-25
        :param request: rest framework request
        :return: rest framework response
        """
        old_counter = OCRedFile.Counters.num_removed_files
        ocred_files = OCRedFile.objects.all()
        for ocred_file in ocred_files:
            ocred_file.remove_file()
        return Response({
            'error': False,
            'removed': True,
            'count': OCRedFile.Counters.num_removed_files-old_counter,
        }, status=status.HTTP_200_OK)


class RemovePdfMd5(APIView):
    """
    Removes the ocred_pdf from the instance of OCRedFile which has md5=md5 or ocred_pdf_md5=md5 2019-03-25
    """
    def delete(self, request, md5=md5):
        """
        Removes the ocred_pdf from the instance of OCRedFile which has md5=md5 or ocred_pdf_md5=md5 2019-03-25
        :param request: rest framework request
        :param md5: The md5 of OCRedFile whose ocred_pdf will be deleted
        :return: rest framework response
        """
        try:
            ocred_file = OCRedFile.objects.get(Q(md5=md5) | Q(ocred_pdf_md5=md5))
        except OCRedFile.DoesNotExist:
            return Response({
                'error': False,
                'exists': False,
                'removed': False,
            }, status=status.HTTP_204_NO_CONTENT)
        if not ocred_file.can_remove_pdf:
            return Response({
                'error': False,
                'exists': True,
                'can_remove_pdf': False,
                'removed': False,
            }, status=status.HTTP_204_NO_CONTENT)
        ocred_file.remove_pdf()
        return Response({
            'error': False,
            'exists': True,
            'removed': True,
        }, status=status.HTTP_200_OK)


class RemovePdfAll(APIView):
    """
    Removes ocred_pdfs from all of instances of OCRedFile 2019-03-25
    """
    def delete(self, request, ):
        """
        Removes ocred_pdfs from all of instances of OCRedFile 2019-03-25
        :param request: rest framework request
        :return: rest framework response
        """
        old_counter = OCRedFile.Counters.num_removed_pdf
        ocred_files = OCRedFile.objects.all()
        for ocred_file in ocred_files:
            ocred_file.remove_pdf()
        return Response({
            'error': False,
            'removed': True,
            'count': OCRedFile.Counters.num_removed_pdf - old_counter,
        }, status=status.HTTP_200_OK)


class CreatePdfMd5(APIView):
    """
    Creates ocred_pdf in the instance of OCRedFile whose md5=md5 or ocred_pdf_md5=md5 if it is possible 2019-03-25
    """
    def get(self, request, md5=md5):
        """
        Creates ocred_pdf in the instance of OCRedFile whose md5=md5 or ocred_pdf_md5=md5 if it is possible 2019-03-25
        :param request: rest framework request
        :param md5: the md5 of the instance of OCRedFile whose ocred_pdf will be created
        :return: rest framework response
        """
        try:
            ocred_file = OCRedFile.objects.get(Q(md5=md5) | Q(ocred_pdf_md5=md5))
        except OCRedFile.DoesNotExist:
            return Response({
                'error': False,
                'exists': False,
                'created': False,
            }, status=status.HTTP_204_NO_CONTENT)
        if not ocred_file.can_create_pdf:
            return Response({
                'error': False,
                'exists': True,
                'can_create_pdf': False,
                'created': False,
            }, status=status.HTTP_204_NO_CONTENT)
        ocred_file.create_pdf()
        return Response({
            'error': False,
            'exists': True,
            'created': True,
        }, status=status.HTTP_201_CREATED)


class CreatePdfAll(APIView):
    """
    Creates ocred_pdf in all instances of OCRedFile where it is possible 2019-03-25
    """
    def get(self, request, ):
        """
        Creates ocred_pdf in all instances of OCRedFile where it is possible 2019-03-25
        :param request: rest framework request
        :return: rest framework response
        """
        old_counter = OCRedFile.Counters.num_created_pdf
        ocred_files = OCRedFile.objects.all()
        for ocred_file in ocred_files:
            ocred_file.create_pdf()
        return Response({
            'error': False,
            'created': True,
            'count': OCRedFile.Counters.num_created_pdf - old_counter,
        }, status=status.HTTP_200_OK)
