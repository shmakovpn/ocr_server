from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.contrib.admin.actions import delete_selected as delete_selected_
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


# Register your models here.
class OCRedFileAdmin(admin.ModelAdmin):

    actions = [delete_selected]
    list_display_links = None
    form = OCRedFileForm

    def save_model(self, request, obj, form, change):
        print("OCRedFileAdmin->save_model")
        super(OCRedFileAdmin, self).save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        print("OCRedFileAdmin->delete_model")
        super(OCRedFileAdmin, self).delete_model(request, obj)


admin.site.register(OCRedFile, OCRedFileAdmin)