==========
 EXAMPLES
==========


How to serialize a relation to ContentType
------------------------------------------

::

    class Resource(RestfulResource):
        fields = (..., ('ct_field', ('natural.key', )), ...)

This will be serialized in a dict containing (JSON example):
::

    {
        ...
        "ct_field": "app.model",
        ...
    }


How to change serialization depending on the request
----------------------------------------------------

::

    class Resource(RestfulResource):
        fieldset_marker = 'fs' # this is the name of the selecting parameter
        fields = FieldSpec(
            default=('a','b','c'),
            alt=('d','e','f'),
            alt2=('i','g','h')
        )
        
This resource will expose the corresponding fields whenever the request
contains ``fs=alt`` or ``fs=alt2`` in the query. In any other case
it exposes the default set of fields.

For the selection to be activated, both ``fieldset_marker`` must be set and 
``field_spec`` must be a mapping (a ``defaultdict`` or ``FieldSet`` instance is
preferred, to allow fallback without raising exceptions).



How to filter over a boolean field
----------------------------------

::

    class Resource(RestfulResource):
        get_lookups = (
            ...
            LookupParameter('bool_field', smart_bool),
            ...
        )

Any request containing the parameter ``bool_field=`` will enable the 
corresponding filter, by adding ``.filter(bool_field=True)`` or
``.filter(bool_field=False)`` to the queryset.
