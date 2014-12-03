#!/usr/bin/env python

import os
import re
import sys
import teizone
import StringIO
import tempfile

from six.moves.urllib.parse import urljoin

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.etree import ElementTree as etree

from .namespaces import XI, TEI, MITH, XML


class Document(object):

    def __init__(self, tei_filename):
        tei = etree.parse(tei_filename).getroot()
        notebook = re.sub(r'[_-]', '/', tei.get('{%s}id' % XML))
        
        self.title = tei.find('.//{%s}msItem[@type="#work"]/{%s}bibl/{%s}title' % 
            (TEI, TEI, TEI)).text
        self.agent = tei.find('.//{%s}msItem[@type="#work"]/{%s}bibl/{%s}author' % 
            (TEI, TEI, TEI)).text
        self.attribution = tei.find('.//{%s}repository' % TEI).text
        self.date = tei.find('.//{%s}msItem[@type="#volume"][0]/{%s}bibl/{%s}date' % 
            (TEI, TEI, TEI)).text
        self.service = "http://shelleygodwinarchive.org/sc/%s" % notebook
        self.state = tei.find('.//{%s}msItem[@type="#work"]/{%s}bibl' % (TEI, TEI)).get("status")
        self.label = tei.find('.//{%s}titleStmt/{%s}title[@type="main"]' % (TEI, TEI)).text
        self.hands = {}
        for hand in tei.findall('.//{%s}physDesc//{%s}handNote' % (TEI, TEI)):
            self.hands[hand.get('{%s}id' % XML)] = hand.findall('{%s}persName' % TEI)[0].text
        self.surfaces = []
        for inc in tei.findall('.//{%s}include' % XI):
            filename = urljoin(tei_filename, inc.attrib['href'])
            surface = Surface(filename, self)
            self.surfaces.append(surface)


class Surface(object):

    def __init__(self, filename, document=None):
        self.filename = filename

        # TODO: at some point we should write the canonical coordinates to the 
        # TEI. For now it is being done dynamically with zoner, saved to a 
        # temporary file, which we then parse with a SAX Parser,

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
        # Mary Shelley is added by default for now. Need to update TEI.
        self.hands_label = "Mary Shelley"

        # Only attempt to populate Document-dependent 
        # properties when the document object is available
        if document:         
            self.hands = []
            for hand in tei.findall('.//*[@hand]'):
                h_id = hand.get('hand')[1:]
                if h_id in document.hands and h_id not in self.hands:
                    self.hands.append(h_id)
                    self.hands_label += ", %s" % document.hands[h_id]
        
        # use a SAX parser to get the line annotations
        # since we need to keep track of text offsets 

        parser = make_parser()
        handler = LineOffsetHandler()
        parser.setContentHandler(handler)
        parser.parse(tmp_filename)
        self.zones = handler.zones

    @property
    def relative_path(self):
        """
        Returns the path to the XML file in the SGA Github repository.
        """
        m = re.search('(/data/.+)', os.path.abspath(self.filename))
        return m.group(1)


class Zone(object):

    def __init__(self, attrs):
        self.ulx = attrs.get('ulx', 0)
        self.uly = attrs.get('uly', 0)
        self.lrx = attrs.get('lrx', 0)
        self.lry = attrs.get('lry', 0)
        self.begin = 0
        self.end = 0
        self.lines = []
        self.adds = []
        self.deletes = []
        self.highlights = []

    @property
    def xywh(self):
        height = int(self.lry) - int(self.uly)
        width = int(self.lrx) - int(self.ulx)
        return "xywh=%s,%s,%s,%s" % (self.ulx, self.uly, width, height)


class Line(object):
    
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""
        self.rend = None

class Add(object):
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""
        self.rend = None
        self.place = None

class Delete(object):
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""
        self.rend = None

class Highlight(object):
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""
        self.rend = None

class LineOffsetHandler(ContentHandler):
    """
    SAX Handler for extracting zones, lines, adds, deletes,
    and highlights from a TEI canvas. Each canvas is a 
    collection of zones. The lines, adds, deletes and highlights
    are added to the zone that they are a part of.
    """

    def __init__(self):
        self.zones = []
        self.pos = 0
        self.height = None
        self.width = None
        self.stack = []

    def startElement(self, name, attrs):
        if name == "zone":
            z = Zone(attrs)
            z.begin = self.pos
            self.zones.append(z)
            self.stack.append(z)
        elif name == "line":
            l = Line()
            l.begin = self.pos
            l.rend = attrs.get('rend')
            self.zones[-1].lines.append(l)
            self.stack.append(l)
        elif name == "add":
            a = Add()
            a.begin = self.pos
            a.rend = attrs.get('rend')
            a.place = attrs.get('place')
            self.zones[-1].adds.append(a)
            self.stack.append(a)
        elif name == "del":
            d = Delete()
            d.begin = self.pos
            d.rend = attrs.get('rend')
            self.zones[-1].deletes.append(d)
            self.stack.append(d)
        elif name == "hi":
            h = Highlight()
            h.begin = self.pos
            h.rend = attrs.get('rend')
            self.zones[-1].highlights.append(h)
            self.stack.append(h)

    def endElement(self, name):
        if name in ("zone", "line", "add", "del", "hi"):
            e = self.stack.pop()
            e.end = self.pos
   
    def characters(self, content):
        self.pos += len(content) # TODO: does unicode matter here?
