import os
#import io
#   # does not convert some ocred_pdf to text (for example pdfs created by tesseract), used for pdfinfo
#import pdftotext  # Faster than tika converts ocred_pdf to text
# import re
# import regex
# import subprocess DEPRECATED

# import pytesseract DEPRECATED
from django.db import models
from .settings import *
# from PIL import Image DEPRECATED
from datetime import datetime
from .utils import md5, ocr_img2str, pdf2text, ocr_img2pdf, pdf_info, pdf_need_ocr, ocr_pdf, read_binary_file




def set_ocredfile_name(instance, filename=None):
    if not STORE_FILES:
        return 'store_files_disabled'
    upload_to = __package__ + '/upload/'
    return upload_to + filename


def set_pdffile_name(instance, filename=None):
    if not STORE_PDF:
        return 'store_pdf_disabled'
    upload_to = __package__ + '/pdf/'
    if instance.md5:
        return upload_to + instance.md5 + '.pdf'
    return upload_to + instance.file.name + '.pdf'


# Create your models here.
class OCRedFile(models.Model):
    """
    The OCRedFile model class. Need to store information about uploaded file.
    """
    md5 = models.CharField(max_length=32, unique=True, blank=True)
    file = models.FileField(upload_to=set_ocredfile_name, null=True)  # the file (if STORE_FILES = True)
    file_type = models.CharField(max_length=20, blank=True, null=True)  # type of file
    text = models.TextField(blank=True, null=True)  # the content of OCRed file (if STORE_PDF = True)
    uploaded = models.DateTimeField(auto_now_add=True)  # datetime when file was uploaded
    ocred = models.DateTimeField(blank=True, null=True)  # datefime when file was OCRed
    ocred_pdf = models.FileField(upload_to=set_pdffile_name, null=True)  # the ocred ocred_pdf (if STORE_PDF = True)
    ocred_pdf_md5 = models.CharField(max_length=32, null=True, blank=True)  # md5 of ocred_pdf file if exists
    pdf_num_pages = models.IntegerField(null=True, blank=True)  #
    # from ocred_pdf info
    pdf_author = models.CharField(max_length=128, null=True, blank=True)
    pdf_creation_date = models.DateTimeField(blank=True, null=True)
    pdf_creator = models.CharField(max_length=128, null=True, blank=True)
    pdf_mod_date = models.DateTimeField(blank=True, null=True)
    pdf_producer = models.CharField(max_length=128, null=True, blank=True)
    pdf_title = models.CharField(max_length=128, null=True, blank=True)


    def remove_file(self):
        """
        This function removes self.file.sile from a disk if it exists, renames self.file.name to 'file_removed' and then saves the model instance
        :return: None
        """
        print('OCRedFile->remove_file')
        if os.path.isfile(self.file.path):
            os.remove(self.file.path)
        self.file.name = 'file_removed'
        super(OCRedFile, self).save()

    def remove_pdf(self):
        """
        This function removes self.pdf.file from a disk if it exists, renames self.pdf.name to 'pdf_removed' and then saves the model instance
        :return: None
        """
        print('OCRedFile->remove_pdf')
        if self.ocred_pdf:
            if os.path.isfile(self.ocred_pdf.path):
                os.remove(self.ocred_pdf.path)
            self.ocred_pdf.name = 'pdf_removed'
            super(OCRedFile, self).save()

    def create_pdf(self):
        """
        This function creates self.pdf.file todo
        :return: None
        """
        print('OCRedFile->create_pdf')
        if not self.ocred_pdf or 'pdf_removed' in self.ocred_pdf.name or 'store_pdf_disabled' in self.ocred_pdf.name:
            # ocred pdf does not exit, check 'ocred' field, if file did not be ocred, then we do not need to create ocred pdf
            if not self.ocred:
                return
            # check if file field exists
            if self.file:
                # check if file exits
                path = self.file.path
                if os.path.isfile(path):
                    # todo
                    pass
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
        print("OCRedFile->delete "+self.file.path)
        self.remove_file()
        self.remove_pdf()
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
        content = self.file.file.read()  # read content of the 'file' field
        self.file.file.seek(0)  # return the reading pointer of the 'file' file to start position
        # calculate md5 of 'file' field if if does not exist
        if self.md5:
            print('OCRedFile->save has md5='+self.md5)
        else:
            print('OCRedFile->save does not have md5')
            self.md5 = md5(content)
        # extract of ocr a content of the 'file' field if 'text' does not exist
        if not self.text:
            print('OCRedFile->save start OCR')
            if 'image' in self.file_type:
                if STORE_PDF:
                    pdf_content = ocr_img2pdf(content)
                    self.text = pdf2text(pdf_content)
                    filename = set_pdffile_name(self)
                    pdf = open(filename, 'wb')
                    pdf.write(content)
                    pdf.close()
                    self.ocred_pdf.name = filename
                    self.ocred_pdf_md5 = md5(pdf_content)
                else:
                    self.text = ocr_img2str(content)  # recognize a content of the 'file' field to a string
                self.ocred = datetime.now()
            elif 'pdf' in self.file_type:
                info = pdf_info(content)
                self.pdf_num_pages = info['numPages']
                self.pdf_author = info['Author']
                self.pdf_creation_date = info['CreationDate']
                self.pdf_creator = info['Creator']
                self.pdf_mod_date = info['ModDate']
                self.pdf_producer = info['Producer']
                self.pdf_title = info['Title']
                pdf_text = pdf2text(content)
                # check that loaded PDF file contains text
                if pdf_need_ocr(pdf_text):
                    print('OCRedFile PDF OCR processing via OCRmyPDF')
                    filename = set_pdffile_name(self)
                    self.text = ocr_pdf(content, filename)
                    self.ocred = datetime.now()  # save datetime when uploaded PDF was ocred
                    self.ocred_pdf.name = filename
                    if STORE_PDF:
                        self.ocred_pdf_md5 = md5(read_binary_file(filename))
                    print('OCRedFile PDF OCR finished')
                else:
                    print('OCRedFile->save use text from loaded pdf')
                    self.text = pdf_text
            print('OCRedFile->save finished OCR: ')
        if not STORE_FILES:
            print('OCRedFile->save STORE_FILES is ' + str(STORE_FILES))
            self.file.truncate()
        super(OCRedFile, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
        if not STORE_FILES:
            os.remove(self.file.path)


