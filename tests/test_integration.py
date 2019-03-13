# encoding: utf8

from __future__ import absolute_import

import json
from datetime import datetime
from unittest import TestCase

from redis import StrictRedis
from schematics import types, models

from redis_schematics import HashRedisMixin, SimpleRedisMixin
from redis_schematics.exceptions import NotFound


client = StrictRedis(host="localhost", port=6379, db=4)


class TestModel(models.Model):
    __redis_client__ = client
    __expire__ = 120

    pk = types.StringType()
    id = types.IntType(required=True)
    name = types.StringType()
    created = types.DateTimeType()
    good_number = types.IntType()


class BaseModelStorageTest(object):
    @property
    def raw_value(self):
        raise NotImplementedError()

    @property
    def stored(self):
        raise NotImplementedError()

    def test_set(self):
        assert self.stored == self.schema.to_primitive()

    def test_match(self):
        result = self.TestModel.match(id=123)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(pk="123")
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number=42)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__lt=43)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__gt=41)
        assert self.stored == result.to_primitive()

    def test_match_on_non_existing(self):
        self.assertRaises(NotFound, self.TestModel.match, id=321)
        self.assertRaises(NotFound, self.TestModel.match, pk="321")
        self.assertRaises(NotFound, self.TestModel.match, good_number__gt=42)
        self.assertRaises(NotFound, self.TestModel.match, good_number__lt=42)

    def test_match_for_pk(self):
        result = self.TestModel.match_for_pk("123")
        assert self.stored == result.to_primitive()

    def test_match_for_values(self):
        result = self.TestModel.match_for_values(name="Bar")
        assert self.stored == result.to_primitive()

    def test_all(self):
        result = self.TestModel.all()
        assert self.stored == result[0].to_primitive()

    def test_all_on_non_existing(self):
        self.schema.delete()
        result = self.TestModel.all()
        assert result == []

    def test_filter(self):
        result = self.TestModel.filter(good_number__lt=43)
        assert self.stored == result[0].to_primitive()
        result = self.TestModel.filter(good_number__lt=42)
        assert result == []

    def test_delete(self):
        self.schema.delete()
        assert self.raw_value is None

    def test_delete_all(self):
        assert self.TestModel.delete_all() == 1
        assert self.raw_value is None

    def test_delete_all_on_non_existing(self):
        self.schema.delete()
        assert self.TestModel.delete_all() == 0
        assert self.raw_value is None

    def test_delete_filter(self):
        assert self.TestModel.delete_filter(name="Bla") == 0
        assert self.raw_value
        assert self.TestModel.delete_filter(name="Bar") == 1
        assert self.raw_value is None

    def test_delete_filter_on_non_existing(self):
        self.schema.delete()
        assert self.TestModel.delete_filter() == 0
        assert self.raw_value is None

    def test_json_serialization(self):
        from redis_schematics.patches import patch_json

        patch_json()
        data = self.TestModel.all()
        data_json = json.dumps(data)
        expected = json.dumps([x.to_primitive() for x in data])
        assert data_json == expected

    def tearDown(self):
        client.delete("TestSimpleModel:123")


class SimpleModelStorageTest(BaseModelStorageTest, TestCase):
    class TestSimpleModel(TestModel, SimpleRedisMixin):
        pass

    def setUp(self):
        self.TestModel = self.TestSimpleModel
        self.schema = self.TestModel(
            {"id": 123, "name": "Bar", "created": datetime.now(), "good_number": 42}
        )
        self.schema.set()

    def tearDown(self):
        client.delete("TestSimpleModel:123")

    @property
    def raw_value(self):
        return client.get("TestSimpleModel:123")

    @property
    def stored(self):
        return json.loads(self.raw_value.decode("utf-8"))


class HashModelStorageTest(BaseModelStorageTest, TestCase):
    class TestHashModel(TestModel, HashRedisMixin):
        pass

    def setUp(self):
        self.TestModel = self.TestHashModel
        self.schema = self.TestModel(
            {"id": 123, "name": "Bar", "created": datetime.now(), "good_number": 42}
        )
        self.schema.set()

    def tearDown(self):
        client.delete("TestHashModel")

    @property
    def raw_value(self):
        return client.hget("TestHashModel", "TestHashModel:123")

    @property
    def stored(self):
        return json.loads(self.raw_value.decode("utf-8"))


class HashModelDynamicKeyStorageTest(BaseModelStorageTest, TestCase):
    class TestHashModel(TestModel, HashRedisMixin):
        hash_id = types.StringType(default="SubKey")

        @property
        def __set_key__(self):
            return self.__key_pattern__(self.hash_id)

    def setUp(self):
        self.TestModel = self.TestHashModel
        self.schema = self.TestModel(
            {"id": 123, "name": "Bar", "created": datetime.now(), "good_number": 42}
        )
        self.schema.set()

    def tearDown(self):
        client.delete("TestHashModel:SubKey")

    @property
    def raw_value(self):
        return client.hget("TestHashModel:SubKey", "TestHashModel:123")

    @property
    def stored(self):
        return json.loads(self.raw_value.decode("utf-8"))
