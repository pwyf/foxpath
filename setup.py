from os.path import join, dirname
from setuptools import setup, find_packages


with open(join(dirname(__file__), 'README.rst')) as f:
    readme_text = f.read()

setup(
    name = "foxpath",
    version = "1.0.1",
    packages = find_packages(),
    author = "Andy Lulham",
    author_email = "andy.lulham@publishwhatyoufund.org",
    description = "Python library for running FoXPath tests against XML",
    long_description = readme_text,
    license = "MIT",
    install_requires = [
        'lxml == 3.7.1',
        'PyYAML == 3.12',
    ],
)
