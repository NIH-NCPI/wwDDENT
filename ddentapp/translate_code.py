from flask import Blueprint, url_for, render_template
from pprint import pformat
from markupsafe import escape
from ddentapp import system_urls

from ddentapp import conceptmap# import cui_conceptmaps, dd_conceptmaps
from ddentapp import fhirclient

from collections import defaultdict

import pdb

bp = Blueprint("translate_code", __name__)

def parse_parameter(param, system, target_type=None):
    content=[]

    transurl = 'translate_code.translate'
    if target_type is not None:
        transurl += f"_{target_type}"

    #print(pformat(param))
    for p in param:
        if p['name'] == 'match':
            for part in p['part']:
                if part['name'] == 'concept':
                    part['valueCoding']['code-url'] = url_for(transurl, system=part['valueCoding']['system'], code=part['valueCoding']['code'])
                    part['valueCoding']['source-url'] = url_for('codesystem.show', url=part['valueCoding']['system'])
                    content.append(part['valueCoding'])

    return content

_count_lookup = defaultdict(dict)
def count_lookup(reset=False):
    global _count_lookup

    if reset:
        _count_lookup = defaultdict(dict)
    
    return _count_lookup

def count_translations(system, code, conceptmaps=None, target_type=None):
    lkup = count_lookup()

    if code in lkup[system]:
        return lkup[system][code]

    if conceptmaps is None:
        conceptmaps = conceptmap.cui_conceptmaps() + conceptmap.dd_conceptmaps()
    
    matches = perform_translate(system, code, conceptmaps, target_type)
    lkup[system][code] = len(matches)

    return len(matches)

def perform_translate(system, code, conceptmaps, target_type=None):
    results = []
    for cm in conceptmaps:
        #print(cm)
        #print(f"ConceptMap/{cm['id']}/$translate?code={code}")
        response = fhirclient().get(f"ConceptMap/{cm['id']}/$translate?code={code}")
        for entry in response.entries:
            #print("--------------OMG-----------")
            #print(entry)
            if 'parameter' in entry:
                results += parse_parameter(entry['parameter'], system, target_type)
    
    return results

_display_lkup = defaultdict(dict)
def get_display_lookup(reset=False):
    global _display_lkup 

    if reset:
        _display_lkup = defaultdict(dict)
    
    return _display_lkup

def get_display(system, code):

    lkup = get_display_lookup()
    if code in lkup[system]:
        return lkup[system][code]

    source_display = code

    # Get information about the source code
    url = f"CodeSystem/$lookup?system={system}&code={code}&&property=code&property=display&property=designations"
    try:
        detail_response = fhirclient().get(url)
        if detail_response.success():
            for param in detail_response.entries[0]['parameter']:
                if param['name'] == 'display':
                    source_display = param['valueString']
    except:
        url = f"CodeSystem?code={code}"
        response = fhirclient().get(url)
        if response.success():
            print(response.entries[0]['resource'].keys())
            for concept in response.entries[0]['resource']['concept']:
                localcode = concept['code']

                if localcode not in lkup[system]:
                    lkup[system][localcode] = concept['display']

                if code == localcode:
                    return concept['display']

    return source_display

@bp.route("/translate/cui/<path:system>/<code>")
def translate_cui(system, code):
    system = escape(system)
    code = escape(code)
    cms = conceptmap.cui_conceptmaps()
    source_display = code

    # Get information about the source code
    source_display = get_display(system, code)

    results = perform_translate(system, code, cms, target_type='dd')
    return render_template("translate.html", 
                            urls=system_urls(), 
                            display=source_display,
                            code=code,  
                            system=system,
                            count_translations=count_translations,
                            matches=results)

@bp.route("/translate/dd/<path:system>/<code>")
def translate_dd(system, code):
    cms = conceptmap.dd_conceptmaps()
    # Get information about the source code
    source_display = get_display(system, code)
    results = perform_translate(system, code, cms, target_type='cui')
    return render_template("translate.html", 
                            urls=system_urls(), 
                            display=source_display, 
                            code=code,  
                            system=system,
                            count_translations=count_translations,
                            matches=results)

@bp.route("/translate/<path:system>/<code>")
def translate(system, code):
    cui_results = perform_translate(system, code, conceptmap.cui_conceptmaps(), 'dd')
    dd_results = perform_translate(system, code, conceptmap.dd_conceptmaps(), 'cui')
    # Get information about the source code
    source_display = get_display(system, code)
    return render_template("translate.html", 
                            urls=system_urls(), 
                            display=source_display,
                            code=code, 
                            system=system,
                            count_translations=count_translations,
                            matches=cui_results + dd_results)
