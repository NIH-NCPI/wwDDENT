from flask import Blueprint, url_for, render_template
from pprint import pformat
from markupsafe import escape

from ddentapp import fhirclient
from ddentapp import system_urls

from ddentapp.translate_code import count_translations

import pdb

bp = Blueprint("conceptmap", __name__)

_cui_conceptmaps = []
_dd_conceptmaps = []

def cui_conceptmaps(reset=False):
    global _cui_conceptmaps

    if reset:
        _cui_conceptmaps = []
    if len(_cui_conceptmaps) == 0:
        response = fhirclient().get(f"ConceptMap?url:below=http://ddent.ncpi.someplace.org/ddent-fhir/ConceptMap/CUI")

        for entry in response.entries:
            entry = entry['resource']
            _cui_conceptmaps.append(entry)
    return _cui_conceptmaps

def dd_conceptmaps(reset=False):
    global _dd_conceptmaps
    if reset:
        _dd_conceptmaps = []
    if len(_dd_conceptmaps) == 0:
        response = fhirclient().get(f"ConceptMap?url:below=http://ddent.ncpi.someplace.org/ddent-fhir/ConceptMap/DD")

        for entry in response.entries:
            entry = entry['resource']
            _dd_conceptmaps.append(entry)
    
    return _dd_conceptmaps

@bp.route("/conceptmap")
def list():
    global _cui_conceptmaps, _dd_conceptmaps
    conceptmaps = cui_conceptmaps() + dd_conceptmaps()

    return render_template("conceptmaps.html", 
                        urls=system_urls(),
                        count=len(conceptmaps), 
                        cuis=_cui_conceptmaps, 
                        dds=_dd_conceptmaps)

@bp.route("/conceptmap/<path:url>")
def show(url):
    url=escape(url)
    response = fhirclient().get(f"ConceptMap?url={url}")
    #print(f"\n\n\nPulling concept map: ConceptMap?url={url}")
    #print(pformat(response.entries))

    if len(response.entries) > 0:
        if 'resource' in response.entries[0]:
            conceptmap = response.entries[0]['resource']

            source_type = conceptmap['sourceUri'].split("/")[-2]
            target_type = conceptmap['targetUri'].split("/")[-2]

            source = url_for('valueset.show', url=conceptmap['sourceUri'])
            target = url_for('valueset.show', url=conceptmap['targetUri'])
            return render_template("conceptmap.html", 
                                    urls=system_urls(),
                                    cm=conceptmap, 
                                    source=source, 
                                    target=target,
                                    count_translations=count_translations,
                                    conceptmaps=cui_conceptmaps() + dd_conceptmaps())
        else:
            return render_template("conceptmap_missing.html", 
                                    urls=system_urls(),
                                    url=url
                                    )
    return render_template("conceptmap_missing.html", 
                                    urls=system_urls(),
                                    url=url
                                    )
