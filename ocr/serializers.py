"""
This file contains serializer for Django REST Framework
"""
__author__ = 'shmakovpn <shmakovpn@yandex.ru>'
__date__ = '2019-03-18'

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import *
from .utils import md5


class OCRedFileSerializer(serializers.ModelSerializer):
    """
    The OCRedFile model serializer 2019-03-18
    """
    def __init__(self, *args, **kwargs):
        """
        OCRedFileSerializer constructor
        :param args:
        :param kwargs:
        """
        super(OCRedFileSerializer, self).__init__(*args, **kwargs)

    def is_valid(self, raise_exception=False):
        """
        The OCRedFile model serializer validator 2019-03-20
        :param raise_exception:
        :return: boolean True if the data is valid
        """
        try:
            file_type = self.initial_data['file'].content_type
        except ValueError as e:
            if raise_exception:
                raise ValidationError(_('OCRedFileSerializer. The "content_type" of the "file" does not exist'))
            else:
                return False
        content = self.initial_data['file'].read()
        self.initial_data['file'].seek(0)
        if not OCRedFile.is_valid_file_type(file_type=file_type, raise_exception=raise_exception):
            return False
        md5_value = md5(content)
        print('OCRedFileSerializer.is_valid md5='+md5_value)
        if not OCRedFile.is_valid_ocr_md5(md5_value=md5_value, raise_exception=raise_exception):
            return False
        return super(OCRedFileSerializer, self).is_valid(raise_exception)

    class Meta:
        model = OCRedFile
        fields = '__all__'
        extra_kwargs = {
            'md5': {'read_only': True},
            'file_type': {'read_only': True},
            'text': {'read_only': True},
            'uploaded': {'read_only': True},
            'ocred': {'read_only': True},
            'ocred_pdf': {'read_only': True},
            'ocred_pdf_md5': {'read_only': True},
            'pdf_num_pages': {'read_only': True},
            'pdf_author': {'read_only': True},
            'pdf_creation_date': {'read_only': True},
            'pdf_creator': {'read_only': True},
            'pdf_mod_date': {'read_only': True},
            'pdf_producer': {'read_only': True},
            'pdf_title': {'read_only': True},
        }
