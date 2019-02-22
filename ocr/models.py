import os
import hashlib
from django.db import models

from django.db.models.signals import pre_save
from django.dispatch import receiver

# Create your models here.
class OCRedFile(models.Model):
    md5 = models.CharField(max_length=32, unique=True, blank=True)
    #pdf = models.BooleanField(default=False)
    file = models.FileField(upload_to=__package__+'/upload/')  # the file (if STORE_FILES = True)
    text = models.TextField(null=True, editable= False)  # the content of OCRed file (if STORE_PDF = True)
    uploaded = models.DateTimeField(auto_now_add=True, editable= False)
    #url = models.URLField(unique=True)

    def __str__(self):
        return self.file.path + ' ' + str(self.md5) + ' ' + str(self.uploaded)

    class Meta:
        verbose_name = 'OCRedFile'
        verbose_name_plural = 'OCRedFile'

    def delete(self, *args, **kwargs):
        print("OCRedFile->delete "+self.file.path)
        if os.path.isfile(self.file.path):
            os.remove(self.file.path)

        super(OCRedFile, self).delete(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        print("OCRedFile->save "+self.file.path)
        super(OCRedFile, self).save(force_insert=False, force_update=False, using=None,
             update_fields=None)


@receiver(pre_save, sender=OCRedFile)
def pre_save_OCRedFile(sender, instance, *args, **kwargs):
    print('pre_save_OCRedFile')
    hash_md5 = hashlib.md5()
    file = instance.file.file
    content = file.read()
    hash_md5.update(content)
    md5_txt = hash_md5.hexdigest()
    instance.md5 = md5_txt
    print(md5_txt)

