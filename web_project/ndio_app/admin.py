from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from ndio_app.models import (
    UserDetail,
    AgentProfile,
    ManagerProfile,
    Order,
    Payment,
    FAQ,
    ServicesContact,
    UserSubscription,
    FibreProduct,
    NetworkProvider,
    Communication,
)

# Register your models here.
admin.site.register(UserDetail)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(FAQ)
admin.site.register(ServicesContact)
admin.site.register(UserSubscription)
admin.site.register(FibreProduct)
admin.site.register(NetworkProvider)
admin.site.register(Communication)


class AgentProfileAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        agent_group, _ = Group.objects.get_or_create(name="agent")
        obj.user.groups.clear()  # Remove other groups if needed
        obj.user.groups.add(agent_group)


class ManagerProfileAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if request.user.is_superuser:
            super().save_model(request, obj, form, change)
            manager_group, _ = Group.objects.get_or_create(name="manager")
            obj.user.groups.clear()
            obj.user.groups.add(manager_group)

        else:
            # Prevent non-superusers from adding managers
            raise PermissionDenied("Only superadmins can add managers.")


admin.site.register(AgentProfile, AgentProfileAdmin)
admin.site.register(ManagerProfile, ManagerProfileAdmin)
