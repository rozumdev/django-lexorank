from django.db import models

from .lexorank import LexoRank


class RankField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 255)
        kwargs.setdefault("insert_to_bottom", False)
        kwargs.setdefault("db_index", True)
        kwargs.setdefault("editable", False)

        self.insert_to_bottom = kwargs.pop("insert_to_bottom")
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        current_rank = super().pre_save(model_instance, add)

        if not current_rank:
            model = model_instance._meta.model

            if model.order_with_respect_to:
                with_respect_to_kwargs = {
                    model.order_with_respect_to: getattr(
                        model_instance, model.order_with_respect_to
                    )
                }
            else:
                with_respect_to_kwargs = {}

            if self.insert_to_bottom:
                previous_rank = model.get_last_object_rank(
                    with_respect_to_kwargs=with_respect_to_kwargs
                )
                kwargs = {
                    "previous_rank": previous_rank,
                    "next_rank": None,
                }
            else:
                next_rank = model.get_first_object_rank(
                    with_respect_to_kwargs=with_respect_to_kwargs
                )
                kwargs = {
                    "previous_rank": None,
                    "next_rank": next_rank,
                }

            objects_count = model.objects.count()

            current_rank = LexoRank.get_lexorank_in_between(
                objects_count=objects_count,
                **kwargs,
            )

            model_instance.rank = current_rank

        return current_rank
