# ==============================================================
# Cell C2.7a | Tests for the layout module (Case 2)
# --------------------------------------------------------------
# Purpose : The form must never lose or duplicate a model input: for both
#           strategies (14 and 18 features) every feature sits in exactly one
#           card, unknown features land in "Other", and values are shown in
#           a readable form.
# Input   : tourism_project/deployment/layout.py
# Output  : pytest result
# ==============================================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "deployment"))

from layout import OTHER_GROUP, format_value, group_features  # noqa: E402

STRATEGY_C = ["Age", "TypeofContact", "CityTier", "Occupation", "Gender", "NumberOfPersonVisiting",
              "PreferredPropertyStar", "MaritalStatus", "NumberOfTrips", "Passport", "OwnCar",
              "NumberOfChildrenVisiting", "Designation", "MonthlyIncome"]
STRATEGY_A = STRATEGY_C + ["DurationOfPitch", "NumberOfFollowups", "ProductPitched", "PitchSatisfactionScore"]


def placed(groups):
    return [f for _, features in groups for f in features]


def test_strategy_c_uses_four_cards_without_loss():
    groups = group_features(STRATEGY_C)
    assert len(groups) == 4
    assert sorted(placed(groups)) == sorted(STRATEGY_C)


def test_strategy_a_adds_the_after_contact_card():
    groups = group_features(STRATEGY_A)
    assert len(groups) == 5 and "After first contact" in groups[-1][0]
    assert sorted(placed(groups)) == sorted(STRATEGY_A)


def test_unknown_feature_goes_to_other():
    groups = group_features(STRATEGY_C + ["LoyaltyScore"])
    assert groups[-1] == (OTHER_GROUP, ["LoyaltyScore"])


def test_values_are_readable():
    assert format_value("Passport", 1) == "Yes" and format_value("OwnCar", 0) == "No"
    assert format_value("MonthlyIncome", 17000) == "17,000"
    assert format_value("Age", 25.0) == "25"
