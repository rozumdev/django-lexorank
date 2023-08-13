from django.contrib import admin

from ..models.scheduled_rebalancing import ScheduledRebalancing


@admin.register(ScheduledRebalancing)
class ScheduledRebalancingAdmin(admin.ModelAdmin):
    list_display = ["id", "model", "with_respect_to", "scheduled_at"]
