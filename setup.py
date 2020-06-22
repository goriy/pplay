from runpy import run_path
from setuptools import setup

version = run_path('./ppplay/version.py')['__version__']

setup(
    version=version,
    entry_points={'gui_scripts': 'pplay=ppplay.__main__:main'},
    include_package_data = True,
)
