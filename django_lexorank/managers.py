from django.db import models

from .lexorank import LexoRank


class RankedModelQuerySet(models.QuerySet):
    pass


class RankedModelManager(models.Manager.from_queryset(RankedModelQuerySet)):  # type: ignore[misc] # noqa: E501
    def add_to_top(self, **kwargs):
        """Adds a new object to the top of the list."""
        if self.model.order_with_respect_to:
            with_respect_to_kwargs = {
                self.model.order_with_respect_to: kwargs[
                    self.model.order_with_respect_to
                ]
            }
        else:
            with_respect_to_kwargs = {}

        qs = self.filter(**with_respect_to_kwargs).order_by("rank")

        objects_count = qs.count()
        first_obj = qs.first()

        rank = LexoRank.get_lexorank_in_between(
            previous_rank=None,
            next_rank=first_obj.rank if first_obj else None,
            objects_count=objects_count,
        )

        self.create(rank=rank, **kwargs)

    def add_to_bottom(self, **kwargs):
        """Adds a new object to the bottom of the list."""
        if self.model.order_with_respect_to:
            with_respect_to_kwargs = {
                self.model.order_with_respect_to: kwargs[
                    self.model.order_with_respect_to
                ]
            }
        else:
            with_respect_to_kwargs = {}

        qs = self.filter(**with_respect_to_kwargs).order_by("-rank")

        objects_count = qs.count()
        last_obj = qs.first()

        rank = LexoRank.get_lexorank_in_between(
            previous_rank=last_obj.rank if last_obj else None,
            next_rank=None,
            objects_count=objects_count,
        )

        self.create(rank=rank, **kwargs)
