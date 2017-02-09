import os.path
from unittest import TestCase

from foxpath import test


class TestLists(TestCase):
    LISTS = {'Sector': ['13040'], 'BudgetIdentifier': ['5.1.1'], 'AidType': ['A01']}
    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sida-tz.xml')

    def test_at_least_one_a_or_b_is_on_list_c(self):
        t = 'at least one sector[@vocabulary="DAC"]/@code or sector[not(@vocabulary)]/@code is on list Sector?'
        result = test.test_doc(self.FILEPATH, [t], lists=self.LISTS)
        self.assertEqual(result['summary'][t]['success'], 20)
        self.assertEqual(result['summary'][t]['fail'], 527)
        self.assertEqual(result['summary'][t]['not_relevant'], 0)
        self.assertEqual(result['summary'][t]['error'], 0)

    def test_at_least_one_a_is_on_list_b_if_c_is_at_least_d_and_e_or_f_is_not_g_or_h(self):
        t = 'at least one country-budget-items[@vocabulary="1"]/budget-item/@code is on list BudgetIdentifier (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01 or A02))?'
        result = test.test_doc(self.FILEPATH, [t], lists=self.LISTS)
        self.assertEqual(result['summary'][t]['success'], 48)
        self.assertEqual(result['summary'][t]['fail'], 485)
        self.assertEqual(result['summary'][t]['not_relevant'], 14)
        self.assertEqual(result['summary'][t]['error'], 0)

    def test_at_least_one_a_is_on_list_b(self):
        t = 'at least one country-budget-items[@vocabulary="1"]/budget-item/@code is on list BudgetIdentifier?'
        result = test.test_doc(self.FILEPATH, [t], lists=self.LISTS)
        self.assertEqual(result['summary'][t]['success'], 48)
        self.assertEqual(result['summary'][t]['fail'], 499)
        self.assertEqual(result['summary'][t]['not_relevant'], 0)
        self.assertEqual(result['summary'][t]['error'], 0)

    def test_a_or_b_is_on_list_c_if_d_is_at_least_e(self):
        t = 'default-aid-type/@code or transaction/aid-type/@code is on list AidType (if activity-status/@code is at least 2)?'
        result = test.test_doc(self.FILEPATH, [t], lists=self.LISTS)
        self.assertEqual(result['summary'][t]['success'], 2)
        self.assertEqual(result['summary'][t]['fail'], 545)
        self.assertEqual(result['summary'][t]['not_relevant'], 0)
        self.assertEqual(result['summary'][t]['error'], 0)
