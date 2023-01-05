from typing import DefaultDict
from flask import Blueprint, Flask, url_for, render_template
from markupsafe import escape
from pprint import pformat
from ddentapp import fhirclient
from ddentapp import system_urls
import collections

from ddent import ddent_properties

import pdb
bp = Blueprint("valueset", __name__)

@bp.route("/valuset")
def list():
    valuesets = []
    # Get a list of the CUI->DD Concept maps and build up some details about the studies
    result = fhirclient().get(f"ValueSet?url:below={ddent_properties['urlbase']}")
    for vs in result.entries:
        vs = vs['resource']
        #print(pformat(cs))
        vs['ddent-url'] = url_for('valueset.show', url=vs['url'])
        valuesets.append(vs)
    return render_template("valuesets.html", 
                            urls=system_urls(),
                            count=len(valuesets), 
                            valuesets=valuesets)

@bp.route("/valueset/<path:url>")
def show(url):
    url = escape(url)
    # Get a list of the CUI->DD Concept maps and build up some details about the studies
    try:
        result = fhirclient().get(f"ValueSet/$expand?url={url}")
    except:
        pdb.set_trace()
        return render_template("valueset.html", 
                            urls=system_urls(), 
                            url=url,
                            vs=None, 
                            included_systems={})
    #pdb.set_trace()
    if result.success():
        if "expansion" in result.entries[0]:
            codings = {}

            for concept in result.entries[0]['expansion']['contains']:
                c_system = concept['system']
                vs_concept = {
                    "code": concept['code'],
                    "display": concept['display'],
                    "url": url_for('translate_code.translate', code=concept['code'], system=c_system)
                }

                if c_system not in codings:
                    codings[c_system] = []
                codings[c_system].append(vs_concept)

            for system in codings:
                codings[system] = ((url_for('codesystem.show', url=system), 
                                    system.split('/')[-1]), 
                                    codings[system])
            return render_template("valueset.html", 
                            urls=system_urls(), 
                            vs=result.entries[0], 
                            url=url,
                            included_systems=codings)
        #pdb.set_trace()
        includes = {}
        for include_chunk in result.entries[0]['compose']['include']:
            concepts = []
            #pdb.set_trace()
            print(include_chunk)
            if 'concept' in include_chunk:
                for concept in include_chunk['concept']:
                    print(concept)
                    concepts.append({
                        "code": concept['code'],
                        "display": concept['display'],
                        "url": url_for('translate_code.translate', code=concept['code'])
                    })
            includes[include_chunk['system']] = ((url_for('codesystem.show', url=include_chunk['system']), 
                                                include_chunk['system'].split('/')[-1]), 
                                                concepts)
        return render_template("valueset.html", 
                            urls=system_urls(), 
                            vs=result.entries[0], 
                            included_systems=includes)

