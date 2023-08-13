# django-lexorank

[![Test workflow](https://github.com/rozumdev/django-lexorank/actions/workflows/tests.yml/badge.svg)](https://github.com/rozumdev/django-lexorank/actions/workflows/test.yml/)
[![PyPI version](https://img.shields.io/pypi/v/django-lexorank.svg)](https://pypi.org/project/django-lexorank/)
[![PyPI downloads](https://img.shields.io/pypi/dm/django-lexorank.svg)](https://pypistats.org/packages/django-lexorank)
[![License](https://img.shields.io/pypi/l/django-lexorank.svg)](https://en.wikipedia.org/wiki/MIT_License)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/django-lexorank.svg)](https://pypi.org/project/django-lexorank/)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This package implements an algorithm similar to JIRA's lexorank, but without using buckets for rebalancing
that can be used with Django projects.


## Installation


```shell
pip install django-lexorank
```


## Configuration

Add `django_lexorank` to your `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = [
    ...
    "django_lexorank",
]
```


## Usage


### Defining models

To add ranking to your model, you need to inherit it from `RankedModel`.

There are 2 ways of using `RankedModel`:

#### Globally

This way, all the objects will be ranked together in the global scope.

**Example:**

```python
from django_lexorank.models import RankedModel
from django.db import models


class Board(RankedModel):
    name = models.CharField(max_length=255)
```

#### Per group

This way, instances of the model will be ranked separately per group.

To do that, you have to set a name of the foreign key to the group
to the `order_with_respect_to` parameter of the model.

**Example:**

```python
from django_lexorank.models import RankedModel
from django.db import models


class Task(RankedModel):
    name = models.CharField(max_length=255)
    board = models.ForeignKey("Board", on_delete=models.CASCADE, related_name="tasks")
    order_with_respect_to = "board"
```

### Field parameters

By default, new instances of the model will be ranked at the top of the list.
Rank field may accept boolean parameter `insert_to_bottom` to override this behaviour.

**Example:**

```python
from django_lexorank.models import RankedModel
from django_lexorank.fields import RankField
from django.db import models


class User(RankedModel):
    name = models.CharField(max_length=255)
    rank = RankField(insert_to_bottom=True)
```


### Manager methods

There are 3 ways to insert models using manager methods:

`model.objects.create(**kwargs)` - will use the default behaviour specified on `RankField` definition.

`model.objects.add_to_bottom(**kwargs)` - will insert the model at the bottom of the list.

`model.objects.add_to_top(**kwargs)` - will insert the model at the top of the list.


### Instance methods

`obj.place_after(after_obj)` - places model instance after provided instance.
If rank length exceeds the limit after the move, rebalancing will be scheduled.

`obj.place_before(before_obj)` - places model instance before provided instance.
If rank length exceeds the limit after the move, rebalancing will be scheduled.

`obj.place_on_top()` - moves model instance to the bottom of the list.
If rank length exceeds the limit after the move, rebalancing will be scheduled.

`obj.place_on_bottom()` - moves model instance to the bottom of the list.
If rank length exceeds the limit after the move, rebalancing will be scheduled.

`obj.get_previous_object()` - return previous object in the list

`obj.get_next_object()` - return next object in the list

`obj.get_previous_object_rank()` - return previous object rank in the list

`obj.get_next_object_rank()` - return next object rank in the list

`obj.schedule_rebalancing()` - schedule rebalancing  for the whole list or a group if `order_with_respect_to` is set

`obj.rebalance()` - rebalance the whole list or a group if `order_with_respect_to` is set

`obj.rebalancing_required()` - returns `True` if rebalancing is required for the whole list,
or for a group if `order_with_respect_to` is set

`obj.rebalancing_scheduled()` - returns `True` if rebalancing is scheduled for the whole list,
or for a group if `order_with_respect_to` is set

### Model methods

`model.get_first_object()` - return first object in the list

`model.get_last_object()` - return last object in the list

`model.get_first_object_rank()` - return first object rank in the list

`model.get_last_object_rank()` - return last object rank in the list


### Rebalancing Schedule

Each time, a rank length exceeds the limit, rebalancing is scheduled for the whole list or a group,
according to the value of `order_with_respect_to` parameter.

`SheduledRebalancing` model can be used to create a task for rebalancing ranks.
