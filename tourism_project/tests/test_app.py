# ==============================================================
# Cell L.8b | Smoke test for the Streamlit app (Case 1)
# --------------------------------------------------------------
# Purpose : Start app.py headless, press Predict with the default inputs and
#           check that a prediction and the business rule are shown.
# Input   : tourism_project/deployment/app.py and its model files
# Output  : pytest result
# ==============================================================
import logging
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "deployment" / "app.py"


def test_app_predicts_and_shows_the_rule():
    for name in logging.root.manager.loggerDict:
        if name.startswith("streamlit"):
            logging.getLogger(name).setLevel(logging.ERROR)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    messages = " ".join(m.value for m in [*at.success, *at.warning, *at.info])
    assert "Purchase probability" in messages
    assert any("Send brochure" in m.value for m in at.markdown), "sidebar should show the brochure rule"
