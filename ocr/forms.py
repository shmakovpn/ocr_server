from django import forms
from .models import *


class OCRedFileForm(forms.ModelForm):
    file = forms.FileField(label='File to upload: ')
    md5 = forms.CharField(label='_md5:', max_length=32, required=False)

    def clean_md5(self):
        print('clean md5')


    class Meta:
        model = OCRedFile
        #exclude = []
        fields = ['md5', 'file']

        def clean_md5(self):
            print('clean md5')

        def clean(self):
            md5 = self.cleaned_data['md5']
            try:
                OCRedFile.objects.get(md5=md5)
            except OCRedFile.DoesNotExist:
                return self.cleaned_data
            raise forms.ValidationError('File is already taken.')


"""   
    file = forms.FileField(label='File to upload: ')
    md5 = forms.CharField(label='md5:', max_length=32)

    def clean_md5(self):
        md5 = self.cleaned_data['md5']
        try:
            OCRedFile.objects.get(md5=md5)
        except OCRedFile.DoesNotExist:
            return md5
        raise forms.ValidationError('File is already taken.')
        
        
"""


