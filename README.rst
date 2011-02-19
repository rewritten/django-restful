DJANGO-RESTFUL
==============


A set of class-based views, mixins and utilities, which will transparently
manage serialization, deserialization and other aspects of RESTful resources
based off a Django site's models.

The views are based off Django 1.3 Class-Based-Views, so Django 1.3 is needed
or a backport of the relevant classes.

See the documentation for in-depth description of the available options.

Why another Restful lib
-----------------------

I used to use piston for a number of projects, and I found a couple of
limitations it its architecture, and other aprts I didn't need at all.

On the other side, Django 1.3 introduces class-based views, and they seem
to be a more natural candidate to base a restful interface upon. 
With CBVs, one can cut into any point of the request process, and change
the behavior.

As an example, in piston it's not possible to use a ValuesQuerySet in a read-object
request, only in read-collection. With our approach, a subclass may
override ``get_query_set()`` and still have it applied when getting
a single object.



Views
-----

The RestfulResource class is a generic view, so it can be used as-is in your
urlconf module:

.. pycode::

    urlpatterns = patterns('',
        ('^users(/(?P<pk>\d+))?(?P<format>\.\w+)?,
            RestfulResource.as_view(model=User)
        ),
        ('^posts(/(?P<slug>\d+))?(?P<format>\.\w+)?,
            RestfulResource.as_view(model=Post)
        ),
        ...
    )

Of course the power of these views resides in the ability to subclass them,
and to reuse the pieces to build limited-scope versions (e.g. let XML out)


GET requests
------------

The format for response serialization is taken from the ``format`` kwarg of
the view, as configured in the url module. It can optionally start with a
single dot, which is ignored.

The choice beween collection and item representation is done like in Django
Class-Based-Views: if there is a kwarg ``pk`` or ``slug`` and it is not 
``None``, then the corresponding item is retrieved, else the collection, 
using the provided queryset and optional filters.

Filters can be extracted from the GET parameters, using a list of 
``LookupParameter`` instances in the ``get_lookups`` or ``kwargs_lookups`` 
class attribute.

Fields for serialization can be defined once for all or depending on a
special GET parameter, which will select among a set of predefined choices.


