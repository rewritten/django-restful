from django.conf.urls.defaults import *

from restful_test_site.testapp.views import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^users(/(?P<pk>\d+))?(?P<format>\.\w+)?', UserResource.as_view()),
    # Example:
    # (r'^restful_test_site/', include('restful_test_site.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
