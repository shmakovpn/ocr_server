import os
import io
import PyPDF2  # does not convert some ocred_pdf to text (for example pdfs created by tesseract), used for pdfinfo
import pdftotext  # Faster than tika converts ocred_pdf to text
import re
import regex
import subprocess

import hashlib
import pytesseract
from django.db import models
from .settings import *
from PIL import Image
from datetime import datetime



def parse_pdf_datetime(pdf_datetime):
    # like D:20190122061133Z
    match_ob = re.match(r'^D\:(\d{14})Z$', pdf_datetime)
    if match_ob:
        pdf_datetime = match_ob[1]
    # like 20190122061133
    if len(pdf_datetime) == 14:
        return pdf_datetime[0:4] + '-' + pdf_datetime[4:6] + '-' + pdf_datetime[6:8] + ' ' + pdf_datetime[8:10] + ':' + pdf_datetime[10:12] + ':' + pdf_datetime[12:14]
    # otherwise
    return pdf_datetime[2:6] + '-' + pdf_datetime[6:8] + '-' + pdf_datetime[8:10] + ' ' + pdf_datetime[10:12] + ':' + pdf_datetime[12:14] + ':' + pdf_datetime[14:16] + '+' + pdf_datetime[17:19]


def set_ocredfile_name(instance, filename):
    upload_to = __package__ + '/upload/'
    if not STORE_FILES:
        filename = 'store_files_disabled'
    return upload_to + filename


def set_pdffile_name(instance, filename=None):
    upload_to = __package__ + '/pdf/'
    if instance.md5:
        return upload_to + instance.md5 + '.pdf'
    return upload_to + instance.file.name + '.pdf'


# Create your models here.
class OCRedFile(models.Model):
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
        print('OCRedFile->remove_file')
        if os.path.isfile(self.file.path):
            os.remove(self.file.path)
        self.file.name = 'file_removed'
        super(OCRedFile, self).save()

    def remove_pdf(self):
        print('OCRedFile->remove_pdf')
        if self.ocred_pdf:
            if os.path.isfile(self.ocred_pdf.path):
                os.remove(self.ocred_pdf.path)
            self.ocred_pdf.name = 'pdf_removed'
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
        print("OCRedFile->delete "+self.file.path)
        self.remove_file()
        self.remove_pdf()
        super(OCRedFile, self).delete(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        print("OCRedFile->save "+self.file.path)
        if self.md5:
            print('OCRedFile->save has md5='+self.md5)
        else:
            print('OCRedFile->save does not have md5')
            hash_md5 = hashlib.md5()
            content = self.file.file.read()
            self.file.file.seek(0)
            hash_md5.update(content)
            self.md5 = hash_md5.hexdigest()
        if not self.text:
            os.environ['OMP_THREAD_LIMIT'] = '1'
            print('OCRedFile->save start OCR')
            #try:
            tesseract_version = pytesseract.get_tesseract_version()
            if 'image' in self.file_type:
                img = Image.open(self.file.file)
                if STORE_PDF:
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, TESSERACT_LANG)  # ocred_pdf is bytes
                    pdf_io = io.BytesIO(pdf_bytes)
                    pdfs = pdftotext.PDF(pdf_io)
                    for page in range(len(pdfs)):
                        self.text += pdfs[page]
                    filename = set_pdffile_name(self, set_pdffile_name(self))
                    pdf = open(filename, 'wb')
                    pdf.write(pdf_bytes)
                    pdf.close()
                    self.ocred_pdf.name = filename
                    hash_md5 = hashlib.md5()
                    hash_md5.update(pdf_bytes)
                    self.ocred_pdf_md5 = hash_md5.hexdigest()
                else:
                    self.text = pytesseract.image_to_string(img, TESSERACT_LANG)
                self.ocred = datetime.now()
            elif 'pdf' in self.file_type:
                # 0 read pdfinfo
                pdfReader = PyPDF2.PdfFileReader(self.file.file)
                self.pdf_num_pages = pdfReader.numPages
                pdf_info = pdfReader.getDocumentInfo()
                if '/Author' in pdf_info:
                    self.pdf_author = pdf_info['/Author']
                if '/CreationDate' in pdf_info:
                    self.pdf_creation_date = parse_pdf_datetime(pdf_info['/CreationDate'])
                if '/Creator' in pdf_info:
                    self.pdf_creator = pdf_info['/Creator']
                if '/ModDate' in pdf_info:
                    self.pdf_mod_date = parse_pdf_datetime(pdf_info['/ModDate'])
                if '/Producer' in pdf_info:
                    self.pdf_producer = pdf_info['/Producer']
                if '/Title' in pdf_info:
                    self.pdf_title = pdf_info['/Title']
                # 1 extract text from ocred_pdf
                self.file.file.seek(0)
                pdfs = pdftotext.PDF(self.file.file)
                self.file.file.seek(0)
                pdf_text = ''
                for page in range(len(pdfs)):
                    pdf_text += pdfs[page]
                # check that loaded PDF file contains text
                if not len(pdf_text) or (not regex.search(r'\p{IsCyrillic}', pdf_text) and not re.search(r'the', pdf_text, re.IGNORECASE)):
                    print('OCRedFile PDF OCR processing via OCRmyPDF')
                    pdf_bytes = self.file.file.read()
                    self.file.file.seek(0)
                    filename = '/dev/null'
                    if STORE_PDF:
                        filename = set_pdffile_name(self, set_pdffile_name(self))
                    popen = subprocess.Popen([
                        'ocrmypdf',
                        '-l',
                        TESSERACT_LANG,
                        '-',  # using STDIN
                        filename,  #
                        '--force-ocr',
                        '--sidecar',
                        '-'  # using STDOUT for sidecar
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    popen.stdin.write(pdf_bytes)
                    result = popen.communicate(input=pdf_bytes)
                    self.text = result[0].decode()
                    self.ocred = datetime.now()  # save datetime when uploaded PDF was ocred
                    self.ocred_pdf.name = filename
                    hash_md5 = hashlib.md5()
                    hash_md5.update(pdf_bytes)
                    self.ocred_pdf_md5 = hash_md5.hexdigest()
                    print('OCRedFile PDF OCR finished')
                else:
                    print('OCRedFile->save use text from loaded pdf')
                    self.text = pdf_text
            print('OCRedFile->save finished OCR: ')
            ### print(self.text)
            #except Exception as e:
                #print('OCRedFile error: '+str(e))
        if not STORE_FILES:
            print('OCRedFile->save STORE_FILES is ' + str(STORE_FILES))
            self.file.truncate()
        super(OCRedFile, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
        if not STORE_FILES:
            os.remove(self.file.path)


