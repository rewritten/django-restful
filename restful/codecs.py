'''
Created on Feb 11, 2011

@author: saverio
'''
from StringIO import StringIO
from collections import defaultdict
from xml.etree import ElementTree
import re
from django.conf import ConfigurationError
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponseBadRequest, HttpResponse
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from restful.utils import serialize


class BaseRequestDecoder(object):
    """ The base for request decoder mixins. Subclasses can be mixed together
    to provide support for multiple content types.
    """

    def decode_postdata(self, request, *args, **kwargs):
        """ Subclasses must implement this method, by checking the compatibility
        of the request's CONTENT_TYPE with the subclass supported one. In case
        of a difference the subclass must delegate to another component. 
        """
        raise NotImplementedError('The method "decode_postdata()" must be implemented in subclasses')

    def dispatch(self, request, *args, **kwargs):
        """ Load the request data into a dictionary, using any decoder 
        implemented by subclasses.
        """
        self.data = None
        self.request_content_type = request.META.get('CONTENT_TYPE', '').split(';')[0].strip()
        if request.method.lower() in ('put', 'post') and request.POST:
            try:
                self.data = self.decode_postdata(request)
                request.POST = dict()
            except NotImplementedError:
                return HttpResponseBadRequest('Cannot decode POST data of type %s.' % self.request_content_type)
            except Exception as e:
                # Any other error is a parsing error
                return HttpResponseBadRequest('Error parsing data of type %s.' % self.request_content_type)
        return super(BaseRequestDecoder, self).dispatch(request, *args, **kwargs)


class DefaultRequestDecoder(BaseRequestDecoder):
    """ The default request decoder, if used, loads the POST data into
    a dictionary when the Content-Type header is ot set or is set to
    form-encoded.
    
    The proper QueryDict object from django request is returned, so list-type
    instances can be retrieved explicitly.
    """
    content_types = ['application/x-www-form-urlencoded', '']
    
    def decode_postdata(self, request, *args, **kwargs):
        if self.request_content_type in DefaultRequestDecoder.content_types:
            return request.POST
        else:
            return super(DefaultRequestDecoder, self).decode_postdata(request, *args, **kwargs)
    

class JSONRequestDecoder(BaseRequestDecoder):
    """ The JSON request decoder. JSON specifies that there must be a root 
    object, which is converted to a dictionary.
    """
    content_types = ['application/json']

    def decode_postdata(self, request, *args, **kwargs):
        if self.request_content_type in JSONRequestDecoder.content_types:
            return simplejson.load(request)
        else:
            return super(JSONRequestDecoder, self).decode_postdata(request, *args, **kwargs)


class XMLRequestDecoder(BaseRequestDecoder):
    # FIXME: This should retrun a dict-like object, not a ElemetTree root.
    content_types = 'application/xml'

    def decode_postdata(self, request, *args, **kwargs):
        if self.request_content_type in XMLRequestDecoder.content_types:
            root = ElementTree.parse(request).getroot()
            return root
        else:
            return super(XMLRequestDecoder, self).decode_postdata(request, *args, **kwargs)




class BaseResponseEncoder(object):
    
    # The mimetype to send along with the response.
    mimetype = None
    
    # The 'format' class attribute acts as default serialization format
    # for instances. If only basic mixins are used, the first mixin determines
    # the default format. Anyway the subclass can set its own default.
    format = None
    
    # A special request parameter which allows the requested resource to be
    # serialized into several different forms.
    fieldset_marker = None
    
    # The field resolver object. Subclasses can use the FieldSpec class or a 
    # simpler defaultdict for fallback behaviour. If the consumer can't
    # specify a serialization form, set it to just a tuple.
    fields = tuple() # for fixed serialization
    # fields = defaultdict(tuple) # for polymorphic serialization
    
    def get_fields(self):
        if self.fieldset_marker and isinstance(self.fields, dict):
            return self.fields[self.request.GET.get(self.fieldset_marker)]
        elif isinstance(self.fields, tuple):
            return self.fields
        else:
            raise ConfigurationError("The 'fields' attribute must be either "
                                "a dict (when 'fieldset_marker' is set) or a "
                                "tuple.")

    def render(self, response):
        raise NotImplementedError('%s extends BaseResponseEncoder but does not '
                            'implement the render() method. Extend one of '
                            'BaseResponseEncoder\'s subclasses, setting also '
                            'a default format, or implement render() '
                            'directly.' % self.__class__.__name__)

    def dispatch(self, request, *args, **kwargs):
        # if the format has ben specified in the request, overwrite the
        # the default.
        if 'format' in kwargs:
            self.format = kwargs['format'].lstrip('.')
        response = super(BaseResponseEncoder, self).dispatch(request, *args, **kwargs)
        if isinstance(response, basestring):
            return HttpResponse(response)
        elif isinstance(response, HttpResponse):
            return response
        else:
            data = serialize(response, self.get_fields())
            return self.render(data)


class JSONResponseEncoder(BaseResponseEncoder):
    mimetype = 'application/json'
    format = 'json'

    def render(self, response):
        if self.format != JSONResponseEncoder.format:
            return super(JSONResponseEncoder, self).render(response)
        content = simplejson.dumps(response, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=2)
        return HttpResponse(content, mimetype=JSONResponseEncoder.mimetype)



class XMLResponseEncoder(BaseResponseEncoder):
    mimetype = 'application/xml'
    format = 'xml'

    def render(self, response):
        if self.format != XMLResponseEncoder.format:
            return super(XMLResponseEncoder, self).render(response)
        stream = StringIO()
        xml = SimplerXMLGenerator(stream, "utf-8")
        xml.startDocument()
        xml.startElement("response", {})
        self._to_xml(xml, response)
        xml.endElement("response")
        xml.endDocument()
        content = stream.getvalue()
        return HttpResponse(content, mimetype=XMLResponseEncoder.mimetype)


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





