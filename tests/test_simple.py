import os.path
from unittest import TestCase
from datetime import datetime

from mock import patch

from foxpath import test


class TestSimple(TestCase):
    FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dfid-tz.xml')

    def test_a_starts_with_b(self):
        t = 'iati-identifier/text() starts with reporting-org/@ref?'
        result = test.test_doc(self.FILEPATH, t)
        self.assertEqual(result['summary']['success'], 273)
        self.assertEqual(result['summary']['fail'], 0)
        self.assertEqual(result['summary']['not_relevant'], 0)
        self.assertEqual(result['summary']['error'], 0)

    @patch('foxpath.mapping.datetime.datetime')
    def test_a_or_b_or_c_or_d_or_e_for_any_f_is_less_than_g_months_ago(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2015, 12, 1)
        mock_datetime.strptime.side_effect = lambda *args, **kw: datetime.strptime(*args, **kw)

        t = 'activity-date[@type="end-planned"]/@iso-date or activity-date[@type="end-planned"]/text() or activity-date[@type="end-actual"]/@iso-date or activity-date[@type="end-actual"]/text() or transaction-date/@iso-date (for any transaction[transaction-type/@code="D"]|transaction[transaction-type/@code="E"]) is less than 13 months ago?'
        result = test.test_doc(self.FILEPATH, t)
        self.assertEqual(result['summary']['success'], 132)
        self.assertEqual(result['summary']['fail'], 141)
        self.assertEqual(result['summary']['not_relevant'], 0)
        self.assertEqual(result['summary']['error'], 0)

    def test_a_or_b_exists_if_c_is_at_least_d_and_e_is_not_f(self):
        t = 'conditions or document-link/category[@code="A04"] exists (if activity-status/@code is at least 2 and conditions/@attached is not 0)?'
        result = test.test_doc(self.FILEPATH, t)
        self.assertEqual(result['summary']['success'], 13)
        self.assertEqual(result['summary']['fail'], 178)
        self.assertEqual(result['summary']['not_relevant'], 82)
        self.assertEqual(result['summary']['error'], 0)

    @patch('foxpath.mapping.datetime.datetime')
    def test_a_or_b_is_available_forward_if_c_is_at_least_d(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2015, 12, 1)
        mock_datetime.strptime.side_effect = lambda *args, **kw: datetime.strptime(*args, **kw)

        t = 'budget or planned-disbursement is available forward (if activity-status/@code is at least 2)?'
        result = test.test_doc(self.FILEPATH, t)
        self.assertEqual(result['summary']['success'], 20)
        self.assertEqual(result['summary']['fail'], 14)
        self.assertEqual(result['summary']['not_relevant'], 239)
        self.assertEqual(result['summary']['error'], 0)

    @patch('foxpath.mapping.datetime.datetime')
    def test_a_or_b_is_available_forward_by_quarters_if_c_is_at_least_d(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2015, 12, 1)
        mock_datetime.strptime.side_effect = lambda *args, **kw: datetime.strptime(*args, **kw)

        t = 'budget or planned-disbursement is available forward by quarters (if activity-status/@code is at least 2)?'
        result = test.test_doc(self.FILEPATH, t)
        self.assertEqual(result['summary']['success'], 0)
        self.assertEqual(result['summary']['fail'], 34)
        self.assertEqual(result['summary']['not_relevant'], 239)
        self.assertEqual(result['summary']['error'], 0)

    def test_a_is_an_integer(self):
        t = 'participating-org/@type is an integer?'
        result = test.test_doc(self.FILEPATH, t)
        self.assertEqual(result['summary']['success'], 273)
        self.assertEqual(result['summary']['fail'], 0)
        self.assertEqual(result['summary']['not_relevant'], 0)
        self.assertEqual(result['summary']['error'], 0)

    def test_a_exists_if_b_is_at_least_c_and_d_or_e_is_not_f_or_g(self):
        t = 'capital-spend exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01 or A02))?'
        result = test.test_doc(self.FILEPATH, t)
        self.assertEqual(result['summary']['success'], 0)
        self.assertEqual(result['summary']['fail'], 257)
        self.assertEqual(result['summary']['not_relevant'], 16)
        self.assertEqual(result['summary']['error'], 0)
