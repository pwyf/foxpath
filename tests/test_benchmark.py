import csv
import os.path
import re
from unittest import TestCase

import yaml
from lxml import etree

from foxpath import Foxpath, test
from tests import codelists


class TestBenchmark(TestCase):
    def load_expressions_from_csvfile(self, filename):
        with open(filename) as f:
            reader = csv.DictReader(f)
            return [
                {
                    'id': t['test_description'],
                    'expression': t['test_name'],
                }
                for t in reader
            ]

    def load_expressions_from_yaml(self, filename):
        whitespace = re.compile(r'\s+')
        with open(filename) as f:
            reader = yaml.load(f)
            return [
                {
                    'id': t['description'],
                    'expression': whitespace.sub(' ', t['expression']).strip(),
                }
                for indicator in reader for t in indicator['tests']
            ]

    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sida-tz.xml')
    LISTS = codelists.CODELISTS

    def test_new(self):
        tests = self.load_expressions_from_yaml(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.yaml'))
        foxpath = Foxpath(tests, self.LISTS)
        foxpath.test_doc(self.FILEPATH)

    def test_old(self):
        tests = self.load_expressions_from_csvfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'old_tests.csv'))
        test.test_doc(self.FILEPATH, tests, lists=self.LISTS)
