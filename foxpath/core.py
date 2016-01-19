
#  FoXPath, tools for processing FoXPath test suites,
#  by Martin Keegan, Mark Brough and Ben Webb

#  Copyright (C) 2013  Martin Keegan
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import re
import itertools
from . import mapping

class TestSyntaxError(Exception): pass

def generate_test_functions(tests):
    mappings = mapping.generate_mappings()

    def get_mappings(ms, line):
        for regex, lam in ms:
            yield regex.match(line), lam

    first_true = lambda tupl: bool(tupl.__getitem__(0))

    test_functions = {}

    def function_for_test(test):
        line = test.name

        match_data = get_mappings(mappings, line)
        matching_mappings = itertools.ifilter(first_true, match_data)

        try:
            m, lam = matching_mappings.next()
        except StopIteration:
            raise TestSyntaxError(line)

        return lam(m.groups())

    def id_of_test(test): return test.id

    def test_data(test):
        f = function_for_test(test)
        test_id = id_of_test(test)
        return test_id, f

    return dict(itertools.imap(test_data, tests))
