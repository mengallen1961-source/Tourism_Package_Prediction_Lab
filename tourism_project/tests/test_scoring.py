# ==============================================================
# Cell L.8a | Tests for the scoring module (Case 1)
# --------------------------------------------------------------
# Purpose : Run by CI on every pull request, before anything reaches main:
#           the rule file is sensible, actions follow the probability order,
#           and on the fixed test split the brochure band holds about 15 %
#           of customers while the call list is unchanged.
# Input   : tourism_project/deployment/{tourism_model.joblib, business_rules.json};
#           artifacts/data/{Xtest,ytest}.csv written by prep.py
# Output  : pytest result (a failing test blocks the merge)
# ==============================================================
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "tourism_project" / "deployment"
SPLIT = ROOT / "artifacts" / "data"
sys.path.insert(0, str(DEPLOY))

from scoring import BROCHURE, CALL, NO_ACTION, action_for, load_bundle, load_rules, score  # noqa: E402


@pytest.fixture(scope="module")
def bundle():
    b = load_bundle(DEPLOY)
    assert b is not None, "no model committed in tourism_project/deployment"
    return b


@pytest.fixture(scope="module")
def rules():
    return load_rules(DEPLOY)


def test_rule_file_is_sensible(bundle, rules):
    floor = rules["brochure_min_probability"]
    assert floor is not None, "business_rules.json is missing"
    assert 0 < floor < bundle["threshold"], "the brochure band must lie below the call threshold"


def test_actions_follow_probability_order(bundle, rules):
    rank = {NO_ACTION: 0, BROCHURE: 1, CALL: 2}
    grid = [i / 100 for i in range(101)]
    levels = [rank[action_for(p, bundle["threshold"], rules)] for p in grid]
    assert levels == sorted(levels), "a higher probability must never get a weaker action"


def test_shares_on_the_fixed_test_split(bundle, rules):
    X = pd.read_csv(SPLIT / "Xtest.csv")
    shares = score(bundle, X, rules)["recommendation"].value_counts(normalize=True)
    print("\n" + shares.round(3).to_string())
    assert abs(shares.get(CALL, 0) - bundle["test_metrics"]["flagged"] / len(X)) < 1e-9, "the call list changed"
    assert 0.10 <= shares.get(BROCHURE, 0) <= 0.20, "brochure band should hold about 15 % of customers"


def test_without_rule_file_nothing_changes(bundle):
    X = pd.read_csv(SPLIT / "Xtest.csv").head(50)
    actions = set(score(bundle, X, None)["recommendation"])
    assert BROCHURE not in actions and actions <= {CALL, NO_ACTION}
