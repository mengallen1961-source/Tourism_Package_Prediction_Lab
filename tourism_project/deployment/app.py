# ==============================================================
# Cell C2.6 | Streamlit app with a grouped, easier-to-check layout (Case 2)
# --------------------------------------------------------------
# Purpose : Same model, rules and batch tab as Case 1; the single-customer
#           tab is redesigned: inputs sit in titled cards by meaning
#           (profile, work, travel habits, this enquiry), the review shows
#           the same cards with readable values, and the result shows the
#           probability, the action and where it sits between the two
#           thresholds. The raw model input stays available as a DataFrame.
# Input   : None (the app reads tourism_model.joblib, metrics.json and
#           business_rules.json next to it, or from TOURISM_MODEL_DIR)
# Output  : tourism_project/deployment/app.py
# ==============================================================
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from layout import YES_NO, format_value, group_features, help_text, label
from scoring import (BROCHURE, CALL, NO_ACTION, load_bundle, load_report_card, load_rules, out_of_range,
                     rank_call_list, score, validate)

MODEL_DIR = Path(os.environ.get("TOURISM_MODEL_DIR", Path(__file__).resolve().parent))

st.set_page_config(page_title="Wellness Package Purchase Prediction", layout="wide")


@st.cache_resource
def get_bundle(model_version):
    # Cached per file version: when the pipeline commits a new model, its modification time changes
    # and the new bundle is loaded instead of the cached one.
    return load_bundle(MODEL_DIR)


model_file = MODEL_DIR / "tourism_model.joblib"
bundle = get_bundle(model_file.stat().st_mtime if model_file.exists() else None)
card = load_report_card(MODEL_DIR)
rules = load_rules(MODEL_DIR)
st.title("Wellness Tourism Package - Purchase Prediction")
st.caption("Visit with Us | scores customers before the first sales call")

if bundle is None:
    st.warning("No model has been deployed yet. The GitHub Actions pipeline commits the model here after its first run.")
    st.stop()

THRESHOLD = bundle["threshold"]
FLOOR = rules.get("brochure_min_probability")

# ---------------- sidebar: model card and business rule
with st.sidebar:
    st.header("Live model")
    st.write(f"**Strategy:** {bundle['strategy']}  \n**Algorithm:** {bundle['algorithm']}  \n"
             f"**Features:** {len(bundle['features'])}  \n**Decision threshold:** {THRESHOLD:.2f}")
    m = bundle["test_metrics"]
    c1, c2 = st.columns(2)
    c1.metric("Test F1", f"{m['f1']:.3f}")
    c2.metric("Test PR-AUC", f"{m['pr_auc']:.3f}")
    c1.metric("Precision", f"{m['precision']:.3f}")
    c2.metric("Recall", f"{m['recall']:.3f}")
    st.caption(f"Trained {bundle['trained_at_utc']} on {bundle['n_train']:,} customers | "
               f"commit {str(bundle.get('git_sha', 'local'))[:7]} | Python {bundle['versions']['python']}")
    if card:
        st.caption(f"Last pipeline decision: {card['last_decision']}")
    st.header("Business rule")
    if FLOOR is None:
        st.write("Below the threshold: no action.")
    else:
        st.write(f"**Call:** probability ≥ {THRESHOLD:.2f}  \n"
                 f"**Send brochure:** {FLOOR:.2f} ≤ probability < {THRESHOLD:.2f}  \n"
                 f"**No action:** probability < {FLOOR:.2f}")
        st.caption(rules.get("note", ""))


def input_widget(box, feature):
    """One input, chosen from the feature's schema (radio, select box, slider or number box)."""
    spec = bundle["input_schema"][feature]
    name, tip = label(feature), help_text(feature)
    if feature in YES_NO:
        default = 1 if int(spec["default"]) == 1 else 0
        return 1 if box.radio(name, ["No", "Yes"], index=default, horizontal=True, help=tip) == "Yes" else 0
    if spec["type"] == "categorical":
        levels = spec["levels"]
        return box.selectbox(name, levels, index=levels.index(spec["default"]), help=tip)
    if spec["integer"] and spec["max"] - spec["min"] <= 60:                 # e.g. age, trips, stars
        return box.slider(name, int(spec["min"]), int(spec["max"]), int(spec["default"]), help=tip)
    if spec["integer"]:                                                       # e.g. monthly income
        return box.number_input(name, min_value=0, value=int(spec["default"]),
                                step=500 if spec["max"] > 1000 else 1, help=tip)
    return box.number_input(name, min_value=0.0, value=float(spec["default"]), help=tip)


def in_pairs(items):
    return [items[i:i + 2] for i in range(0, len(items), 2)]


def action_bar(p):
    """Probability bar with the brochure and call thresholds marked."""
    marks = [(THRESHOLD, "call")] + ([(FLOOR, "brochure")] if FLOOR is not None else [])
    ticks = "".join(
        f'<div style="position:absolute;left:{x * 100:.1f}%;top:-4px;height:22px;border-left:2px dashed #888;"></div>'
        f'<div style="position:absolute;left:{x * 100:.1f}%;top:20px;font-size:0.75rem;color:#999;'
        f'transform:translateX(-50%);">{name} {x:.2f}</div>' for x, name in marks)
    colour = "#21c354" if p >= THRESHOLD else ("#ffbd45" if FLOOR is not None and p >= FLOOR else "#8b8b9a")
    return (f'<div style="position:relative;height:14px;background:rgba(128,128,128,0.25);border-radius:7px;margin:8px 0 34px 0;">'
            f'<div style="width:{min(p, 1) * 100:.1f}%;height:100%;background:{colour};border-radius:7px;"></div>'
            f'{ticks}</div>')


groups = group_features(bundle["features"])
single, batch = st.tabs(["Score one customer", "Score a customer list (CSV)"])

# ---------------- single customer: inputs in titled cards, two cards per row, two fields per card
with single:
    with st.form("customer"):
        values = {}
        for row in in_pairs(groups):
            for column, (title, features) in zip(st.columns(2, gap="large"), row):
                with column.container(border=True):
                    st.markdown(f"#### {title}")
                    for pair in in_pairs(features):
                        for box, feature in zip(st.columns(2, gap="medium"), pair):
                            values[feature] = input_widget(box, feature)
        submitted = st.form_submit_button("Predict", type="primary", use_container_width=True)

    if submitted:
        input_df = pd.DataFrame([values])[bundle["features"]]      # the inputs, saved into a dataframe

        st.subheader("Result")
        result = score(bundle, input_df, rules).iloc[0]
        p, action = float(result["purchase_probability"]), result["recommendation"]
        left, right = st.columns([1, 2], gap="large")
        left.metric("Purchase probability", f"{p:.1%}")
        with right:
            if action == CALL:
                st.success(f"**CALL** - likely buyer (probability ≥ {THRESHOLD:.0%}).")
            elif action == BROCHURE:
                st.warning(f"**SEND BROCHURE** - close to the call threshold "
                           f"({FLOOR:.0%}-{THRESHOLD:.0%}).")
            else:
                st.info(f"**NO ACTION** - unlikely buyer for now (probability < "
                        f"{(FLOOR if FLOOR is not None else THRESHOLD):.0%}).")
            st.markdown(action_bar(p), unsafe_allow_html=True)
        for note in out_of_range(bundle, input_df):                  # only free-typed numbers can leave the range
            st.warning(note)

        st.subheader("Please check the inputs")
        for row in in_pairs(groups):
            for column, (title, features) in zip(st.columns(2, gap="large"), row):
                with column.container(border=True):
                    st.markdown(f"**{title}**")
                    st.markdown("| Field | Value |\n|---|---|\n" + "\n".join(
                        f"| {label(f)} | **{format_value(f, values[f])}** |" for f in features))
        with st.expander("Model input (technical): the DataFrame passed to the model"):
            st.dataframe(input_df, hide_index=True, use_container_width=True)

# ---------------- batch: CSV -> ranked call list (unchanged from Case 1)
with batch:
    st.write("Upload a CSV with one row per customer and the columns: " + ", ".join(f"`{f}`" for f in bundle["features"]))
    upload = st.file_uploader("Customer list", type="csv")
    if upload is not None:
        customers = pd.read_csv(upload)
        problems = validate(bundle, customers)
        if problems:
            st.error("The file cannot be scored:\n\n" + "\n".join(f"- {p}" for p in problems))
        else:
            for note in out_of_range(bundle, customers):
                st.warning(note)
            ranked = rank_call_list(bundle, customers, rules)
            counts = ranked["recommendation"].value_counts()
            n_call = int(counts.get(CALL, 0))
            st.success(f"{n_call} of {len(ranked)} customers recommended for a call "
                       f"({n_call / len(ranked):.0%}); sorted from most to least likely buyer.")
            summary = pd.DataFrame({"customers": [int(counts.get(a, 0)) for a in (CALL, BROCHURE, NO_ACTION)]},
                                   index=[CALL, BROCHURE, NO_ACTION])
            summary["share %"] = (summary["customers"] / len(ranked) * 100).round(1)
            summary.loc["Overall"] = [len(ranked), 100.0]
            st.dataframe(summary, use_container_width=False)
            st.dataframe(ranked, hide_index=True, use_container_width=True)
            st.download_button("Download call list", ranked.to_csv(index=False), "call_list.csv", "text/csv")
