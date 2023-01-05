import os
from setuptools import setup, find_packages
from pathlib import Path
import ddentapp

root_dir = Path.cwd()
req_file = root_dir / "requirements.txt"

requirements = req_file.open().read().split("\n")
print(requirements)

setup(
    name='WebDDENT',
    version=ddentapp.__version__,
    setup_requires=["setuptools_scm"],
    description=f'WebDDENT {ddentapp.__version__}',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements
)
