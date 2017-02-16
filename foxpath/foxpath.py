import datetime
import re

from lxml import etree


class Foxpath(object):
    def load_tests(self, tests, codelists=None):
        whitespace = re.compile(r'\s+')

        def strip_and_parse(expression):
            trimmed_expr = whitespace.sub(' ', expression).strip()
            return self.parse(trimmed_expr, codelists)

        return {
            test['id']: strip_and_parse(test['expression'])
            for test in tests
        }

    def parse(self, test, codelists):
        def mkdate(date_str):
            try:
                return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None

        def xpath(activity, groups, **kwargs):
            # [1:-1] gets rid of the backticks
            return activity.xpath(groups[0][1:-1])

        def integer(activity, groups, **kwargs):
            return int(groups[0])

        def code(activity, groups, **kwargs):
            return groups[0]

        def regex(activity, groups, **kwargs):
            return re.compile(groups[0][6:])

        def codelist(activity, groups, codelists, **kwargs):
            # [:-9] gets rid of ' codelist'
            codelist = codelists.get(groups[0][:-9])
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
            const = groups[1](activity)
            if len(vals) < 1:
                print('note: is_at_least was expecting to find one and only one element. Found 0')
                return True
            if len(vals) > 1:
                print('note: is_at_least was expecting to find one and only one element. Found {}'.format(len(vals)))
            return any([int(val) >= const for val in vals])

        def is_before(activity, groups, **kwargs):
            comparison = 'date'
            less = groups[0](activity)
            more = groups[1](activity)
            if len(less) < 1 or len(more) < 1:
                return None
            if comparison == 'date':
                less = mkdate(less[0])
                more = mkdate(more[0])
            if less is None or more is None:
                return None
            return less <= more

        def exists(activity, groups, **kwargs):
            return any([val != '' for val in groups[0](activity)])

        def is_on_list(activity, groups, **kwargs):
            def check_list(vals, codelist):
                for v in vals:
                    v = str(v)
                    versions = [v, v.lower(), v.upper()]
                    yield any([v in codelist for v in versions])
            vals = groups[1](activity)
            on_list = check_list(vals, groups[2](activity))
            if groups[0] == 'every':
                return all(on_list)
            else:
                return any(on_list)

        def matches_regex(activity, groups, **kwargs):
            exp = groups[0](activity)
            regex = groups[1](activity)
            return all([bool(regex.search(x)) for x in exp])

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

        # defaults to false
        def is_less_than_x_months_ago(activity, groups, **kwargs):
            current_date = datetime.date.today()
            def less_than_x_months_ago(date_str, months_ago):
                date = mkdate(date_str)
                if not date:
                    # date was invalid, so just fail
                    return False
                year_diff = current_date.year - date.year
                month_diff = 12 * year_diff + current_date.month - date.month
                if month_diff == months_ago:
                    return date.day > current_date.day
                return month_diff < months_ago

            dates = groups[0](activity)
            months_ago = groups[1](activity)
            return any([less_than_x_months_ago(date_str, months_ago) for date_str in dates])

        def is_available_forward(activity, groups, **kwargs):
            els = groups[0](activity)
            period = groups[1]
            today = datetime.date.today()

            def max_date(dates, default):
                if dates != []:
                    return max(filter(lambda x: x is not None, [mkdate(d) for d in dates]))
                else:
                    return default

            # Window start is from today onwards. We're only interested in budgets
            # that start or end after today.

            # Window period is for the next 365 days. We don't want to look later
            # than that; we're only interested in budgets that end before then.
            #
            # We get the latest date for end and start; 365 days fwd
            # if there are no dates
            one_years_time = today.replace(today.year + 1)
            end_dates = activity.xpath('activity-date[@type="end-planned"]/@iso-date|activity-date[@type="end-actual"]/@iso-date|activity-date[@type="3"]/@iso-date|activity-date[@type="4"]/@iso-date')
            end_date = max_date(end_dates, one_years_time)

            # If the activity ends earlier than the end of the window period,
            # don't penalise the donor for not having a budget
            escape_end_date = today + datetime.timedelta(days=177)
            if end_date < escape_end_date:
                return None

            def check_after(element, today):
                dates = element.xpath('period-start/@iso-date|period-end/@iso-date')
                return any([mkdate(date) >= today for date in dates])

            def max_budget_length(element, max_budget_length):
                # NB this will error if there's no period-end/@iso-date
                start = mkdate(element.xpath('period-start/@iso-date')[0])
                end = mkdate(element.xpath('period-end/@iso-date')[0])
                return ((end-start).days <= max_budget_length)

            # We set a maximum number of days for which a budget can last,
            # depending on the number of quarters that should be covered.
            if period == 'quarterly':
                max_days = 94
            else:
                # annually
                max_days = 370

            # A budget has to be:
            # 1) period-end after today
            # 2) a maximum number of days, depending on # of qtrs.
            for element in els:
                after_today = check_after(element, today)
                within_length = max_budget_length(element, max_days)
                if after_today and within_length:
                    return True
            return False

        ignored_constants = [
            'at least one', 'every',
            'annually', 'quarterly',
            'date',
        ]
        if test in ignored_constants:
            return test

        def is_past(activity, groups, **kwargs):
            el = groups[0](activity)
            if len(el) < 1:
                return None
            el = mkdate(el[0])
            if not el:
                return None
            today = datetime.date.today()
            return el <= today

        mappings = (
            (re.compile(r'^if (.*) then (.*)$'), if_then),
            (re.compile(r'\S* codelist$'), codelist),
            (re.compile(r'regex .*$'), regex),
            (re.compile(r'`[^`]+`$'), xpath),
            (re.compile(r'^\d+$'), integer),
            (re.compile(r'[A-Z]+\d+$'), code),
            (re.compile(r'^for any (`[^`]+`), (.*)$'), for_any),
            (re.compile(r'^(`[^`]+`) (?:should be|is) today, or in the past$'), is_past),
            (re.compile(r'^(.*) or (.*)$'), either),
            (re.compile(r'^(.*) and (.*)$'), both),
            (re.compile(r'^(`[^`]+`) (?:should be|is) not (\S*)$'), is_not),
            (re.compile(r'^(`[^`]+`) (?:should be|is) before (`[^`]+`)$'), is_before),
            (re.compile(r'^(`[^`]+`) (?:should be|is) at least (\d+)$'), is_at_least),
            (re.compile(r'^(`[^`]+`) (?:should be|is) present$'), exists),
            (re.compile(r'^(`[^`]+`) (?:should start|starts) with (`[^`]+`)$'), starts_with),
            (re.compile(r'^(at least one|every) (`[^`]+`) (?:should be|is) on the (\S* codelist)$'), is_on_list),
            (re.compile(r'^(`[^`]+`) (?:should have|has) more than (\d+) characters$'), is_more_than_x_characters),
            (re.compile(r'^(.*) (?:should be|is) less than (\d+) months ago$'), is_less_than_x_months_ago),
            (re.compile(r'^(`[^`]+`) (?:should be|is) available forward (annually|quarterly)$'), is_available_forward),
            (re.compile(r'^(`[^`]+`) (?:should match|matches) the (regex .*)$'), matches_regex),
        )
        for regex, fn in mappings:
            r = regex.match(test)
            if r:
                if r.groups():
                    groups = [self.parse(g, codelists) for g in r.groups()]
                else:
                    groups = [r.group()]
                return lambda x: fn(x, groups=groups, codelists=codelists)
        raise Exception('I don\'t understand {}'.format(test))

    def test_activity(self, activity, tests):
        def translate_result(result_value):
            results = {
                False: 'fail',
                True: 'pass',
                None: 'not-relevant',
            }
            return results[result_value]

        hierarchy = activity.xpath('@hierarchy')
        hierarchy = hierarchy[0] if hierarchy != [] else ''
        try:
            iati_identifier = activity.xpath('iati-identifier/text()')[0]
        except Exception:
            iati_identifier = 'Unknown'
        results = {
            test_id: translate_result(test_fn(activity))
            for test_id, test_fn in tests.items()
        }
        return {
            'results': results,
            'iati-identifier': iati_identifier,
            'hierarchy': hierarchy,
        }

    def test_activities(self, activities, tests):
        return [self.test_activity(activity, tests) for activity in activities]

    def test_doc(self, filepath, tests):
        doc = etree.parse(filepath)
        activities = doc.xpath('//iati-activity')
        return self.test_activities(activities, tests)

    def summarize_results(self, activities_results):
        scores = {
            'fail': 0,
            'pass': 0,
            'not-relevant': 0,
        }
        summary = {
            'overall': scores.copy(),
            'by-test': {},
        }
        for activity_results in activities_results:
            for test_id, result in activity_results['results'].items():
                if test_id not in summary['by-test']:
                    summary['by-test'][test_id] = scores.copy()
                summary['by-test'][test_id][result] += 1
                summary['overall'][result] += 1
        return summary
