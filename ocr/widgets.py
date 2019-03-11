from django.forms.widgets import Widget
from django.template import loader
from django.utils.safestring import mark_safe
from .settings import *


class FileLink(Widget):
    template_name = 'ocr/forms/widgets/file_link.html'
    file_type = None

    def __init__(self,  *args, **kwargs):
        if 'file_type' in kwargs:
            self.file_type = kwargs['file_type']
        kwargs.pop('file_type')
        super(FileLink, self).__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super(FileLink, self).get_context(name, value, attrs)
        context['file_preview'] = FILE_PREVIEW
        if not STORE_FILES:
            context['store_files_disabled'] = True
        if 'store_files_disabled' in context['widget']['value']:
            context['file_missing'] = True
        elif 'file_removed' in context['widget']['value']:
            context['file_removed'] = True
        elif 'image' in self.file_type:
            context['file_image'] = True
        return context


class PdfLink(Widget):
    template_name = 'ocr/forms/widgets/pdf_link.html'

    def get_context(self, name, value, attrs):
        context = super(PdfLink, self).get_context(name, value, attrs)
        if not value or 'file' not in value or not value.file.name:
            context['create_pdf_button'] = True
            print('PdfLink widget need button "Create PDF"')
        if not STORE_PDF:
            context['store_pdf_disabled'] = True
        if not context['widget']['value']:
            return context
        if 'store_pdf_disabled' in context['widget']['value']:
            context['pdf_missing'] = True
        elif 'pdf_removed' in context['widget']['value']:
            context['pdf_removed'] = True
        else:
            context['pdf_exists'] = True
        return context


class PdfInfo(Widget):
    template_name = 'ocr/forms/widgets/pdf_info.html'
    pdf_info = None

    def __init__(self, *args, **kwargs):
        if 'pdf_info' in kwargs:
            self.pdf_info = kwargs['pdf_info']
            kwargs.pop('pdf_info')
            super(PdfInfo, self).__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super(PdfInfo, self).get_context(name, value, attrs)
        context['pdf_info'] = self.pdf_info
        return context