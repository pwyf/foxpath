import os.path
from unittest import TestCase

import csv
from lxml import etree

from foxpath import Foxpath, test
import codelists


class Test(object):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.name = kwargs['name']

class TestBenchmark(TestCase):
    def load_expressions_from_csvfile(self, filename):
        with open(filename) as f:
            reader = csv.DictReader(f)
            return [
                Test(id=t["test_description"], name=t["test_name"])
                for t in reader
            ]

    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sida-tz.xml')
    LISTS = codelists.CODELISTS

    def test_new(self):
        tests = self.load_expressions_from_csvfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.csv'))
        foxpath = Foxpath(tests, self.LISTS)
        foxpath.test_doc(self.FILEPATH)

    def test_old(self):
        tests = self.load_expressions_from_csvfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'old_tests.csv'))
        test.test_doc(self.FILEPATH, tests, lists=self.LISTS)
