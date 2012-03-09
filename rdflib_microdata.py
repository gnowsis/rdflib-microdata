"""
This rdflib plugin lets you parse html5 microdata into an RDF graph. You 
shouldn't have to use this module directly, since it's a plugin. You'll just 
want to:

>>> import rdflib
>>> import rdflib_microdata
>>> g = rdflib.Graph()
>>> g.parse("https://raw.github.com/edsu/microdata/master/test-data/example.html", format="microdata")
>>> print g.serialize()
"""

import microdata
import urlparse

from rdflib import URIRef, Literal, BNode, Namespace, RDF
from rdflib.plugin import register
from rdflib.parser import Parser

register("microdata", Parser, "rdflib_microdata", "MicrodataParser")

class MicrodataParser(Parser):

    def parse(self, source, sink, **kwargs):
        """
        Pass in a file or file-like object containing html5 microdata
        and populate the sink graph with triples.
        """
        for item in microdata.get_items(source.getByteStream()):
            self._add_item(item, sink, source.getPublicId() or source.getSystemId() or "")

    def _add_item(self, item, sink, publicID):
        # the URI to hang our assertions off of
        if item.itemid:
            s = URIRef(_make_absolute(item.itemid.string, publicID))
        else:
            s = BNode()

        # MUST have a profile for the item to convert to rdf data model
        if not item.itemtype:
            return

        # create a vocab namespace, appending a # if it isn't a hash or slash 
        # already
        ns = str(item.itemtype)
        if ns.endswith("#") or ns.endswith("/"):
            ns = Namespace(item.itemtype)
        else:
            ns = Namespace(ns + "#")

        # type the resource
        sink.add((s, RDF.type, URIRef(_make_absolute(item.itemtype, publicID))))

        # go through each property/value and add triples to the graph
        for item_property, item_values in item.props.items():
            p = ns[item_property]
            for v in item_values:
                if isinstance(v, microdata.Item):
                    o = self._add_item(v, sink, publicID) 
                elif isinstance(v, microdata.URI):
                    o = URIRef(_make_absolute(unicode(v), publicID))
                else:
                    o = Literal(v)
                # TODO: handle dates
                sink.add((s, p, o))

        return s

def _make_absolute(uri, base):
    if urlparse.urlparse(unicode(uri)).scheme:
        return unicode(uri)
    else:
        return urlparse.urljoin(unicode(base), unicode(uri))
