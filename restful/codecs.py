'''
Created on Feb 11, 2011

@author: saverio
'''
from StringIO import StringIO
from collections import defaultdict
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponseBadRequest, HttpResponse
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from restful.utils import serialize
from xml.etree import ElementTree
import re


class BaseRequestDecoder(object):
    content_type = None

    def decode_postdata(self, request, *args, **kwargs):
        raise NotImplementedError('This method must be implemented in subclasses')

    def dispatch(self, request, *args, **kwargs):
        """ If the request is POST or PUT, load the postdata into self.data
        after converting to an object. """
        self.data = None
        if request.method.lower() in ('put', 'post') and request.POST:
            try:
                self.data = self.decode_postdata(request)
                request.POST = dict()
            except NotImplementedError:
                return HttpResponseBadRequest('Cannot decode POST data of type %s.' % request.META.get('CONTENT_TYPE'))
            except Exception:
                return HttpResponseBadRequest('Error parsing data of type %s.' % request.META.get('CONTENT_TYPE'))
        return super(BaseRequestDecoder, self).dispatch(request, *args, **kwargs)


class DefaultRequestDecoder(BaseRequestDecoder):
    # By default, no content type will be accepted too
    content_type = 'application/x-www-form-urlencoded'
    
    def decode_postdata(self, request, *args, **kwargs):
        if request.META.get('CONTENT_TYPE', 'application/x-www-form-urlencoded').startswith(DefaultRequestDecoder.content_type):
            return request.POST
        else:
            return super(JSONRequestDecoder, self).decode_postdata(request, *args, **kwargs)
    

class JSONRequestDecoder(BaseRequestDecoder):
    content_type = 'application/json'

    def decode_postdata(self, request, *args, **kwargs):
        if request.META.get('CONTENT_TYPE', '').startswith(JSONRequestDecoder.content_type):
            return simplejson.load(request)
        else:
            return super(JSONRequestDecoder, self).decode_postdata(request, *args, **kwargs)


class XMLRequestDecoder(BaseRequestDecoder):
    content_type = 'application/xml'

    def decode_postdata(self, request, *args, **kwargs):
        if request.META.get('CONTENT_TYPE', '').startswith(XMLRequestDecoder.content_type):
            root = ElementTree.parse(request).getroot()
            return root
        else:
            return super(XMLRequestDecoder, self).decode_postdata(request, *args, **kwargs)




class BaseResponseEncoder(object):
    mimetype = None
    format = None
    field_spec_marker = None
    field_spec = defaultdict()
    fields = ()

    def render(self, response):
        raise NotImplementedError('This method must be implemented in subclasses')

    def get_default_format(self):
        return None


    def dispatch(self, request, *args, **kwargs):
        self.format = re.sub(r'^\.+', '', kwargs.get('format') or self.get_default_format())
        print "format set to %s" % self.format
        response = super(BaseResponseEncoder, self).dispatch(request, *args, **kwargs)
        print "got response: %s" % response
        if isinstance(response, basestring):
            return HttpResponse(response)
        elif isinstance(response, HttpResponse):
            return response
        else:
            data = serialize(response, self.get_fields())
            return self.render(data)


    def get_fields(self):
        if self.field_spec_marker:
            return self.field_spec[self.request.GET.get(self.field_spec_marker)]
        else:
            return self.fields


    def get_format(self):
        return self.format


class JSONResponseEncoder(BaseResponseEncoder):
    mimetype = 'application/json'
    format = 'json'

    def render(self, response):
        if self.format == JSONResponseEncoder.format:
            print "rendering %s in json" % `response`
            content = simplejson.dumps(response, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=2)
            return HttpResponse(content, mimetype=JSONResponseEncoder.mimetype)
        else:
            return super(JSONResponseEncoder, self).render(response)




class XMLResponseEncoder(BaseResponseEncoder):
    mimetype = 'application/xml'
    format = 'xml'

    def render(self, response):
        if self.format == XMLResponseEncoder.format:
            stream = StringIO()

            xml = SimplerXMLGenerator(stream, "utf-8")
            xml.startDocument()
            xml.startElement("response", {})

            self._to_xml(xml, response)

            xml.endElement("response")
            xml.endDocument()

            content = stream.getvalue()

            return HttpResponse(content, mimetype=XMLResponseEncoder.mimetype)
        else:
            return super(XMLResponseEncoder, self).render(response)


    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement("resource", {})
                self._to_xml(xml, item)
                xml.endElement("resource")
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                if value is not None:
                    # Skip tag if value is None
                    xml.startElement(key, {})
                    self._to_xml(xml, value)
                    xml.endElement(key)
        elif isinstance(data, bool):
            xml.characters(smart_unicode(int(data)))
        else:
            xml.characters(smart_unicode(data))





