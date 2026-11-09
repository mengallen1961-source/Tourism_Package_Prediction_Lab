# ==============================================================
# Cell C2.7b | Smoke test for the Streamlit app (Cases 1 and 2)
# --------------------------------------------------------------
# Purpose : Start app.py headless and check what a user sees: the four input
#           cards, a prediction with one of the three actions, the readable
#           review (Yes/No, thousands separator), the technical DataFrame
#           and the business rule in the sidebar.
# Input   : tourism_project/deployment/app.py and its model files
# Output  : pytest result
# ==============================================================
import logging
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "deployment" / "app.py"
CARDS = ["Customer profile", "Work & income", "Travel habits", "This enquiry"]


def run_app():
    for name in logging.root.manager.loggerDict:
        if name.startswith("streamlit"):
            logging.getLogger(name).setLevel(logging.ERROR)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    return at


def test_form_is_grouped_in_cards():
    at = run_app()
    headings = " ".join(m.value for m in at.markdown)
    for card in CARDS:
        assert card in headings, f"missing input card: {card}"


def test_prediction_review_and_rule():
    at = run_app()
    at.button[0].click().run()
    assert not at.exception
    actions = " ".join(m.value for m in [*at.success, *at.warning, *at.info])
    assert any(a in actions for a in ("CALL", "SEND BROCHURE", "NO ACTION")), "no action shown"
    assert any(m.label == "Purchase probability" for m in at.metric)
    review = " ".join(m.value for m in at.markdown)
    assert "| Holds a passport | **No** |" in review or "| Holds a passport | **Yes** |" in review
    assert "| Monthly income | **22,368** |" in review
    assert len(at.expander) == 1 and len(at.expander[0].dataframe) == 1, "technical DataFrame missing"
    assert any("Send brochure" in m.value for m in at.sidebar.markdown), "sidebar should show the brochure rule"
