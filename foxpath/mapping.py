
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

    @add_partial('(\S*) exists (\S*) times?\?')
    def exist_times(activity, groups):
        return len(rm_blank(activity.xpath(groups[0]))) == int(groups[1])

    @add_partial('(\S*) exists more than (\S*) times?\?')
    def exist_times(activity, groups):
        return len(rm_blank(activity.xpath(groups[0]))) > int(groups[1])

    def exist_check(activity, xpath):
        return bool(rm_blank(activity.xpath(xpath)))

    def exist_check_list(activity, xpath, codelist):
        outcome = False
        try:
            if bool(str(activity.xpath(xpath)[0]) in codelist):
                outcome = True  
            elif bool(str(activity.xpath(xpath)[0]).lowercase in codelist):
                outcome = True 
            elif bool(str(activity.xpath(xpath)[0]).uppercase in codelist):
                outcome = True
            return outcome
        except Exception:
            return False

    def x_months_ago_check(activity, xpath, months, many=False):
        outcome = False
        months = int(months)
        current_date = datetime.datetime.utcnow()
        if many:
            for check in activity.findall(many):
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

    @add_partial('(\S*) exists\?') 
    def exist(activity, groups):
        return exist_check(activity, groups[0]) 

    @add_partial_with_list('(\S*) is on list (\S*)\?') 
    def exist_list(data, groups):
        return exist_check_list(data['activity'], groups[0], data['lists'][groups[1]])

    @add_partial('(\S*) or (\S*) \(for each (\S*)\) is less than (\S*) months? ago\?')
    def less_than_x_months_ago(activity, groups):
        return (x_months_ago_check(activity, groups[0], groups[3]) or 
                x_months_ago_check(activity, groups[1], groups[3], groups[2]))

    return mappings
