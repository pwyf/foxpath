
#  FoXPath, tools for processing FoXPath test suites,
#  by Martin Keegan, Mark Brough and Ben Webb

#  Copyright (C) 2013  Ben Webb
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import re
import datetime
from functools import partial

def generate_mappings():
    mappings = []

    def add(regex):
        def append_to_mappings(fn):
            mappings.append((re.compile(regex),fn))
            return fn
        return append_to_mappings

    def add_partial(regex):
        def append_to_mappings(fn):
            def partial_fn(groups):
                return partial(fn, groups=groups)
            mappings.append((re.compile(regex), partial_fn))
            return fn
        return append_to_mappings

    def add_partial_with_list(regex):
        def append_to_mappings(fn):
            def partial_fn(groups):
                return partial(fn, groups=groups)
            mappings.append((re.compile(regex), partial_fn))
            return fn
        return append_to_mappings

    @add('(\S*) is an? (.*)\?')
    def is_an(groups):
        if groups[1] == 'iso date':
            return None
        elif groups[1] == 'integer':
            def int_check(x):
                try:
                    int(x)
                    return True
                except ValueError:
                    return False
            def is_an_integer(activity):
                return reduce(lambda x,y: x and y,
                            map(lambda x: int_check(x),
                                    activity.xpath(groups[0])),
                            False)
            return is_an_integer

    @add_partial('(\S*) has more than (\S*) characters\?')
    def text_chars(activity, groups):
        return bool(reduce(lambda x,y: x or y,
                        map(lambda x: len(x)>int(groups[1]),
                            activity.xpath(groups[0])),
                        False))

    def rm_blank(alist):
        return filter(lambda x: x!='', alist)

    @add_partial('(\S*) sum to (\S*)\?')
    def sum(activity, groups):
        return (reduce(lambda x,y: float(x)+float(y),
                           rm_blank(activity.xpath(groups[0])),
                           0)
                   == float(groups[1]))

    @add_partial('(\S*) starts with (\S*)\?')
    def x_startswith_y(activity, groups):
        return activity.xpath(groups[0])[0].startswith(activity.xpath(groups[1])[0])

    @add_partial('(\S*) exists (\S*) times?\?')
    def exist_times(activity, groups):
        return len(rm_blank(activity.xpath(groups[0]))) == int(groups[1])

    @add_partial('(\S*) exists more than (\S*) times?\?')
    def exist_times(activity, groups):
        return len(rm_blank(activity.xpath(groups[0]))) > int(groups[1])

    def exist_check(activity, xpath):
        return bool(rm_blank(activity.xpath(xpath)))

    def check_value_is(activity, xpath, value, default):
        # This is slightly odd. If there is no value provided,
        # we should return what the expression would like us
        # to say.
        # e.g. if there is no aid type, then you might want
        # to include this activity anyway, rather
        # than excluding it.
        if not exist_check(activity, xpath):
            return default
        if rm_blank(activity.xpath(xpath)[0]) == value:
            return True
        return False

    def check_value_gte(activity, xpath, amount, default):
        # This is slightly odd. If there is no value provided,
        # we should return what the expression would like us
        # to say.
        # e.g. if there is no activity status, then you might 
        # want to include this activity anyway, rather
        # than excluding it.
        if not bool(rm_blank(activity.xpath(xpath))):
            return default
        return bool(int(rm_blank(activity.xpath(xpath)[0])) >= int(amount))

    def exist_check_two_list(activity, xpath_one, xpath_two, codelist):
        outcome = False
        data = activity.xpath(xpath_one)+activity.xpath(xpath_two)
        for d in data:
            try:
                if bool(str(d) in codelist):
                    outcome = True  
                elif bool(str(d).lowercase in codelist):
                    outcome = True 
                elif bool(str(d).uppercase in codelist):
                    outcome = True
                return outcome
            except Exception:
                return False

    def exist_check_list(activity, xpath, codelist):
        outcome = False
        data = activity.xpath(xpath)
        for d in data:
            try:
                if bool(str(d) in codelist):
                    outcome = True  
                elif bool(str(d).lowercase in codelist):
                    outcome = True 
                elif bool(str(d).uppercase in codelist):
                    outcome = True
                return outcome
            except Exception:
                return False

    def get_forward_date(end_dates, default_date):
        latest_date = datetime.datetime.strptime(default_date, "%Y-%m-%d")

        def get_latest(end_dates):
            if len(end_dates)==2:
                if (datetime.datetime.strptime(end_dates[1], "%Y-%m-%d") > datetime.datetime.strptime(end_dates[0], "%Y-%m-%d")):
                    return end_dates[1]
                else:
                    return end_dates[0]
            elif len(end_dates)==1:
                return end_dates[0]

        latest_end_date=get_latest(end_dates)
        if latest_end_date:
            if (datetime.datetime.strptime(latest_end_date, "%Y-%m-%d") < datetime.datetime.strptime(default_date, "%Y-%m-%d")):
                return latest_end_date
        return default_date

    def date_gte_than(the_dates, later_date):
        for the_date in the_dates:
            if (datetime.datetime.strptime(the_date, "%Y-%m-%d") >= datetime.datetime.strptime(later_date, "%Y-%m-%d")):
                return True
        return False

    def exist_forward(activity, xpath):
        # Check if any corresponding xpath is later than Dec 2014. If the
        # activity ended earlier than Dec 2014, then it will be ignored.
        default_date="2014-12-31"
        end_dates=activity.xpath('activity-date[@type="end-planned"]/@iso-date|activity-date[@type="end-actual"]/@iso-date')
        end_date = get_forward_date(end_dates, default_date)

        if mkdate(end_date) < mkdate(default_date):
            return None

        # Check if xpath (budget, planned-disbursement available for one year before the end date.
        element = activity.xpath(xpath)
        for e in element:
            if date_gte_than(e.xpath('period-end/@iso-date'), end_date):
                return True
        return False

    def twelve_months_before(end_date):
        newdate = datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.timedelta(days=365)
        return datetime.datetime.strftime(newdate, "%Y-%m-%d")

    def mkdate(date):
        return datetime.datetime.strptime(date, "%Y-%m-%d")

    def check_fwd_within_scope(e, xpath, start_date, end_date):
        if ((mkdate(start_date) <= mkdate(e.xpath('period-end/@iso-date')[0])
                and (mkdate(e.xpath('period-end/@iso-date')[0]) <= mkdate(end_date)))):
            return True
        return False

    def exist_forward_qtrs(activity, xpath, qtrs):
        # Check, for period 12 months prior to Dec 2014
        # whether forward budgets are available.
        # Check whether at least {qtrs} elements are available in 12 months
        # before the relevant end date.
        # Used both for `forward` (>=1 elements) and `forward by quarters`
        # (>=3 elements) tests.
        default_date="2014-12-31"
        end_dates=activity.xpath('activity-date[@type="end-planned"]/@iso-date|activity-date[@type="end-actual"]/@iso-date')
        end_date = get_forward_date(end_dates, default_date)

        if mkdate(end_date) < mkdate(default_date):
            return None

        start_date = twelve_months_before(end_date)
        count = 0
        for element in activity.xpath(xpath):
            if check_fwd_within_scope(element, xpath, start_date, end_date):
                count +=1
        if count >=qtrs:
            return True
        return False

    def x_months_ago_check(activity, xpath, months, many=False):
        outcome = False
        months = int(months)
        current_date = datetime.datetime.utcnow()
        if many:
            for check in activity.xpath(many):
                try:
                    if ((current_date-datetime.datetime.strptime(check.xpath(xpath)[0], "%Y-%m-%d")) 
                        < (datetime.timedelta(days=(30*months)))):
                        outcome = True
                except IndexError:
                    pass
        else:
            try:
                if ((current_date-(datetime.datetime.strptime(activity.xpath(xpath)[0], "%Y-%m-%d")))
                        < (datetime.timedelta(days=(30*months)))):
                    outcome = True
            except IndexError:
                pass
        return outcome

    @add_partial('only one of (\S*) or (\S*) exists\?')
    def exist_xor(activity, groups):
        return (exist_check(activity, groups[0]) != 
                exist_check(activity, groups[1]))

    @add_partial('(\S*) or (\S*) exists\?')
    def exist_or(activity, groups):
        return (exist_check(activity, groups[0]) or 
                exist_check(activity, groups[1]))

    @add_partial('(\S*) is (\S*)\?')
    def x_is_y(activity, groups):
        return check_value_is(activity, groups[0], groups[1], False)

    @add_partial('(\S*) exists\?') 
    def exist(activity, groups):
        return exist_check(activity, groups[0]) 

    @add_partial_with_list('(\S*) is on list (\S*)\?') 
    def exist_list(data, groups):
        return exist_check_list(data['activity'], groups[0], data['lists'][groups[1]])

    @add_partial_with_list('at least one (\S*) is on list (\S*)\?') 
    def atleastone_x_on_list_z(data, groups):
        return exist_check_list(data['activity'], groups[0], data['lists'][groups[1]])

    @add_partial_with_list('(\S*) or (\S*) is on list (\S*)\?')
    def x_or_y_on_list_z(data, groups):
        return exist_check_two_list(data['activity'], groups[0], groups[1], data['lists'][groups[2]])

    @add_partial('(\S*) or (\S*) is available forward by quarters \(if (\S*) is at least (\S*)\)\?')
    def x_on_list_z_cond(activity, groups):
        if check_value_gte(activity, groups[2], groups[3], True):
            return (exist_forward_qtrs(activity, groups[0], 3) or
                    exist_forward_qtrs(activity, groups[1], 3))

    @add_partial('(\S*) or (\S*) is available forward \(if (\S*) is at least (\S*)\)\?')
    def x_on_list_z_cond(activity, groups):
        if check_value_gte(activity, groups[2], groups[3], True):
            return (exist_forward_qtrs(activity, groups[0], 1) or
                    exist_forward_qtrs(activity, groups[1], 1))

    @add_partial_with_list('(\S*) is on list (\S*) \(if (\S*) is at least (\S*)\?')
    def x_on_list_z_cond(data, groups):
        if check_value_gte(activity, groups[2], groups[3], True):
            return exist_check_list(data['activity'], groups[0], data['lists'][groups[1]])

    @add_partial_with_list('(\S*) or (\S*) is on list (\S*) \(if (\S*) is at least (\S*)\?')
    def x_or_y_on_list_z_cond(data, groups):
        if check_value_gte(activity, groups[3], groups[4], True):
            return exist_check_two_list(data['activity'], groups[0], groups[1], data['lists'][groups[2]])

    @add_partial_with_list('at least one \((\S*) or (\S*)\) is on list (\S*)\?')
    def atleastone_x_y_on_list_z(data, groups):
        return exist_check_two_list(data['activity'], groups[0], groups[1], data['lists'][groups[2]])

    @add_partial('(\S*) or (\S*) \(for each (\S*)\) is less than (\S*) months? ago\?')
    def less_than_x_months_ago(activity, groups):
        return (x_months_ago_check(activity, groups[0], groups[3]) or 
                x_months_ago_check(activity, groups[1], groups[3], groups[2]))

    @add_partial('(\S*) or (\S*) or (\S*) or (\S*) is less than (\S*) months? ago\?')
    def less_than_x_months_ago(activity, groups):
        return (x_months_ago_check(activity, groups[0], groups[4]) or 
                x_months_ago_check(activity, groups[1], groups[4]) or 
                x_months_ago_check(activity, groups[2], groups[4]) or 
                x_months_ago_check(activity, groups[3], groups[4]))

    @add_partial('(\S*) or (\S*) or (\S*) or (\S*) or (\S*) \(for any (\S*)\) is less than (\S*) months? ago\?')
    def less_than_x_months_ago(activity, groups):
        return (x_months_ago_check(activity, groups[0], groups[6]) or 
                x_months_ago_check(activity, groups[1], groups[6]) or 
                x_months_ago_check(activity, groups[2], groups[6]) or 
                x_months_ago_check(activity, groups[3], groups[6]) or
                x_months_ago_check(activity, groups[4], groups[6], groups[5]))

    ## Conditional tests (only run if something)
    
    @add_partial('(\S*) exists \(if (\S*) is at least (\S*)\)\?') 
    def exist_if_gte(activity, groups):
        if check_value_gte(activity, groups[1], groups[2], True):
            return exist_check(activity, groups[0])
        else:
            return None

    @add_partial('(\S*) or (\S*) exists \(if (\S*) is at least (\S*)\)\?') 
    def exist_or_if_gte(activity, groups):
        if check_value_gte(activity, groups[2], groups[3], True):
            return (exist_check(activity, groups[0]) or 
                    exist_check(activity, groups[1]))
        else:
            return None

    @add_partial('(\S*) exists \(if (\S*) is at least (\S*) and (\S*) is not (\S*)\)\?') 
    def exist_if_both(activity, groups):
        if (check_value_gte(activity, groups[1], groups[2], True) and not (check_value_is(activity, groups[3], groups[4], False))):
            return exist_check(activity, groups[0])
        else:
            return None

    @add_partial('(\S*) exists \(if (\S*) is at least (\S*) and \((\S*) or (\S*) is not (\S*)\)\)\?') 
    def exist_if_both_or(activity, groups):
        if (check_value_gte(activity, groups[1], groups[2], True) and not (check_value_is(activity, groups[3], groups[5], False) or check_value_is(activity, groups[4], groups[5], False))):
            return exist_check(activity, groups[0])
        else:
            return None

    @add_partial('(\S*) or (\S*) exists \(if (\S*) is at least (\S*) and (\S*) is not (\S*)\)\?') 
    def exist_or_if_both(activity, groups):
        if (check_value_gte(activity, groups[2], groups[3], True) and not (check_value_is(activity, groups[4], groups[5], False))):
            return (exist_check(activity, groups[0]) or 
                    exist_check(activity, groups[1]))
        else:
            return None

    @add_partial('(\S*) or (\S*) exists \(if (\S*) is at least (\S*) and \((\S*) or (\S*) is not (\S*)\)\)\?') 
    def exist_or_if_both(activity, groups):
        if (check_value_gte(activity, groups[2], groups[3], True) and not (check_value_is(activity, groups[4], groups[6], False) or check_value_is(activity, groups[5], groups[6], False))):
            return (exist_check(activity, groups[0]) or 
                    exist_check(activity, groups[1]))
        else:
            return None

    return mappings
