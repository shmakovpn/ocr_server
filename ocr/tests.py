"""
This script makes tests for the django-ocr-server/ocr application
"""
__author__ = "shmakovpn <shmakovpn@yandex.ru>"
__date__ = "03/10/2019"
# utils
from django.urls import reverse
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from bs4 import BeautifulSoup

# djnago tests
from django.test import TestCase, SimpleTestCase, override_settings
from django.test import Client  # Client to perform test requests

# settings
from django.conf import settings
from ocr import settings as ocr_default_settings

# rest framework
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import APIClient   # Client to perform test requests to API views

# models
from django.contrib.auth.models import User

# views
from .apiviews import *

PWD = "%s/%s" % (settings.BASE_DIR, __package__)  # directory of the django-ocr-server/ocr application
TESTS_DIR = "%s/%s/" % (PWD, 'tests')  # directory of the tests of the django-ocr-server/ocr application


class OcrClientBase:
    """
    The parent for OcrClient and OcrApiClient 2019-03-28
    """
    user = None
    token = None
    user_counter = 0  # static

    def _init_user(self):
        self.user = User.objects.create_user(username='test-{}-{}'.format(self.__class__.__name__, OcrClientBase.user_counter))
        OcrClientBase.user_counter += 1
        self.token = Token.objects.create(user=self.user)


class OcrClient(Client, OcrClientBase):
    """
    The client to performing tests for views (not API vies).
    Do not use directly, because ocr application does not
    contain views (expect admin, and api views) 2019-03-28
    """
    def __init__(self):
        """
        Calls parent __init__, then force login self.user 2019-03-28
        """
        super(OcrClient, self).__init__()
        self._init_user()
        self.force_login(user=self.user)


class OcrAdminClient(OcrClient):
    """
    The client to performing tests for admin views. 2019-03-28
    """
    def __init__(self):
        """
        Making self.user the staff, and add according permissions to him 2019-03-28
        """
        super(OcrAdminClient, self).__init__()
        # making the self.user the stuff
        self.user.is_staff = True
        self.user.save()
        # set according permissions to the self.user
        content_type = ContentType.objects.get_for_model(OCRedFile)
        permissions = Permission.objects.filter(content_type=content_type)
        self.user.user_permissions.set(permissions)


class OcrApiClient(APIClient, OcrClientBase):
    """
    The client to performing test for API views 2019-03-28
    """
    def __init__(self):
        """
        Calls parent __init__, then force login self.user 2019-03-28
        """
        super(OcrApiClient, self).__init__()
        self._init_user()
        self.force_login(user=self.user)


class OcrTestCaseBase(TestCase):
    """
    The parent for OcrTestCase, OcrAdminTestCase, OcrApiTestCase 2019-03-29
    """
    def _clean(self):
        """
        Cleans folders ocr/upload/ and ocr/pdf from trash remaining after tests 2019-03-29
        :return: None
        """
        ocred_files = OCRedFile.objects.all()
        for ocred_file in ocred_files:
            ocred_file.delete()

    def tearDown(self):
        """
        This function starts after each test. Collects trash 2019-03-29
        :return: None
        """
        self._clean()  # Cleans folders ocr/upload/ and ocr/pdf from trash remaining after tests

    @staticmethod
    def createOCRedFile(filename, file_type):
        """
        Creates OCRedFile for the file named with filename and having the passed file_type 2019-03-29
        :param filename: the name of the file
        :param file_type: the type of the file
        :return: created instance of OCRedFile
        """
        content = read_binary_file(TESTS_DIR + filename)
        ocred_file = OCRedFile()
        ocred_file.file_type = file_type
        ocred_file.file.save(name=filename, content=BytesIO(content), save=False)
        ocred_file.save()
        return ocred_file

    def assertOCRedFile(self, ocred_file, md5=None, text=None, ):
        """
        Assert that the ocred_file is not None,
        the ocred_file.id is not None,
        the ocred_file.md5, if the md5 is not None, is equal md5,
        the ocred_file.text, if the text is not None, is equal text
        the bool(ocred_file.ocred) is equal the ocred
        the ocred_file.file.path is a file path if STORE_FILES is enabled
        the ocred_file.ocred_pdf.path is a file if STORE_PDF is enabled
        the ocred_file.file.path is not a file path if STORE_FILES is disabled
        the ocred_file.ocred_pdf.path is not a file if STORE_PDF is disabled
        the ocred_file.file.name is equal 'store_files_disabled' if STORE_FILES is disabled
        the ocred_file.ocred_pdf.name is equal 'store_pdf_disabled' if STORE_PDF is disabled
        :param ocred_file: the instance of OCRedFile to check
        :param md5: the md5 to compare with ocred_file.md5
        :param text: the text to compare with ocred_file.text
        :param ocred: the ocred boolean to compare with the ocred_file.ocred
        :return: None
        """
        self.assertTrue(bool(ocred_file), 'The ocred_file is None')
        self.assertTrue(bool(ocred_file.id), 'The ocred_file does not have id')
        if md5:
            self.assertEqual(md5, ocred_file.md5, "The ocred_file.md5 '{}' does not equal md5 '{}'."
                             .format(ocred_file.md5, md5))
        if text:
            self.assertIn(text, ocred_file.text, "The ocred_file.text '{}' does not contain text '{}'."
                          .format(ocred_file.text, text))
        self.assertTrue(bool(ocred_file.uploaded), 'The ocred_file.uploaded is None')
        if not ocred_file.is_pdf or not ocred_file.has_pdf_text:  # the ocred_file is an image or pdf without text
            self.assertTrue(bool(ocred_file.ocred))
        else:  # the ocred_file is a pdf document with text, it was not ocred
            self.assertFalse(bool(ocred_file.ocred))
        if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            self.assertTrue(os.path.isfile(ocred_file.file.path),
                            'The ocred_file.file.path is not a file path when STORE_FILES is True')
            self.assertTrue(ocred_file.can_remove_file,
                            'The ocred_file.can_remove_file is False when STORE_FILES is True')
        else:
            self.assertFalse(os.path.isfile(ocred_file.file.path),
                             'The ocred_file.file.path is a file path when STORE_FILES is False')
            self.assertIn('store_files_disabled', ocred_file.file.name,
                          "The ocred_file.file.name '{}' is not 'store_files_disabled' when STORE_FILES is False"
                          .format(ocred_file.file.name))
            self.assertFalse(ocred_file.can_remove_file)
        if getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
            if not ocred_file.is_pdf or not ocred_file.has_pdf_text:
                self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path),
                                "The ocred_file.ocred_pdf.path is not a file path when STORE_PDF is True")
                self.assertTrue(ocred_file.can_remove_pdf,
                                'The ocred_file.can_remove_pdf is False')
            else:
                self.assertFalse(bool(ocred_file.ocred),
                                 'The ocred_file.file is PDF and it contains a text but it was OCRed')
                self.assertFalse(bool(ocred_file.ocred_pdf),
                                 'The ocred_file.file is PDF and it contains a text but it was OCRed')
                self.assertFalse(bool(ocred_file.ocred_pdf_md5),
                                 'The ocred_file.file is PDF and it contains a text but it was OCRed')
                self.assertFalse(ocred_file.can_remove_pdf)
                self.assertFalse(ocred_file.can_create_pdf)
        else:
            self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path),
                             "The ocred_file.ocred_pdf.path is a file path when STORE_PDF is False")
            self.assertIn('store_pdf_disabled', ocred_file.ocred_pdf.name,
                          "The ocred_file.ocred_pdf.name '{}' is not 'store_pdf_disabled' when STORE_PDF is False")
            self.assertFalse(ocred_file.can_remove_pdf)
            if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
                self.assertTrue(ocred_file.can_create_pdf,
                                'The ocred_files.can_create_pdf returns False \
                                 when STORE_PDF is False and STORE_FILES is True')
            else:
                self.assertFalse(ocred_file.can_create_pdf)


class OcrTestCase(OcrTestCaseBase):
    """
    This class is intended to tests that affect database and are not related to the API and Admin 2019-03-29
    because OCR does not have view except API and admin, this class is stay empty
    """
    pass


class OcrApiTestCaseBase(OcrTestCaseBase):
    """
    This base class is intended to tests that affect database and are related to the API 2019-03-29,
    It is the parent of OcrApiSerializerTestCase, OcrApiViewTestCase
    """
    client_class = OcrApiClient


class OcrApiSerializerTestCase(OcrApiTestCaseBase):
    """
    This class is intended to tests OCRedFileSerializer 2019-03-29
    """
    @staticmethod
    def create_in_memory_uploaded_file(filename, file_type):
        """
        This function opens file and returns InMemoryUploadedFile 2019-03-29
        :param filename: the name of the file to opening
        :param file_type: the type of the opening file
        :return: InMemoryUploadedFile
        """
        content = read_binary_file(TESTS_DIR + filename)
        return InMemoryUploadedFile(BytesIO(content), 'file', filename, file_type, content.__sizeof__(), None)

    def create_serializer(self, filename, file_type, text=None):
        """
        This function creates OCRedFileSerializer for the file with the file_type 2019-03-29
        :param filename: the name of the file used for the creating serializer
        :param file_type: the type of the file used for the creating serializer
        :param text: the text to compare with created serialized['data'].text if it is not None
        :return: OCRedFileSerializer for the file with the file_type
        """
        in_memory_file = OcrApiSerializerTestCase.create_in_memory_uploaded_file(filename=filename, file_type=file_type)
        data = {
            'file': in_memory_file
        }
        ocred_file_serializer = OCRedFileSerializer(data=data)
        self.assertTrue(ocred_file_serializer.is_valid(raise_exception=True), 'The ocred_file_serialized does not valid')
        ocred_file_serializer.save()
        if text:
            self.assertIn(text, ocred_file_serializer.data['text'],
                          "The text '{}' is not equal the ocred_file_serializer['data'].text '{}'"
                          .format(text, ocred_file_serializer.data['text']))
        return ocred_file_serializer


class OcrApiViewTestCase(OcrApiTestCaseBase):
    """
    This class intended to test that views of API of OCR Server works as expected
    """
    def upload_file(self, filename, ):
        """
        This function uploads the file to OCR Server using OcrApiClient
        and returns Response 2019-03-24/2019-03-29
        :param filename: the name of uploaded file
        :return: rest framework response
        """
        with open(TESTS_DIR + filename, 'rb') as fp:
            return self.client.post(reverse(__package__+':upload'),
                                    {'file': fp},
                                    format='multipart', )

    def assertUploadFileResponse(self, response, md5=None, text=None):
        """
        This function tests response of page of uploading file of OCR Server that it works as expected 2019-03-29
        :param response: rest api framework response of upload file view of OCR Server API
        :param md5: the md5 to compare with the response.data['data']['md5'] if it exists
        :param text: the text to compare with the response.data['data']['text'] if it exists
        :return: None
        """
        self.assertEqual(201, response.status_code,
                         'Expected Response Code 201 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'], 'An error has occured in upload API view')
        self.assertTrue(response.data['created'], 'Created must be True')
        if md5:
            self.assertEqual(md5, response.data['data']['md5'])
        if text:
            self.assertIn(text, response.data['data']['text'])

    def assertUploadFileDuplicationResponse(self, response, md5=None, text=None):
        """
        This function tests response of page of uploading file of OCR Server
        when uploaded file already exist in OCR Server 2019-03-30
        :param response: the response of the page of uploading file of OCR Server
        :param md5: the md5 to compare with the response.data['data']['md5'] if it exists
        :param text: the text to compare with the response.data['data']['text'] if it exists
        :return: None
        """
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'], 'An error has occured in upload API view')
        self.assertFalse(response.data['created'], 'Created must be False')
        if md5:
            self.assertEqual(md5, response.data['data']['md5'])
        if text:
            self.assertIn(text, response.data['data']['text'])

    def assertUploadFileWrongTypeResponse(self, response):
        """
        This function tests response of page of uploading file of OCR Server
        when type of uploaded file is neither image nor pdf
        :param response: the response of the page of uploading file of OCR Server
        :return: None
        """
        self.assertEqual(400, response.status_code,
                         'Expected Response Code 400 received {} instead.'.format(response.status_code))
        self.assertTrue(response.data['error'], "The 'error' of the response must be True")
        self.assertEqual('wrong_file_type', response.data['code'],
                         "The 'code' of response '{}' must be 'wrong_file_type'"
                         .format(response.data['code']))


class OcrAdminTestCase(OcrTestCaseBase):
    """
    This class is responsible to test admin 2019-03-31
    """
    client_class = OcrAdminClient

    def setUp(self):
        """
        Prepares each test of admin 2019-03-31
        :return: None
        """
        super(OcrAdminTestCase, self).setUp()

# Create your tests here.
class TestMd5(SimpleTestCase):
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


class TestPdf2text(SimpleTestCase):
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


class TestPdfInfo(SimpleTestCase):
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


class TestTesseract(SimpleTestCase):
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
        if 'rus' not in getattr(settings, 'OCR_TESSERACT_LANG', ocr_default_settings.TESSERACT_LANG):
            return
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


class TestOcrMyPdf(SimpleTestCase):
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


class TestSaveModel(OcrTestCase):
    """
    This class create instances of OCRedFile using files with different types of content.
    Then examines that each of these are saves as expected.
     2019-03-16/2019-03-29
    """
    @override_settings(OCR_STORE_FILES=True, OCR_STORE_PDF=True)
    def test_save_model_file_pdf(self):
        """
        This function creates instances of OCRedFile using files with different types of content
        when OCR_STORE_FILES=True, OCR_STORE_PDF=True. 2019-04-05
        Then examines that each of these are saves as expected.
        :return: None
        """
        # testing png
        ocred_file = OcrTestCase.createOCRedFile(filename='test_eng.png', file_type='image/png')
        self.assertOCRedFile(ocred_file,
                             md5='8aabb1f2d2d92893b5604da701f05505',
                             text='A some english text to test Tesseract')
        self.assertTrue(ocred_file.can_remove_file)
        self.assertTrue(ocred_file.can_remove_pdf)
        self.assertTrue(os.path.isfile(ocred_file.file.path))
        self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
        self.assertFalse(ocred_file.can_create_pdf)
        # testing remove ocred_pdf
        ocred_file.remove_pdf()
        self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path))
        self.assertEqual('pdf_removed', ocred_file.ocred_pdf.name)
        self.assertTrue(ocred_file.can_create_pdf)
        self.assertFalse(ocred_file.can_remove_pdf)
        # testing creating ocred_pdf
        ocred_file.create_pdf()
        self.assertTrue(ocred_file.can_remove_pdf)
        self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
        self.assertFalse(ocred_file.can_create_pdf)
        # testing remove file
        ocred_file.remove_file()
        self.assertFalse(os.path.isfile(ocred_file.file.path))
        self.assertFalse(ocred_file.can_remove_file)
        self.assertFalse(ocred_file.can_create_pdf)
        self.assertEqual('file_removed', ocred_file.file.name)
        # testing after remove file and ocred_pdf
        ocred_file.remove_pdf()
        self.assertFalse(ocred_file.can_create_pdf)
        # testing pdf without text
        ocred_file = OcrTestCase.createOCRedFile(filename='the_pdf_withtext.pdf', file_type='application/pdf')
        self.assertOCRedFile(ocred_file,
                             md5='55afdb2874e53370a1565776a6bd4ad7',
                             text='The test if pdf with text')
        self.assertEqual('2019-03-17 03:45:57+00', str(ocred_file.pdf_creation_date))
        self.assertEqual('Tesseract 4.0.0-beta.1', ocred_file.pdf_producer)
        self.assertFalse(ocred_file.can_create_pdf)
        self.assertFalse(ocred_file.can_remove_pdf)
        # testing pdf without text
        ocred_file = OcrTestCase.createOCRedFile(filename='test_eng_notext.pdf', file_type='application/pdf')
        self.assertOCRedFile(ocred_file,
                             md5='4ee3751a767b02d072d33424a84457a9',
                             text='A some english text to test Tesseract')
        self.assertEqual('2019-03-17 09:52:26+07', str(ocred_file.pdf_creation_date))
        self.assertEqual('2019-03-17 09:52:26+07', str(ocred_file.pdf_mod_date))
        self.assertEqual('GPL Ghostscript 9.26', ocred_file.pdf_producer)
        # testing md5_duplication
        try:
            ocred_file2 = OcrTestCase.createOCRedFile(filename='the_pdf_withtext.pdf', file_type='application/pdf')
            self.assertTrue(False, 'OCRedFile md5 deduplication does not work')
        except Md5DuplicationError as e:
            pass

    @override_settings(OCR_STORE_FILES=True, OCR_STORE_PDF=False)
    def test_save_model_file_nopdf(self):
        # testing png
        ocred_file = OcrTestCase.createOCRedFile(filename='test_eng.png', file_type='image/png')
        self.assertOCRedFile(ocred_file,
                             md5='8aabb1f2d2d92893b5604da701f05505',
                             text='A some english text to test Tesseract')
        self.assertIn('store_pdf_disabled', ocred_file.ocred_pdf.name)
        self.assertTrue(ocred_file.can_remove_file)
        self.assertFalse(ocred_file.can_remove_pdf)
        self.assertTrue(os.path.isfile(ocred_file.file.path))
        self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path))
        self.assertTrue(ocred_file.can_create_pdf)
        # testing creating pdf
        ocred_file.create_pdf()
        self.assertTrue(ocred_file.can_remove_pdf)
        self.assertFalse(ocred_file.can_create_pdf)
        self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))

    def test_save_model(self):
        """
        This function creates instances of OCRedFile using files with different types of content.
        Then examines that each of these are saves as expected. 2019-03-29
        :return: None
        """
        # testing png
        ocred_file = OcrTestCase.createOCRedFile(filename='test_eng.png', file_type='image/png')
        self.assertOCRedFile(ocred_file,
                             md5='8aabb1f2d2d92893b5604da701f05505',
                             text='A some english text to test Tesseract')
        # testing removing file
        if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            ocred_file.remove_file()
            self.assertFalse(os.path.isfile(ocred_file.file.path))
            self.assertEqual('file_removed', ocred_file.file.name)
        # testing pdf that has not a text
        ocred_file = OcrTestCase.createOCRedFile(filename='test_eng_notext.pdf', file_type='application/pdf')
        self.assertOCRedFile(ocred_file,
                             md5='4ee3751a767b02d072d33424a84457a9',
                             text='A some english text to test Tesseract')
        self.assertEqual('2019-03-17 09:52:26+07', str(ocred_file.pdf_creation_date))
        self.assertEqual('2019-03-17 09:52:26+07', str(ocred_file.pdf_mod_date))
        self.assertEqual('GPL Ghostscript 9.26', ocred_file.pdf_producer)
        # testing removing ocred_pdf
        if getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
            ocred_file.remove_pdf()
            self.assertFalse(os.path.isfile(ocred_file.ocred_pdf.path))
            self.assertEqual('pdf_removed', ocred_file.ocred_pdf.name)
        # testing creating pdf
        if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            self.assertTrue(ocred_file.can_create_pdf, 'ocred_file.can_create_pdf is False when it must be True')
            ocred_file.create_pdf()
            self.assertTrue(os.path.isfile(ocred_file.ocred_pdf.path))
        # testing pdf that contains a text
        ocred_file = OcrTestCase.createOCRedFile(filename='the_pdf_withtext.pdf', file_type='application/pdf')
        self.assertOCRedFile(ocred_file,
                             md5='55afdb2874e53370a1565776a6bd4ad7',
                             text='The test if pdf with text')
        self.assertEqual('2019-03-17 03:45:57+00', str(ocred_file.pdf_creation_date))
        self.assertEqual('Tesseract 4.0.0-beta.1', ocred_file.pdf_producer)
        # testing md5_duplication
        try:
            ocred_file2 = OcrTestCase.createOCRedFile(filename='the_pdf_withtext.pdf', file_type='application/pdf')
            self.assertTrue(False, 'OCRedFile md5 deduplication does not work')
        except Md5DuplicationError as e:
            pass


class TestAPISerializer(OcrApiSerializerTestCase):
    """
    This class tests that the API works as expected 2019-03-19
    """
    def test_api_serializer(self):
        """
        This class tests that the OCRedFileSerializer works as expected 2019-03-29
        :return: None
        """
        # uploading test_eng.png using a OCRedFileSerializer
        self.create_serializer(filename='test_eng.png', file_type='image/png',
                               text='A some english text to test Tesseract')
        # test md5 deduplication
        try:
            self.create_serializer(filename='test_eng.png', file_type='image/png', text=None)
            self.assertTrue(False, 'MD5 deduplication does not work for OCRedFileSerializer')
        except Md5DuplicationError as e:
            pass
        # uploading the_pdf_withtext.pdf
        self.create_serializer('the_pdf_withtext.pdf', 'application/pdf', text=None)
        # uploading test_eng.pdf
        self.create_serializer('test_eng.pdf', 'application/pdf', text=None)
        # uploading deming.pdf
        self.create_serializer('deming.pdf', 'application/pdf', text=None)
        # testing list_view
        request = APIRequestFactory().get(reverse(__package__+':list'),
                                          HTTP_AUTHORIZATION='Token {}'.format(self.client.token), )
        response = OCRedFileList.as_view()(request)
        self.assertEqual(200, response.status_code, )


class TestApiUploadView(OcrApiViewTestCase):
    """
    This class intended to test the upload of OCR Server API 2019-03-29
    """
    def test_upload_file_view(self):
        """
        This function tests uploading files via API 2019-03-21
        :return: None
        """
        filename = 'test_eng.png'
        # uploading file
        response = self.upload_file(filename=filename)
        self.assertUploadFileResponse(response,
                                      md5='8aabb1f2d2d92893b5604da701f05505',
                                      text='A some english text to test Tesseract')
        # uploading the same file once again
        response = self.upload_file(filename=filename)
        self.assertUploadFileDuplicationResponse(response,
                                      md5='8aabb1f2d2d92893b5604da701f05505',
                                      text='A some english text to test Tesseract')
        # uploading the file with wrong file_type
        response = self.upload_file(filename='not_image.txt')
        self.assertUploadFileWrongTypeResponse(response)


class TestApiMd5Views(OcrApiViewTestCase):
    """
    This class tests next views:
    <md5:md5>/
    remove/<md5:md5>/
    remove/file/<md5:md5>/
    remove/pdf/<md5:md5>/
    create/pdf/<md5:md5>/
    2019-03-30
    """
    filename = 'test_eng.png'
    file_type = 'image/png'
    md5 = '8aabb1f2d2d92893b5604da701f05505'
    text = 'A some english text to test Tesseract'
    ocred_file = None

    def setUp(self):
        """
        This function prepare each test
        1. create OCRedFile
        :return: None
        """
        super(TestApiMd5Views, self).setUp()
        # create OCRedFile
        self.ocred_file = self.createOCRedFile(filename=self.filename, file_type=self.file_type)
        self.assertOCRedFile(self.ocred_file, md5=self.md5, text=self.text, )

    def get_self(self):
        """
        This function send get request to <md5:md5> page of OCR Server with md5=self.md5
        then compare:
        1. response.status_code is 200
        2. response.data['error'] is False
        3. response.data['exists'] is True
        4. response.data['data']['md5'] is equal self.md5
        5. response.data['data']['text'] is equal self.text
        2019-03-30
        :return: rest framework response
        """
        response = self.client.get(reverse(__package__ + ':md5', kwargs={'md5': self.md5}))
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertEqual(self.md5, response.data['data']['md5'])
        self.assertIn(self.text, response.data['data']['text'])
        return response

    def test_md5_view(self):
        """
        This function tests that CheckMd5 view works as expected 2019-03-24
        :return: None
        """
        # get md5 view OCRedFile
        response = self.get_self()
        if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            self.assertTrue(response.data['data']['can_remove_file'])
        else:
            self.assertFalse(response.data['data']['can_remove_file'])
        if getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
            self.assertTrue(response.data['data']['can_remove_pdf'])
        else:
            self.assertFalse(response.data['data']['can_remove_pdf'])
        if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES) \
                and not getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
            self.assertTrue(response.data['data']['can_create_pdf'])
        else:
            self.assertFalse(response.data['data']['can_create_pdf'])
        # remove pdf from OCRedFile and get md5 view again
        if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES) \
                and getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
            self.ocred_file.remove_pdf()
            response = self.get_self()
            self.assertTrue(response.data['data']['can_create_pdf'])
            self.assertFalse(response.data['data']['can_remove_pdf'])
        if getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            self.ocred_file.remove_file()
            response = self.get_self()
            self.assertFalse(response.data['data']['can_remove_file'])
        # check md5 that does not exist
        response = self.client.get(reverse(__package__ + ':md5', kwargs={'md5': '7aabb1f2d2d92893b5604da701f05500'}))
        self.assertEqual(204, response.status_code,
                         'Expected Response Code 204 received {0} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertFalse(response.data['exists'])

    def test_remove_md5_view(self):
        """
        This function tests that RemoveMd5 view works as expected 2019-03-24
        :return: None
        """
        # delete instance of OCRedFile
        response = self.client.delete(reverse(__package__+':remove_md5', kwargs={'md5': self.md5}))
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertTrue(response.data['removed'])
        # try delete instance of OCRedFile that does not exist
        response = self.client.delete(reverse(__package__+':remove_md5', kwargs={'md5': self.md5}))
        self.assertFalse(response.data['error'])
        self.assertFalse(response.data['exists'])
        self.assertFalse(response.data['removed'])

    def test_remove_file_md5_view(self):
        """
        This function tests that RemoveFileMd5 view works as expected 2019-03-25
        :return: None
        """
        if not getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            return
        response = self.client.delete(reverse(__package__+':remove_file_md5', kwargs={'md5': self.md5}))
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertTrue(response.data['removed'])
        # remove file that does not exist from the instance of OCRedFile (try to remove the same file again)
        response = self.client.delete(reverse(__package__ + ':remove_file_md5', kwargs={'md5': self.md5}))
        self.assertEqual(204, response.status_code,
                         'Expected Response Code 204 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertFalse(response.data['can_remove_file'])
        self.assertFalse(response.data['removed'])
        # remove file from the instance that does not exist
        response = self.client.delete(reverse(__package__ + ':remove_file_md5', kwargs={'md5': '7aabb1f2d2d92893b5604da701f05504'}))
        self.assertEqual(204, response.status_code,
                         'Expected Response Code 204 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertFalse(response.data['exists'])
        self.assertFalse(response.data['removed'])

    def test_remove_pdf_md5_view(self):
        """
        This function tests that RemovePdfMd5 view works as expected 2019-03-25
        :return: None
        """
        if not getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
            return
        # remove ocred_pdf from the instance of OCRedFile
        response = self.client.delete(reverse(__package__+':remove_pdf_md5', kwargs={'md5': self.md5}))
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertTrue(response.data['removed'])
        # remove ocred_pdf that does not exist from the instance of OCRedFile (try to remove the same file again)
        response = self.client.delete(reverse(__package__ + ':remove_pdf_md5', kwargs={'md5': self.md5}))
        self.assertEqual(204, response.status_code,
                         'Expected Response Code 204 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertFalse(response.data['can_remove_pdf'])
        self.assertFalse(response.data['removed'])
        # remove ocred_pdf from the instance that does not exist
        response = self.client.delete(reverse(__package__ + ':remove_pdf_md5', kwargs={'md5': '7aabb1f2d2d92893b5604da701f05504'}))
        self.assertEqual(204, response.status_code,
                         'Expected Response Code 204 received {} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertFalse(response.data['exists'])
        self.assertFalse(response.data['removed'])

    def test_create_pdf_md5_view(self):
        """
        This function tests that CreatePdfMd5 view works as expected 2019-03-25
        :return: None
        """
        if not getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            return
        # remove ocred_pdf from the instance of OCRedFile
        self.ocred_file.remove_pdf()
        # create ocred_pdf in instance of OCRedFile
        response = self.client.get(reverse(__package__+':create_pdf_md5', kwargs={'md5': self.md5}))
        self.assertEqual(201, response.status_code,
                         'Expected Response Code 201 received {0} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertTrue(response.data['created'])
        # create ocred_pdf in the instance of OCRedFile whose ocred_pdf already exists
        response = self.client.get(reverse(__package__+':create_pdf_md5', kwargs={'md5': self.md5}))
        self.assertEqual(204, response.status_code,
                         'Expected Response Code 204 received {0} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['exists'])
        self.assertFalse(response.data['can_create_pdf'])
        self.assertFalse(response.data['created'])


class TestApiAllViews(OcrApiViewTestCase):
    """
    This class tests next views:
    remove/all/
    remove/file/all/
    remove/pdf/all/
    create/pdf/all/
    2019-03-30
    """
    def setUp(self):
        """
        This function prepare each test
        1. create three OCRedFiles
        1.1 png image
        1.2 pdf without text
        1.3 pdf with text
        :return: None
        """
        super(TestApiAllViews, self).setUp()
        # create OCRedFile 1
        self.ocred_file = self.createOCRedFile(filename='test_eng.png', file_type='image/png')
        self.assertOCRedFile(self.ocred_file, md5='8aabb1f2d2d92893b5604da701f05505',
                             text='A some english text to test Tesseract', )
        # create OCRedFile 2
        self.ocred_file = self.createOCRedFile(filename='test_eng_notext.pdf', file_type='application/pdf')
        self.assertOCRedFile(self.ocred_file, md5='4ee3751a767b02d072d33424a84457a9',
                             text='A some english text to test Tesseract', )
        # create OCRedFile 3
        self.ocred_file = self.createOCRedFile(filename='the_pdf_withtext.pdf', file_type='application/pdf')
        self.assertOCRedFile(self.ocred_file, md5='55afdb2874e53370a1565776a6bd4ad7',
                             text='The test if pdf with text', )

    def test_remove_all_view(self):
        """
        This functions tests that RemoveAll view function works as expected 2019-03-25
        :return: None
        """
        response = self.client.delete(reverse(__package__+':remove_all'))
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {0} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['removed'])
        self.assertEqual(3, response.data['count'])

    def test_remove_file_all_view(self):
        """
        This function tests that RemoveFileAll view works as expected 2019-03-25
        :return: None
        """
        if not getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_PDF):
            return
        response = self.client.delete(reverse(__package__ + ':remove_file_all'))
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {0} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['removed'])
        self.assertEqual(3, response.data['count'])

    def test_remove_create_pdf_all_view(self):
        """
        This function tests that RemovePdfAll view works as expected 2019-03-25
        :return: None
        """
        if not getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
            return
        # remove pdf
        response = self.client.delete(reverse(__package__+':remove_pdf_all'))
        self.assertEqual(200, response.status_code,
                         'Expected Response Code 200 received {0} instead.'.format(response.status_code))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['removed'])
        self.assertEqual(2, response.data['count'])
        # test create ocred_pdfs
        if not getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            return
        response = self.client.get(reverse(__package__+':create_pdf_all'))
        self.assertFalse(response.data['error'])
        self.assertTrue(response.data['created'])
        self.assertEqual(2, response.data['count'])


class TestAdmin(OcrAdminTestCase):
    """
    This class is responsible to test admin 2019-03-31
    """
    def setUp(self):
        """
        This function prepare each test
        1. create three OCRedFiles
        1.1 png image
        1.2 pdf without text
        1.3 pdf with text
        :return: None
        """
        super(TestAdmin, self).setUp()
        # create OCRedFile 1
        self.ocred_file = self.createOCRedFile(filename='test_eng.png', file_type='image/png')
        self.assertOCRedFile(self.ocred_file, md5='8aabb1f2d2d92893b5604da701f05505',
                             text='A some english text to test Tesseract', )
        # create OCRedFile 2
        self.ocred_file = self.createOCRedFile(filename='test_eng_notext.pdf', file_type='application/pdf')
        self.assertOCRedFile(self.ocred_file, md5='4ee3751a767b02d072d33424a84457a9',
                             text='A some english text to test Tesseract', )
        # create OCRedFile 3
        self.ocred_file = self.createOCRedFile(filename='the_pdf_withtext.pdf', file_type='application/pdf')
        self.assertOCRedFile(self.ocred_file, md5='55afdb2874e53370a1565776a6bd4ad7',
                             text='The test if pdf with text', )

    @override_settings(OCR_STORE_FILES=True, OCR_STORE_PDF=True)
    def test_admin(self):
        """
        2019-03-31
        :return: None
        """
        # testing /admin/
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context_data['app_list']))
        self.assertEqual(__package__, response.context_data['app_list'][0]['app_label'])
        # testing /admin/ocr/
        response = self.client.get(reverse('admin:app_list', kwargs={'app_label': __package__}))
        self.assertEqual(200, response.status_code)
        html = response.content.decode()
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual(1, len(soup.select('tr.model-ocredfile')))
        # make get request /admin/ocr/ocredfile (OCRedFileList)
        response = self.client.get(reverse('admin:{}_ocredfile_changelist'.format(__package__)))
        self.assertEqual(200, response.status_code)
        html = response.content.decode()
        soup = BeautifulSoup(html, 'html.parser')
        trs = soup.select('table#result_list tbody tr')
        # three files was uploaded. Let's check it
        self.assertEqual(3, len(trs))
        # test each tr that it contains a md5
        #    the_pdf_withtext.pdf
        self.assertEqual('55afdb2874e53370a1565776a6bd4ad7', trs[0].select(':matches(th,td).field-md5 a')[0].text)
        #    test_eng_notext.pdf
        self.assertEqual('4ee3751a767b02d072d33424a84457a9', trs[1].select(':matches(th,td).field-md5 a')[0].text)
        #    'test_eng.png'
        self.assertEqual('8aabb1f2d2d92893b5604da701f05505', trs[2].select(':matches(th,td).field-md5 a')[0].text)
        # test each tr filefield_to_listdisplay that it contains the Remove file button
        for tr in trs:
            self.assertEqual(1, len(tr.select('td.field-filefield_to_listdisplay a.button:contains(Remove)')))
        # go to trs[2] page test_eng.png
        url_test_eng_png_change = trs[2].select(':matches(th,td).field-md5 a')[0]['href']
        response_test_eng_png = self.client.get(url_test_eng_png_change)
        self.assertEqual(200, response_test_eng_png.status_code)
        html_test_eng_png = response_test_eng_png.content.decode()
        soup_test_eng_png = BeautifulSoup(html_test_eng_png, 'html.parser')
        # search for a link to downloading file
        a_download_test_eng_png = soup_test_eng_png.select('a#id_file[target=_blank][href*=download][href*=file]')
        self.assertEqual(1, len(a_download_test_eng_png))
        remove_file_button = soup_test_eng_png.select('a#id_file[target=_blank][href*=download][href*=file] + input[type=submit][value=Remove][name=_removefile]')
        x=3


