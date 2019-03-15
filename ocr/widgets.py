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
    """
    Widget that shows a link to pdf file on the update model admin page.
    If pdf file exists the 'Remove PDF' button shows.
    If pdf file does not exists and it is possible to create it the 'Create PDF' button will shows
    """
    template_name = 'ocr/forms/widgets/pdf_link.html'
    no_source_file = False
    ocred = False

    def __init__(self, *args, **kwargs):
        if 'no_source_file' in kwargs:
            self.no_source_file = kwargs['no_source_file']
            kwargs.pop('no_source_file')
        if 'ocred' in kwargs:
            self.ocred = kwargs['ocred']
            kwargs.pop('ocred')
        super(PdfLink, self).__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        """
        This function creates context for rendering widget template.
        If pdf file exists the context['pdf_exists'] will be True
        If pdf file does not exist and it is possible to create it context['create_pdf_button'] will be True
        :param name:
        :param value:
        :param attrs:
        :return:
        """
        context = super(PdfLink, self).get_context(name, value, attrs)
        try:
            filename = value.file.name
        except (ValueError, FileNotFoundError) as e:
            if not self.no_source_file and self.ocred:
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