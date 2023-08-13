from django.db import models


class ScheduledRebalancing(models.Model):
    model = models.CharField(max_length=255)
    with_respect_to = models.CharField(
        default="", max_length=255, blank=True, help_text="PK of the respected object."
    )
    scheduled_at = models.DateTimeField(auto_now_add=True)
