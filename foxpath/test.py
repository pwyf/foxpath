
#  FoXPath, tools for processing FoXPath test suites,
#  by Martin Keegan, Mark Brough and Ben Webb

#  Copyright (C) 2013  Mark Brough, Martin Keegan
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import re
import itertools
import mapping
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
    test_fn=generate_function(test)
    doc = etree.parse(filename)
    activities=doc.xpath("//iati-activity")
    success =0
    fail = 0
    error = 0
    notrelevant = 0
    for activity in activities:
        result = test_fn(activity)
        if result == 0:
            fail +=1
        elif result == 1:
            success +=1
        elif result == 2:
            error +=1
        elif result == None:
            notrelevant +=1
    print test
    print "Success:", success
    print "Fail:", fail
    print "Error:", error
    print "Not relevant:", notrelevant
    print "Percentage:", float(success)/float(success+fail)*100.0

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
    print test
    print "Success:", success
    print "Fail:", fail
    print "Error:", error
    print "Not relevant:", notrelevant
    print "Percentage:", float(success)/float(success+fail)*100.0
