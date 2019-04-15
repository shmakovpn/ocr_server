"""
This file contains default settings for OCR Server
"""
__author__ = 'shmakovpn <shmakovpn@yandex.ru>'
__date__ = '21.02.2019/2019-03-29/2019-04-12'

STORE_FILES = True  # store uploaded files or not (True for debug)
FILE_PREVIEW = True  # show file preview in admin
TESSERACT_LANG = 'rus+eng'  # languages used by tesseract
STORE_PDF = True  # generate ocred_pdf from uploaded file and store it

STORE_FILES_DISABLED_LABEL = 'store_files_disabled'
STORE_PDF_DISABLED_LABEL = 'store_pdf_disabled'

FILE_REMOVED_LABEL = 'file_removed'
PDF_REMOVED_LABEL = 'pdf_removed'

# The types of file allowed to uploading to OCR Server 2019-03-18
ALLOWED_FILE_TYPES = (
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/bmp',
    'image/tiff',
)

FILES_UPLOAD_TO = __package__ + '/upload/'
PDF_UPLOAD_TO = __package__ + '/pdf/'

"""
TimeToLive settings
{PARAM_NAME}_TTL = timedelta(..)
FILES_TTL = 0  # TTL for OCRedFile.files is disabled
PDF_TTL = 0  # TTL for OCRedFile.ocred_pdfs is disabled
TTL = 0  # TTL for OCRedFile is disabled
When current datetime will grater OCRedFile.uploaded+{PARAM}_TTL corresponding object will be removed
"""
FILES_TTL = 0
PDF_TTL = 0
TTL = 0


