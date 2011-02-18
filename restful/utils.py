'''
Created on Feb 11, 2011

@author: saverio
'''
from collections import namedtuple, Mapping, Iterable
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Manager, ForeignKey, ManyToManyField
from django.http import HttpResponse
from django.utils.encoding import smart_unicode
from numbers import Number
import collections
import inspect
import itertools

def constant_factory(value): return itertools.repeat(value).next

# conversion functions for the LookupParameter class
def identity(z): return z

def smart_bool(value):
    """ Converts to a boolean value. 
    Bools are returned unmodified; strings evaluate as False if empty or 
    "false"; numbers are bool-evaluated; any other argument evals to False.
    """
    if isinstance(value, bool): return value
    if value is None: return False
    if isinstance(value, basestring): return value and value.lower() != 'false'
    if isinstance(value, Number): return bool(value)
    return False

def smart_contenttype(value):
    try:
        if '.' in value:
            return ContentType.objects.get_by_natural_key(*value.split('.', 1))
        else:
            return ContentType.objects.get(model=value)
    except ContentType.DoesNotExist:
        return None



class LookupParameter(namedtuple('LookupParameter', ['parameter', 'conversion', 'split', 'field'])):
    """ An object which will check a mapping (typically a request.GET) and 
    returns a possibly empty tuple of pairs ((k,v),). The resulting tuples 
    can be chained together using itertools, to construct a mapping for 
    filtering a QuerySet object.
    It optionally splits the value, apply a conversion and assigns to a different field. 
    
    If the parameter is not present, then an empty tuple is returned, but any exception raised by the
    conversion or the splitting gives rise to a ((k, None),) tuple.
    """
    def __new__(cls, parameter, conversion=identity, split=False, field=None):
        if split is True:
            split = ','
        if field is None:
            field = parameter
        return super(LookupParameter, cls).__new__(cls, parameter, conversion, split, field)

    def __call__(self, mapping):
        if not isinstance(mapping, Mapping):
            raise TypeError('argument must be a mapping type')
        if self.parameter in mapping:
            try:
                value = mapping[self.parameter]
                if self.split:
                    value = [self.conversion(v) for v in value.split(self.split)]
                else:
                    value = self.conversion(value)
            except:
                value = None
            return ((self.field, value),)
        else:
            return ()



def model_to_dict(instance, fields=None, exclude=None):
    """
    Returns a dict containing the data in ``instance`` suitable for serializing.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    
    This is similar to the django.forms.models.model_to_dict(), but including
    read_only fields and navigating fully the m2m (when specified).
    """
    # avoid a circular import

    if tuple(fields) == ('natural_key',):
        return instance.natural_key()
    elif tuple(fields) == ('natural.key',):
        return '.'.join(instance.natural_key())

    opts = instance._meta
    data = {}
    for f in opts.fields + opts.many_to_many:
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if fields and isinstance(f, ManyToManyField):
            # Recurse m2m only when fields are explicitly specified
            if instance.pk is None:
                data[f.name] = []
            else:
                data[f.name] = f.value_from_object(instance)
        elif fields and isinstance(f, ForeignKey):
            if fields[f.name] is None:
                data[f.name] = f.value_from_object(instance)
            else:
                data[f.name] = getattr(instance, f.name)
        else:
            data[f.name] = f.value_from_object(instance)
    # add extra attributes/method
    if fields:
        missing = [f for f in fields if f not in data]
        for field in missing:
            try:
                attribute = getattr(instance, field)
            except:
                print "Attribute %s not found in %s." % (field, instance)
                continue # fail??
            try:
                data[field] = attribute()
            except:
                data[field] = attribute

    return data





def serialize(data, fields=()):
    """
    Recursively serialize a lot of types, and
    in cases where it doesn't recognize the type,
    it will fall back to Django's `smart_unicode`.
    
    Returns `dict`.
    """
    def _any(thing, fields=()):
        """
        Dispatch, all types are routed through here.
        """
        ret = None
        if isinstance(thing, Mapping):
            ret = dict([(k, _any(thing[k], fields)) for k in thing])
        elif isinstance(thing, basestring):
            ret = smart_unicode(thing)
        elif isinstance(thing, Iterable): # includes QuerySet, list and tuple
            ret = [_any(v, fields) for v in thing]
        elif isinstance(thing, Decimal):
            ret = str(thing)
        elif isinstance(thing, Model):
            ret = _model(thing, fields)
        elif isinstance(thing, HttpResponse):
            ret = thing
        elif inspect.isfunction(thing): # argument-less function
            if not inspect.getargspec(thing)[0]:
                ret = _any(thing())
        elif isinstance(thing, Manager):
            ret = _any(thing.all(), fields)
        else:
            ret = smart_unicode(thing, strings_only=True)

        return ret


    def _model(thing, fields=()):
        """
        Models. 

        data is an instance of Model.
        """
        fields = fields or ()
        if hasattr(fields, 'serialize'): # fields is a View, use it to serialize
            ret = fields.serialize(thing)
        else: # transform fields into more suitable form
            extended_fields = {}
            for field_spec in fields:
                if isinstance(field_spec, tuple):
                    extended_fields[field_spec[0]] = field_spec[1]
                else:
                    extended_fields[field_spec] = None
            # prepare initial dict
            probably = model_to_dict(thing, extended_fields)
            # recurse serialization:
            if isinstance(probably, basestring):
                ret = probably
            elif isinstance(probably, Mapping):
                ret = dict(
                    (key, _any(probably[key], extended_fields.get(key)))
                    for key in probably
                    )
            else:
                ret = [_any(key) for key in probably]
        return ret
    # Kickstart the seralizin'.
    return _any(data, fields)



class FieldSpec(collections.defaultdict):
    """ A dict-like object with explicit default value. Used for resources
    in which the serialization format can be configured by the consumer.
    """
    def __init__(self, default, **kwargs): 
        super(FieldSpec, self).__init__(constant_factory(default), **kwargs)

    @property
    def default(self): return self.default_factory()
