import os
from django.db import models
from django.conf import settings
from ocr import settings as ocr_default_settings
# from datetime import datetime
from django.utils import timezone
from .utils import md5, ocr_img2str, pdf2text, ocr_img2pdf, pdf_info, pdf_need_ocr, ocr_pdf, read_binary_file
from io import BytesIO
from django.utils.translation import gettext_lazy as _
from .exceptions import *


def set_ocredfile_name(instance, filename=None):
    """
    This function returns a filename for OCRedFile.file 2019-03-18
    :param instance: an instance of the OCRedFile model
    :param filename: a name of a uploaded file
    :return: a filename for OCRedFile.file
    """
    upload_to = __package__ + '/upload/'
    if not getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
        filename = 'store_files_disabled'
    return upload_to + filename


def set_pdffile_name(instance, filename=None):
    """
    This function returns a filename for OCRedFile.ocred_pdf 2019-03-18
    :param instance: an instance of the OCRedFile model
    :param filename: boolean if False 'store_pdf_disabled' will not use as ocred_pdf.file.name
    :return: a filename for OCRedFile.ocred_pdf
    """
    upload_to = __package__ + '/pdf/'
    if not filename and not getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
        filename = 'store_pdf_disabled'
    elif instance.md5:
        filename = instance.md5
    else:
        filename = instance.file.name
    return upload_to + filename + '.pdf'


# Create your models here.
class OCRedFile(models.Model):
    """
    The OCRedFile model class. Need to store information about uploaded file.
    """
    md5 = models.CharField('md5', max_length=32, unique=True, blank=True, )
    file = models.FileField('uploaded file', upload_to=set_ocredfile_name, null=True)
    file_type = models.CharField('content type', max_length=20, blank=True, null=True, )
    text = models.TextField('OCRed content', blank=True, null=True)
    uploaded = models.DateTimeField('uploaded datetime', auto_now_add=True,)
    ocred = models.DateTimeField('OCRed datetime', blank=True, null=True)
    ocred_pdf = models.FileField('Searchable PDF', upload_to=set_pdffile_name, null=True)
    ocred_pdf_md5 = models.CharField("Searchable PDF's md5", max_length=32, null=True, blank=True)
    pdf_num_pages = models.IntegerField("PDF's num pages", null=True, blank=True)  #
    # from ocred_pdf info
    pdf_author = models.CharField("PDF's author", max_length=128, null=True, blank=True)
    pdf_creation_date = models.DateTimeField("PDF's creation date", blank=True, null=True)
    pdf_creator = models.CharField("PDF's creator", max_length=128, null=True, blank=True)
    pdf_mod_date = models.DateTimeField("PDF's mod date", blank=True, null=True)
    pdf_producer = models.CharField("PDF's producer", max_length=128, null=True, blank=True)
    pdf_title = models.CharField("PDF's title", max_length=128, null=True, blank=True)

    @staticmethod
    def is_valid_file_type(file_type, raise_exception=False):
        """
        This functions checks that file_type contains a correct value. 2019-03-20
        :param file_type:
        :param raise_exception:
        :return: boolean. True if file_type contains a correct value
        """
        print('validate_oc_file_type')
        if not file_type:
            print('validate_oc_file_type. the file_type is None')
            if raise_exception:
                raise FileTypeError(_('The content type of the file is null'))
            else:
                return False
        if file_type not in getattr(settings, 'OCR_ALLOWED_FILE_TYPES', ocr_default_settings.ALLOWED_FILE_TYPES):
            print('validate_oc_file_type. the file_type is not in allowed file types')
            if raise_exception:
                raise FileTypeError(file_type)
            else:
                return False
        return True

    @staticmethod
    def is_valid_ocr_md5(md5_value, raise_exception=False):
        """
        This function validates that the md5 does not already exist in the md5 field and ocred_pdf_md5.
        :param md5_value:
        :param raise_exception:
        :return: boolean. True if md5 does not already exist
        """
        print('is_valid_ocr_md5')
        if not md5_value:
            if raise_exception:
                raise ValidationError(_('The md5 value is empty'))
            else:
                return False
        if OCRedFile.objects.filter(md5=md5_value).exists():
            if raise_exception:
                raise Md5DuplicationError(md5_value)
            else:
                return False
        if OCRedFile.objects.filter(ocred_pdf_md5=md5_value).exists():
            if raise_exception:
                raise Md5PdfDuplicationError(md5_value)
            else:
                return False
        return True

    @property
    def can_remove_file(self):
        """
        This function returns True if it is possible to remove self.file 2019-03-24
        :return: boolean True if it is possible to remove self.file
        """
        if os.path.isfile(self.file.path):
            return True
        return False

    @property
    def can_remove_pdf(self):
        """
        This function returns True if it is possible to remove self.ocred_pdf 2019-03-24
        :return: boolean True if it is possible to remove self.ocred_pdf
        """
        if self.ocred_pdf:
            if os.path.isfile(self.ocred_pdf.path):
                return True
        return False

    @property
    def file_removed(self):
        """
        This function returns True if file was removed 2019-04-05
        :return: boolean True if file was removed
        """
        if 'file_removed' in self.file.name:
            return True
        return False

    @property
    def pdf_removed(self):
        """
        This function returns True if ocred_pdf was removed 2019-04-05
        :return: boolean True if ocred_pdf was removed
        """
        if bool(self.ocred) and 'pdf_removed' in self.ocred_pdf.name:
            return True
        return False

    def remove_file(self):
        """
        This function removes self.file.sile from a disk if it exists,
        renames self.file.name to 'file_removed' and then saves the model instance
        :return: None
        """
        print('OCRedFile->remove_file')
        if os.path.isfile(self.file.path):
            os.remove(self.file.path)
        self.file.name = 'file_removed'
        OCRedFile.Counters.num_removed_files += 1
        super(OCRedFile, self).save()

    def remove_pdf(self):
        """
        This function removes self.pdf.file from a disk if it exists,
        renames self.pdf.name to 'pdf_removed' and then saves the model instance
        :return: None
        """
        print('OCRedFile->remove_pdf')
        if self.ocred_pdf:
            if os.path.isfile(self.ocred_pdf.path):
                os.remove(self.ocred_pdf.path)
            self.ocred_pdf.name = 'pdf_removed'
            self.ocred_pdf_md5 = None
            OCRedFile.Counters.num_removed_pdf += 1
            super(OCRedFile, self).save()

    @property
    def is_pdf(self):
        """
        This function returns True if the uploaded file is pdf 2019-03-21
        :return: boolean True if the uploaded file is pdf
        """
        if 'pdf' in self.file_type:
            return True
        return False

    @property
    def has_pdf_text(self):
        """
        This function returns True if the uploaded file is pdf and it contains text 2019-03-21
        :return: boolean True if the uploaded file is pdf and it contains text
        """
        if self.is_pdf and not self.ocred:
            return True
        return False

    @property
    def can_create_pdf(self):
        """
        This function return True if it is possible to create searchable PDF 2019-03-24
        :return: boolean True if it is possible to create searchable PDF
        """
        if self.file:
            if not os.path.isfile(self.file.path):
                return False
        if not self.ocred_pdf or 'pdf_removed' in self.ocred_pdf.name or 'store_pdf_disabled' in self.ocred_pdf.name:
            if not self.is_pdf or not self.has_pdf_text:
                return True
        return False

    def create_pdf(self, admin_obj=None, request=None):
        """
        This function creates self.pdf.file if it is possible 2019-03-13
        :admin_obj: An admin instance of the model
        :request: A request instance of the current http request
        :return: None
        """
        if self.can_create_pdf:
            content = self.file.file.read()
            self.file.file.seek(0)
            if 'image' in self.file_type:
                pdf_content = ocr_img2pdf(content)
                filename = set_pdffile_name(self, True)
                pdf = open(filename, 'wb')
                pdf.write(content)
                pdf.close()
                self.ocred_pdf.name = filename
                self.ocred_pdf_md5 = md5(pdf_content)
                OCRedFile.Counters.num_created_pdf += 1
                if admin_obj and request:
                    admin_obj.message_user(request,
                                           'PDF created')
            elif 'pdf' in self.file_type:
                filename = set_pdffile_name(self, True)
                ocr_pdf(content, filename)
                self.ocred_pdf.name = filename
                self.ocred_pdf_md5 = md5(read_binary_file(filename))
                OCRedFile.Counters.num_created_pdf += 1
                if admin_obj and request:
                    admin_obj.message_user(request,
                                           'PDF created')
            super(OCRedFile, self).save()

    def __str__(self):
        if 'store_files_disabled' in self.file.name:
            return 'NO FILE "' + str(self.md5) + '" "' + str(self.uploaded) + '"'
        elif 'file_removed' in self.file.name:
            return 'REMOVED "' + str(self.md5) + '" "' + str(self.uploaded) + '"'
        return self.file.path + ' "' + str(self.md5) + '" "' + str(self.uploaded) + '"'

    class Meta:
        verbose_name = 'OCRedFile'
        verbose_name_plural = 'OCRedFile'

    def delete(self, *args, **kwargs):
        """
        This function deletes the instance of the model
        :param args:
        :param kwargs:
        :return: None
        """
        self.remove_file()
        self.remove_pdf()
        OCRedFile.Counters.num_removed_instances += 1
        super(OCRedFile, self).delete(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        This function save the instance of the model, or create it
        :param force_insert:
        :param force_update:
        :param using:
        :param update_fields:
        :return: None
        """
        print("OCRedFile->save "+self.file.path)
        if self.uploaded is not None:  # ocred_file already exists
            return
        if not self.file_type:
            self.file_type = self.file.file.content_type
        OCRedFile.is_valid_file_type(file_type=self.file_type, raise_exception=True)
        content = self.file.file.read()  # read content of the 'file' field
        self.file.file.seek(0)  # return the reading pointer of the 'file' file to start position
        # calculate md5 of 'file' field if if does not exist
        if self.md5:
            print('OCRedFile->save has md5='+self.md5)
        else:
            self.md5 = md5(content)
            print('OCRedFile->save does not have md5, created md5='+self.md5)
        OCRedFile.is_valid_ocr_md5(md5_value=self.md5, raise_exception=True)
        # extract of ocr a content of the 'file' field if 'text' does not exist
        if not self.text:
            print('OCRedFile->save start OCR')
            if 'image' in self.file_type:
                if getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
                    pdf_content = ocr_img2pdf(content)
                    self.text = pdf2text(pdf_content)
                    self.ocred_pdf_md5 = md5(pdf_content)
                    self.ocred_pdf.save(set_pdffile_name(self), BytesIO(pdf_content), False)
                else:
                    self.text = ocr_img2str(content)  # recognize a content of the 'file' field to a string
                    self.ocred_pdf.name = set_pdffile_name(self)
                self.ocred = timezone.now()
            elif 'pdf' in self.file_type:
                info = pdf_info(content)
                self.pdf_num_pages = info['numPages']
                self.pdf_author = info['Author']
                if info['CreationDate']:
                    self.pdf_creation_date = info['CreationDate']
                self.pdf_creator = info['Creator']
                if info['ModDate']:
                    self.pdf_mod_date = info['ModDate']
                self.pdf_producer = info['Producer']
                self.pdf_title = info['Title']
                pdf_text = pdf2text(content)
                # check that loaded PDF file contains text
                if pdf_need_ocr(pdf_text):
                    print('OCRedFile PDF OCR processing via OCRmyPDF')
                    filename = set_pdffile_name(self)
                    self.text = ocr_pdf(content, filename)
                    self.ocred = timezone.now()  # save datetime when uploaded PDF was ocred
                    self.ocred_pdf.name = filename
                    if getattr(settings, 'OCR_STORE_PDF', ocr_default_settings.STORE_PDF):
                        self.ocred_pdf_md5 = md5(read_binary_file(filename))
                    print('OCRedFile PDF OCR finished')
                else:
                    print('OCRedFile->save use text from loaded pdf')
                    self.text = pdf_text
            print('OCRedFile->save finished OCR: ')
        if not getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            print('OCRedFile->save STORE_FILES is ' + str(getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES)))
            try:
                self.file.truncate()
            except Exception as e:
                print('Warning. Can not truncate OCRedFile.file '+str(e))
        super(OCRedFile, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
        if not getattr(settings, 'OCR_STORE_FILES', ocr_default_settings.STORE_FILES):
            os.remove(self.file.path)
        OCRedFile.Counters.num_created_instances += 1

    class Counters:
        """
        Counters of events 2019-03-25
        """
        num_removed_instances = 0  # number of removed instances of OCRedFile
        num_removed_files = 0  # number of removed files from instances of OCRedFile
        num_removed_pdf = 0  # number of removed ocred_pdfs from instances of OCRedFile
        num_created_pdf = 0  # number of created ocred_pdfs in instances of OCRedFile
        num_created_instances = 0  # number of created instances of OCRedFile
