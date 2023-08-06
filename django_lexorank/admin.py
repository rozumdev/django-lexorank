from django.contrib import admin


class RankedModelAdmin(admin.ModelAdmin):
    actions = ["rebalance_ranks"]

    @admin.action(description="Rebalance ranks")
    def rebalance_ranks(modeladmin, request, queryset):
        model = queryset.first().model

        if model.order_with_respect_to:
            queryset = queryset.distinct(model.order_with_respect_to)

            for obj in queryset:
                obj.rebalance()

        else:
            queryset.first().rebalance()
