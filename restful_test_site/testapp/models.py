from django.db import models
from django.contrib.contenttypes.models import ContentType

# Create your models here.

class TestModel(models.Model):
    bool_field = models.BooleanField()
    ct_field = models.ForeignKey(ContentType)
    