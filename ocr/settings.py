# 21.02.2019 shmakovpn
# settings file for the ocr application
STORE_FILES = True  # store uploaded files or not (True for debug)
FILE_PREVIEW = False  # show file preview in admin
TESSERACT_LANG = 'rus+eng'  # languages used by tesseract
STORE_PDF = True  # generate ocred_pdf from uploaded file and store it

# The types of file allowed to uploading to OCR Server 2019-03-18
ALLOWED_FILE_TYPES = (
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/bmp',
    'image/tiff',
)
