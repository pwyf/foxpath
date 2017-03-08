from collections import OrderedDict
import datetime
import re

from lxml import etree


class Foxpath(object):
    def load_tests(self, tests, codelists=None):
        whitespace = re.compile(r'\s+')

        def strip_and_parse(expression):
            expression = expression.replace('*', '')
            trimmed_expr = whitespace.sub(' ', expression).strip()
            return self.parse(trimmed_expr, codelists)

        return {
            test['name']: strip_and_parse(test['expression'])
            for test in tests
        }

    def parse(self, test_expression, codelists):
        def mkdate(date_str):
            try:
                return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None

        def for_every_activity(activity, groups, **kwargs):
            result, explain = groups[0](activity)
            explain = 'for every activity, ' + explain
            return result, explain

        def xpath(activity, groups, **kwargs):
            # [1:-1] gets rid of the backticks
            return activity.xpath(groups[0][1:-1]), groups[0]

        def integer(activity, groups, **kwargs):
            return int(groups[0]), groups[0]

        def integer_list(activity, groups, **kwargs):
            return groups[0], groups[0]

        def code(activity, groups, **kwargs):
            return groups[0], groups[0]

        def regex(activity, groups, **kwargs):
            return re.compile(groups[0][7:-1]), groups[0]

        def codelist(activity, groups, codelists, **kwargs):
            # [:-9] gets rid of ' codelist'
            codelist = codelists.get(groups[0][:-9])
            if not codelist:
                raise Exception('That codelist doesn\'t exist')
            return codelist, groups[0]

        def for_loop(activity, groups, **kwargs):
            every = groups[0] == 'every'
            exps, exps_explain = groups[1](activity)
            if len(exps) == 0:
                return False, 'no {exps_explain} is present'.format(exps_explain=exps_explain)

            if every:
                explain = 'for every {exps_explain}, {result_explain}'
            else:
                explain = 'for not one of {exps_explain}, {result_explain}'
            for exp in exps:
                result, result_explain = groups[2](exp)
                if result and not every:
                    explain = 'for at least one {exps_explain}, {result_explain}'
                    break
                if not result and every:
                    explain = 'for at least one {exps_explain}, the following was not true: {result_explain}'
                    break

            explain = explain.format(exps_explain=exps_explain, result_explain=result_explain)
            return result, explain

        def either(activity, groups, **kwargs):
            res1, expl1 = groups[0](activity)
            res2, expl2 = groups[1](activity)
            result = res1 or res2
            if not result:
                explain = '{expl1}. Additionally, {expl2}'
            elif res1:
                explain = '{expl1}'
            elif res2:
                explain = '{expl2}'
            explain = explain.format(expl1=expl1, expl2=expl2)
            return result, explain

        def both(activity, groups, **kwargs):
            res1, expl1 = groups[0](activity)
            res2, expl2 = groups[1](activity)
            result = res1 and res2
            if not result:
                if res1 and res2 is None:
                    result = True
                elif res2 and res1 is None:
                    result = True

            if res1 and res2:
                explain = '{expl1} and {expl2}'
            elif not res1:
                explain = '{expl1}'
            else:
                explain = '{expl2}'
            explain = explain.format(expl1=expl1, expl2=expl2)
            return result, explain

        def if_then(activity, groups, **kwargs):
            ante, ante_explain = groups[0](activity)
            cons, cons_explain = groups[1](activity)
            if not ante:
                # if the condition fails,
                # return not relevant
                return None, ante_explain
            return cons, cons_explain

        def equals(activity, groups, **kwargs):
            vals, vals_explain = groups[0](activity)
            const, const_explain = groups[1](activity)
            result = False
            for val in vals:
                if val == str(const):
                    result = True
                    break
            if result:
                explain = '{vals_explain} is equal to {const_explain}'
            else:
                explain = 'the activity has {vals_explain} equal to {const_explain}'
            explain = explain.format(vals_explain=vals_explain, const_explain=const_explain)
            return result, explain

        # defaults to true
        def is_not(activity, groups, **kwargs):
            vals, vals_explain = groups[0](activity)
            should_not_is_not = groups[1]
            const, const_explain = groups[2](activity)
            result = True
            for val in vals:
                if val == str(const):
                    result = False
                    break
            if result:
                explain = '{vals_explain} {should_not_is_not} equal to {const_explain}'
            else:
                if should_not_is_not == 'is not':
                    explain = 'the activity has {vals_explain} equal to {const_explain}'
                else:
                    explain = 'the activity shouldn\'t have {vals_explain} equal to {const_explain}, but does'
            explain = explain.format(vals_explain=vals_explain, const_explain=const_explain, should_not_is_not=should_not_is_not)
            return result, explain

        def is_one_of(activity, groups, **kwargs):
            val = None
            vals, vals_explain = groups[0](activity)
            consts, const_explain = groups[1](activity)
            consts_list = consts.split(', ')
            if len(vals) == 0:
                explain = '{vals_explain} should be one of {const_explain}. However, the activity doesn\'t contain that element'
                result = True
            else:
                result = False
                for val in vals:
                    if val in consts_list:
                        result = True
                        break
                if result:
                    explain = '{vals_explain} is one of {const_explain} (it\'s {val})'
                else:
                    explain = '{vals_explain} is not one of {const_explain} (it\'s {val})'
            explain = explain.format(vals_explain=vals_explain, const_explain=const_explain, val=val)
            return result, explain


        # defaults to true
        def is_at_least(activity, groups, **kwargs):
            val = None
            vals, vals_explain = groups[0](activity)
            should_be_is = groups[1]
            const, const_explain = groups[2](activity)
            if len(vals) == 0:
                explain = '{vals_explain} should be at least {const_explain}. However, the activity doesn\'t contain that element'
                result = True
            else:
                result = False
                for val in vals:
                    if int(val) >= const:
                        result = True
                        break
                if result:
                    explain = '{vals_explain} is at least {const_explain} (it\'s {val})'
                else:
                    if should_be_is == 'is':
                        explain = '{vals_explain} is less than {const_explain}'
                    else:
                        explain = '{vals_explain} should be at least {const_explain}, but is only {val}'
            explain = explain.format(vals_explain=vals_explain, const_explain=const_explain, val=val)
            return result, explain

        def is_before(activity, groups, **kwargs):
            comparison = 'date'
            less, less_explain = groups[0](activity)
            more, more_explain = groups[1](activity)
            if len(less) == 0 or len(more) == 0:
                if len(less) == 0 and len(more) == 0:
                    result = None
                    explain = 'Neither {less_explain} nor {more_explain} are present, so can\'t determine their ordering'
                elif len(less) == 0:
                    result = None
                    explain = '{less_explain} is not present, so can\'t determine if it is before {more_explain}'
                elif len(more) == 0:
                    result = None
                    explain = '{more_explain} is not present, so can\'t determine if it is before {less_explain}'
                return None, explain.format(less_explain=less_explain, more_explain=more_explain)
            if comparison == 'date':
                less = mkdate(less[0])
                more = mkdate(more[0])
                if less is None or more is None:
                    result = None
                    if less is None and more is None:
                        explain = 'Neither {less_explain} ({less}) nor {more_explain} ({more}) use the format YYYY-MM-DD, so can\'t determine their ordering'
                    elif less is None:
                        explain = '{less_explain} ({less}) does not use the format YYYY-MM-DD, so can\'t determine if it is before {more_explain} ({more})'
                    elif more is None:
                        explain = '{more_explain} ({more}) does not use the format YYYY-MM-DD, so can\'t determine if it is after {less_explain} ({less})'
                    explain = explain.format(less_explain=less_explain, more_explain=more_explain, less=less, more=more)
                    return result, explain
            diff = (more - less).days
            result = diff >= 0
            diff_str = '{} days {}'.format(abs(diff), 'before' if result else 'after')
            explain = '{less_explain} ({less}) is {diff_str} {more_explain} ({more})'
            explain = explain.format(less_explain=less_explain, more_explain=more_explain, less=less, more=more, diff_str=diff_str)
            return result, explain

        def exists(activity, groups, **kwargs):
            vals, vals_explain = groups[0](activity)
            result = False
            for val in vals:
                if val != '':
                    result = True
                    break
            if result:
                explain = '{vals_explain} is present'
            else:
                explain = '{vals_explain} isn\'t present'
            explain = explain.format(vals_explain=vals_explain)
            return result, explain

        def not_exists(activity, groups, **kwargs):
            vals, vals_explain = groups[0](activity)
            result = True
            for val in vals:
                if val != '':
                    result = False
                    break
            if result:
                explain = '{vals_explain} isn\'t present'
            else:
                explain = '{vals_explain} is present'
            explain = explain.format(vals_explain=vals_explain)
            return result, explain

        def is_on_list(activity, groups, **kwargs):
            def check_list(val, codelist):
                val = str(val)
                versions = [val, val.lower(), val.upper()]
                return any([v in codelist for v in versions])

            val = None
            vals_comma = None
            every = groups[0] == 'every'
            vals, vals_explain = groups[1](activity)
            codelist, codelist_explain = groups[2](activity)

            if len(vals) == 0:
                result = False
                explain = 'there are no codes present, so there definitely aren\'t any from the {codelist_explain}'
            else:
                result = every
                for val in vals:
                    on_list = check_list(val, codelist)
                    if not on_list and every:
                        result = False
                        explain = 'every code used should be from the {codelist_explain}, but at least one ({val}) is not'
                        break
                    if on_list and not every:
                        result = True
                        explain = 'at least one code used is from the {codelist_explain} (e.g. {val})'
                        break
                if result and every:
                    explain = 'every code used is from the {codelist_explain}'
                if not result and not every:
                    explain = 'none of the codes used are from the {codelist_explain} (the following codes are used: {vals_comma})'
            explain = explain.format(codelist_explain=codelist_explain, vals_explain=vals_explain, val=val, vals_comma=', '.join(vals))
            return result, explain

        def matches_regex(activity, groups, **kwargs):
            exps, exps_explain = groups[0](activity)
            regex, regex_explain = groups[1](activity)
            exp = None
            results = True
            for exp in exps:
                if not bool(regex.search(exp)):
                    results = False
                    break
            if results:
                explain = 'All {exps_explain} match the {regex_explain}'
            else:
                explain = 'The {exps_explain} {exp} does not match the {regex_explain}'
            explain = explain.format(exps_explain=exps_explain, regex_explain=regex_explain, exp=exp)
            return results, explain

        # defaults to false
        def is_more_than_x_characters(activity, groups, **kwargs):
            most_chars = None
            most_str = None
            exps, exps_explain = groups[0](activity)
            reqd_chars, reqd_chars_explain = groups[1](activity)
            if len(exps) == 0:
                result = False
                explain = '{exps_explain} is not present'
            else:
                most_chars, most_str = max([(len(exp), exp) for exp in exps])
                result = most_chars > reqd_chars
                if result:
                    explain = '\'{most_str}\' is more than {reqd_chars_explain} characters long (it\'s {most_chars})'
                if not result:
                    explain = '\'{most_str}\' is too short (it\'s only {most_chars} characters long)'
            explain = explain.format(exps_explain=exps_explain, reqd_chars_explain=reqd_chars_explain, most_chars=most_chars, most_str=most_str)
            return result, explain

        # defaults to false
        def starts_with(activity, groups, **kwargs):
            x, x_explain = groups[0](activity)
            y, y_explain = groups[1](activity)
            if x == [] and y == []:
                result = False
                explain = '{x_explain} should start with {y_explain}, but neither are present on the activity'.format(x_explain=x_explain, y_explain=y_explain)
            elif x == []:
                result = False
                explain = '{x_explain} should start with {y_explain} (\'{y}\'), but {x_explain} isn\'t present on the activity'.format(x_explain=x_explain, y_explain=y_explain, y=y[0])
            elif y == []:
                result = False
                explain = '{x_explain} (\'{x}\') should start with {y_explain}, but {y_explain} isn\'t present on the activity'.format(x_explain=x_explain, y_explain=y_explain, x=x[0])
            else:
                result = x[0].startswith(str(y[0]))
                if result:
                    explain = '{x_explain} (\'{x}\') correctly starts with {y_explain} (\'{y}\')'.format(x_explain=x_explain, y_explain=y_explain, x=x[0], y=y[0])
                else:
                    explain = '{x_explain} (\'{x}\') should start with {y_explain} (\'{y}\'), but doesn\'t'.format(x_explain=x_explain, y_explain=y_explain, x=x[0], y=y[0])

            return result, explain

        # defaults to false
        def is_less_than_x_months_ago(activity, groups, **kwargs):
            dates, dates_explain = groups[0](activity)
            months_ago, months_ago_explain = groups[1](activity)

            if len(dates) == 0:
                explain = '{dates_explain} is not present, so assuming it is not less than {months_ago_explain} months ago'
                explain = explain.format(dates_explain=dates_explain, months_ago_explain=months_ago_explain)
                return False, explain

            valid_dates = list(filter(lambda x: x, [mkdate(date_str) for date_str in dates]))
            if not valid_dates:
                explain = '{dates_explain} ({date}) does not use format YYYY-MM-DD, so assuming it is not less than {months_ago_explain} months ago'
                explain = explain.format(dates_explain=dates_explain, months_ago_explain=months_ago_explain, date=dates[0])
                return False, explain

            max_date = max(valid_dates)
            prefix = '' if len(valid_dates) == 1 or max_date == min(valid_dates) else 'the most recent '

            current_date = datetime.date.today()
            if max_date > current_date:
                result = True
                explain = '{prefix}{dates_explain} ({max_date}) is in the future'
            else:
                year_diff = current_date.year - max_date.year
                month_diff = 12 * year_diff + current_date.month - max_date.month
                if month_diff == months_ago:
                    result = max_date.day > current_date.day
                else:
                    result = month_diff < months_ago
                if result:
                    explain = '{prefix}{dates_explain} ({max_date}) is less than {months_ago_explain} months ago'
                else:
                    explain = '{prefix}{dates_explain} ({max_date}) is not less than {months_ago_explain} months ago'
            explain = explain.format(prefix=prefix, dates_explain=dates_explain, months_ago_explain=months_ago_explain, max_date=max_date)
            return result, explain

        def is_available_forward(activity, groups, **kwargs):
            els, els_explain = groups[0](activity)
            period = groups[1]
            today = datetime.date.today()

            def max_date(dates, default):
                dates = list(filter(lambda x: x is not None, [mkdate(d) for d in dates]))
                if dates == []:
                    return default
                return max(dates)

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
                explain = 'activity is ending soon ({}) so we do not expect a budget'.format(end_date)
                return None, explain

            def check_after(element, today):
                dates = element.xpath('period-start/@iso-date|period-end/@iso-date')
                dates = list(filter(lambda x: x is not None, [mkdate(d) for d in dates]))
                return any([date >= today for date in dates])

            def max_budget_length(element, max_budget_length):
                # NB this will error if there's no period-end/@iso-date
                try:
                    start = mkdate(element.xpath('period-start/@iso-date')[0])
                    end = mkdate(element.xpath('period-end/@iso-date')[0])
                    within_length = ((end-start).days <= max_budget_length)
                except TypeError:
                    return False
                return within_length

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
            result = False
            for element in els:
                after_today = check_after(element, today)
                within_length = max_budget_length(element, max_days)
                if after_today and within_length:
                    result = True
                    break
            if result:
                explain = '{els_explain} is available forward {period}'
            else:
                explain = '{els_explain} is not available forward {period}'
            explain = explain.format(els_explain=els_explain, period=period)
            return result, explain

        ignored_constants = [
            'should be', 'is',
            'should not be', 'is not',
            'at least one', 'every',
            'annually', 'quarterly',
            'date',
        ]
        if test_expression in ignored_constants:
            return test_expression

        def is_past(activity, groups, **kwargs):
            el, el_explain = groups[0](activity)
            if len(el) == 0:
                explain = '{el_explain} is not present, so the test is not relevant'.format(el_explain=el_explain)
                return None, explain
            el = el[0]
            d = mkdate(el)
            if not d:
                result = None
                explain = 'the date given for {el_explain} ({el}) does not use the format YYYY-MM-DD, so we can\'t test if it is in the past'
            else:
                today = datetime.date.today()
                result = d <= today
                if result:
                    explain = 'the date given for {el_explain} ({el}) is in the past'
                else:
                    explain = 'the date given for {el_explain} ({el}) is in the future'
            explain = explain.format(el_explain=el_explain, el=el)
            return result, explain

        mappings = (
            (re.compile(r'^for every activity, (.*)$'), for_every_activity),
            (re.compile(r'^if (.*) then (.*)$'), if_then),
            (re.compile(r'^(`[^`]+`) is one of \((.*)\)$'), is_one_of),
            (re.compile(r'\S* codelist$'), codelist),
            (re.compile(r'regex `.*`$'), regex),
            (re.compile(r'`[^`]+`$'), xpath),
            (re.compile(r'^\d+$'), integer),
            (re.compile(r'^\d+(?:, \d+)+$'), integer_list),
            (re.compile(r'[A-Z]+\d+$'), code),
            (re.compile(r'^for (at least one|every) (`[^`]+`), (.*)$'), for_loop),
            (re.compile(r'^(`[^`]+`) (?:should be|is) today, or in the past$'), is_past),
            (re.compile(r'^(.*)(?: or|\. Alternatively,) (.*)$'), either),
            (re.compile(r'^(.*) (?:and|but) (.*)$'), both),
            (re.compile(r'^(`[^`]+`) (?:should not be|is not) present$'), not_exists),
            (re.compile(r'^(`[^`]+`) is (\d+)$'), equals),
            (re.compile(r'^(`[^`]+`) (should not be|is not) (\S*)$'), is_not),
            (re.compile(r'^(`[^`]+`) (?:should be|is) chronologically before (`[^`]+`)$'), is_before),
            (re.compile(r'^(`[^`]+`) (should be|is) at least (\d+)$'), is_at_least),
            (re.compile(r'^(`[^`]+`) (?:should be|is) present$'), exists),
            (re.compile(r'^(`[^`]+`) (?:should start|starts) with (`[^`]+`)$'), starts_with),
            (re.compile(r'^(at least one|every) (`[^`]+`) (?:should be|is) on the (\S* codelist)$'), is_on_list),
            (re.compile(r'^(`[^`]+`) (?:should have|has) more than (\d+) characters$'), is_more_than_x_characters),
            (re.compile(r'^(.*) (?:should be|is) less than (\d+) months ago$'), is_less_than_x_months_ago),
            (re.compile(r'^(`[^`]+`) (?:should be|is) available forward (annually|quarterly)$'), is_available_forward),
            (re.compile(r'^(`[^`]+`) (?:should match|matches) the (regex .*)$'), matches_regex),
        )
        for regex, fn in mappings:
            r = regex.match(test_expression)
            if r:
                if r.groups():
                    groups = [self.parse(g, codelists) for g in r.groups()]
                else:
                    groups = [r.group()]
                return lambda x: fn(x, groups=groups, codelists=codelists)
        raise Exception('I don\'t understand {}'.format(test_expression))

    def test_activity(self, activity, tests, **kwargs):
        def translate_result(result_value, explanation, **kwargs):
            results = {
                True: 1,
                False: 0,
                None: -1,
            }
            if kwargs.get('explain'):
                return results[result_value], explanation
            else:
                return results[result_value]

        try:
            title = activity.xpath('title/narrative/text()')[0]
        except Exception:
            try:
                title = activity.xpath('title/text()')[0]
            except Exception:
                title = None

        hierarchy = activity.xpath('@hierarchy')
        hierarchy = hierarchy[0] if hierarchy != [] else ''
        try:
            iati_identifier = activity.xpath('iati-identifier/text()')[0]
        except Exception:
            iati_identifier = 'Unknown'
        results = OrderedDict([
            (test_id, translate_result(*test_fn(activity), **kwargs))
            for test_id, test_fn in tests.items()
        ])
        return {
            'results': results,
            'iati-identifier': iati_identifier,
            'hierarchy': hierarchy,
            'title': title,
        }

    def test_activities(self, activities, tests, **kwargs):
        return [self.test_activity(activity, tests, **kwargs) for activity in activities]

    def test_doc(self, filepath, tests, **kwargs):
        doc = etree.parse(filepath)
        activities = doc.xpath('//iati-activity')
        return self.test_activities(activities, tests, **kwargs)

    @staticmethod
    def summarize_results(activities_results):
        scores = {
            1: 0,
            0: 0,
            -1: 0,
        }
        summary = OrderedDict()
        remove_explanations = type(list(activities_results[0]['results'].values())[0]) is not int
        for activity_results in activities_results:
            for test_name, result in activity_results['results'].items():
                if test_name not in summary:
                    summary[test_name] = scores.copy()
                if remove_explanations:
                    summary[test_name][result[0]] += 1
                else:
                    summary[test_name][result] += 1
        return summary
