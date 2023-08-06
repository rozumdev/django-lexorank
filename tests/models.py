from django.db import models

from django_lexorank.fields import RankField
from django_lexorank.models import RankedModel


class Team(RankedModel):
    name = models.CharField(max_length=255)


class User(RankedModel):
    name = models.CharField(max_length=255)
    rank = RankField(insert_to_bottom=True)

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="users")
    order_with_respect_to = "team"


class Board(RankedModel):
    name = models.CharField(max_length=255)


class Task(RankedModel):
    name = models.CharField(max_length=255)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    order_with_respect_to = "board"

    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tasks"
    )
