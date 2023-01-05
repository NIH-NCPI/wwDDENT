from flask import Flask, url_for, render_template
#from ddentapp import app
import ddentapp.webddent
import ddentapp.dbgap

from pathlib import Path
from ncpi_fhir_client.fhir_client import FhirClient
from yaml import safe_load

from ddentapp import conceptmap, translate_code, dbgap, valueset, codesystem

from ddentapp import fhirclient, create_app

import sys

import pdb

__version__ = "0.0.1"

from ddentapp import system_urls

if __name__ == '__main__':

    hostname = '0.0.0.0'
    if len(sys.argv) > 1:
        hostname = sys.argv[1]

    app = create_app()
    app.run(host=hostname, port=3001)