from datetime import datetime
from importlib.machinery import SourceFileLoader
import re

from gherkin.parser import Parser as GherkinParser


def given(pattern):
    def decorated(fn):
        Foxpath.mappings.append((re.compile(r'^{}$'.format(pattern)), fn))
        return fn
    return decorated


def then(pattern):
    def decorated(fn):
        Foxpath.mappings.append((re.compile(r'^{}$'.format(pattern)), fn))
        return fn
    return decorated


class Foxpath():
    mappings = []

    def __init__(self, stepfile_filepath):
        self._load_step_definitions(stepfile_filepath)
        self.gherkinparser = GherkinParser()

    def _load_step_definitions(self, filepath):
        Foxpath.mappings = []
        # remarkably, this seems to be sufficient
        SourceFileLoader('', filepath).load_module()

    def load_feature(self, feature_txt, codelists={}, today=datetime.today()):
        kwargs = {
            'codelists': codelists,
            'today': today,
        }
        return self._gherkinify_feature(feature_txt, **kwargs)

    def _find_matching_expr(self, mappings, line):
        for regex, fn in mappings:
            r = regex.match(line)
            if r:
                return fn, r.groups()
        print('I did not understand {}'.format(line))

    def _parse(self, ctx, **kwargs):
        def __parse(activity):
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
        return __parse

    def _gherkinify_feature(self, feature_txt, **kwargs):
        feature = self.gherkinparser.parse(feature_txt)
        feature = feature['feature']
        feature_name = feature['name']
        tests = []
        for test in feature['children']:
            test_name = test['name']
            test_steps = test['steps']
            ctx = []
            for step in test_steps:
                step_type = step['keyword'].lower().strip()
                expr_fn, expr_groups = self._find_matching_expr(
                    Foxpath.mappings, step['text'])
                ctx.append((step_type, expr_fn, expr_groups))
            tests.append((test_name, self._parse(ctx, **kwargs)))
        return (feature_name, tests)
