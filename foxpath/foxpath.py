import re

from lxml import etree


class Foxpath(object):
    def __init__(self, tests, codelists=None):
        self.tests = {
            test['id']: self.parse(test['expression'], codelists)
            for test in tests
        }

    def __getitem__(self, index):
        return self.tests[index]

    def parse(self, test, codelists):
        def xpath(activity, groups, **kwargs):
            return activity.xpath(groups[0][1:-1])

        def integer(activity, groups, **kwargs):
            return int(groups[0])

        def code(activity, groups, **kwargs):
            return groups[0]

        def a_list(activity, groups, codelists, **kwargs):
            codelist = codelists.get(groups[0][5:])
            if not codelist:
                raise Exception('That codelist doesn\'t exist!')
            return codelist

        def for_any(activity, groups, **kwargs):
            return any([groups[1](exp) for exp in groups[0](activity)])

        def either(activity, groups, **kwargs):
            return groups[0](activity) or groups[1](activity)

        def both(activity, groups, **kwargs):
            return groups[0](activity) and groups[1](activity)

        def if_then(activity, groups, **kwargs):
            if groups[0](activity):
                return groups[1](activity)
            else:
                # if the condition fails,
                # return not relevant
                return None

        # defaults to true
        def is_not(activity, groups, **kwargs):
            vals = groups[0](activity)
            const = groups[1](activity)
            return not any([val == str(const) for val in vals])

        # defaults to true
        def is_at_least(activity, groups, **kwargs):
            vals = groups[0](activity)
            if len(vals) < 1:
                print('note: is_at_least was expecting to find one and only one element. Found 0')
                return True
            if len(vals) > 1:
                print('note: is_at_least was expecting to find one and only one element. Found {}'.format(len(vals)))
            return int(groups[0](activity)[0]) >= groups[1](activity)

        def exists(activity, groups, **kwargs):
            return [x for x in groups[0](activity) if x != ''] != []

        # defaults to true
        def is_on_list(activity, groups, **kwargs):
            def check_list(vals, codelist):
                for v in vals:
                    v = str(v)
                    versions = [v, v.lower(), v.upper()]
                    yield any([v in codelist for v in versions])
            vals = groups[0](activity)
            return all(check_list(vals, groups[1](activity)))

        # defaults to false
        def is_more_than_x_characters(activity, groups, **kwargs):
            exp = groups[0](activity)
            val = groups[1](activity)
            return any([len(x) > val for x in exp])

        # defaults to false
        def starts_with(activity, groups, **kwargs):
            x = groups[0](activity)
            y = groups[1](activity)
            if x == [] or y == []:
                return False
            return x[0].startswith(str(y[0]))

        def is_less_than_x_months_ago(activity, groups, **kwargs):
            pass

        def is_available_forward(activity, groups, **kwargs):
            pass

        def is_available_forward_by_qtrs(activity, groups, **kwargs):
            pass

        mappings = (
            (re.compile(r'^if (.*) then (.*)$'), if_then, 'if_then'),
            (re.compile(r'list \S*$'), a_list, 'list'),
            (re.compile(r'`[^`]+`$'), xpath, 'xpath'),
            (re.compile(r'^\d+$'), integer, 'integer'),
            (re.compile(r'[A-Z]+\d+$'), code, 'code'),
            (re.compile(r'^for any (`\S*`), (.*)$'), for_any, 'for_any'),
            (re.compile(r'^(.*) or (.*)$'), either, 'or'),
            (re.compile(r'^(.*) and (.*)$'), both, 'and'),
            (re.compile(r'^(`\S*`) is not (\S*)$'), is_not, 'is_not'),
            (re.compile(r'^(`\S*`) is at least (\d+)$'), is_at_least, 'is_at_least'),
            (re.compile(r'^(`\S*`) exists$'), exists, 'exists'),
            (re.compile(r'^(`\S*`) starts with (`\S*`)$'), starts_with, 'starts_with'),
            (re.compile(r'^every (`\S*`) is on (list \S*)$'), is_on_list, 'is_on_list'),
            (re.compile(r'^(`\S*`) has more than (\d+) characters$'), is_more_than_x_characters, 'is_more_than_x_characters'),
            (re.compile(r'^(.*) is less than (\d+) months ago$'), is_less_than_x_months_ago, 'is_less_than_x_months_ago'),
            (re.compile(r'^(`\S*`) is available forward$'), is_available_forward, 'is_available_forward'),
            (re.compile(r'^(`\S*`) is available forward by quarters$'), is_available_forward_by_qtrs, 'is_available_forward_by_qtrs'),
        )
        for regex, fn, name in mappings:
            r = regex.match(test)
            if r:
                if r.groups():
                    groups = [self.parse(g, codelists) for g in r.groups()]
                else:
                    groups = [r.group()]
                return lambda x: fn(x, groups=groups, codelists=codelists)
        raise Exception('I don\'t understand {}'.format(test))

    def test_activity(self, activity):
        def translate_result(result_value):
            results = {
                False: 'fail',
                True: 'pass',
                None: 'not-relevant',
            }
            return results[result_value]

        # hierarchy = activity.xpath("@hierarchy")
        # hierarchy = hierarchy[0] if hierarchy != [] else ""
        # try:
        #     iati_identifier = activity.xpath('iati-identifier/text()')[0]
        # except Exception:
        #     iati_identifier = "Unknown"
        return {
            test_id: translate_result(test_fn(activity))
            for test_id, test_fn in self.tests.items()
        }
        # return {
        #     'results': results,
        #     'iati-identifier': iati_identifier,
        #     'hierarchy': hierarchy,
        # }

    def test_activities(self, activities):
        return [self.test_activity(activity) for activity in activities]

    def test_doc(self, filepath):
        doc = etree.parse(filepath)
        activities = doc.xpath('//iati-activity')
        return self.test_activities(activities)
