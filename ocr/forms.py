from django import forms
from .models import *
from .widgets import *
from django.core.validators import ValidationError
from django.utils.translation import gettext as _
import hashlib
from .utils import md5


class OCRedFileViewForm(forms.ModelForm):
    md5 = forms.CharField(label='md5:', max_length=32, required=False,
                          widget=forms.TextInput(attrs={'size': 32, 'readonly': True}))
    file = forms.FileField(label='File to upload', )  # SEE __init__ below
    file_type = forms.CharField(label='type:', max_length=20, required=False,
                                widget=forms.TextInput(attrs={'readonly': True}))
    uploaded = forms.DateTimeField(label='Uploaded:', required=False,
                                   widget=forms.DateTimeInput(attrs={'readonly': True}))
    ocred = forms.DateTimeField(label='Processed:', required=False,
                                widget=forms.DateTimeInput(attrs={'readonly': True}))
    text = forms.CharField(label='OCRed content', required=False,
                           widget=forms.Textarea(attrs={'readonly': True, 'rows': 4}))
    ocred_pdf = forms.FileField(label='OCRed PDF', widget=PdfLink(attrs={'target': '_blank'}))
    ocred_pdf_md5 = forms.CharField(label='OCRed PDF md5:', max_length=32, required=False,
                                    widget=forms.TextInput(attrs={'size': 32, 'readonly': True}))
    pdf_num_pages = forms.IntegerField(label='PDF nPages:', required=False,
                                       widget=forms.TextInput(attrs={'readonly': True}))

    pdf_info = forms.Field(label='PDF Info', required=False, )  # SEE __init__ below

    def __init__(self, *args, **kwargs):
        super(OCRedFileViewForm, self).__init__(*args, **kwargs)
        file_type = self.instance.file_type
        self.fields['file'].widget = FileLink(attrs={'target': '_blank'}, file_type=file_type)
        pdf_info = {}
        #if 'pdf_num_pages' in self.instance:
        pdf_info['pdf_num_pages'] = self.instance.pdf_num_pages
        #if 'pdf_author' in self.instance:
        pdf_info['pdf_author'] = self.instance.pdf_author
        #if 'pdf_creation_date' in self.instance:
        pdf_info['pdf_creation_date'] = self.instance.pdf_creation_date
        #if 'pdf_creator' in self.instance:
        pdf_info['pdf_creator'] = self.instance.pdf_creator
        #if 'pdf_mod_date' in self.instance:
        pdf_info['pdf_mod_date'] = self.instance.pdf_mod_date
        #if 'pdf_producer' in self.instance:
        pdf_info['pdf_producer'] = self.instance.pdf_producer
        #if 'pdf_title' in self.instance:
        pdf_info['pdf_title'] = self.instance.pdf_title
        self.fields['pdf_info'].widget = PdfInfo(attrs={}, pdf_info=pdf_info)

    class Meta:
        model = OCRedFile
        exclude = []


class OCRedFileAddForm(forms.ModelForm):
    md5 = forms.CharField(required=False, widget=forms.HiddenInput())
    file = forms.FileField(label='File to upload')
    file_type = forms.CharField(required=False, widget=forms.HiddenInput())
    uploaded = forms.DateTimeField(required=False, widget=forms.HiddenInput())
    ocred = forms.DateTimeField(required=False, widget=forms.HiddenInput())
    text = forms.CharField(required=False, widget=forms.HiddenInput())
    ocred_pdf = forms.FileField(required=False, widget=forms.HiddenInput())
    ocred_pdf_md5 = forms.CharField(required=False, widget=forms.HiddenInput())
    pdf_num_pages = forms.IntegerField(required=False, widget=forms.HiddenInput())
    pdf_info = forms.Field(required=False, widget=forms.HiddenInput())  # not model field

    def clean(self):
        print('OCRedFileAddForm->clean')
        cleaned_data = super(OCRedFileAddForm, self).clean()
        file = self.files.get('file')
        if not file:
            raise ValidationError(_('A file does not present'),
                                  code='invalid')
        cleaned_data['file_type'] = file.content_type
        print('OCRedFileAddForm->clean content_type='+cleaned_data['file_type'])
        if cleaned_data['file_type'] != 'application/pdf'\
                and cleaned_data['file_type'] != 'image/jpeg'\
                and cleaned_data['file_type'] != 'image/png'\
                and cleaned_data['file_type'] != 'image/bmp'\
                and cleaned_data['file_type'] != 'image/tiff':
            print('OCRedFileAddForm->clean invalid content_type=' + cleaned_data['file_type'])
            raise ValidationError(_('The content type of the file='+cleaned_data['file_type']+' is invalid'), code='invalid')
        content = file.read()
        file.seek(0)
        md5_txt = md5(content)
        print('OCRedFileAddForm->clean md5='+md5_txt)
        if OCRedFile.objects.filter(md5=md5_txt).exists():
            print('OCRedFileAddForm->clean md5=' + md5_txt + ' already exists')
            raise ValidationError(_('The file with md5='+md5_txt+' already exists'), code='invalid')
        cleaned_data['md5'] = md5_txt
        return cleaned_data

    class Meta:
        model = OCRedFile
        exclude = []

