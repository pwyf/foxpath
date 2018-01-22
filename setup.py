from os.path import join, dirname
from setuptools import setup, find_packages


with open(join(dirname(__file__), 'README.rst')) as f:
    readme_text = f.read()

setup(
    name="foxpath",
    version="2.0.6",
    packages=find_packages(),
    author="Andy Lulham",
    author_email="andy.lulham@publishwhatyoufund.org",
    description="Python library for running FoXPath tests against XML",
    long_description=readme_text,
    license="MIT",
    install_requires=[
        'six==1.11.0',
        'gherkin-official==4.1.3',
    ],
)
