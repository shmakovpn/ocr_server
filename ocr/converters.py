"""
converters.py
This file contains urls.converters for OCR Server 2019-03-24
"""
__author__ = "shmakovpn <shmakovpn@yandex.ru>"
__date__ = '2019-03-24'


from django.urls.converters import StringConverter


class Md5Converter(StringConverter):
    """
    The md5 converter for path function 2019-03-24
    """
    regex = '[a-fA-F\d]{32}'


