from functools import cached_property
from typing import Optional

from django.contrib import admin
from django.db import models, transaction
from django.db.models import CharField
from django.db.models.functions import Length

from .fields import RankField
from .lexorank import LexoRank
from .managers import RankedModelManager

CharField.register_lookup(Length, "length")


class RankedModel(models.Model):
    objects = RankedModelManager()

    rank = RankField()
    order_with_respect_to = None

    class Meta:
        abstract = True
        ordering = ["rank"]

    @cached_property
    def model(self):
        return self._meta.model

    @property
    def with_respect_to_kwargs(self):
        if not self.order_with_respect_to:
            return {}

        return {self.order_with_respect_to: getattr(self, self.order_with_respect_to)}

    @property
    def objects_count(self):
        return self.model.objects.filter(**self.with_respect_to_kwargs).count()

    def move_after(self, after_obj: "RankedModel") -> "RankedModel":
        """Place object after selected one."""
        previous_rank = after_obj.rank
        next_rank = after_obj.get_next_object_rank()

        middle_rank = LexoRank.get_lexorank_in_between(
            previous_rank=previous_rank,
            next_rank=next_rank,
            objects_count=self.objects_count,
        )

        self.rank = middle_rank  # type: ignore[assignment]
        self.save(update_fields=["rank"])

        return self

    def move_before(self, before_obj: "RankedModel") -> "RankedModel":
        """Place object before selected one."""
        next_rank = before_obj.rank
        previous_rank = before_obj.get_previous_object_rank()

        middle_rank = LexoRank.get_lexorank_in_between(
            previous_rank=previous_rank,
            next_rank=next_rank,
            objects_count=self.objects_count,
        )

        self.rank = middle_rank  # type: ignore[assignment]
        self.save(update_fields=["rank"])

        return self

    @classmethod
    def get_first_object(cls, with_respect_to_kwargs: dict) -> Optional["RankedModel"]:
        """Return the first object if exists.."""
        return cls.objects.filter(**with_respect_to_kwargs).order_by("rank").first()

    @classmethod
    def get_first_object_rank(cls, with_respect_to_kwargs: dict) -> Optional[str]:
        """Return the rank of the first object or None if no objects exist."""
        first_object = cls.get_first_object(
            with_respect_to_kwargs=with_respect_to_kwargs
        )
        return first_object.rank if first_object else None

    def get_previous_object(self) -> Optional["RankedModel"]:
        """
        Return object that precedes provided object,
        or None if provided object is the first.
        """
        return (
            self.model.objects.filter(rank__lt=self.rank, **self.with_respect_to_kwargs)
            .order_by("-rank")
            .first()
        )

    def get_previous_object_rank(self) -> Optional[str]:
        """
        Return object rank that precedes provided object,
        or None if provided object is the first.
        """
        previous_object = self.get_previous_object()
        return previous_object.rank if previous_object else None

    def get_next_object(self) -> Optional["RankedModel"]:
        """
        Return object that follows provided object,
        or None if provided object is the last.
        """
        return (
            self.model.objects.filter(rank__gt=self.rank, **self.with_respect_to_kwargs)
            .order_by("rank")
            .first()
        )

    def get_next_object_rank(self) -> Optional[str]:
        """
        Return object rank that follows provided object,
        or None if provided object is the last.
        """
        next_object = self.get_next_object()
        return next_object.rank if next_object else None

    @classmethod
    def get_last_object(cls, with_respect_to_kwargs: dict) -> Optional["RankedModel"]:
        """Return the last object if exists."""
        return cls.objects.filter(**with_respect_to_kwargs).order_by("-rank").first()

    @classmethod
    def get_last_object_rank(cls, with_respect_to_kwargs: dict) -> Optional[str]:
        """Return the rank of the last object or None if no objects exist."""
        last_object = cls.get_last_object(with_respect_to_kwargs=with_respect_to_kwargs)
        return last_object.rank if last_object else None

    @admin.display(boolean=True)
    def rebalancing_required(self) -> bool:
        """
        Return `True` if any object has rank length greater than 128, `False` otherwise.
        """
        return self.model.objects.filter(
            rank__length__gte=LexoRank.rebalancing_length, **self.with_respect_to_kwargs
        ).exists()

    @transaction.atomic
    def rebalance(self) -> "RankedModel":
        """Rebalance ranks of all objects."""
        qs = (
            self.model.objects.filter(**self.with_respect_to_kwargs)
            .order_by("rank")
            .select_for_update()
        )

        objects_to_update = []

        rank = LexoRank.get_min_rank(
            objects_count=self.objects_count,
        )
        for obj in qs:
            rank = LexoRank.increment_rank(
                rank=rank,
                objects_count=self.objects_count,
            )
            obj.rank = rank
            objects_to_update.append(obj)

        self.model.objects.bulk_update(objects_to_update, ["rank"])

        self.refresh_from_db()

        return self
