Redis Schematics
================

*Provides Redis persistence to Schematics models with cutomizable abstraction levels.*


Installing
----------

Using pip::

    pip install redis_schamatics


Understanding Persistence layers
--------------------------------

There are several ways to implement complex objects persitence on a key-value-set
database such as redis. The best way to do it depends on your application constraints.
We think that providing a good abstraction for your application is to allow you
to choose which abstraction you want to use. Below you can find a comparison on different
provided abstraction layers.

*Currently we only support a SimpleRedisMixin and SimpleRedisModel, but you can
use BaseRedisMixin to build your own persistance layers.*


**SimpleRedisMixin**

Add Redis persistance to an object using a simple approach. Each object
correnspond to a single key on redis prefixed with the object namespace,
which correnponds to a serialized object. To use this mixin you just need
to declare a primary key such as:

You may use this Mixin when you have frequent match on primary key and set
operations, unique expires, hard memory contraints or just wants a 1-1 object-key
approach. You may not use this Mixin if you need performance on filter, all
and get on non primary key operations.

**HashRedisMixin**

Add Redis persistance to an object using a single hash approach. Each type
correnspond to a single key on redis containing a hash set with every instance
as an entry on the set which contains a serialized object.

You may use this Mixin when you have frequent match on primary key, set and
all operations, hard memory contraints or wants a single key approach.
You may not use this Mixin if you need performance on filter and get on
non primary key operations.


Quickstart
----------

**Creating models with persistence**

Note: you should include a pk, but don't bother setting it's value manually.
We can infer it from an ``id`` field or by setting a tuple of field names using
``__unique_together__``.


.. code-block:: python

    from datetime import datetime, timedelta

    from redis import StrictRedis
    from redis_schematics import SimpleRedisMixin
    from schematics import models, types


    class IceCreamModel(models.Model, SimpleRedisMixin):
        pk = types.StringType()  # Just include a pk
        id = types.StringType()
        flavour = types.StringType()
        amount_kg = types.IntType()
        best_before = types.DateTimeType()


**Setting on Redis**

Saving is simple as ``set()``.

.. code-block:: python

    vanilla = IceCreamModel(dict(
        id='vanilla',
        flavour='Sweet Vanilla',
        amount_kg=42,
        best_before=datetime.now() + timedelta(days=2),
    ))

   chocolate = IceCreamModel(dict(
        id='chocolate',
        flavour='Delicious Chocolate',
        amount_kg=12,
        best_before=datetime.now() + timedelta(days=3),
    ))

    vanilla.set()
    chocolate.set()

**Getting from Redis**

There are two basic ways to get an element from Redis: by pk or by value.
You can use the classmethods ``match_for_pk(pk)`` or ``match_for_values(**Kwargs)``
or just simply ``match(**kwargs)`` to let us choose which one. Notice that the
performance from both methods is a lot different, so you may avoid matching
for values on high performance environments. You may also use refresh to reload
an object from storage if it has been modified.

.. code-block:: python

    IceCreamModel.match_for_pk('vanilla')
    IceCreamModel.match_for_values(amount__gte=30)

    IceCreamModel.match(id='vanilla')  # match on pk
    IceCreamModel.match(best_before__gte=datetime.now())  # match on values

    vanilla.refresh()


**Fetching all and filtering**

You can also use ``all()`` to deserialize all and filters. Notice that
this invlolves deserializing all stored objects.

.. code-block:: python

    IceCreamModel.all()
    IceCreamModel.filter(amount__gte=30)


**Deleting and expiring**

To remove objects, you can set ``__expire__`` or use the ``delete()`` method.
Notice that expires work differently on single key and multiple keys approaches.

.. code-block:: python

    class MyVolatileModel(models.Model, SimpleRedisMixin):
        __expire__ = 3600  # model expire (in seconds)
        pk = types.StringType()

    vanilla.delete()


Roadmap
-------

- Support a distributed Mixin with one key per field.
- Support a distributed Hash Mixin with one hash per field.
- Consistent set of unit tests.
- Support redis relationships between models.
- Support transaction aware methods.
