import re


class Foxpath(object):
    def __init__(self, tests, codelists):
        self.tests = [
            dict(test.items() + [(
                'fn', self.parse(test['expression'], codelists)
            )])
        for test in tests]

    def xpath(self, activity, groups, **kwargs):
        return activity.xpath(groups[0][1:-1])

    def integer(self, activity, groups, **kwargs):
        return int(groups[0])

    def code(self, activity, groups, **kwargs):
        return groups[0]

    def a_list(self, activity, groups, codelists, **kwargs):
        codelist = codelists.get(groups[0][5:])
        if not codelist:
            raise Exception('That codelist doesn\'t exist!')
        return codelist

    def where(self, activity, groups, **kwargs):
        return [groups[1](exp) for exp in groups[0](activity)]

    def either(self, activity, groups, **kwargs):
        return groups[0](activity) or groups[1](activity)

    def both(self, activity, groups, **kwargs):
        return groups[0](activity) and groups[1](activity)

    def if_then(self, activity, groups, **kwargs):
        if groups[0](activity):
            return groups[1](activity)
        else:
            # if the condition fails,
            # return not relevant
            return None

    # defaults to true
    def is_not(self, activity, groups, **kwargs):
        exp = groups[0](activity)
        val = groups[0](activity)
        if filter(lambda x: x != '', exp) == []:
            return True
        return exp[0] != val

    # defaults to true
    def is_at_least(self, activity, groups, **kwargs):
        vals = groups[0](activity)
        if len(vals) < 1:
            print('note: is_at_least was expecting to find one and only one element. Found 0')
            return True
        if len(vals) > 1:
            print('note: is_at_least was expecting to find one and only one element. Found {}'.format(len(vals)))
        return int(groups[0](activity)[0]) >= groups[1](activity)

    def exists(self, activity, groups, **kwargs):
        return filter(lambda x: x != '', groups[0](activity)) != []

    # defaults to true
    def is_on_list(self, activity, groups, **kwargs):
        def check_list(vals, codelist):
            for v in vals:
                v = str(v)
                versions = [v, v.lower(), v.upper()]
                yield any((bool(v in codelist) for v in versions))
        vals = groups[0](activity)
        return all(check_list(vals, groups[1](activity)))

    # defaults to false
    def is_more_than_x_characters(self, activity, groups, **kwargs):
        exp = groups[0](activity)
        val = groups[1](activity)
        return bool(
            reduce(lambda x, y: x or y, map(lambda x: len(x) > val, exp), False)
        )

    # defaults to false
    def starts_with(self, activity, groups, **kwargs):
        x = groups[0](activity)
        y = groups[1](activity)
        if x == [] or y == []:
            return False
        return x[0].startswith(y[0])

    def is_less_than_x_months_ago(self, activity, groups, **kwargs):
        pass

    def is_available_forward(self, activity, groups, **kwargs):
        pass

    def is_available_forward_by_qtrs(self, activity, groups, **kwargs):
        pass

    def parse(self, test, codelists):
        mappings = (
            (re.compile(r'^if (.*) then (.*)$'), self.if_then, 'if_then'),
            (re.compile(r'list \S*$'), self.a_list, 'list'),
            (re.compile(r'`[^`]+`$'), self.xpath, 'xpath'),
            (re.compile(r'^\d+$'), self.integer, 'integer'),
            (re.compile(r'[A-Z]+\d+$'), self.code, 'code'),
            (re.compile(r'^where (`\S*`) exists, (`\S*`)$'), self.where, 'where'),
            (re.compile(r'^(.*) or (.*)$'), self.either, 'or'),
            (re.compile(r'^(.*) and (.*)$'), self.both, 'and'),
            (re.compile(r'^(`\S*`) is not (\S*)$'), self.is_not, 'is_not'),
            (re.compile(r'^(`\S*`) is at least (\d+)$'), self.is_at_least, 'is_at_least'),
            (re.compile(r'^(`\S*`) exists$'), self.exists, 'exists'),
            (re.compile(r'^(`\S*`) starts with (`\S*`)$'), self.starts_with, 'starts_with'),
            (re.compile(r'^every (`\S*`) is on (list \S*)$'), self.is_on_list, 'is_on_list'),
            (re.compile(r'^(`\S*`) has more than (\d+) characters$'), self.is_more_than_x_characters, 'is_more_than_x_characters'),
            (re.compile(r'^(.*) is less than (\d+) months ago$'), self.is_less_than_x_months_ago, 'is_less_than_x_months_ago'),
            (re.compile(r'^(`\S*`) is available forward$'), self.is_available_forward, 'is_available_forward'),
            (re.compile(r'^(`\S*`) is available forward by quarters$'), self.is_available_forward_by_qtrs, 'is_available_forward_by_qtrs'),
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
        return [test['fn'](activity) for test in self.tests]

    def test_activities(self, activities):
        return [self.test_activity(activity) for activity in activities]
