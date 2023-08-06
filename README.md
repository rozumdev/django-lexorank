# django-lexorank

---

[![PyPI version](https://img.shields.io/pypi/v/django-lexorank.svg)](https://pypi.python.org/pypi/django-lexorank/)


This project implements an algorithm similar to JIRA's lexorank, but without using buckets for rebalancing.


## Installation

---

```shell
pip install django-lexorank
```


## Configuration

---

Add `django_lexorank` to `INSTALLED_APPS` in your Django settings:


## Usage

---

### Defining models

To add ranking to your model, you need to inherit it from `RankedModel`.

There are 2 ways of using `RankedModel`:

**Globally**

This way, all the objects will be ranked together in the global scope.

#### Example:

```python
from django_lexorank.models import RankedModel
from django.db import models


class Contributor(RankedModel):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
```

**Per group**

This way, instances of the model will be ranked separately per group.

To do that, you have to set a name of the foreign key to the group
to the `order_with_respect_to` parameter of the model.

#### Example:

```python
from django_lexorank.models import RankedModel
from django.db import models


class Repository(RankedModel):
    name = models.CharField(max_length=255)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    order_with_respect_to = "user"
```

### Field parameters

By default, new instances of the model will be ranked at the top of the list.
Rank field may accept boolean parameter `insert_to_bottom` to override this behaviour.

#### Example:

```python
from django_lexorank.models import RankedModel
from django_lexorank.fields import RankField
from django.db import models


class Contributor(RankedModel):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    rank = RankField(insert_to_bottom=True)
```


### Manager methods

There are 3 ways to insert models using manager methods:

`model.objects.create(**kwargs)` - will use the default behaviour specified on `RankField` definition.

`model.objects.add_to_bottom(**kwargs)` - will insert the model at the bottom of the list.

`model.objects.add_to_top(**kwargs)` - will insert the model at the top of the list.


### Instance methods

`obj.place_after(after_obj)` - places model instance after provided instance

`obj.place_before(before_obj)` - places model instance before provided instance

`obj.move_to_top()` - moves model instance to the bottom of the list

`obj.move_to_bottom()` - moves model instance to the bottom of the list

`obj.get_previous_object()` - return previous object in the list

`obj.get_next_object()` - return next object in the list

`obj.get_previous_object_rank()` - return previous object rank in the list

`obj.get_next_object_rank()` - return next object rank in the list

`obj.rebalance()` - rebalance the whole list or a group if `order_with_respect_to` is set


### Instance properties

`obj.rebalancing_required` - returns `True` if rebalancing is required for the whole list,
or for a group if `order_with_respect_to` is set

### Model methods

`model.get_first_object()` - return first object in the list

`model.get_last_object()` - return last object in the list

`model.get_first_object_rank()` - return first object rank in the list

`model.get_last_object_rank()` - return last object rank in the list

``
