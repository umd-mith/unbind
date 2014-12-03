# unbind

[![Build Status](https://travis-ci.org/umd-mith/unbind.svg)](http://travis-ci.org/umd-mith/unbind)

unbind is a Python utility for generating a [Shared Canvas](http://iiif.io/model/shared-canvas/1.0/index.html) manifest from [Shelley-Godwin TEI](http://github.com/umd-mith/sga/). It's also a work in progress...

## Setup

    git clone https://github.com/umd-mith/unbind.git
    cd unbind
    pip install -r requirements.txt
    python setup.py install

or if you'd rather install it so you can work on it:

    python setup.py develop

## Command Line

When you install you will get a command line program `unbind` which you 
can pass the path to a TEI file and the URI you'd like to use for the 
manifest, and it will write a Shared Canvas document as JSON-LD to stdout:

    % unbind /path/to/tei.xml http://example.com/manifest.jsonld > manifest.jsonld

##  As a Library

To create a manifest programatically you need to give `Manifest` the path to a 
TEI XML file, and also the URI where the manifest is going to be published:

```python

from unbind.shared_canvas import Manifest

m = Manifest("/path/to/a/tei/file.xml", "http://example.com/manifest.jsonld")
print m.jsonld()
```

## Test

To run the tests you will need a copy of the Shelley-Godwin TEI data:

    git clone https://github.com/umd-mith/sga.git

then:

    python setup.py test
