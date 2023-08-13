from django.db import models

from .lexorank import LexoRank


class RankedModelQuerySet(models.QuerySet):
    pass


class RankedModelManager(models.Manager.from_queryset(RankedModelQuerySet)):  # type: ignore[misc] # noqa: E501
    def _add(self, ordering: str, **kwargs):
        if self.model.order_with_respect_to:
            with_respect_to_kwargs = {
                self.model.order_with_respect_to: kwargs[
                    self.model.order_with_respect_to
                ]
            }
        else:
            with_respect_to_kwargs = {}

        qs = self.filter(**with_respect_to_kwargs).order_by(f"{ordering}rank")

        objects_count = qs.count()
        first_obj = qs.first()

        new_rank_field = "previous_rank" if ordering == "-" else "next_rank"
        existing_rank_field = "next_rank" if ordering == "-" else "previous_rank"

        rank = LexoRank.get_lexorank_in_between(
            **{  # type: ignore[arg-type]
                existing_rank_field: None,
                new_rank_field: first_obj.rank if first_obj else None,
            },
            objects_count=objects_count,
        )

        return self.create(rank=rank, **kwargs)

    def add_to_top(self, **kwargs):
        """Adds a new object to the top of the list."""
        ordering = ""
        return self._add(ordering, **kwargs)

    def add_to_bottom(self, **kwargs):
        """Adds a new object to the bottom of the list."""
        ordering = "-"
        return self._add(ordering, **kwargs)
