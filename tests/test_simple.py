import os.path
from unittest import TestCase
from datetime import date

from mock import patch

from foxpath import Foxpath


class TestSimple(TestCase):
    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dfid-tz.xml')

    def test_a_starts_with_b(self):
        t = {
            'name': '_',
            'expression': '`iati-identifier/text()` should start with `reporting-org/@ref`',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 273)
        self.assertEqual(summary['_'][0], 0)
        self.assertEqual(summary['_'][-1], 0)

    @patch('foxpath.foxpath.datetime.date')
    def test_a_or_b_or_c_or_d_or_e_for_any_f_is_less_than_g_months_ago(self, mock_date):
        mock_date.today.return_value = date(2015, 12, 1)

        t = {
            'name': '_',
            'expression': '''
                `activity-date[@type="end-planned"]/@iso-date|activity-date[@type="end-planned"]/text()` is less than 12 months ago
                or
                `activity-date[@type="end-actual"]/@iso-date|activity-date[@type="end-actual"]/text()` is less than 12 months ago
                or
                for at least one `transaction[transaction-type/@code="D"]|transaction[transaction-type/@code="E"]`,
                        `transaction-date/@iso-date` is less than 12 months ago
            ''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 132)
        self.assertEqual(summary['_'][0], 141)
        self.assertEqual(summary['_'][-1], 0)

    def test_a_or_b_exists_if_c_is_at_least_d_and_e_is_not_f(self):
        t = {
            'name': '_',
            'expression': '''
                if `activity-status/@code` is one of (2, 3, 4)
                and `conditions/@attached` is not 0
                then `conditions` should be present
                or `document-link/category[@code="A04"]` should be present
            ''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 13)
        self.assertEqual(summary['_'][0], 178)
        self.assertEqual(summary['_'][-1], 82)

    @patch('foxpath.foxpath.datetime.date')
    def test_a_or_b_is_available_forward_if_c_is_at_least_d(self, mock_date):
        mock_date.today.return_value = date(2015, 12, 1)
        t = {
            'name': '_',
            'expression': '''
                if `activity-status/@code` is at least 2
                then `budget` should be available forward annually
                or `planned-disbursement` should be available forward annually
            ''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 20)
        self.assertEqual(summary['_'][0], 14)
        self.assertEqual(summary['_'][-1], 239)

    @patch('foxpath.foxpath.datetime.date')
    def test_a_or_b_is_available_forward_by_quarters_if_c_is_at_least_d(self, mock_date):
        mock_date.today.return_value = date(2015, 12, 1)
        t = {
            'name': '_',
            'expression': '''
                if `activity-status/@code` is at least 2
                then `budget` should be available forward quarterly
                or `planned-disbursement` should be available forward quarterly
            ''',
        }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 0)
        self.assertEqual(summary['_'][0], 34)
        self.assertEqual(summary['_'][-1], 239)

    def test_a_exists_if_b_is_at_least_c_and_d_or_e_is_not_f_or_g(self):
        t = {
                'name': '_',
                'expression': '''
                    if `activity-status/@code` is at least 2
                    and `default-aid-type/@code` is not A01
                    and `default-aid-type/@code` is not A02
                    and `transaction/aid-type/@code` is not A01
                    and `transaction/aid-type/@code` is not A02
                    then `capital-spend` should be present
                ''',
            }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 0)
        self.assertEqual(summary['_'][0], 257)
        self.assertEqual(summary['_'][-1], 16)

    def test_a_is_before_b(self):
        t = {
                'name': '_',
                'expression': '''
                   `activity-date[@type='start-planned']/@iso-date`
                   should be chronologically before
                   `activity-date[@type='start-actual']/@iso-date`
                ''',
            }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)

    def test_sectors(self):
        t = {
                'name': '_',
                'expression': '''
                 for every activity, `sector` should be present
                 but if `transaction` is present then
                 for every `transaction`, `sector` *should not* be present.

                 Alternatively,
                 `transaction` should be present
                 and for every `transaction`, `sector` *should* be present
                 and for every activity, `sector` *should not* be present
                ''',
            }
        foxpath = Foxpath()
        tests = foxpath.load_tests([t])
        result = foxpath.test_doc(self.FILEPATH, tests)
        summary = foxpath.summarize_results(result)
        self.assertEqual(summary['_'][1], 180)
        self.assertEqual(summary['_'][0], 93)
        self.assertEqual(summary['_'][-1], 0)
