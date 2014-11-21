# unbind

[![Build Status](https://travis-ci.org/umd-mith/unbind.svg)](http://travis-ci.org/umd-mith/unbind)

unbind is a Python utility for generating a [Shared Canvas](http://iiif.io/model/shared-canvas/1.0/index.html) manifest from [Shelley-Godwin TEI](http://github.com/umd-mith/sga/). It's also a work in progress...

## Setup

    python setup.py install

## Command Line

When you install you will get a command line program `unbind` which you 
can pass the path to a TEI file and the URI you'd like to use for the 
manifest, and it will print out a Shared Canvas document as JSON-LD:

    % unbind /path/to/tei.xml http://example.com/manifest.jsonld > manifest.jsonld

##  As a Library

```python

from unbind.shared_canvas import Manifest

m = Manifest("/path/to/a/tei/file.xml")
print m.jsonld()
```

## Test

To run the tests you will need a copy of the Shelley-Godwin TEI data:

    git clone https://github.com/umd-mith/sga.git

then:

    python setup.py test
