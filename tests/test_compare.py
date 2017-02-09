import csv
import os.path
from unittest import TestCase

import yaml
from lxml import etree

from foxpath import Foxpath, test
from tests import codelists


class TestCompare(TestCase):
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
        with open(filename) as f:
            reader = yaml.load(f)
            return [
                {
                    'id': t['description'],
                    'expression': t['expression'],
                }
                for indicator in reader for t in indicator['tests']
            ]

    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sida-tz.xml')
    LISTS = codelists.CODELISTS

    def test_compare(self):
        tests_old = self.load_expressions_from_csvfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'old_tests.csv'))
        result_old = test.test_doc(self.FILEPATH, tests_old, lists=self.LISTS)
        summary_old = result_old['summary']

        tests_new = self.load_expressions_from_yaml(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.yaml'))
        foxpath = Foxpath(tests_new, self.LISTS)
        result_new = foxpath.test_doc(self.FILEPATH)
        summary_new = foxpath.summarize_results(result_new)

        for k, v in summary_old.items():
            self.assertEqual(summary_new[k]['fail'], v['fail'])
            self.assertEqual(summary_new[k]['pass'], v['success'])
            self.assertEqual(summary_new[k]['not-relevant'], v['not_relevant'])
