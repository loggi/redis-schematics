Redis Schematics
================

*Provides Redis persistence to Schematics models with cutomizable abstraction levels.*


Installing
----------

Using pip::

    pip install redis_schamatics


Quickstart
----------

*Currently we only support a SimpleRedisMixin.*


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

.. code-block:: python

    class MyVolatileModel(models.Model, SimpleRedisMixin):
        __expire__ = 3600  # model expire (in seconds)
        pk = types.StringType()

    vanilla.delete()


Roadmap
-------

- [ ] Support a distributed Mixin with one key per field.
- [ ] Consistent set of unit tests.
- [ ] Support redis relationships between models.
- [ ] Support transaction aware methods.
