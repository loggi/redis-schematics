# encoding: utf8

from __future__ import absolute_import

import json
from datetime import datetime
from unittest import TestCase

from redis import StrictRedis
from schematics import types

from redis_schematics import SimpleRedisModel, HashRedisModel


client = StrictRedis(host='localhost', port=6379, db=4)


class TestSimpleModelStorage(TestCase):

    class TestSimpleModel(SimpleRedisModel):
        __redis_client__ = client
        __expire__ = 120

        id = types.IntType(required=True)
        name = types.StringType()
        created = types.DateTimeType()
        good_number = types.IntType()

    def setUp(self):
        self.TestModel = self.TestSimpleModel
        self.schema = self.TestModel({
            'id': 123,
            'name': 'Bar',
            'created': datetime.now(),
            'good_number': 42,
        })
        self.schema.set()

    @property
    def raw_value(self):
        return client.get('TestSimpleModel:123')

    @property
    def stored(self):
        return json.loads(self.raw_value)

    def test_set(self):
        assert self.stored == self.schema.to_primitive()

    def test_match(self):
        result = self.TestModel.match(id=123)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(pk='123')
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number=42)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__lt=43)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__gt=41)
        assert self.stored == result.to_primitive()

    def test_match_on_non_existing(self):
        self.assertRaises(self.TestModel.match, id=321)
        self.assertRaises(self.TestModel.match, pk='321')
        self.assertRaises(self.TestModel.match, good_number__gt=42)
        self.assertRaises(self.TestModel.match, good_number__lt=42)

    def test_match_for_pk(self):
        result = self.TestModel.match_for_pk('123')
        assert self.stored == result.to_primitive()

    def test_match_for_values(self):
        result = self.TestModel.match_for_values(name='Bar')
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
        assert self.TestModel.delete_filter(name='Bla') == 0
        assert self.raw_value
        assert self.TestModel.delete_filter(name='Bar') == 1
        assert self.raw_value is None

    def test_delete_filter_on_non_existing(self):
        self.schema.delete()
        assert self.TestModel.delete_filter() == 0
        assert self.raw_value is None

    def tearDown(self):
        client.delete('TestSimpleModel:123')


class TestHashModelStorage(TestCase):

    class TestHashModel(HashRedisModel):
        __redis_client__ = client
        __expire__ = 120

        id = types.IntType(required=True)
        name = types.StringType()
        created = types.DateTimeType()
        good_number = types.IntType()

    def setUp(self):
        self.TestModel = self.TestHashModel
        self.schema = self.TestModel({
            'id': 123,
            'name': 'Bar',
            'created': datetime.now(),
            'good_number': 42,
        })
        self.schema.set()

    @property
    def raw_value(self):
        return client.hget('TestHashModel', 'TestHashModel:123')

    @property
    def stored(self):
        return json.loads(self.raw_value)

    def test_set(self):
        assert self.stored == self.schema.to_primitive()

    def test_match(self):
        result = self.TestModel.match(id=123)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(pk='123')
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number=42)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__lt=43)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__gt=41)
        assert self.stored == result.to_primitive()

    def test_match_on_non_existing(self):
        self.assertRaises(self.TestModel.match, id=123)
        self.assertRaises(self.TestModel.match, pk='123')
        self.assertRaises(self.TestModel.match, good_number__gt=42)
        self.assertRaises(self.TestModel.match, good_number__lt=42)

    def test_match_for_pk(self):
        result = self.TestModel.match_for_pk('123')
        assert self.stored == result.to_primitive()

    def test_match_for_values(self):
        result = self.TestModel.match_for_values(name='Bar')
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
        assert self.TestModel.delete_filter(name='Bla') == 0
        assert self.raw_value
        assert self.TestModel.delete_filter(name='Bar') == 1
        assert self.raw_value is None

    def test_delete_filter_on_non_existing(self):
        self.schema.delete()
        assert self.TestModel.delete_filter() == 0
        assert self.raw_value is None

    def tearDown(self):
        client.delete('TestHashModel')
