#!/usr/bin/env python

import re
import sys
import tei
import json
import pyld

from six.moves.urllib.parse import urljoin
from rdflib.plugin import register, Parser, Serializer
from rdflib import ConjunctiveGraph, URIRef, RDF, RDFS, BNode, Literal

from .namespaces import DC, OA, OAX, ORE, SC, SGA, TEI, EXIF, CNT


class Manifest(object):

    def __init__(self, tei_filename, manifest_uri, page=None):
        """
        Create a Shared Canvas manifest using the path to a given TEI file 
        and the URI where the manifest will be published. 

        m = Manifest("/path/to/tei.xml", "http://example.com/manifest.jsonld")
        
        Optionally pass in a page number if you are debugging and want 
        to limit the manifest to a specific page.
        """

        g = self.g = ConjunctiveGraph()
        self.tei = tei.Document(tei_filename)
        self.uri = URIRef(manifest_uri)

        ta = self.text_annotations = BNode()
        g.add((self.uri, ORE.aggregates, ta))
        g.add((ta, RDF.type, ORE.Aggregation))
        g.add((ta, RDF.type, SC.AnnotationList))
        g.add((ta, RDF.type, SC.Layer))
        g.add((ta, RDFS.label, Literal("Transcription")))
        g.add((ta, SC.forMotivation, SC.painting))

        za = self.zone_annotations = BNode()
        g.add((self.uri, ORE.aggregates, za))
        g.add((za, RDF.type, ORE.Aggregation))
        g.add((za, RDF.type, SC.AnnotationList))
        g.add((za, RDF.type, SC.Layer))
        g.add((za, RDFS.label, Literal("Zones")))

        ha = self.html_annotations = BNode()
        g.add((self.uri, ORE.aggregates, ha))
        g.add((ha, RDF.type, SC.AnnotationList))
        g.add((ha, RDF.type, ORE.Aggregation))
        g.add((ha, RDF.type, SC.Layer))
        g.add((ha, SC.forMotivation, SGA.reading))
        g.add((ha, RDFS.label, Literal("Reading layer")))

        xa = self.xml_annotations = BNode()
        g.add((self.uri, ORE.aggregates, xa))
        g.add((xa, RDF.type, SC.AnnotationList))
        g.add((xa, RDF.type, ORE.Aggregation))
        g.add((xa, RDF.type, SC.Layer))
        g.add((xa, SC.forMotivation, SGA.source))
        g.add((xa, RDFS.label, Literal("TEI source")))

        self._build(page)

    def jsonld(self, indent=2):
        # somewhat inefficient since we are serializing the json
        # and then reading it back in, to compact it with jsonld
        # jsonld's compaction actually works properly with the context
        # unlike rdflib_jsonld's at the moment. Ideally we could 
        # also use rdflib_jsonld.serlializer.from_rdf to skip 
        # the serialization, but unofortunately it seems to introduce 
        # errors into the graph.
        j = self.g.serialize(format='json-ld')
        j = json.loads(j)
        j = pyld.jsonld.compact(j, self._context())
        return j

    def tei_url(self, surface):
        path = surface.relative_path
        path = path.replace('/data', '')
        return urljoin(self.uri, path)

    def html_url(self, surface):
        # a hack until we've got a better way of coordinating the deployment
        # of the xml, html and images
        html_url = 'http://shelleygodwinarchive.org/tei/readingTEI/html'
        html_url += surface.relative_path.replace('/data/tei/ox', '')
        html_url = html_url.replace('.xml', '.html')
        return html_url

    def _build(self, page=None):
        self.g.add((self.uri, RDF.type, SC.Manifest))
        self.g.add((self.uri, RDFS.label, Literal(self.tei.label)))
        self.g.add((self.uri, DC.title, Literal(self.tei.title)))
        self.g.add((self.uri, SC.agentLabel, Literal(self.tei.agent)))
        self.g.add((self.uri, SC.attributionLabel, Literal(self.tei.agent)))
        self.g.add((self.uri, SC.dateLabel, Literal(self.tei.date)))
        self.g.add((self.uri, SGA.stateLabel, Literal(self.tei.state)))
        self.g.add((self.uri, SC.service, URIRef(self.tei.service)))
        self._add_canvases(page)

    def _add_canvases(self, page=None):
        g = self.g

        # add the list of sequences
        sequences_uri = BNode()
        g.add((self.uri, SC.hasSequences, sequences_uri))
        g.add((sequences_uri, RDF.type, RDF.List))

        # add the sequence, which itself is list of canvases
        sequence_uri = BNode()
        g.add((sequences_uri, RDF.first, sequence_uri))
        g.add((sequences_uri, RDF.rest, RDF.nil))
        g.add((sequence_uri, RDF.type, SC.Sequence))
        g.add((sequence_uri, RDF.type, RDF.List))
        g.add((sequence_uri, RDF.rest, RDF.nil))
        g.add((sequence_uri, RDFS.label, Literal("Physical sequence")))

        # add the image list
        image_list_uri = BNode()
        g.add((self.uri, SC.hasImageAnnotations, image_list_uri))
        g.add((image_list_uri, RDF.type, RDF.List))

        # add the canvas list
        canvas_list_uri = BNode()
        g.add((self.uri, SC.hasCanvases, canvas_list_uri))
        g.add((canvas_list_uri, RDF.type, RDF.List))

        # now add each surface
        page_count=0

        for surface in self.tei.surfaces:

            page_count += 1
            if page is not None and page_count != page:
                continue

            # add the canvas
            canvas_uri = BNode()
            g.add((canvas_uri, RDF.type, SC.Canvas))
            g.add((canvas_uri, RDFS.label, Literal(surface.folio)))
            g.add((canvas_uri, SGA.folioLabel, Literal(surface.folio)))
            g.add((canvas_uri, SGA.shelfmarkLabel, Literal(surface.shelfmark)))
            g.add((canvas_uri, SGA.handLabel, Literal(surface.hands_label)))
            g.add((canvas_uri, EXIF.height, Literal(surface.height)))
            g.add((canvas_uri, EXIF.width, Literal(surface.width)))
            g.add((canvas_list_uri, RDF.first, canvas_uri))
            next_canvas_list_uri = BNode()
            g.add((canvas_list_uri, RDF.rest, next_canvas_list_uri))
            canvas_list_uri = next_canvas_list_uri

            # add the image
            image_uri = URIRef(surface.image)
            g.add((image_uri, DC['format'], Literal('image/jp2')))
            g.add((image_uri, EXIF.height, Literal(surface.height)))
            g.add((image_uri, EXIF.width, Literal(surface.width)))
            g.add((image_uri, SC.hasRelatedService, URIRef("http://shelleygodwinarchive.org/adore-djatoka/resolver")))

            # add the image annotation
            image_ann_uri = BNode()
            g.add((image_ann_uri, RDF.type, OA.Annotation))
            g.add((image_ann_uri, OA.hasTarget, canvas_uri))
            g.add((image_ann_uri, OA.hasBody, URIRef(surface.image)))
            g.add((image_list_uri, RDF.first, image_ann_uri))
            next_image_list_uri = BNode()
            g.add((image_list_uri, RDF.rest, next_image_list_uri))
            image_list_uri = next_image_list_uri
 
            # add the canvas to the sequence
            g.add((sequence_uri, RDF.first, canvas_uri))
            next_sequence_uri = BNode()
            g.add((sequence_uri, RDF.rest, next_sequence_uri))
            sequence_uri = next_sequence_uri

            # add the zone annotations
            self._add_zone_annotations(surface, canvas_uri)

            # add the line annotations
            self._add_text_annotations(surface)

            # add the html annotations
            self._add_html_annotations(surface, canvas_uri)

            # add the xml annotations
            self._add_xml_annotations(surface, canvas_uri)

        # close off the sequence list
        g.add((sequence_uri, RDF.rest, RDF.nil))
        g.add((image_list_uri, RDF.rest, RDF.nil))
        g.add((canvas_list_uri, RDF.rest, RDF.nil))

    def _add_zone_annotations(self, surface, canvas):
        g = self.g

        for zone in surface.zones:

            annotation = BNode()
            g.add((self.zone_annotations, ORE.aggregates, annotation))
            g.add((annotation, RDF.type, OA.Annotation))
            g.add((annotation, RDF.type, SC.ContentAnnotation))

            body = BNode()
            g.add((annotation, OA.hasBody, body))
            g.add((body, RDF.type, OA.SpecificResource))

            # construct a URL for the tei xml file assuming that the 
            # sga data is mounted next to the manifest
            g.add((body, OA.hasSource, URIRef(self.tei_url(surface))))

            selector = BNode()
            g.add((body, OA.hasSelector, selector))
            g.add((selector, RDF.type, OAX.TextOffsetSelector))
            g.add((selector, OAX.begin, Literal(zone.begin)))
            g.add((selector, OAX.end, Literal(zone.end)))

            target = BNode()
            g.add((annotation, OA.hasTarget, target))
            g.add((target, RDF.type, OA.SpecificResource))
            g.add((target, OA.hasSource, canvas))

            selector = BNode()
            g.add((target, OA.hasSelector, selector))
            g.add((selector, RDF.type, OA.FragmentSelector))
            g.add((selector, RDF.value, Literal(zone.xywh)))

    def _add_text_annotations(self, surface):
        g = self.g

        for zone in surface.zones:
            # TODO: process adds, deletes and highlights too
            for line in zone.lines:
                self._add_text_annotation(line, surface)
            for add in zone.adds:
                self._add_text_annotation(add, surface)
            for delete in zone.deletes:
                self._add_text_annotation(delete, surface)
            for space in zone.spaces:
                self._add_text_annotation(space, surface)

    def _add_text_annotation(self, a, surface):
        # Skip possible *Span elements that failed to get an end pos
        if not a.end:
            return 0

        g = self.g
        if type(a) == tei.Line:
            ann_type = SGA.LineAnnotation
        elif type(a) == tei.Delete:
            ann_type = SGA.DeletionAnnotation
        elif type(a) == tei.Add:
            ann_type = SGA.AdditionAnnotation
        elif type(a) == tei.Space:
            ann_type = SGA.SpaceAnnotation

        # link AnnotationList to Annotation
        annotation = BNode()
        g.add((self.text_annotations, ORE.aggregates, annotation))
        g.add((annotation, RDF.type, ann_type))
        g.add((annotation, RDF.type, OAX.Highlight))

        # add rendering styles
        if a.rend:
            m = re.match('indent(\d+)', a.rend)
            if m:
                indent = int(m.group(1))
                g.add((annotation, SGA.textIndentLevel, Literal(indent)))
            else:
                g.add((annotation, SGA.textAlignment, Literal(a.rend)))
        if ann_type == SGA.SpaceAnnotation:
            g.add((annotation, SGA.spaceExt, Literal(a.ext)))
   
        # link LineAnnotation to SpecificResource and TEI file
        target = BNode()
        g.add((annotation, OA.hasTarget, target))
        g.add((target, RDF.type, OA.SpecificResource))
        g.add((target, OA.hasSource, URIRef(self.tei_url(surface))))

        if a.hand:
            g.add((target, SGA.hasClass, Literal('hand-' + a.hand)))

        # link SpecificResource and TextOffsetSelector
        selector = BNode()
        g.add((target, OA.hasSelector, selector))
        g.add((selector, RDF.type, OAX.TextOffsetSelector))
        g.add((selector, OAX.begin, Literal(a.begin)))
        g.add((selector, OAX.end, Literal(a.end)))

        # link SpecificResource to CSS as needed
        if ann_type == SGA.AdditionAnnotation and a.place: 
            if a.place == "superlinear":
                text = "vertical-align: super;"
            elif a.place == "sublinear":
                text = "vertical-align: sub;"
            else:
                text = None
            if text:
                css = BNode()
                g.add((target, OA.hasStyle, css))
                g.add((css, RDF.type, CNT.ContentAsText))
                g.add((css, DC['format'], Literal("text/css")))
                g.add((css, CNT.chars, Literal(text)))

    def _add_html_annotations(self, surface, canvas_uri):
        ann = BNode()
        g = self.g
        g.add((self.html_annotations, ORE.aggregates, ann))
        g.add((ann, RDF.type, OA.Annotation))
        g.add((ann, SC.motivatedBy, SGA.reading))
        g.add((ann, OA.hasTarget, canvas_uri))
        g.add((ann, OA.hasBody, URIRef(self.html_url(surface))))

    def _add_xml_annotations(self, surface, canvas_uri):
        ann = BNode()
        g = self.g
        g.add((self.xml_annotations, ORE.aggregates, ann))
        g.add((ann, RDF.type, OA.Annotation))
        g.add((ann, SC.motivatedBy, SGA.source))
        g.add((ann, OA.hasTarget, canvas_uri))
        g.add((ann, OA.hasBody, URIRef(self.tei_url(surface))))

    def _context(self):
      # TODO: pare this down, and make it more sane over time
      # We should only be asserting things that are needed by the viewer
      return {
        "sc" : "http://www.shared-canvas.org/ns/",
        "sga" : "http://www.shelleygodwinarchive.org/ns1#",
        "ore" : "http://www.openarchives.org/ore/terms/",
        "exif" : "http://www.w3.org/2003/12/exif/ns#",
        "iiif" : "http://library.stanford.edu/iiif/image-api/ns/",
        "oa" : "http://www.w3.org/ns/openannotation/core/",
        "oax" : "http://www.w3.org/ns/openannotation/extension/",
        "cnt" : "http://www.w3.org/2011/content#",
        "dc" : "http://purl.org/dc/elements/1.1/",
        "dcterms" : "http://purl.org/dc/terms/",
        "dctypes" : "http://purl.org/dc/dcmitype/",
        "foaf" : "http://xmlns.com/foaf/0.1/",
        "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs" : "http://www.w3.org/2000/01/rdf-schema#",
        "skos" : "http://www.w3.org/2004/02/skos/core#",
        "xsd" : "http://www.w3.org/2001/XMLSchema#",
        "license" : {
          "@type" : "@id",
          "@id" : "dcterms:license"
        },
        "service" : {
          "@type" : "@id",
          "@id" : "sc:hasRelatedService"
        },
        "seeAlso" : {
          "@type" : "@id",
          "@id" : "sc:hasRelatedDescription"
        },
        "within" : {
          "@type" : "@id",
          "@id" : "dcterms:isPartOf"
        },
        "profile" : {
          "@type" : "@id",
          "@id" : "dcterms:conformsTo"
        },
        "sequences" : {
          "@type" : "@id",
          "@id" : "sc:hasSequences",
          "@container" : "@list"
        },
        "canvases" : {
          "@type" : "@id",
          "@id" : "sc:hasCanvases",
          "@container" : "@list"
        },
        "resources" : {
          "@type" : "@id",
          "@id" : "sc:hasAnnotations",
          "@container" : "@list"
        },
        "images" : {
          "@type" : "@id",
          "@id" : "sc:hasImageAnnotations",
          "@container" : "@list"
        },
        "otherContent" : {
          "@type" : "@id",
          "@id" : "sc:hasLists",
          "@container" : "@list"
        },
        "structures" : {
          "@type" : "@id",
          "@id" : "sc:hasRanges",
          "@container" : "@list"
        },
        "metadata" : {
          "@type" : "@id",
          "@id" : "sc:metadataLabels",
          "@container" : "@list"
        },
        "description" : "dc:description",
        "attribution" : "sc:attributionLabel",
        "height" : {
          "@id" : "exif:height"
        },
        "width" : {
          "@id" : "exif:width"
        },
        "viewingDirection" : "sc:viewingDirection",
        "viewingHint" : "sc:viewingHint",
        "tile_height" : {
          "@type" : "xsd:integer",
          "@id" : "iiif:tileHeight"
        },
        "tile_width" : {
          "@type" : "xsd:integer",
          "@id" : "iiif:tileWidth"
        },
        "scale_factors" : {
          "@id" : "iiif:scaleFactor",
          "@container" : "@list"
        },
        "formats" : {
          "@id" : "iiif:formats",
          "@container" : "@list"
        },
        "qualities" : {
          "@id" : "iiif:qualities",
          "@container" : "@list"
        },
        "motivation" : {
          "@type" : "@id",
          "@id" : "oa:motivatedBy"
        },
        "resource" : {
          "@type" : "@id",
          "@id" : "oa:hasBody"
        },
        "on" : {
          "@type" : "@id",
          "@id" : "oa:hasTarget"
        },
        "full" : {
          "@type" : "@id",
          "@id" : "oa:hasSource"
        },
        "selector" : {
          "@type" : "@id",
          "@id" : "oa:hasSelector"
        },
        "stylesheet" : {
          "@type" : "@id",
          "@id" : "oa:styledBy"
        },
        "style" : "oa:styleClass",
        "painting" : "sc:painting",
        "hasState" : {
          "@type" : "@id",
          "@id" : "oa:hasState"
        },
        "hasScope" : {
          "@type" : "@id",
          "@id" : "oa:hasScope"
        },
        "annotatedBy" : {
          "@type" : "@id",
          "@id" : "oa:annotatedBy"
        },
        "serializedBy" : {
          "@type" : "@id",
          "@id" : "oa:serializedBy"
        },
        "equivalentTo" : {
          "@type" : "@id",
          "@id" : "oa:equivalentTo"
        },
        "cachedSource" : {
          "@type" : "@id",
          "@id" : "oa:cachedSource"
        },
        "conformsTo" : {
          "@type" : "@id",
          "@id" : "dcterms:conformsTo"
        },
        "default" : {
          "@type" : "@id",
          "@id" : "oa:default"
        },
        "item" : {
          "@type" : "@id",
          "@id" : "oa:item"
        },
        "first" : {
          "@type" : "@id",
          "@id" : "rdf:first"
        },
        "rest" : {
          "@type" : "@id",
          "@id" : "rdf:rest",
          "@container" : "@list"
        },
        "beginOffset" : {
          "@id" : "oax:begin"
        },
        "endOffset" : {
          "@id" : "oax:end"
        },
        "textOffsetSelector" : {
          "@type" : "@id",
          "@id" : "oax:TextOffsetSelector"
        },
        "chars" : "cnt:chars",
        "encoding" : "cnt:characterEncoding",
        "bytes" : "cnt:bytes",
        "format" : "dc:format",
        "language" : "dc:language",
        "annotatedAt" : "oa:annotatedAt",
        "serializedAt" : "oa:serializedAt",
        "when" : "oa:when",
        "value" : "rdf:value",
        "start" : "oa:start",
        "end" : "oa:end",
        "exact" : "oa:exact",
        "prefix" : "oa:prefix",
        "suffix" : "oa:suffix",
        "label" : "rdfs:label",
        "name" : "foaf:name",
        "mbox" : "foaf:mbox"
      }

register('json-ld', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')
