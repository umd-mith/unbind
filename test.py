#!/usr/bin/env python

import json
import pytest

from rdflib.plugin import register, Parser
from rdflib import ConjunctiveGraph, URIRef, RDF

from unbind.tei import Document, Surface
from unbind.shared_canvas import Manifest
from unbind.namespaces import SGA

from xml.etree import ElementTree as etree


def test_doc():
    tei_file = "sga/data/tei/ox/ox-frankenstein_notebook_c1.xml"
    d = Document(tei_file)
    assert len(d.surfaces) == 36

def test_surface():
    tei_file = "sga/data/tei/ox/ox-ms_abinger_c58/ox-ms_abinger_c58-0001.xml"
    s = Surface(tei_file)
    assert s.width == 5410
    assert s.height == 6660
    assert s.shelfmark == "MS. Abinger c. 58"
    assert s.folio == "1r"
    assert s.image == "http://shelleygodwinarchive.org/images/ox/ox-ms_abinger_c58-0001.jp2"

    assert len(s.zones) == 3
    z = s.zones[2]

    assert z.xywh == "xywh:0,333,6327,5410"
    assert len(z.lines) == 15

    l = z.lines[0]
    assert l.text == 'satisfied that nothing on earth will have the power'
    assert l.begin == 25
    assert l.end == 76

def test_deletion():
    # TODO: what should we do here?
    tei_file = "sga/data/tei/ox/ox-ms_abinger_c58/ox-ms_abinger_c58-0001.xml"
    s = Surface(tei_file)
    l = s.zones[2].lines[13]

def test_addition():
    # TODO: what should we do here?
    pass

def test_jsonld():
    # generate shared canvase json-ld
    tei_file = "sga/data/tei/ox/ox-frankenstein_notebook_c1.xml"
    manifest_uri = 'http://example.com/frankenstein.json'
    m = Manifest(tei_file, manifest_uri)
    jsonld = m.jsonld()

    # sanity check the json-ld
    manifest = None
    for r in jsonld['@graph']:
        if '@type' in r and r['@type'] == 'sc:Manifest':
            manifest = r
    assert manifest
    print json.dumps(manifest, indent=2)
    assert 'images' in manifest

    # parse the json-ld as rdf
    register('json-ld', Parser, 'rdflib_jsonld.parser', 'JsonLDParser')
    g = ConjunctiveGraph()
    jsonld_str = json.dumps(jsonld)
    g.parse(data=jsonld_str, format='json-ld')

    # sanity check the graph
    assert g.value(URIRef('http://example.com/frankenstein.json'), RDF.type) == URIRef('http://www.shared-canvas.org/ns/Manifest')
    line_anns = list(g.triples((None, RDF.type, SGA.LineAnnotation)))
    assert len(line_anns) == 638
    
