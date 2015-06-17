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
        ns = {'tei': TEI, 'xi': XI, 'xml': XML}
        tei = etree.parse(tei_filename).getroot()

        # extract some document level metadata
        page_sequence = re.sub(r'[_-]', '/', tei.get('{%(xml)s}id' % ns))
        self.title = tei.find('.//{%(tei)s}msItem[@class="#work"][0]/{%(tei)s}bibl/{%(tei)s}title' % ns).text
        self.agent = tei.find('.//{%(tei)s}msItem[@class="#work"][0]/{%(tei)s}bibl/{%(tei)s}author' % ns).text
        self.attribution = tei.find('.//{%(tei)s}repository' % ns).text
        self.date = tei.find('.//{%(tei)s}msItem/{%(tei)s}bibl/{%(tei)s}date' % ns).text
        self.service = "http://shelleygodwinarchive.org/sc/%s" % page_sequence
        self.state = tei.find('.//{%(tei)s}msItem[@class="#work"]/{%(tei)s}bibl' % ns).get("status").replace("_", " ")
        self.label = tei.find('.//{%(tei)s}titleStmt/{%(tei)s}title[@type="main"]' % ns).text

        # get the hands that are used
        self.hands = {}
        for hand in tei.findall('.//{%(tei)s}physDesc//{%(tei)s}handNote[@{%(xml)s}id]' % ns):
            self.hands[hand.get('{%(xml)s}id' % ns)] = hand.findall('{%(tei)s}persName' % ns)[0].text

        # get all loci to locate works scattered across pages
        self.work_loci = {}
        for work in tei.findall('.//{%(tei)s}msItem[@class="#work"]' % ns):
            title = work.find('./{%(tei)s}bibl/{%(tei)s}title' % ns).text
            title = title.strip()
            for locus in work.findall('.//{%(tei)s}locus' % ns):                
                if locus.attrib.get('target'):
                    targets = re.split(r'\s+', locus.attrib.get('target').strip())
                    for target in targets:
                        target = target.lstrip("#")
                        self.work_loci[target] = title.lower().replace(' ', '_')

        # load each surface
        self.surfaces = []
        for inc in tei.findall('.//{%(tei)s}sourceDoc/{%(xi)s}include' % ns):
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
        self.xmlid = tei.attrib.get('{%s}id' % XML)
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
        handler = LineOffsetHandler(document, self)
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
        self.type = None
        self.begin = 0
        self.end = 0
        self.lines = []
        self.segments = []
        self.adds = []
        self.deletes = []
        self.highlights = []
        self.spaces = []

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
        self.hand = None
        self.hand_attr = None
        self.in_work = None

class Segment(object):
    ''' A generic text segment encoded with milestones '''
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""
        self.spanTo = None
        self.rend = None
        self.hand = None
        self.hand_attr = None
        self.in_work = None

class Space(object):    
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""
        self.rend = None
        self.hand = None
        self.hand_attr = None
        self.ext = 0

class Add(object):
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.spanTo = None
        self.text = ""
        self.rend = None
        self.place = None
        self.hand = None
        self.hand_attr = None

class Delete(object):
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.spanTo = None
        self.text = ""
        self.rend = None
        self.hand = None
        self.hand_attr = None

class Highlight(object):
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.text = ""
        self.rend = None
        self.hand = None
        self.hand_attr = None

class LineOffsetHandler(ContentHandler):
    """
    SAX Handler for extracting zones, lines, adds, deletes,
    and highlights from a TEI canvas. Each canvas is a 
    collection of zones. The lines, adds, deletes and highlights
    are added to the zone that they are a part of.
    """

    def __init__(self, document=None, surface=None):
        self.document = document
        self.surface = surface
        self.zones = []
        self.pos = 0
        self.height = None
        self.width = None
        self.hand_stack = ["mws"] # We must assume mws as default. This needs to be fixed in the TEI.
        self.work_stack = []
        self.stack = []

    def startElement(self, name, attrs):

        def _determine_hand(hand):
            if hand:
                if hand[0]=="#": hand = hand[1:]
                if self.hand_stack[-1] != hand:
                    self.hand_stack.append(hand)
                return hand
            return self.hand_stack[-1]

        def _is_in_work(xmlid):
            if xmlid:
                xmlid = xmlid.strip()
                if xmlid in self.document.work_loci.keys():
                    return self.document.work_loci[xmlid]
            else:
                s_xmlid = self.surface.xmlid.strip()
                if s_xmlid in self.document.work_loci.keys():
                    return self.document.work_loci[s_xmlid]
            return False

        if name == "zone":
            z = Zone(attrs)
            z.begin = self.pos
            z.type = attrs.get("type")
            self.zones.append(z)
            self.stack.append(z)
        elif name == "line":
            l = Line()
            l.begin = self.pos
            l.rend = attrs.get('rend')
            l.hand_attr = attrs.get('hand')
            l.hand = _determine_hand(l.hand_attr)
            l.in_work = _is_in_work(attrs.get('xml:id'))
            self.zones[-1].lines.append(l)
            self.stack.append(l)
        elif name == "add":
            a = Add()
            a.begin = self.pos
            a.rend = attrs.get('rend')
            a.place = attrs.get('place')
            a.hand_attr = attrs.get('hand')
            a.hand = _determine_hand(a.hand_attr)
            self.zones[-1].adds.append(a)
            self.stack.append(a)
        elif name == "addSpan":
            d = Add()
            d.begin = self.pos
            d.spanTo = attrs.get('spanTo').lstrip('#')
            d.rend = attrs.get('rend')
            d.hand_attr = attrs.get('hand')
            d.hand = _determine_hand(d.hand_attr)
            self.zones[-1].adds.append(d)
        elif name == "del":
            d = Delete()
            d.begin = self.pos
            d.rend = attrs.get('rend')
            d.hand_attr = attrs.get('hand')
            d.hand = _determine_hand(d.hand_attr)
            self.stack.append(d)
            # Don't add it to a zone if it's unmarked
            if d.rend != 'unmarked':
                self.zones[-1].deletes.append(d)
        elif name == "delSpan":
            d = Delete()
            d.begin = self.pos
            d.spanTo = attrs.get('spanTo').lstrip('#')
            d.rend = attrs.get('rend')
            d.hand_attr = attrs.get('hand')
            d.hand = _determine_hand(d.hand_attr)
            # Don't add it to a zone if it's unmarked
            if d.rend != 'unmarked':
                self.zones[-1].deletes.append(d)
        elif name == "hi":
            h = Highlight()
            h.begin = self.pos
            h.rend = attrs.get('rend')
            h.hand_attr = attrs.get('hand')
            h.hand = _determine_hand(h.hand_attr)
            self.zones[-1].highlights.append(h)
            self.stack.append(h)
        elif name == "handShift":
            hand = attrs.get('new')
            if hand:
                if hand[0]=="#": hand = hand[1:]
                if self.hand_stack[-1] != hand:
                    # set new hand at the top of the stack
                    self.hand_stack[-1] = hand
        elif name == "milestone":
            if attrs.get('unit') == 'tei:seg':
                xmlid = attrs.get('xml:id')
                work = _is_in_work(xmlid)
                if work:
                    s = Segment()
                    s.begin = self.pos
                    s.hand_attr = attrs.get('hand')
                    s.hand = _determine_hand(s.hand_attr)
                    s.in_work = work
                    s.spanTo = attrs.get('spanTo').lstrip('#')
                    self.zones[-1].segments.append(s)
        # Turn vertical spaces into lines
        elif name == "space":
            if attrs.get('dim') == 'vertical':
                s = Space()
                s.begin = self.pos
                s.end = self.pos
                s.ext = int(attrs.get('extent'))
                self.zones[-1].spaces.append(s)
        elif name == "anchor":
            # anchors must always occur after the anchored element
            # so looking back is safe
            anchor_id = attrs.get('xml:id')
            for zone in self.zones:
                for delete in zone.deletes:
                    spanTo = delete.spanTo
                    if spanTo and spanTo == anchor_id:
                        delete.end = self.pos
                for add in zone.adds:
                    spanTo = add.spanTo
                    if spanTo and spanTo == anchor_id:
                        add.end = self.pos
                for segment in zone.segments:
                    spanTo = segment.spanTo
                    if spanTo and spanTo == anchor_id:
                        segment.end = self.pos

    def endElement(self, name):
        if name in ("zone", "line", "add", "del", "hi"):
            e = self.stack.pop()
            e.end = self.pos
            # pop hand from stack if it was specified as an attribute            
            if name != "zone":
                hand = e.hand_attr
                if hand and hand[0]=="#": hand = hand[1:]
                # make sure to keep "mws" at the bottom of the hand stack
                if len(self.hand_stack) > 1 and hand == self.hand_stack[-1]:
                    self.hand_stack.pop()
   
    def characters(self, content):
        self.pos += len(content) # TODO: does unicode matter here?
