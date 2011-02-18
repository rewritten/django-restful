EXAMPLES
========


How to serialize a relation to ContentType
------------------------------------------

fields = (..., ('ct_field', ('natural.key', )), ...)

This will be serialized in a dict containing (JSON example):

   ...
   "ct_field": "app.model",
   ...


How to filter over a boolean field
----------------------------------

get_lookups = (
    ...
    LookupParameter('bool_field', smart_bool),
    ...
)

Any request containing the parameter 'bool_field' will enable the 
corresponding filter.
