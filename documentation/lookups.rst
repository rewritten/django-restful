#######################################
Lookups based on the request parameters
#######################################

Subclasses of RestfulResource may define a list of parameters that have to be
used form the query part of the requestd url, in the ``get_lookups``
attribute (a sequence type).

Each of the elements of ``get_lookups`` must be a callable that will accept
a mapping as only argument and return a sequence of tuples (possibly empty)
in a form suitable to be chained to build the arguments for a .filter()
of a QuerySet. It will be called with the GET dictionary as argument, and
all the results are used to filter the resource list.

The same behaviour can be obtained for the keyword arguments of the view, by
defining the ``kwargs_lookups`` attribute in the same way.

*****************************
The ``LookupParameter`` class
*****************************

The LookupParameter class is prepared to provide easily an implementation of
the previously described behaviour.

A LookupParameter instance is initialized by the key to be searched in the
mapping, plus a number of optional keywords:

 ``conversion``:
   A one-argument callable that will be applied to the found value, to convert
   it to its actual meaning. For instance, it can be ``int`` to convert to
   an integer, or ``smart_bool`` or ``smart_contenttype`` defined in the
   ``utils`` module, or any other function. 
   *Default:* identity.
   
 ``split``:
   Either a boolean or a string, used to split the value when it represents
   a list. If ``True``, the value is splitted by commas. Splitting by 
   semicolons is not supported because Django already splits the Query on ';'
   and '&' characters (in this context they are semantically equivalent).
   If ``conversion`` is specified, it is applied to each of the elements, after
   splitting.
   *Default:* ``False``
   
 ``field``:
   If the name of the paremeter and the name of the field lookup are different,
   this argument indicates the name of the field lookup to be used in the
   filter method.
   *Default:* same as the mapping key.
   
   
**********************
Specialized converters
**********************

With the library a number of prepared conversion functions are provided:


``smart_bool``
==============

Converts an empty value (as in ``...&param=&...``), a literal 0 and any
mixed-capital version of ``'False'`` to ``False``, any other value to ``True``.


``smart_contenttype``
=====================

Converts a dot-separated ``appname.modelname`` value into the ``ContentType``
instance identified by the natural key ``('appname', 'modelname')``. This will 
take advantage of the contenttypes cache.

If a dot is not present, then a normal ``.get(model='modelname')`` is executed over the 
installed ContentTypes, and the result is returned. This doesn't take
advantage of the contenttypes cache.

If a ContentType is not found (or not unique in the latter case), then the
corresponding value for the filter will be ``None``.



