from flask import Blueprint, Flask, url_for, render_template
from markupsafe import escape
from pprint import pformat
from ddentapp import fhirclient
from ddent.ddent import transform_dd_codesystem
from ddent.dbgap import extract_xmls_for_id, transform_to_codesystem
from ddent.nlp import default_nlp_module
from ddentapp import system_urls

from ddentapp.conceptmap import cui_conceptmaps, dd_conceptmaps
from ddentapp.translate_code import count_lookup, get_display_lookup
from flask import request

import pdb
bp = Blueprint("dbgap", __name__)
_nlp = "http://localhost:8080"

def NLP(nlp=None):
    global _nlp
    if nlp is not None:
        _nlp = nlp
    return _nlp

@bp.route("/dbgap")
def list():
    class DbGapStudy:
        def __init__(self, datachunk):
            self.study_id = datachunk.get('identifier')['value']
            self.name = datachunk.get('name')
            self.title = datachunk.get('title')
            self.desc = datachunk.get('description')
            self.id = datachunk.get('id')
            self.ddcui_url = datachunk.get('url')
            self.cuidd_url = None

        def ddcui_href(self):
            return url_for('conceptmap.show', 
                            urls=system_urls(), 
                            url=self.ddcui_url)

        def cuidd_href(self):
            return url_for('conceptmap.show', 
                            urls=system_urls(), 
                            url=self.cuidd_url)
            #return url_for('dbgap.show', fhirid=self.id)
    #pdb.set_trace()
    # Get a list of the CUI->DD Concept maps and build up some details about the studies
    result = fhirclient().get("ConceptMap?identifier=http://ddent.ncpi.someplace.org/ddent-fhir/study/cm/dd-cui|&_elements=id,identifier,url,name,title,description")

    if result.success():
        studies = {}

        for study in result.entries:
            study = DbGapStudy(study['resource'])
            studies[study.study_id] = study

        result = fhirclient().get("ConceptMap?identifier=http://ddent.ncpi.someplace.org/ddent-fhir/study/cm/cui-dd/|&_elements=id,identifier,url,name,title,description")
        
        if result.success():
            for study in result.entries:
                #print(pformat(study))
                cuidd_url = study['resource']['url']
                cuidd_id = study['resource']['identifier']['value']

                if cuidd_id in studies:
                    studies[cuidd_id].cuidd_url = cuidd_url
                else:
                    pdb.set_trace()

        return render_template("dbgap_studies.html", 
                            urls=system_urls(),
                            study_count=len(studies), 
                            studies=studies)
       
    return "This is the DbGAP index page"

@bp.route("/dbgap/<fhirid>")
def show(fhirid):
    fhirid=escape(fhirid)
    result = fhirclient().get(f"ConceptMap/{fhirid}")
    if result.success:
        print(pformat(result.entries[0]))
        return render_template("dbgap_study.html", 
                            urls=system_urls(),
                            study=result.entries[0], 
                            source_link=url_for('valueset.show', url=result.entries[0]['sourceUri']),
                            target_link=url_for('valueset.show', url=result.entries[0]['targetUri']))
    rval = "<p>This is the magical index of the DDENT web application</p>"

    print(fhirid)
    if fhirid:
        rval += f"<p>Looking for study: {fhirid}</p>"

    return rval    

@bp.route("/dbgap/new", methods=("GET", "POST"))
def new():
    if request.method == "POST":
        accid = request.form['accession_id']
        title = request.form['title']
        desc = request.form['description']

        nlp = default_nlp_module()

        codesystems = []
        xmls = extract_xmls_for_id(accid)
        if len(xmls) > 0:
            for xml in xmls.keys():
                codesystem = transform_to_codesystem(xml, tname=xmls[xml][0], tdesc=xmls[xml][1])
                codesystems.append(codesystem)

            if len(codesystem) > 0:
                tfresult = transform_dd_codesystem(accid, title, desc, codesystems, nlp, fhirclient())
                #print(f"VS: {tfresult.valueset['dd']['url']}")
                #pdb.set_trace()
                # Reset the cached concept maps to make sure the new ones
                # get loaded
                cui_conceptmaps(reset=True)
                dd_conceptmaps(reset=True)
                count_lookup(reset=True)
                get_display_lookup(reset=True)
                return render_template("dbgap_review.html", 
                                        urls=system_urls(),
                                        result=tfresult)

        else:
            return render_template("dbgap_empty_study.html",
                                        urls=system_urls(),
                                        accid=accid)

    return render_template("dbgap_new.html", 
                            urls=system_urls())