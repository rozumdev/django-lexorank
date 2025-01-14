from functools import cached_property
from typing import Optional, Type

from django.contrib import admin
from django.db import models, transaction
from django.db.models import CharField
from django.db.models.functions import Length
from django.forms.models import model_to_dict

from ..fields import RankField
from ..lexorank import LexoRank
from ..managers import RankedModelManager
from .scheduled_rebalancing import ScheduledRebalancing

CharField.register_lookup(Length, "length")


class RankedModel(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial_values = model_to_dict(self)

    objects = RankedModelManager()

    rank = RankField()
    order_with_respect_to: Optional[str] = None

    class Meta:
        abstract = True
        ordering = ["rank"]

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._state.adding = False
        instance._state.db = db
        instance._initial_values = dict(zip(field_names, values))
        return instance

    def field_value_has_changed(self, field: str) -> bool:
        if not self.pk or not self.__initial_values:
            return False

        current_value = getattr(self, field)
        initial_value = self.__initial_values[field]

        if isinstance(current_value, models.Model):
            current_value = current_value.pk

        return current_value != initial_value

    @transaction.atomic
    def save(self, *args, **kwargs) -> None:
        if self.order_with_respect_to:
            if self.field_value_has_changed(self.order_with_respect_to):
                self.rank = None  # type: ignore[assignment]

        super().save(*args, **kwargs)

        if self.rebalancing_required():
            self.schedule_rebalancing()

    @cached_property
    def _model(self) -> Type[models.Model]:
        return self._meta.model

    @property
    def _with_respect_to_kwargs(self) -> dict:
        if not self.order_with_respect_to:
            return {}

        return {self.order_with_respect_to: getattr(self, self.order_with_respect_to)}

    @property
    def _with_respect_to_value(self) -> str:
        if self.order_with_respect_to:
            return getattr(self, self.order_with_respect_to).pk

        return ""

    @property
    def _objects_count(self):
        return self._model.objects.filter(**self._with_respect_to_kwargs).count()

    def _move_to(self, rank: str) -> "RankedModel":
        self.rank = rank  # type: ignore[assignment]
        self.save(update_fields=["rank"])
        return self

    def place_on_top(self) -> "RankedModel":
        """Place object at the top of the list."""
        first_object_rank = self.get_first_object_rank(
            with_respect_to_kwargs=self._with_respect_to_kwargs
        )

        rank = LexoRank.get_lexorank_in_between(  # type: ignore[assignment]
            previous_rank=None,
            next_rank=first_object_rank,
            objects_count=self._objects_count,
        )

        return self._move_to(rank)

    def place_on_bottom(self) -> "RankedModel":
        """Place object at the bottom of the list."""
        last_object_rank = self.get_last_object_rank(
            with_respect_to_kwargs=self._with_respect_to_kwargs
        )

        rank = LexoRank.get_lexorank_in_between(  # type: ignore[assignment]
            previous_rank=last_object_rank,
            next_rank=None,
            objects_count=self._objects_count,
        )

        return self._move_to(rank)

    def place_after(self, after_obj: "RankedModel") -> "RankedModel":
        """Place object after selected one."""
        previous_rank = after_obj.rank
        next_rank = after_obj.get_next_object_rank()

        rank = LexoRank.get_lexorank_in_between(
            previous_rank=previous_rank,
            next_rank=next_rank,
            objects_count=self._objects_count,
        )

        return self._move_to(rank)

    def place_before(self, before_obj: "RankedModel") -> "RankedModel":
        """Place object before selected one."""
        next_rank = before_obj.rank
        previous_rank = before_obj.get_previous_object_rank()

        rank = LexoRank.get_lexorank_in_between(
            previous_rank=previous_rank,
            next_rank=next_rank,
            objects_count=self._objects_count,
        )

        return self._move_to(rank)

    def get_previous_object(self) -> Optional["RankedModel"]:
        """
        Return object that precedes provided object,
        or None if provided object is the first.
        """
        return (
            self._model.objects.filter(
                rank__lt=self.rank, **self._with_respect_to_kwargs
            )
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
            self._model.objects.filter(
                rank__gt=self.rank, **self._with_respect_to_kwargs
            )
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

    @transaction.atomic
    def rebalance(self) -> "RankedModel":
        """Rebalance ranks of all objects."""
        qs = (
            self._model.objects.filter(**self._with_respect_to_kwargs)
            .order_by("rank")
            .select_for_update()
        )

        objects_to_update = []

        rank = LexoRank.get_min_rank(
            objects_count=self._objects_count,
        )
        for obj in qs:
            rank = LexoRank.increment_rank(
                rank=rank,
                objects_count=self._objects_count,
            )
            obj.rank = rank
            objects_to_update.append(obj)

        self._model.objects.bulk_update(objects_to_update, ["rank"])

        self.refresh_from_db()

        return self

    @admin.display(boolean=True)
    def rebalancing_required(self) -> bool:
        """
        Return `True` if any object has rank length greater than 128, `False` otherwise.
        """
        return self._model.objects.filter(
            rank__length__gte=LexoRank.rebalancing_length,
            **self._with_respect_to_kwargs
        ).exists()

    @admin.display(boolean=True)
    def rebalancing_scheduled(self) -> bool:
        """
        Return `True` if rebalancing was scheduled for a list that includes that object,
        `False` otherwise.
        """
        return ScheduledRebalancing.objects.filter(
            model=self._meta.model_name,
            with_respect_to=self._with_respect_to_value,
        ).exists()

    @classmethod
    def get_first_object(cls, with_respect_to_kwargs: dict) -> Optional["RankedModel"]:
        """Return the first object if exists.."""
        if cls.order_with_respect_to and not with_respect_to_kwargs:
            raise ValueError("with_respect_to_kwargs must be provided")

        return cls.objects.filter(**with_respect_to_kwargs).order_by("rank").first()

    @classmethod
    def get_first_object_rank(cls, with_respect_to_kwargs: dict) -> Optional[str]:
        """Return the rank of the first object or None if no objects exist."""
        if cls.order_with_respect_to and not with_respect_to_kwargs:
            raise ValueError("with_respect_to_kwargs must be provided")

        first_object = cls.get_first_object(
            with_respect_to_kwargs=with_respect_to_kwargs
        )
        return first_object.rank if first_object else None

    @classmethod
    def get_last_object(cls, with_respect_to_kwargs: dict) -> Optional["RankedModel"]:
        """Return the last object if exists."""
        if cls.order_with_respect_to and not with_respect_to_kwargs:
            raise ValueError("with_respect_to_kwargs must be provided")

        return cls.objects.filter(**with_respect_to_kwargs).order_by("-rank").first()

    @classmethod
    def get_last_object_rank(cls, with_respect_to_kwargs: dict) -> Optional[str]:
        """Return the rank of the last object or None if no objects exist."""
        if cls.order_with_respect_to and not with_respect_to_kwargs:
            raise ValueError("with_respect_to_kwargs must be provided")

        last_object = cls.get_last_object(with_respect_to_kwargs=with_respect_to_kwargs)
        return last_object.rank if last_object else None

    def schedule_rebalancing(self):
        ScheduledRebalancing.objects.update_or_create(
            model=self._meta.model_name,
            with_respect_to=self._with_respect_to_value,
        )
