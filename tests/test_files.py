# import os.path
# from unittest import TestCase
# from datetime import date

# from mock import patch
# import yaml
# from lxml import etree

# from foxpath import Foxpath
# from tests import codelists


# '''
# Doesn't actually run any tests - this is purely here so I have some
# useful sample code!
# '''
# class TestFiles(TestCase):
#     def load_expressions_from_yaml(self, filename):
#         with open(filename) as f:
#             reader = yaml.load(f)
#             return [
#                 t for indicator in reader for t in indicator['tests']
#             ]

#     LISTS = codelists.CODELISTS

#     def run_tests(self, filename):
#         filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)

#         tests = self.load_expressions_from_yaml(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.yaml'))
#         foxpath = Foxpath()
#         tests = foxpath.load_tests(tests, self.LISTS)
#         result = foxpath.test_doc(filepath, tests)
#         summary = foxpath.summarize_results(result)

#     @patch('foxpath.foxpath.datetime.date')
#     def test_compare_sida(self, mock_date):
#         mock_date.today.return_value = date(2015, 12, 1)
#         self.run_tests('sida-tz.xml')

#     @patch('foxpath.foxpath.datetime.date')
#     def test_compare_dfid(self, mock_date):
#         mock_date.today.return_value = date(2015, 12, 1)
#         self.run_tests('dfid-tz.xml')
