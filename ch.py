#!/usr/bin/env python

import re
import json

vols = [
    "ox-frankenstein-volume_i",
    "ox-frankenstein-volume_ii",
    "ox-frankenstein-volume_iii"
]

for vol in vols:
    manifest_file = vol + "/Manifest-index.jsonld"
    manifest = json.loads(open(manifest_file).read())
    fh = open(vol + '.txt', "w")
    for canvas in manifest['sequences'][0]['canvases']:
        d, s = re.search('/data/ox/(.+)/canvas/(\d+)$', canvas).groups()
        tei_file = d + "/" + d + "-" + s + ".xml"
        fh.write('<xi:include href="' + tei_file + '" />\n')
    fh.close()
