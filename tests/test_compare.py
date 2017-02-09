import csv
import os.path
from unittest import TestCase
from datetime import date

from mock import patch
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

    LISTS = codelists.CODELISTS

    def run_comparison(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)

        tests_old = self.load_expressions_from_csvfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'old_tests.csv'))
        result_old = test.test_doc(filepath, tests_old, lists=self.LISTS)
        summary_old = result_old['summary']

        tests_new = self.load_expressions_from_yaml(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.yaml'))
        foxpath = Foxpath(tests_new, self.LISTS)
        result_new = foxpath.test_doc(filepath)
        summary_new = foxpath.summarize_results(result_new)

        for k, v in summary_old.items():
            # for key in [('fail', 'fail'), ('pass', 'success'), ('not-relevant', 'not_relevant')]:
            #     if summary_new[k][key[0]] != v[key[1]]:
            #         print('---')
            #         print('{} - {}'.format(k, key[0]))
            #         print((summary_new[k][key[0]], v[key[1]]))
            #         print('---')
            self.assertEqual(summary_new[k]['fail'], v['fail'])
            self.assertEqual(summary_new[k]['pass'], v['success'])
            self.assertEqual(summary_new[k]['not-relevant'], v['not_relevant'])

    @patch('foxpath.mapping.datetime.date')
    def test_compare_sida(self, mock_date):
        mock_date.today.return_value = date(2015, 12, 1)
        self.run_comparison('sida-tz.xml')

    @patch('foxpath.mapping.datetime.date')
    def test_compare_dfid(self, mock_date):
        mock_date.today.return_value = date(2015, 12, 1)
        self.run_comparison('dfid-tz.xml')
