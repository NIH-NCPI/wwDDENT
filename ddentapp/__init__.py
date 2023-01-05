from flask import url_for, Flask, render_template
from pathlib import Path
from yaml import safe_load
import sys
from ddent.terminologies import BioPortalClient, NlmClient, load_terminologies
from ncpi_fhir_client.fhir_client import FhirClient

from ddent.nlp import get_extraction_modules

from ddent.nlm import nlm_error_log

__version__ = "0.0.1"

_fhirclient = None
def fhirclient(fc=None):
    global _fhirclient 

    if fc is not None:
        _fhirclient = fc
    return _fhirclient

_url_list = None
def system_urls():
    global _url_list 

    if _url_list is None:
        _url_list = {
            'dbgap': url_for('dbgap.list'),
            'dbgap-new': url_for('dbgap.new'),
            'conceptmap': url_for('conceptmap.list'),
            'valueset': url_for('valueset.list'),
            'codesystem': url_for('codesystem.list')
        }
    return _url_list

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        CONFIG_FILE=str(Path(app.instance_path) / 'config.yaml'),
    )
    print("Welcome to DDENT...the app!")
    app.jinja_env.globals.update(url_for=url_for)
    app.jinja_env.globals.update(len=len)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if Path(app.config['CONFIG_FILE']).is_file():
        nlm_error_log(str(Path(app.instance_path) / "missing_codes.csv"))

        keys = safe_load(open(app.config['CONFIG_FILE']))

        # Loads the NLM Extractors into memory and sets the default to be 
        # whatever happens to have the highest score among the active modules
        get_extraction_modules(keys)

        if 'NLM' not in keys or "BioPortal" not in keys:
            print("You must have API Keys for both NLM and BioPortal to proceed")
            sys.exit(1)

        # These function like singletons. We don't need to keep copies to pass
        # around since they can request without any parameters
        NlmClient(keys.get('NLM'))
        BioPortalClient(keys.get('BioPortal'))
        fhirclient(FhirClient(keys.get('fhirauth')))
        load_terminologies(_fhirclient)


        @app.route('/')
        def index():
            return render_template("index.html", urls=system_urls())
        
        from ddentapp import conceptmap, translate_code, dbgap, valueset, codesystem

        app.register_blueprint(conceptmap.bp)
        app.register_blueprint(translate_code.bp)
        app.register_blueprint(dbgap.bp)
        app.register_blueprint(valueset.bp)
        app.register_blueprint(codesystem.bp)

        return app
    
    print(f"""There is no configuration present which is required to proceed. 

File Path: {app.config['CONFIG_FILE']}

API Keys are required for NLM (https://uts.nlm.nih.gov/uts/umls/home) as well as 
BioPortal (https://bioportal.bioontology.org/). Directions for finding/creating 
the keys are provide at each site and require the user to create an account. 

A Fhir Auth configuration is also required. An example config.yaml file might look
like the following:

NLM: -your-key-here-
BioPortal: -your-key-here-
fhirauth:
    auth_type: 'auth_basic'
    username: 'admin'
    password: 'password'
    host_desc: 'Example Test'
    target_service_url: 'http://localhost:8000'

Please note that there are many forms that the fhirauth config can take 
depending on the platform being accessed and the authentication used.  

TODO: provide README associated with setting up the different auth objects
    """)
    sys.exit(1)


if __name__ == '__main__':
    hostname = '0.0.0.0'
    if len(sys.argv) > 1:
        hostname = sys.argv[1]
    app = create_app()
    app.run(host=hostname, post=3001)

