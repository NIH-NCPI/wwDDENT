from flask import Blueprint, Flask, url_for, render_template
from markupsafe import escape
from pprint import pformat
from ddentapp import fhirclient
from ddent import ddent_properties, build_uri
from ddentapp import system_urls

from ddentapp.translate_code import count_translations
from ddentapp import conceptmap

import pdb
bp = Blueprint("codesystem", __name__)
                            
@bp.route("/codesystem")
def list():
    codesystems = []
    # Get a list of the CUI->DD Concept maps and build up some details about the studies
    result = fhirclient().get(f"CodeSystem?url:below={ddent_properties['urlbase']}")
    for cs in result.entries:
        cs = cs['resource']
        codesystems.append(cs)
    return render_template("codesystems.html", 
                            urls=system_urls(),
                            count=len(codesystems), 
                            codesystems=codesystems)

@bp.route("/codesystem/<path:url>")
def show(url):
    url = escape(url)
    related_valuesets = []
    result = fhirclient().get(f"ValueSet?reference={url}&_element=id,url,name,identifier")
    for entry in result.entries:
        entry = entry['resource']
        related_valuesets.append(entry)
    # Get a list of the CUI->DD Concept maps and build up some details about the studies
    result = fhirclient().get(f"CodeSystem?url={url}")
    if result.success():
        #pdb.set_trace()
        #print(pformat(result.entries))
        if len(result.entries) > 0 and 'resource' in result.entries[0]:
            cs = result.entries[0]['resource']
            return render_template("codesystem.html", 
                            urls=system_urls(), 
                            cs=cs, 
                            url=url, 
                            count_translations=count_translations,
                            valuesets=related_valuesets)
        else:
            return render_template("codesystem.html", 
                            urls=system_urls(), 
                            cs=None, 
                            url=url, 
                            valuesets=None)
