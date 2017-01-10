
#  FoXPath, tools for processing FoXPath test suites,
#  by Martin Keegan, Mark Brough and Ben Webb

#  Copyright (C) 2013  Mark Brough, Martin Keegan
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from collections import defaultdict
import re
import itertools
from . import mapping
from lxml import etree

# Take the test expression and turn it into a function

# Take the test expression and some XML and return true/false

class TestSyntaxError(Exception): pass

def generate_test_functions(tests, lists):
    mappings = mapping.generate_mappings()

    def get_mappings(mappings, line):
        for regex, lam in mappings:
            yield regex.match(line), lam

    first_true = lambda tupl: bool(tupl.__getitem__(0))

    # yuck
    def test_getattr(test, attr):
        try:
            return getattr(test, attr)
        except AttributeError:
            return test

    def function_for_test(test):
        line = test_getattr(test, 'name')

        match_data = get_mappings(mappings, line)
        matching_mappings = itertools.ifilter(first_true, match_data)

        try:
            m, lam = matching_mappings.next()
        except StopIteration:
            raise TestSyntaxError(line)

        return lam(m.groups(), lists)

    def test_data(test):
        f = function_for_test(test)
        return test_getattr(test, 'id'), f

    return dict(itertools.imap(test_data, tests))

def result_t(result_value):
    results = {0: "FAIL",
               1: "PASS",
               2: "ERROR",
               None: "NOT-RELEVANT",
            }
    return results[result_value]

def test_doc(filename, tests, current_test=None, lists=None):
    data = {}
    test_fns = generate_test_functions(tests, lists)
    if current_test:
        current_test_fn = generate_test_functions(current_test, lists).values()[0]
    doc = etree.parse(filename)
    activities = doc.xpath("//iati-activity")
    success = defaultdict(int)
    fail = defaultdict(int)
    error = defaultdict(int)
    notrelevant = defaultdict(int)
    data['activities'] = []
    data['summary'] = defaultdict(dict)
    for activity in activities:
        hierarchy = activity.xpath("@hierarchy")
        hierarchy = hierarchy[0] if hierarchy != [] else ""

        if current_test:
            try:
                current_result = current_test_fn(activity)
            except Exception:
                current_result = 2
        else:
            current_result = None
        current_text = result_t(current_result)

        for test_id, test_fn in test_fns.items():
            try:
                result = test_fn(activity)
            except Exception:
                result = 2

            if result == 0:
                data['summary']
                fail[test_id] += 1
            elif result == 1:
                success[test_id] += 1
            elif result == 2:
                error[test_id] += 1
            elif result == None:
                notrelevant[test_id] += 1

            result_text = result_t(result)

            try:
                iati_identifier = activity.xpath('iati-identifier/text()')[0]
            except Exception:
                iati_identifier = "Unknown"
            activitydata = {
                        'iati-identifier': iati_identifier,
                        'result': result_text,
                        'current-result': current_text,
                        'hierarchy': hierarchy,
                           }
            data['activities'].append(activitydata)

    for test_id in test_fns.keys():
        data['summary'][test_id]['success'] = success[test_id]
        data['summary'][test_id]['fail'] = fail[test_id]
        data['summary'][test_id]['error'] = error[test_id]
        data['summary'][test_id]['not_relevant'] = notrelevant[test_id]
        try:
            data['summary'][test_id]['percentage'] = float(success[test_id]) / float(success[test_id] + fail[test_id]) * 100.0
        except ZeroDivisionError:
            data['summary'][test_id]['percentage'] = 0.00
    data['summary'] = dict(data['summary'])
    return data

# deprecated
def test_doc_json_out(filename, test, current_test=None, lists=None):
    return test_doc(filename, test, current_test=None, lists=None)
