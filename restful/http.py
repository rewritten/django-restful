'''
A predefined set of Responses, not included in the standard Django
http module.
'''
from django.http import HttpResponse

class HttpResponseNoContent(HttpResponse):

    def __init__(self, content=None, **kwargs):
        super(HttpResponseNoContent, self).__init__(status=204, **kwargs)

class HttpResponseCreated(HttpResponse):
    status_code = 201

    def __init__(self, content="CREATED", *args, **kwargs):
        super(HttpResponseCreated, self).__init__(content, *args, **kwargs)


class HttpResponseNotAcceptable(HttpResponse):
    status_code = 406

class HttpResponseConflict(HttpResponse):
    status_code = 409
