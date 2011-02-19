'''
Created on Feb 14, 2011

@author: saverio
'''

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, \
    ImproperlyConfigured
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404, HttpResponseBadRequest, HttpResponseGone
from django.views.generic.base import View
from itertools import chain
from logging import getLogger
from restful.http import HttpResponseNoContent
from restful.codecs import JSONRequestDecoder, XMLRequestDecoder,\
    JSONResponseEncoder, XMLResponseEncoder


log = getLogger('restful.resource')

class RestfulMixin(object):

    allow_empty = True
    queryset = None
    model = None
    paginate_by = None
    context_object_name = None
    paginator_class = Paginator
    singleton = False
    get_lookups = ()
    kwargs_lookups = ()


    def is_collection(self):
        """ Whether the represented resource is a collection or a single resource """
        if self.singleton:
            return False
        return self.kwargs.get('pk') is None \
             and self.kwargs.get('slug') is None


    def get_object(self, queryset=None):
        """
        Returns the object the resource is representing.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()
        # if it is a singleton, skip the PK/slug filter
        if not self.singleton:
            pk = self.kwargs.get('pk')
            slug = self.kwargs.get('slug')
            if pk is not None: # Next, try looking up by primary key.
                queryset = queryset.filter(pk=pk)
            elif slug is not None: # Next, try looking up by slug.
                slug_field = self.get_slug_field()
                queryset = queryset.filter(**{slug_field: slug})
            else: # If none of those are defined, it's an error.
                raise AttributeError(u"Generic detail view %s must be called with "
                                     u"either an object id or a slug."
                                     % self.__class__.__name__)
        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(u"No %s found matching the query" %
                          (queryset.model._meta.verbose_name))
        except MultipleObjectsReturned:
            raise AttributeError(u"Singleton view %s must be configured with "
                                     u"a univalued queryset."
                                     % self.__class__.__name__)
        return obj

    def get_queryset(self):
        """ Get the queryset to look up. """
        if self.queryset is None:
            if self.model:
                return self.model._default_manager.all()
            else:
                raise ImproperlyConfigured(u"%(cls)s is missing a queryset. Define "
                                           u"%(cls)s.model, %(cls)s.queryset, or override "
                                           u"%(cls)s.get_object()." % {
                                                'cls': self.__class__.__name__
                                        })
        parameters = dict()
        # update with the optional get_lookups filter
        parameters.update(chain(*(lookup(self.request.GET) for lookup in self.get_lookups)))
        # update with the optional kwargs_lookups filter
        parameters.update(chain(*(lookup(self.kwargs) for lookup in self.kwargs_lookups)))
        return self.queryset._clone().filter(**parameters)


    def get_slug_field(self):
        """ Get the name of a slug field to be used to look up by slug. """
        return self.slug_field

    def paginate_queryset(self, queryset, page_size):
        """ Paginate the queryset, if needed. """
        page_size = int(page_size)
        if page_size:
            paginator = self.get_paginator(queryset, page_size, allow_empty_first_page=self.get_allow_empty())
            page = self.kwargs.get('page') or self.request.GET.get('page') or 1
            try:
                page_number = int(page)
            except ValueError:
                if page == 'last':
                    page_number = paginator.num_pages
                else:
                    raise Http404("Page is not 'last', nor can it be converted to an int.")
            try:
                page = paginator.page(page_number)
                return {
                    'pages': paginator.num_pages,
                    'from': page.start_index(),
                    'to': page.end_index(),
                    'total': paginator.count,
                    'items': page.object_list,
                }
            except InvalidPage:
                raise Http404(u'Invalid page (%s)' % page_number)
        else:
            return queryset

    def get_paginate_by(self, queryset=None):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.
        Allow to specify the item number only when already set in the resource.
        If request sets to 0 disable pagination, if unset use default.
        """
        if self.paginate_by is not None:
            return self.request.GET.get('items') or self.paginate_by
        else:
            return 0

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        """
        Return an instance of the paginator for this view.
        """
        return self.paginator_class(queryset, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)

    def get_allow_empty(self):
        """
        Returns ``True`` if the view should display empty lists, and ``False``
        if a 404 should be raised instead.
        """
        return self.allow_empty


    def update_attrs(self, instance, data):
        opts = self.model._meta
        _fields = dict((field.name, field) 
                for field in opts.fields
                if field.name in data
                and field.name != instance._meta.pk.name)
        _fields.update(dict((field.attname, field) 
                for field in opts.fields
                if field.attname in data
                and field.name != instance._meta.pk.name))
        for key, field in _fields.items():
            if field.rel:
                to = field.rel.to
                value = data[key]
                if isinstance(value, dict) and 'id' in value:
                    value = value['id']
                if isinstance(value, basestring) and '.' in value and to == ContentType:
                    setattr(instance, key, ContentType.objects.get_by_natural_key(*value.split('.')))
                    continue
                elif isinstance(value, (tuple, list)) and hasattr(to.objects, 'get_by_natural_key'):
                    try:
                        setattr(instance, key, to.objects.get_by_natural_key(*value))
                    except:
                        pass
                else:
                    try:
                        setattr(instance, key, to.objects.get(pk=value))
                    except:
                        pass
            else:
                setattr(instance, key, data[key])
        return instance


    def save_m2m(self, instance, data):
        opts = self.model._meta
        for field in opts.many_to_many:
            if field.name in data and field.rel:
                to = field.rel.to
                pks = data[field.name]
                if pks:
                    if isinstance(pks[0], dict):
                        pks = [pk['id'] for pk in pks]
                    try:
                        getattr(instance, field.name).clear()
                        getattr(instance, field.name).add(*to.objects.in_bulk(pks))
                    except Exception, e:
                        log.debug(e)
                else:
                    getattr(instance, field.name).clear()




class BaseRestfulResource(RestfulMixin, View):

    @classmethod
    def as_view(cls, *args, **initkwargs):
        """ Adding to the super, use the positional args to allow http_method_names """
        if args:
            initkwargs.update(http_method_names=[m for m in args])
        return super(BaseRestfulResource, cls).as_view(**initkwargs)


    def get(self, request, *args, **kwargs):
        if self.is_collection():
            self.object = None
            self.object_list = self.get_queryset()
            allow_empty = self.get_allow_empty()
            if not allow_empty and len(self.object_list) == 0:
                raise Http404(u"Empty list and '%s.allow_empty' is False."
                          % self.__class__.__name__)
            return self.paginate_queryset(self.object_list, self.get_paginate_by())
        else:
            self.object = self.get_object()
            self.object_list = None
            return self.object


    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.update_attrs(instance, self.data)
            instance.save()
            self.save_m2m(instance, self.data)
            return instance
        except Http404:
            return HttpResponseBadRequest()
        except Exception, e:
            return HttpResponseBadRequest(e)


    def post(self, request, *args, **kwargs):
        try:
            new_instance = self.model()
            self.update_attrs(new_instance, self.data)
            new_instance.save()
            self.save_m2m(new_instance, self.data)
            return new_instance
        except Exception, e:
            return HttpResponseBadRequest(e)

    def delete(self, request, *args, **kwargs):
        try:
            self.get_object().delete()
            return HttpResponseNoContent()
        except Http404:
            return HttpResponseGone()



class RestfulResource(JSONRequestDecoder, XMLRequestDecoder,
    JSONResponseEncoder, XMLResponseEncoder, BaseRestfulResource):
    def get_default_format(self):
        return 'json'




