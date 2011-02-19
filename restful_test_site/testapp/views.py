from django.contrib.auth.models import User
from restful.resource import RestfulResource

class UserResource(RestfulResource):
    model = User
    