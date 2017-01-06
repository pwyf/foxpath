import os.path
from unittest import TestCase

import csv
from lxml import etree

from foxpath import Foxpath, test
import codelists


class TestBenchmark(TestCase):
    def load_expressions_from_csvfile(self, filename):
        with open(filename) as f:
            reader = csv.DictReader(f)
            return [
                {
                    'name': t["test_description"],
                    'expression': t["test_name"],
                } for t in reader
            ]

    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sida-tz.xml')
    LISTS = codelists.CODELISTS

    def test_new(self):
        tests = self.load_expressions_from_csvfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.csv'))
        foxpath = Foxpath(tests, self.LISTS)
        foxpath.test_doc(self.FILEPATH)

    def test_old(self):
        tests = self.load_expressions_from_csvfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'old_tests.csv'))
        for t in tests:
            test.test_doc(self.FILEPATH, t['expression'], lists=self.LISTS)
