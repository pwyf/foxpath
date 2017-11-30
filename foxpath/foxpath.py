from datetime import datetime

from . import step_definitions, utils


def find_matching_expr(mappings, line):
    for regex, fn in mappings:
        r = regex.match(line)
        if r:
            return fn, r.groups()
    print('I did not understand {}'.format(line))


def parse(ctx, **kwargs):
    def _parse(activity):
        for step_type, expr_fn, expr_groups in ctx:
            result = True
            try:
                if expr_groups:
                    expr_fn(activity, *expr_groups, **kwargs)
                else:
                    expr_fn(activity, **kwargs)
            except Exception as e:
                result = False
                explain = str(e)
            if step_type == 'given':
                if not result:
                    return None, explain
            else:
                if result:
                    return True, ''
                else:
                    return False, explain
    return _parse


def load_tests(tests, codelists={}, today=datetime.today()):
    kwargs = {
        'codelists': codelists,
        'today': today,
    }
    loader = {}
    for test in tests:
        test_name = test['name']
        test_expr = test['expression']
        lines = [line.strip() for line in test_expr.strip().split('\n')]
        ctx = []
        for line in lines:
            step_type, expr = line.split(' ', 1)
            step_type = 'given' if step_type.lower() != 'then' else 'then'
            expr_fn, expr_groups = find_matching_expr(utils.mappings, expr)
            ctx.append((step_type, expr_fn, expr_groups))
        loader[test_name] = parse(ctx, **kwargs)
    return loader


# def test_activity(activity, tests, **kwargs):
#     def translate_result(result_value, explanation, **kwargs):
#         results = {
#             True: 1,
#             False: 0,
#             None: -1,
#         }
#         if kwargs.get('explain'):
#             return results[result_value], explanation
#         else:
#             return results[result_value]

#     try:
#         title = activity.xpath('title/narrative/text()')[0]
#     except Exception:
#         try:
#             title = activity.xpath('title/text()')[0]
#         except Exception:
#             title = None

#     hierarchy = activity.xpath('@hierarchy')
#     hierarchy = hierarchy[0] if hierarchy != [] else ''
#     try:
#         iati_identifier = activity.xpath('iati-identifier/text()')[0]
#     except Exception:
#         iati_identifier = 'Unknown'
#     results = OrderedDict([
#         (test_id, translate_result(*test_fn(activity), **kwargs))
#         for test_id, test_fn in tests.items()
#     ])
#     return {
#         'results': results,
#         'iati-identifier': iati_identifier,
#         'hierarchy': hierarchy,
#         'title': title,
#     }


# def test_activities(activities, tests, **kwargs):
#     return [test_activity(activity, tests, **kwargs) for activity in activities]


# def test_doc(filepath, tests, **kwargs):
#     doc = etree.parse(filepath)
#     activities = doc.xpath('//iati-activity')
#     return test_activities(activities, tests, **kwargs)


# @staticmethod
# def summarize_results(activities_results):
#     scores = {
#         1: 0,
#         0: 0,
#         -1: 0,
#     }
#     summary = OrderedDict()
#     remove_explanations = type(list(activities_results[0]['results'].values())[0]) is not int
#     for activity_results in activities_results:
#         for test_name, result in activity_results['results'].items():
#             if test_name not in summary:
#                 summary[test_name] = scores.copy()
#             if remove_explanations:
#                 summary[test_name][result[0]] += 1
#             else:
#                 summary[test_name][result] += 1
#     return summary
