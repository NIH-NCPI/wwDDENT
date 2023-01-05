""" CodeSystem Stub

For the time being, we'll cache all of our values as a linear list of codes and 
add to them as we go. The system will be able to "push" updates as it goes. The
other option is to deal with loading full code systems into the system which 
isn't necessarily a trivial task. 

"""
import re
from terminologies import NameCui, NameRxNorm, NameSnomed
import pdb

_basecs_snomed = {      
    "resourceType": "CodeSystem",
    "id": "snomed-ct",
    "url": "http://snomed.info/sct",
    "name": "snomed-ct",
    "title": "SNOMED CT",
    "status": "draft",
    "experimental": False,
    "description": "SNOMED CT",
    "caseSensitive": True
}

_basecs_umls = {
    "resourceType" : "CodeSystem",
    "url" : "http://terminology.hl7.org/CodeSystem/umls",
    "identifier" : [
        {
            "system" : "urn:ietf:rfc:3986",
            "value" : "urn:oid:2.16.840.1.113883.6.86"
        }
    ],
    "version" : "2.0.0",
    "name" : "Umls",
    "title" : "Unified Medical Language System",
    "status" : "active",
    "experimental" : False,
    "description" : "UMLS codes as CUIs making up the values in a coding system. More information may be found at http://www.nlm.nih.gov/research/umls/",
}

_basecs_rxnorm = {
    "resourceType": "CodeSystem",
    "id": "rxnorm",
    "url": "http://www.nlm.nih.gov/research/umls/rxnorm",
    "name": "RxNorm",
    "title": "RxNorm",
    "status": "draft",
    "experimental": False,
    "description": "RxNorm",
    "caseSensitive": True
}

class CuiSystem:
    def __init__(self, name, regex, use_findall, base_cs, display_source=None):
        self.name = name
        self.matchers = [re.compile(x) for x in regex]
        self.use_findall = use_findall
        self.base_cs = base_cs
        self.url = base_cs['url']
        self.codes = {}
        self.display_source = display_source
    
    def pull_current_version(self, fhirclient):
        response = fhirclient.get(f"CodeSystem?url={self.url}")

        if response.success():
            for entry in response.entries:
                self.base_cs['id'] = entry['id']

                for concept in entry['concept']:
                    self.codes[concept['code']] = concept
        return response

    def push_current_vrsion(self, fhirclient):
        self.base_cs['concept'] = []
        for code in self.codes:
            self.base_cs['concept'].append(self.codes[code])
        
        self.base_cs['count'] = len(self.codes)
        response = fhirclient.load("CodeSystem", self.base_cs)

        return response

    def get_vs_concept(self, cui):
        if cui not in self.codes:
            concept = self.display_source(cui)
            if concept:
                self.codes[cui] = concept

        self.codes.get(cui)        


    def match(self, cui_data, match_list):
        chars_used = 0
        chars_spanned = 0
        cui_list = set()
        matched_concepts = []
        for rex in self.matchers:
            if chars_spanned > 0:
                chars_spanned += 1
            if self.use_findall:
                matches = rex.findall(cui_data)
                if len(matches) == 0:
                    matches = None
                else:
                    for cui in matches.split(","):
                        chars_spanned += len(cui)
                        cui_list.add(cui)

                    chars_spanned += len(matches) - 1
            else:
                matches = rex.search(cui_data)
                if matches:
                    gspan = matches.span()
                    chars_spanned += (gspan[1] - gspan[0])

                    for group in matches.groups():
                        for cui in group.split(","):
                            cui_list.add(cui)
                        
            if matches is not None:
                for match in matches:
                    if len(match_list) > 0:
                        chars_used += 1     # Account for any commas

        for cui in cui_list:
            matched_concepts.append(self.get_vs_concept(cui))

        return matched_concepts         



            
cui_cs = [ 
    CuiSystem("SNOMED", [r"SNOMEDCT_US\[([0-9,]+)\]"], False, _basecs_snomed, display_source=NameSnomed),
    CuiSystem("UMLS", [r"(C[0-9]+)"], True, _basecs_umls, display_source=NameCui),
    CuiSystem("RxNorm", [r"RxNorm=\[([0-9,]+)\]", r"Generic=\[([0-9,]+)\]"], False, _basecs_rxnorm, display_source=NameRxNorm)
]
