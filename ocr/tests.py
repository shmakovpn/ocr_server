"""
This script makes tests for the django-ocr-server/ocr application
"""
__author__ = "shmakovpn <shmakovpn@yandex.ru>"
__date__ = "03/10/2019"
import os
from io import BytesIO
# utils
from .utils import *

from django.test import TestCase
from django.core.files.uploadedfile import InMemoryUploadedFile
# settings
from django.conf import settings
from ocr import settings as ocr_settings
# rest framework
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import APIClient
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
# models
from django.contrib.auth.models import User
from .models import *
# views
from .views import *
from .apiviews import *

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


class TestSaveModel(TestCase):
    """
    This class tests creating, updating and deleting instances of the OCRedFile model 2019-03-16
    """
    def test_model_png_save_delete(self):
        """
        This function create the instance of the OCRedFile model,
        upload the png file into it,
        save it,
        check that all fields of it contain correct values,
        remove it,
        check that all files (self.file and self.ocred_pdf was removed) 2019-03-17
        :return: None
        """
        print("TestSaveModel::test_model_png_save_delete()")
        filename = 'test_eng.png'
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = 'image/png'
        ocred_file.file.save(filename, BytesIO(content), False)
        ocred_file.save()
        print("TestSaveModel::test_model_png_save_delete() The model was saved")
        if ocr_settings.STORE_FILES:
            self.assertTrue(os.path.isfile(ocred_file.file.path))
        else:
            self.assertFalse(os.path.isfile(ocred_file.file.path))
            self.assertIn('store_files_disabled', ocred_file.file.name)
        self.assertEqual(ocred_file.id, 1)
        self.assertEqual(ocred_file.md5, '8aabb1f2d2d92893b5604da701f05505')
        self.assertIn('A some english text to test Tesseract', ocred_file.text)
        self.assertTrue(bool(ocred_file.uploaded))
        self.assertTrue(bool(ocred_file.ocred))
        if ocr_settings.STORE_PDF:
            self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
            pdf_content = ocred_file.ocred_pdf.file.read()
            ocred_file.ocred_pdf.file.seek(0)
            print('TestSaveModel::test_model_png_save_delete(). ocred_pdf_mf5=' + ocred_file.ocred_pdf_md5)
            self.assertEqual(ocred_file.ocred_pdf_md5, md5(pdf_content))
        else:
            self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path))
            self.assertIn('store_pdf_disabled', ocred_file.ocred_pdf.name)
        ocred_file.delete()
        print("TestSaveModel::test_model_png_save_delete(). The model was deleted")

    def test_model_pdf_notext_save_delete(self):
        """
        This function create the instance of the OCRedFile model,
        upload the pdf without text layer file into it,
        save it,
        check that all fields of it contain correct values,
        remove it,
        check that all files (self.file and self.ocred_pdf was removed) 2019-03-17
        :return: None
        """
        filename = 'test_eng_notext.pdf'
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = 'application/pdf'
        ocred_file.file.save(filename, BytesIO(content), False)
        ocred_file.save()
        print("TestSaveModel::test_model_pdf_notext_save_delete() The model was saved")
        if ocr_settings.STORE_FILES:
            self.assertTrue(os.path.isfile(ocred_file.file.path))
        else:
            self.assertFalse(os.path.isfile(ocred_file.file.path))
            self.assertIn('store_files_disabled', ocred_file.file.name)
        self.assertEqual(ocred_file.id, 1)
        self.assertEqual(ocred_file.md5, '4ee3751a767b02d072d33424a84457a9')
        self.assertIn('A some english text to test Tesseract', ocred_file.text)
        self.assertTrue(bool(ocred_file.uploaded))
        self.assertTrue(bool(ocred_file.ocred))
        # print('pdf_author='+ocred_file.pdf_author)
        self.assertEqual('2019-03-17 09:52:26+07', str(ocred_file.pdf_creation_date))
        # print('pdf_creator='+ocred_file.pdf_creator)
        self.assertEqual('2019-03-17 09:52:26+07', str(ocred_file.pdf_mod_date))
        self.assertEqual('GPL Ghostscript 9.26', ocred_file.pdf_producer)
        # print('pdf_title='+ocred_file.pdf_title)
        if ocr_settings.STORE_PDF:
            self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
            pdf_content = ocred_file.ocred_pdf.file.read()
            ocred_file.ocred_pdf.file.seek(0)
            print('TestSaveModel::test_model_pdf_notext_save_delete(). ocred_pdf_mf5=' + ocred_file.ocred_pdf_md5)
            self.assertEqual(ocred_file.ocred_pdf_md5, md5(pdf_content))
        else:
            self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path))
            self.assertIn('store_pdf_disabled', ocred_file.ocred_pdf.name)
        ocred_file.delete()
        print("TestSaveModel::test_model_pdf_notext_save_delete(). The model was deleted")

    def test_model_pdf_withtext_save_delete(self):
        """
        This function create the instance of the OCRedFile model,
        upload the pdf with text layer file into it,
        save it,
        check that all fields of it contain correct values,
        remove it,
        check that the file self.file was removed) 2019-03-17
        :return: None
        """
        filename = 'the_pdf_withtext.pdf'
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = 'application/pdf'
        ocred_file.file.save(filename, BytesIO(content), False)
        ocred_file.save()
        print("TestSaveModel::test_model_pdf_withtext_save_delete() The model was saved")
        if ocr_settings.STORE_FILES:
            self.assertTrue(os.path.isfile(ocred_file.file.path))
        else:
            self.assertFalse(os.path.isfile(ocred_file.file.path))
            self.assertIn('store_files_disabled', ocred_file.file.name)
        self.assertEqual(ocred_file.id, 1)
        self.assertEqual(ocred_file.md5, '55afdb2874e53370a1565776a6bd4ad7')
        self.assertIn('The test if pdf with text', ocred_file.text)
        self.assertTrue(bool(ocred_file.uploaded))
        self.assertFalse(bool(ocred_file.ocred))
        # print('pdf_author='+ocred_file.pdf_author)
        self.assertEqual('2019-03-17 03:45:57+00', str(ocred_file.pdf_creation_date))
        # print('pdf_creator='+ocred_file.pdf_creator)
        # print('pdf_mod_date='+str(ocred_file.pdf_mod_date))
        self.assertEqual('Tesseract 4.0.0-beta.1', ocred_file.pdf_producer)
        # print('pdf_title='+ocred_file.pdf_title)
        self.assertFalse(bool(ocred_file.ocred_pdf))
        self.assertFalse(bool(ocred_file.ocred_pdf_md5))
        ocred_file.delete()
        print("TestSaveModel::test_model_pdf_withtext_save_delete(). The model was deleted")

    def test_remove_file(self):
        """
        This function tests that OCRredFile.remove_file() works as expected 2019-03-18
        :return: None
        """
        if not ocr_settings.STORE_FILES:
            return
        filename = 'test_eng.png'
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = 'image/png'
        ocred_file.file.save(filename, BytesIO(content), False)
        ocred_file.save()
        print("TestSaveModel::test_remove_file() The model was saved")
        self.assertTrue(os.path.isfile(ocred_file.file.path))
        ocred_file.remove_file()
        self.assertFalse(os.path.isfile(ocred_file.file.path))
        self.assertEqual('file_removed', ocred_file.file.name)
        ocred_file.delete()
        print("TestSaveModel::test_remove_file(). The model was deleted")

    def test_remove_pdf(self):
        """
        This function tests that OCRedFile.remove_pdf() works as expected 2019-03-18
        :return: None
        """
        if not ocr_settings.STORE_PDF:
            return
        filename = 'test_eng.png'
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = 'image/png'
        ocred_file.file.save(filename, BytesIO(content), False)
        ocred_file.save()
        print("TestSaveModel::test_remove_pdf() The model was saved")
        self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
        ocred_file.remove_pdf()
        self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path))
        self.assertEqual('pdf_removed', ocred_file.ocred_pdf.name)
        ocred_file.delete()
        print("TestSaveModel::test_remove_pdf(). The model was deleted")

    def test_create_pdf(self):
        """
        This function tests that OCRedFile.create_pdf(admin_obj=None, request=None) works as expected
        :return: None
        """
        if not ocr_settings.STORE_FILES:
            return
        if not ocr_settings.STORE_PDF:
            return
        filename = 'test_eng.png'
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = 'image/png'
        ocred_file.file.save(filename, BytesIO(content), False)
        ocred_file.save()
        print("TestSaveModel::test_create_pdf() The model was saved")
        self.assertTrue(os.path.isfile(ocred_file.file.path))
        self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
        ocred_file.remove_pdf()
        self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path))
        self.assertEqual('pdf_removed', ocred_file.ocred_pdf.name)
        ocred_file.create_pdf()
        self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
        print(ocred_file.ocred_pdf.name)
        ocred_file.delete()
        print("TestSaveModel::test_create_pdf(). The model was deleted")

    def test_md5_duplication(self):
        """
        This function tries to create two model with the same file,
        then catches an error
        :return: None
        """
        filename = 'test_eng.png'
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = 'image/png'
        ocred_file.file.save(filename, BytesIO(content), False)
        ocred_file.save()
        ocred_file2 = OCRedFile()
        ocred_file2.file_type = 'image/png'
        ocred_file2.file.save(filename, BytesIO(content), False)
        try:
            ocred_file2.save()
            self.assertTrue(False, 'OCRedFile md5 deduplication does not work')
        except ValidationError as e:
            pass
        if os.path.isfile(ocred_file2.file.path):
            os.remove(ocred_file2.file.path)


class TestUsers(TestCase):
    """
    This class test creating users 2019-03-19
    """
    def test_create_superuser(self):
        """
        This class tests a superuser creation 2019-03-19
        :return: None
        """
        user = User(
            username='test_root',
            email='test_root@test.com',
        )
        user.set_password('test_passwd')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.assertEqual(1, user.id)


class TestAPI(APITestCase):
    """
    This class tests that the API works as expected 2019-03-19
    """
    @staticmethod
    def open_file(filename, file_type):
        """
        This function opens file and returns InMemoryUploadedFile 2019-03-21
        :param filename:
        :param file_type:
        :return: InMemoryUploadedFile
        """
        content = read_binary_file(TESTS_DIR + filename)
        return InMemoryUploadedFile(BytesIO(content), 'file', filename, file_type, content.__sizeof__(), None)

    @staticmethod
    def file_to_serializer(filename, file_type):
        """
        This funtion creates OCRedFileSerializer for the file with the file_type 2019-03-21
        :param filename:
        :param file_type:
        :return: OCRedFileSerializer for the file with the file_type
        """
        in_memory_file = TestAPI.open_file(filename=filename, file_type=file_type)
        data = {
            'file': in_memory_file
        }
        return OCRedFileSerializer(data=data)

    @staticmethod
    def get_test_user():
        """
        Creates the test user and the token
        :return: User
        """
        user = User(
            username='test',
            email='test@test.com',
        )
        user.set_password('test')
        user.save()
        Token.objects.create(user=user)
        return user

    @staticmethod
    def get_upload_request(filename, token):
        """
        Create the Request for uploading the file 2019-03-21
        :param filename: the name of the uploading file
        :param token: token for authentication
        :return: Request
        """
        f = File(open(TESTS_DIR + filename, 'rb'))
        uploaded_file = SimpleUploadedFile(filename, f.read(), content_type='application/x-www-form-urlencoded')
        data = {
            'file': uploaded_file,
        }
        return APIRequestFactory().post('/upload/',
                                        HTTP_AUTHORIZATION='Token {}'.format(token),
                                        content_type='application/x-www-form-urlencoded',
                                        data=data)

    def test_ocred_file_serializer_is_valid(self):
        """
        This function tests that the OCRedFileSerializer.is_valid() function works as expected 2019-03-19
        :return: None
        """
        ocred_file_serializer = TestAPI.file_to_serializer('test_eng.png', 'image/png')
        self.assertTrue(ocred_file_serializer.is_valid())
        ocred_file_serializer.save()
        self.assertEqual('A some english text to test Tesseract', ocred_file_serializer.data['text'])
        # test md5 deduplication
        ocred_file_serializer2 = TestAPI.file_to_serializer('test_eng.png', 'image/png')
        self.assertFalse(ocred_file_serializer2.is_valid())
        ocred_file = OCRedFile.objects.get(pk=ocred_file_serializer.data['id'])
        ocred_file.delete()

    def test_list_view(self):
        """
        Create several OCRedFiles,
        then get the Response from OCRedFileList
        check the Response as expected 2019-03-21
        :return: None
        """
        ocred_file_serializer = TestAPI.file_to_serializer('test_eng.png', 'image/png')
        self.assertTrue(ocred_file_serializer.is_valid())
        ocred_file_serializer.save()
        ocred_file_serializer = TestAPI.file_to_serializer('test_rus.png', 'image/png')
        self.assertTrue(ocred_file_serializer.is_valid())
        ocred_file_serializer.save()
        ocred_file_serializer = TestAPI.file_to_serializer('the_pdf_withtext.pdf', 'application/pdf')
        self.assertTrue(ocred_file_serializer.is_valid())
        ocred_file_serializer.save()
        ocred_file_serializer = TestAPI.file_to_serializer('test_eng.pdf', 'application/pdf')
        self.assertTrue(ocred_file_serializer.is_valid())
        ocred_file_serializer.save()
        ocred_file_serializer = TestAPI.file_to_serializer('test_eng_notext.pdf', 'application/pdf')
        self.assertTrue(ocred_file_serializer.is_valid())
        ocred_file_serializer.save()
        ocred_file_serializer = TestAPI.file_to_serializer('deming.pdf', 'application/pdf')
        self.assertTrue(ocred_file_serializer.is_valid())
        ocred_file_serializer.save()
        token = TestAPI.get_test_user().auth_token.key
        request = APIRequestFactory().get('/list/',
                                          HTTP_AUTHORIZATION='Token {}'.format(token),)
        response = OCRedFileList.as_view()(request)
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {0} instead.'.format(response.status_code))
        response.json = response.data


    def test_upload_file_view(self):
        """
        This function tests uploading files via API 2019-03-21
        :return: None
        """
        # token = TestAPI.get_test_user().auth_token.key
        filename = 'test_eng.png'
        file = File(open(TESTS_DIR+filename, 'rb'))
        uploaded_file = SimpleUploadedFile(filename, file.read(),
                                           content_type='application/x-www-form-urlencoded',)
        client = APIClient()
        user = TestAPI.get_test_user()
        client.force_authenticate(user=user)
        url = '/upload/'
        response = client.post(url, {'file': uploaded_file}, format='multipart')

        """request = TestAPI.get_upload_request(filename='test_eng.png', token=token)
        response = UploadFile.as_view()(request)
        self.assertEqual(201, response.status_code,
                         'Expected Response Code 201 received {0} instead.'.format(response.status_code))"""


