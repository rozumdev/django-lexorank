from django.db import models

from .lexorank import LexoRank


class RankField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 255)
        kwargs.setdefault("default_rank_length", 6)

        self.default_rank_length = kwargs.pop("default_rank_length")

        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        current_rank = super().pre_save(model_instance, add)

        if not current_rank:
            with_respect_to_field = getattr(model_instance, "order_with_respect_to")
            with_respect_to_value = getattr(model_instance, with_respect_to_field)
            next_rank = type(model_instance).get_first_object_rank(
                with_respect_to_kwargs={with_respect_to_field: with_respect_to_value}
            )
            objects_count = type(model_instance).objects.count()
            current_rank = LexoRank.get_lexorank_in_between(
                previous_rank=None,
                next_rank=next_rank,
                objects_count=objects_count,
                default_rank_length=self.default_rank_length,
            )
            model_instance.rank = current_rank

        return current_rank
