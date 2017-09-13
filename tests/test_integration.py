# encoding: utf8

from __future__ import absolute_import

import json
from datetime import datetime
from unittest import TestCase

from redis import StrictRedis
from schematics import types

from redis_schematics import SimpleRedisModel


client = StrictRedis(host='localhost', port=6379, db=4)


class TestBasicModelStorage(TestCase):

    class TestModel(SimpleRedisModel):
        __redis_client__ = client
        __expire__ = 120

        id = types.StringType(required=True)
        name = types.StringType()
        created = types.DateTimeType()
        good_number = types.IntType()

    def setUp(self):
        self.schema = self.TestModel({
            'id': 'Foo',
            'name': 'Bar',
            'created': datetime.now(),
            'good_number': 42,
        })
        self.schema.set()
        self.stored = json.loads(client.get('TestModel:Foo'))

    def test_set(self):
        assert self.stored == self.schema.to_primitive()

    def test_match(self):
        result = self.TestModel.match(id='Foo')
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(pk='Foo')
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number=42)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__lt=43)
        assert self.stored == result.to_primitive()

        result = self.TestModel.match(good_number__gt=41)
        assert self.stored == result.to_primitive()

    def test_on_non_existing(self):
        self.assertRaises(self.TestModel.match, id='Bar')
        self.assertRaises(self.TestModel.match, pk='Bar')
        self.assertRaises(self.TestModel.match, good_number__gt=42)
        self.assertRaises(self.TestModel.match, good_number__lt=42)

    def test_match_for_pk(self):
        result = self.TestModel.match_for_pk('Foo')
        assert self.stored == result.to_primitive()

    def test_match_for_values(self):
        result = self.TestModel.match_for_values(name='Bar')
        stored = client.get('TestModel:Foo')
        assert json.loads(stored) == result.to_primitive()

    def test_all(self):
        result = self.TestModel.all()
        stored = client.get('TestModel:Foo')
        assert json.loads(stored) == result[0].to_primitive()

    def test_filter(self):
        result = self.TestModel.filter(good_number__lt=43)
        assert self.stored == result[0].to_primitive()
        result = self.TestModel.filter(good_number__lt=42)
        assert result == []

    def tearDown(self):
        client.delete('TestModel:Foo')
