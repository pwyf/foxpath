
#  FoXPath, tools for processing FoXPath test suites,
#  by Martin Keegan, Mark Brough and Ben Webb

#  Copyright (C) 2013  Mark Brough, Martin Keegan
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import re
import itertools
from . import mapping
from lxml import etree

# Take the test expression and turn it into a function

# Take the test expression and some XML and return true/false

class TestSyntaxError(Exception): pass

def generate_function(test):
    mappings = mapping.generate_mappings()

    def get_mappings(ms, line):
        for regex, lam in ms:
            yield regex.match(line), lam

    first_true = lambda tupl: bool(tupl.__getitem__(0))

    def function_for_test(test):
        line = test

        match_data = get_mappings(mappings, line)
        matching_mappings = itertools.ifilter(first_true, match_data)

        try:
            m, lam = matching_mappings.next()
        except StopIteration:
            raise TestSyntaxError(line)

        return lam(m.groups())

    f = function_for_test(test)
    return f

def test_doc(filename, test):
    j = test_doc_json_out(filename, test)
    print(test)
    print("Success: {}".format(j["summary"]["success"]))
    print("Fail: {}".format(j["summary"]["fail"]))
    print("Error: {}".format(j["summary"]["error"]))
    print("Not relevant: {}".format(j["summary"]["not_relevant"]))
    print("Percentage: {}".format(j["summary"]["percentage"]))

def result_t(result_value):
    results = {0: "FAIL",
               1: "PASS",
               2: "ERROR",
               None: "NOT-RELEVANT",
            }
    return results[result_value]

def binary_test(test_name):
    if re.compile("(.*) is on list (.*)").match(test_name):
        return True
    return False

def test_doc_json_out(filename, test, current_test=None, lists=None):
    data = {}
    test_fn=generate_function(test)
    if current_test:
        current_test_fn = generate_function(current_test)
    doc = etree.parse(filename)
    activities=doc.xpath("//iati-activity")
    success =0
    fail = 0
    error = 0
    notrelevant = 0
    data['activities'] = []
    for activity in activities:
        hierarchy = activity.xpath("@hierarchy")
        hierarchy = hierarchy[0] if hierarchy != [] else ""
        try:
            if binary_test(test):
                result = test_fn({"activity": activity, "lists": lists})
            else:
                result = test_fn(activity)
        except Exception:
            result = 2
        if current_test:
            try:
                current_result = current_test_fn(activity)
            except Exception:
                current_result = 2
        else:
            current_result = None

        if result == 0:
            fail +=1
        elif result == 1:
            success +=1
        elif result == 2:
            error +=1
        elif result == None:
            notrelevant +=1

        result_text = result_t(result)
        current_text = result_t(current_result)
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

    data['summary'] = {}
    data['summary']['success'] = success
    data['summary']['fail'] = fail
    data['summary']['error'] = error
    data['summary']['not_relevant'] = notrelevant
    try:
        data['summary']['percentage'] = float(success)/float(success+fail)*100.0
    except ZeroDivisionError:
        data['summary']['percentage'] = 0.00
    return data

def test_doc_lists(filename, test, lists):
    test_fn=generate_function(test)
    doc = etree.parse(filename)
    activities=doc.xpath("//iati-activity")
    success =0
    fail = 0
    error = 0
    notrelevant = 0
    for activity in activities:
        result = test_fn({'activity': activity, 'lists': lists})
        if result == 0:
            fail +=1
        elif result == 1:
            success +=1
        elif result == 2:
            error +=1
        elif result == None:
            notrelevant +=1
    print(test)
    print("Success: {}".format(success))
    print("Fail: {}".format(fail))
    print("Error: {}".format(error))
    print("Not relevant: {}".format(notrelevant))
    print("Percentage: {}".format(float(success)/float(success+fail)*100.0))
