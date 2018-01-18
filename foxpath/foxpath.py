from datetime import datetime
from importlib.machinery import SourceFileLoader

from . import utils


def load_step_definitions(filepath):
    # remarkably, this seems to be sufficient
    SourceFileLoader('', filepath).load_module()


def load_features(feature_path, codelists={}, today=datetime.today()):
    kwargs = {
        'codelists': codelists,
        'today': today,
    }

    features = utils.gherkinify(feature_path)

    out = []
    for feature in features:
        feature = feature['feature']
        feature_name = feature['name']
        tests = []
        for test in feature['children']:
            test_name = test['name']
            test_steps = test['steps']
            ctx = []
            for step in test_steps:
                step_type = step['keyword'].lower().strip()
                expr_fn, expr_groups = utils.find_matching_expr(
                    utils.mappings, step['text'])
                ctx.append((step_type, expr_fn, expr_groups))
            tests.append((test_name, utils.parse(ctx, **kwargs)))
        out.append((feature_name, tests))
    return out
