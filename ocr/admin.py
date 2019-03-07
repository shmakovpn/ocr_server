from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.contrib.admin.actions import delete_selected as delete_selected_
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.urls import path, reverse
from .models import *
from .forms import *


def delete_selected(modeladmin, request, queryset):
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied
    if request.POST.get('post'):
        for obj in queryset:
            obj.delete()
    else:
        return delete_selected_(modeladmin, request, queryset)


delete_selected.short_description = "Delete selected objects"


def remove_file_selected(modeladmin, request, queryset):
    if not modeladmin.has_change_permission(request):
        raise PermissionDenied
    for obj in queryset:
        obj.remove_file()


def remove_pdf_selected(modeladmin, request, queryset):
    if not modeladmin.has_change_permission(request):
        raise PermissionDenied
    for obj in queryset:
        obj.remove_pdf()


def filefield_to_listdisplay(obj):
    if 'store_files_disabled' in obj.file.name:
        return 'NO FILE'
    elif 'file_removed' in obj.file.name:
        return 'REMOVED'
    return format_html('<a href="/{}" target="_blank">{}</a><a class="button" href="{}">Remove</a>',
                       obj.file.name,
                       obj.file.name,
                       reverse('admin:ocredfile-file-remove', args=[obj.pk])
                       )


filefield_to_listdisplay.short_description = "File"


def pdffield_to_listdisplay(obj):
    if not obj.ocred_pdf:
        return
    if 'store_pdf_disabled' in obj.ocred_pdf.name:
        return 'NO PDF'
    elif 'pdf_removed' in obj.ocred_pdf.name:
        return 'REMOVED'
    return format_html('<a href="/{}" target="_blank">{}</a><a class="button" href="{}">Remove</a>',
                       obj.ocred_pdf.name,
                       obj.ocred_pdf.name,
                       reverse('admin:ocredfile-ocred_pdf-remove', args=[obj.pk])
                       )


pdffield_to_listdisplay.short_description = "PDF"


def pdfinfo_to_listdisplay(obj):
    html = ''
    if obj.pdf_num_pages:
        html += '<div>nPages: '+str(obj.pdf_num_pages)+'</div>'
    if obj.pdf_author:
        html += '<div>Author: '+str(obj.pdf_author)+'</div>'
    if obj.pdf_creation_date:
        html += '<div>Created: '+str(obj.pdf_creation_date)+'</div>'
    if obj.pdf_creator:
        html += '<div>Creator: '+str(obj.pdf_creator)+'</div>'
    if obj.pdf_mod_date:
        html += '<div>Modified: '+str(obj.pdf_mod_date)+'</div>'
    if obj.pdf_producer:
        html += '<div>Producer: '+str(obj.pdf_producer)+'</div>'
    if obj.pdf_title:
        html += '<div>Title: '+str(obj.pdf_title)+'</div>'
    return format_html(html)


#def test_return():
#    return 'hello'


# Register your models here.
class OCRedFileAdmin(admin.ModelAdmin):

    actions = [delete_selected, remove_file_selected, remove_pdf_selected]
    list_display = ('md5', 'uploaded', 'ocred', filefield_to_listdisplay, pdffield_to_listdisplay, pdfinfo_to_listdisplay, 'ocred_pdf_md5')
    readonly_fields = ('uploaded', 'ocred', )
    fieldsets = (
        (None, {
            'fields': ('file', 'ocred_pdf')
        }),
        (None, {
            'fields': ('file_type', )
        }),
        (None, {
            'fields': (('md5', 'ocred_pdf_md5'), )
        }),
        (None, {
            'fields': (('uploaded', 'ocred',), 'pdf_info')
        }),
        (None, {
            'fields': ('text', )
        })
    )

    def process_file_remove(self, request, ocredfile_id, *args, **kwargs):
        print('OCRedFileAdmin->process_file_remove')
        try:
            ocredfile = OCRedFile.objects.get(pk=ocredfile_id)
            ocredfile.remove_file()
            self.message_user(request, 'File removed "'+ocredfile.file.name+'" ')
        except Exception as e:
            self.message_user(request, 'An error has occurred: '+str(e))
        return HttpResponseRedirect(reverse('admin:ocr_ocredfile_changelist'))

    def process_pdf_remove(self, request, ocredfile_id, *args, **kwargs):
        print('OCRedFileAdmin->process_pdf_remove')
        try:
            ocredfile = OCRedFile.objects.get(pk=ocredfile_id)
            ocredfile.remove_pdf()
            self.message_user(request, 'PDF removed "'+ocredfile.pdf.name+'" ')
        except Exception as e:
            self.message_user(request, 'An error has occurred: '+str(e))
        return HttpResponseRedirect(reverse('admin:ocr_ocredfile_changelist'))

    def get_urls(self):
        urls = super(OCRedFileAdmin, self).get_urls()
        custom_urls = [
            path(
                 '<int:ocredfile_id>/file_remove/',
                 self.admin_site.admin_view(self.process_file_remove),
                 name='ocredfile-file-remove',
                 ),
            path(
                '<int:ocredfile_id>/pdf_remove/',
                self.admin_site.admin_view(self.process_pdf_remove),
                name='ocredfile-ocred_pdf-remove',
            ),
        ]
        return custom_urls+urls

    def response_change(self, request, obj):
        if '_removefile' in request.POST:
            self.message_user(request, 'File removed')
            obj.remove_file()  # remove file from filesystem and rename filefield to 'file_removed'
            return HttpResponseRedirect('.')
        if '_removepdf' in request.POST:
            self.message_user(request, 'PDF removed')
            obj.remove_pdf()  # remove ocred_pdf from filesystem and rename filefield to 'pdf_removed'
            return HttpResponseRedirect('.')
        return super(OCRedFileAdmin, self).response_change(request, obj)

    def add_view(self, request, form_url='', extra_context=None):
        print("OCRedFileAdmin->add_view")
        self.form = OCRedFileAddForm
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['ocr_show_save_and_add_another'] = True
        extra_context['ocr_show_save_and_view'] = True
        return super(OCRedFileAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        print("OCRedFileAdmin->change_view")
        self.form = OCRedFileViewForm
        extra_context = extra_context or {}
        extra_context['show_save'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['ocr_show_save_and_add_another'] = False
        return super(OCRedFileAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        print("OCRedFileAdmin->save_model")
        return super(OCRedFileAdmin, self).save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        print("OCRedFileAdmin->delete_model")
        return super(OCRedFileAdmin, self).delete_model(request, obj)


admin.site.register(OCRedFile, OCRedFileAdmin)