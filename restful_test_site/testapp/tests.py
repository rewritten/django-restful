"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from itertools import chain
from django.test import TestCase
from django.http import QueryDict
from restful.utils import *
from restful.http import *
from restful.codecs import *
from restful.resource import *

class UtilsTest(TestCase):
    def test_conversors_identity(self):
        self.assertEqual(identity(self), self)
        self.assertEqual(identity(None), None)
        self.assertEqual(identity(42), 42)
        self.assertEqual(identity(TestCase), TestCase)
        
    def test_conversors_smart_bool(self):
        self.assertEqual(smart_bool(None), False)
        self.assertEqual(smart_bool(''), False)
        self.assertEqual(smart_bool('0'), False)
        self.assertEqual(smart_bool(0), False)
        self.assertEqual(smart_bool('FALSE'), False)
        self.assertEqual(smart_bool('false'), False)
        self.assertEqual(smart_bool(False), False)
        self.assertEqual(smart_bool('1'), True)
        self.assertEqual(smart_bool('None'), True)
        self.assertEqual(smart_bool('flase'), True)
        self.assertEqual(smart_bool(True), True)
        self.assertEqual(smart_bool(42), True)
        
    def test_conversors_smart_contenttype(self):
        self.assertEqual(smart_contenttype(''), None)
        self.assertEqual(smart_contenttype('blah'), None)
        self.assertEqual(smart_contenttype('users'), None)
        self.assertNotEqual(smart_contenttype('contenttypes.contenttype'), None)
        self.assertNotEqual(smart_contenttype('auth.user'), None)
        self.assertNotEqual(smart_contenttype('auth.group'), None)
        self.assertNotEqual(smart_contenttype('testapp.testmodel'), None)
        self.assertNotEqual(smart_contenttype('contenttype'), None)
        self.assertNotEqual(smart_contenttype('user'), None)
        self.assertNotEqual(smart_contenttype('group'), None)
        self.assertNotEqual(smart_contenttype('testmodel'), None)


        
    def test_lookups(self):
        foo = LookupParameter('foo')
        bar = LookupParameter('bar', split=True)
        baz = LookupParameter('baz', int, field='alternative')
        bee = LookupParameter('bee', int, split=':')
        bork = LookupParameter('bork', int, split='-')
        mapping = QueryDict('foo=1&bar=merry,christmas&baz=42&bee=0:1&fake=not_me')
        result = dict(chain(*(par(mapping) for par in (foo, bar, baz, bee, bork))))
        self.assertEqual(result['foo'], '1')
        self.assertEqual(frozenset(result['bar']), frozenset(['merry', 'christmas']))
        self.assertEqual(frozenset(result['bee']), frozenset([0, 1]))
        self.assertEqual(result['alternative'], 42)
        self.assertNotIn('bork', result)
        self.assertNotIn('fake', result)

