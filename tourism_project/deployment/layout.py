# ==============================================================
# Cell C2.5 | Layout module: groups, labels and display formats (Case 2)
# --------------------------------------------------------------
# Purpose : Keep the screen layout decisions out of app.py so that they can
#           be tested without a browser: which card each feature belongs to,
#           its friendly label and help text, and how its value is shown in
#           the review summary. Unknown features fall into an "Other" card,
#           so the form still follows whatever the live model needs.
# Input   : None
# Output  : tourism_project/deployment/layout.py
# ==============================================================
"""Screen layout for the app: feature groups, labels and value formats."""

GROUPS = [
    ("👤 Customer profile", ["Age", "Gender", "MaritalStatus"]),
    ("💼 Work & income", ["Occupation", "Designation", "MonthlyIncome"]),
    ("✈️ Travel habits", ["NumberOfTrips", "PreferredPropertyStar", "Passport", "OwnCar"]),
    ("🧳 This enquiry", ["TypeofContact", "CityTier", "NumberOfPersonVisiting", "NumberOfChildrenVisiting"]),
    ("📞 After first contact", ["ProductPitched", "DurationOfPitch", "NumberOfFollowups", "PitchSatisfactionScore"]),
]
OTHER_GROUP = "🗂️ Other"

LABELS = {   # friendly label and help text; unknown features fall back to their column name
    "Age": ("Age", "Customer's age in years"),
    "Gender": ("Gender", None),
    "MaritalStatus": ("Marital status", None),
    "Occupation": ("Occupation", None),
    "Designation": ("Designation", "Job level in the current organisation"),
    "MonthlyIncome": ("Monthly income", "Gross monthly income"),
    "NumberOfTrips": ("Trips per year", "Average number of trips per year"),
    "PreferredPropertyStar": ("Preferred hotel rating", "Stars"),
    "Passport": ("Holds a passport", None),
    "OwnCar": ("Owns a car", None),
    "TypeofContact": ("Type of contact", "How the lead arrived"),
    "CityTier": ("City tier", "1 = most developed city category, 3 = least"),
    "NumberOfPersonVisiting": ("Persons travelling", "Total number of people on the trip"),
    "NumberOfChildrenVisiting": ("Children under 5 travelling", None),
    "ProductPitched": ("Product pitched", None),
    "DurationOfPitch": ("Pitch duration (minutes)", "Known only after the first contact"),
    "NumberOfFollowups": ("Follow-ups", "Known only after the first contact"),
    "PitchSatisfactionScore": ("Pitch satisfaction (1-5)", "Known only after the first contact"),
}
YES_NO = {"Passport", "OwnCar"}
MONEY = {"MonthlyIncome"}


def label(feature):
    return LABELS.get(feature, (feature, None))[0]


def help_text(feature):
    return LABELS.get(feature, (feature, None))[1]


def group_features(features):
    """Return [(group title, [features in model order])] for the features the model uses.
    Every feature appears in exactly one group; groups without features are left out."""
    grouped = []
    placed = set()
    for title, members in GROUPS:
        in_model = [f for f in features if f in members]
        if in_model:
            grouped.append((title, in_model))
            placed.update(in_model)
    rest = [f for f in features if f not in placed]
    if rest:
        grouped.append((OTHER_GROUP, rest))
    return grouped


def format_value(feature, value):
    """How a value is shown to people in the review summary."""
    if feature in YES_NO:
        return "Yes" if int(value) == 1 else "No"
    if feature in MONEY:
        return f"{int(value):,}"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
