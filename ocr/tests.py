"""
This script makes tests for the django-ocr-server/ocr application
"""
__author__ = "shmakovpn <shmakovpn@yandex.ru>"
__date__ = "03/10/2019"
from django.test import TestCase
from django.conf import settings
import os
from .utils import md5, ocr_img2str, read_binary_file, ocr_img2pdf, pdf2text, pdf_info, pdf_need_ocr, ocr_pdf


PWD = "%s/%s/" % (settings.BASE_DIR, __package__)  # directory of the django-ocr-server/ocr application
TESTS_DIR = "%s/%s/" % (PWD, 'tests')  # directory of the tests of the django-ocr-server/ocr application

print("Directory of the django-ocr-server/ocr application is %s" % PWD)
print("Directory of the tests of the django-ocr-server/ocr application is %s" % TESTS_DIR)


# Create your tests here.
class TestMd5(TestCase):
    """
    This class tests that md5 calculation works   03/10/2019
    """
    def test_md5(self):
        """
        This function tests that md5 calculation works
        :return: None
        """
        content = read_binary_file(TESTS_DIR+'test_eng.png')
        self.assertEqual(md5(content), '8aabb1f2d2d92893b5604da701f05505')


class TestPdf2text(TestCase):
    """
    This class tests that extraction text from pdf works as expected   03/10/2019
    """
    def test_pdf2text(self):
        """
        This function tests that extraction text from pdf works as expected   03/10/2019
        :return: None
        """
        content = read_binary_file(TESTS_DIR+'test_eng.pdf')
        self.assertIn('A some english text to test Tesseract', pdf2text(content))

    def test_pdf_need_ocr(self):
        """
        This function tests that the pdf_need_ocr analyzer as works as expected
        :return: None
        """
        self.assertTrue(pdf_need_ocr(''))
        self.assertFalse(pdf_need_ocr('The string with русский text'))
        self.assertFalse(pdf_need_ocr('The string with "the"'))
        self.assertTrue(pdf_need_ocr('3TO ownOKa'))


class TestPdfInfo(TestCase):
    """
    This class tests that pdfInfo extraction from pdf works as expected   03/11/2019
    """
    def test_pdf_info(self):
        """
        This function tests that pdfInfo extraction from pdf works as expected   03/11/2019
        :return: None
        """
        content = read_binary_file(TESTS_DIR+'deming.pdf')
        info = pdf_info(content)
        self.assertIn('Ascensio System SIA Copyright (c) 2018', info['Producer'])


class TestTesseract(TestCase):
    """
    This class tests that tesseract-ocr works   10 05:09:50 MSK 2019
    """
    def test_img2str_eng(self):
        """
        This function tests that tesseract-ocr of image with english content works as expected   03/10/2019
        :return: None
        """
        content = read_binary_file(TESTS_DIR+'test_eng.png')
        self.assertIn('A some english text to test Tesseract', ocr_img2str(content))

    def test_img2str_rus(self):
        """
        This function tests that tesseract-ocr of image with russian content works as expected   03/10/2019
        :return: None
        """
        content = read_binary_file(TESTS_DIR + 'test_rus.png')
        self.assertIn('Проверяем tesseract', ocr_img2str(content))

    def test_img2pdf_eng(self):
        """
        This function tests that tesseract-ocr of image with english content generates pdf as expected   03/10/2019
        :return: None
        """
        content = read_binary_file(TESTS_DIR + 'test_eng.png')
        pdf_bytes = ocr_img2pdf(content)
        self.assertIn('A some english text to test Tesseract', pdf2text(pdf_bytes))


class TestOcrMyPdf(TestCase):
    """
    This class tests that ocrmypdf works as expected 2019-03-11
    """
    def test_pdf2pdf(self):
        """
        This function tests that ocrmypdf works as expected 2019-03-11
        :return: None
        """
        content = read_binary_file(TESTS_DIR + 'test_eng.pdf')
        md5_content = md5(content)
        filename = TESTS_DIR + '/pdf/' + md5_content + '.pdf'
        pdf_text = ocr_pdf(content, filename)
        new_content = read_binary_file(filename)
        if os.path.isfile(filename):
            os.remove(filename)
        new_pdf_text = pdf2text(new_content)
        self.assertIn('A some english text to test Tesseract', pdf_text)
        self.assertIn('A some english text to test Tesseract', new_pdf_text)
