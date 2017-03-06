import os.path
from unittest import TestCase

from foxpath import Foxpath


class TestLists(TestCase):
    LISTS = {'Sector': ['13040'], 'BudgetIdentifier': ['5.1.1'], 'AidType': ['A01']}
    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sida-tz.xml')

    def test_at_least_one_a_or_b_is_on_list_c(self):
        t = {
            'name': '_',
            'expression': '''
                at least one `sector[@vocabulary="DAC"]/@code | sector[not(@vocabulary)]/@code`
                should be on the Sector codelist''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t], self.LISTS)
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 20)
        self.assertEqual(summary['_'][0], 527)
        self.assertEqual(summary['_'][-1], 0)

    def test_at_least_one_a_is_on_list_b_if_c_is_at_least_d_and_e_or_f_is_not_g_or_h(self):
        t = {
            'name': '_',
            'expression': '''
                if `activity-status/@code` is at least 2
                and `default-aid-type/@code` is not A01
                and `default-aid-type/@code` is not A02
                and `transaction/aid-type/@code` is not A01
                and `transaction/aid-type/@code` is not A02
                then at least one `country-budget-items[@vocabulary="1"]/budget-item/@code`
                should be on the BudgetIdentifier codelist
            ''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t], self.LISTS)
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 48)
        self.assertEqual(summary['_'][0], 485)
        self.assertEqual(summary['_'][-1], 14)

    def test_at_least_one_a_is_on_list_b(self):
        t = {
            'name': '_',
            'expression': '''
                at least one `country-budget-items[@vocabulary="1"]/budget-item/@code`
                should be on the BudgetIdentifier codelist''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t], self.LISTS)
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 48)
        self.assertEqual(summary['_'][0], 499)
        self.assertEqual(summary['_'][-1], 0)

    def test_a_or_b_is_on_list_c_if_d_is_at_least_e(self):
        t = {
            'name': '_',
            'expression': '''
                if `activity-status/@code` is at least 2
                then at least one `default-aid-type/@code`
                should be on the AidType codelist
                or at least one `transaction/aid-type/@code`
                should be on the AidType codelist
            ''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t], self.LISTS)
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 2)
        self.assertEqual(summary['_'][0], 545)
        self.assertEqual(summary['_'][-1], 0)
