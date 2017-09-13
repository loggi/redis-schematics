# encoding: utf8

"""
Redis is and Python are an awesome combination. And they deserve the right
amount of abstraction both can provide. Not more and not less. The objective
here is not to provide an ORM-like interface for redis because redis is not
a relational database.
"""

from __future__ import absolute_import

import uuid
import json

from schematics import models, types
from redis_schematics.exceptions import (
    NotFound,
    MultipleFound,
    StrictPerformanceException
)
from redis_schematics.utils import (
    group_filters_by_suffix,
    match_filters
)


class BaseRedisMixin(object):
    """
    Base mixin to add Redis persistance to schematics models.
    """

    __redis_client__ = None
    """Redis client to be used by this mixin."""

    __expire__ = None
    """Object expire time in seconds. Default(None) is no expire."""

    __unique_args__ = None
    __strict_performance__ = False

    @property
    def __prefix__(self):
        """Prefix used on for this object keys on the redis database."""
        return self.__class__.__name__

    @staticmethod
    def __serializer__(obj):
        """Method used to serialize to string prior to dumping complex objects."""
        return json.dumps(obj)

    @staticmethod
    def __deserializer__(dump):
        """Method used to deserialize to string prior to loading complex objects."""
        return json.loads(dump.decode("utf-8"))

    @property
    def key(self):
        """Key for the object on the redis database."""
        return self.__key_pattern__(self.__primary_key__)

    @property
    def __primary_key__(self):
        """Callable that returns an unique identifier for an object on a
        given namespace. By default it uses pk, id and __unique_args__."""
        if getattr(self, 'pk', None):
            return self.pk

        if getattr(self, 'id', None):
            return self.id

        if self.__unique_args__:
            return '.'.join([getattr(self, const) for const in self.__unique_args__])

    def __key_pattern__(self, *args):
        """Pattern used to build a key or a query for a given object."""
        namespace = []

        if self.__prefix__:
            namespace.append(self.__prefix__)

        if args:
            namespace += list(args)

        return ":".join(namespace)


class SimpleRedisMixin(BaseRedisMixin):
    """
    Add Redis persistance to an object using a simple approach. Each object
    correnspond to a single key on redis prefixed with the object namespace,
    which correnponds to a serialized object. To use this mixin you just need
    to declare a primary key such as:

    ..code::python
        pk = types.StringType()

    You may use this Mixin when you have frequent get on primary key operations
    and set operations, hard memory contraints or wants a single key approach.
    You may not use this Mixin if you need performance on filter and get on
    non primary key operations.
    """

    @classmethod
    def match(cls, **kwargs):
        """
        Gets an element from storage matching any arguments.
        Returns an instance if only one object is found.

        Args:
            **kwargs: filter attributes matching the object to search.

        Returns:
            (SimpleRedisMixin): Schema object instance.

        Raises:
            (NotFound): Object matching query does not exist.
            (MultipleFound): Multiple objects matching query found.
            (StrictPerformanceException): Low performance query not allowed by the
                current configuration.

        Perfomance:
            On primary key: O(1)
            On non-primary fields: O(n*k) where n is the number of elements in the
                set and k is the is the number of kwargs.
        """

        schema = cls().import_data(kwargs)

        if schema.__primary_key__:
            return cls.match_for_pk(schema.__primary_key__)

        return cls.match_for_values(**kwargs)

    @classmethod
    def match_for_pk(cls, pk):
        """
        Gets an element from storage using its primary key. Returns an instance if
        an object is found.

        Args:
            pk(str): object primary key.

        Returns:
            (SimpleRedisMixin): Schema object instance.

        Raises:
            (NotFound): Object matching query does not exist.

        Perfomance: O(1)
        """
        schema = cls({'pk': pk})
        result = cls.__redis_client__.get(schema.key)

        if result is None:
            raise NotFound()

        obj = schema.__deserializer__(result)
        return schema.import_data(obj)

    @classmethod
    def match_for_values(cls, **kwargs):
        """
        Gets an element from storage matching value arguments.
        Returns an instance if only one object is found.

        Args:
            **kwargs: filter attributes matching the object to search.

        Returns:
            (SimpleRedisMixin): Schema object instance.

        Raises:
            (NotFound): Object matching query does not exist.
            (MultipleFound): Multiple objects matching query found.
            (StrictPerformanceException): Low performance query not allowed by the
                current configuration.

        Perfomance: O(n*k) where n is the number of elements in the
            set and k is the is the number of kwargs.
        """

        query = cls.filter(**kwargs)

        if len(query) == 0:
            raise NotFound()

        elif len(query) > 1:
            raise MultipleFound()

        return query[0]

    @classmethod
    def all(cls):
        """
        Gets all elements from storage.

        Returns:
            List(SimpleRedisMixin): Schema object instances.

        Perfomance: O(n) where n is the number of elements.
        """
        _, keys = cls.__redis_client__.scan(0, cls().__key_pattern__("*"))
        results = cls.__redis_client__.mget(*keys)
        return [cls().import_data(cls.__deserializer__(r)) for r in results]

    @classmethod
    def filter(cls, **kwargs):
        """
        Gets all elements from storage matching value arguments.
        Returns an instance if only one object is found.

        Args:
            **kwargs: filter attributes matching objects to search.

        Returns:
            List(SimpleRedisMixin): Schema object instances.

        Raises:
            (StrictPerformanceException): Low performance query not allowed by the
                current configuration.

        Perfomance: O(n*k) where n is the number of elements in the
            set and k is the is the number of kwargs.
        """
        if cls.__strict_performance__:
            raise StrictPerformanceException()

        filter_group = group_filters_by_suffix(kwargs)
        return [r for r in cls.all() if match_filters(r, filter_group)]

    def set(self):
        """
        Sets the element on storage.

        Perfomance: O(1)
        """
        self.pk = self.__primary_key__ or str(uuid.uuid4)

        self.__redis_client__.set(
            self.key,
            self.__serializer__(self.to_primitive()),
            self.__expire__
        )

    def refresh(self):
        """
        Updates current object from storage.

        Raises:
            (NotFound): Object was deleted meanwhile.

        Perfomance: O(1)
        """
        result = self.__redis_client__.get(self.key)

        if result is None:
            raise NotFound()

        self.import_data(self.__deserializer__(result))

    def delete(self):
        """
        Deletes the element from storage.

        Perfomance: O(1)
        """
        self.__redis_client__.delete(self.key)


class SimpleRedisModel(models.Model, SimpleRedisMixin):
    """Shortcut to a Model using SimpleRedisMixin."""

    pk = types.StringType()
