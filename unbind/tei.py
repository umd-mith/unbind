#!/usr/bin/env python

import re
import sys
import teizone
import StringIO
import tempfile

from six.moves.urllib.parse import urljoin

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.etree import ElementTree as etree

from .namespaces import XI, TEI, MITH


class Document(object):

    def __init__(self, tei_filename):
        tei = etree.parse(tei_filename).getroot()
        # XXX: get these from the TEI document
        self.title = "Frankenstein"
        self.agent = "Mary Shelley"
        self.attribution = "Bodleian Library, University of Oxford"
        self.date = "18 April-[?13] May 1817"
        self.service = "http://dev.shelleygodwinarchive.org/sc/oxford/frankenstein/notebook/c1"
        self.state = "Fair copy"
        self.label = "Fair-Copy Notebook C1"
        self.surfaces = []
        for inc in tei.findall('.//{%s}include' % XI):
            filename = urljoin(tei_filename, inc.attrib['href'])
            surface = Surface(filename)
            self.surfaces.append(surface)


class Surface(object):

    def __init__(self, filename):
        self.filename = filename

        # TODO: at some point we should write the canonical coordinates to the 
        # TEI. For now it is being done dynamically

        surface = teizone.Surface(filename)
        surface.guess_coordinates()
        tmp_fh, tmp_filename = tempfile.mkstemp()
        surface.save(tmp_filename)

        doc = surface.doc
        tei = doc.getroot()
        self.height = int(tei.attrib.get('lry'))
        self.width = int(tei.attrib.get('lrx'))
        self.folio = tei.attrib.get("{%s}folio" % MITH)
        self.shelfmark = tei.attrib.get("{%s}shelfmark" % MITH)
        self.image = tei.find('.//{%s}graphic' % TEI).get('url')
        # XXX: get this from the TEI document
        self.hand = "Mary Shelley"
        
        # use a SAX parser to get the line annotations
        # since we need to keep track of text offsets 

        parser = make_parser()
        handler = LineOffsetHandler()
        parser.setContentHandler(handler)
        parser.parse(tmp_filename)
        self.zones = handler.zones

    @property
    def uri(self):
        m = re.search('(/data/.+$)', self.filename)
        return m.group(1)


class Zone(object):

    def __init__(self, attrs):
        self.lines = []
        self.ulx = attrs.get('ulx', 0)
        self.uly = attrs.get('uly', 0)
        self.lrx = attrs.get('lrx', 0)
        self.lry = attrs.get('lry', 0)

    @property
    def begin(self):
        if len(self.lines) > 0:
            return self.lines[0].begin
        else:
            return None

    @property
    def end(self):
        if len(self.lines) > 0:
            return self.lines[0].end
        else:
            return None

    @property
    def xywh(self):
        height = int(self.lry) - int(self.uly)
        width = int(self.lrx) - int(self.ulx)
        return "xywh:%s,%s,%s,%s" % (self.ulx, self.uly, height, width)


class Line(object):
    
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""


class LineOffsetHandler(ContentHandler):
    """
    SAX Handler for extracting zones and lines from a TEI canvas.
    """

    def __init__(self):
        self.zones = []
        self.pos = 0
        self.height = None
        self.width = None
        self.in_line = False

    def startElement(self, name, attrs):
        if name == "zone":
            self.zones.append(Zone(attrs))
        elif name == "line":
            self.in_line = True
            l = Line()
            l.begin = self.pos
            self.zones[-1].lines.append(l)

    def endElement(self, name):
        if name == "line":
            self.zones[-1].lines[-1].end = self.pos
            self.in_line = False
   
    def characters(self, content):
        self.pos += len(content) # TODO: unicode characters?
        if self.in_line:
            self.zones[-1].lines[-1].text += content


