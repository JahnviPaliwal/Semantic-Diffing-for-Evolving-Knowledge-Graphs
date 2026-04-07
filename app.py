"""
app.py – Streamlit frontend for Semantic Diffing of Knowledge Graphs
Run with:  streamlit run app.py
"""

import os
import json
import streamlit as st
from semantic_diff import extract_entities_and_relations, compute_diff, summarise_diff
from graph_utils import build_graph, visualise_diff

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Semantic Knowledge Graph Diff",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Semantic Diffing for Evolving Knowledge Graphs")
st.markdown(
    "Upload a **baseline document** and a **new document**. "
    "The app extracts entities & relations from both, then highlights "
    "what changed in the knowledge graph."
)

# ── API key check ──────────────────────────────────────────────────────────
if not os.environ.get("GROQ_API_KEY"):
    st.error("⚠️  Please set the `GROQ_API_KEY` environment variable before running.")
    st.stop()

# ── Sidebar – load sample data ─────────────────────────────────────────────
st.sidebar.header("📂 Quick-load Sample Data")
if st.sidebar.button("Load sample documents"):
    sample_dir = os.path.join(os.path.dirname(__file__), "data")
    old_path = os.path.join(sample_dir, "doc_v1.txt")
    new_path = os.path.join(sample_dir, "doc_v2.txt")
    if os.path.exists(old_path) and os.path.exists(new_path):
        st.session_state["old_text"] = open(old_path).read()
        st.session_state["new_text"] = open(new_path).read()
        st.sidebar.success("Sample documents loaded!")
    else:
        st.sidebar.warning("Sample files not found in data/ folder.")

# ── File upload section ────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Baseline Document (v1)")
    uploaded_old = st.file_uploader("Upload old document (.txt)", type=["txt"],
                                    key="upload_old")
    if uploaded_old:
        st.session_state["old_text"] = uploaded_old.read().decode("utf-8")
    if "old_text" in st.session_state:
        st.text_area("Preview", st.session_state["old_text"][:600] + "…",
                     height=180, disabled=True)

with col2:
    st.subheader("📄 New Document (v2)")
    uploaded_new = st.file_uploader("Upload new document (.txt)", type=["txt"],
                                    key="upload_new")
    if uploaded_new:
        st.session_state["new_text"] = uploaded_new.read().decode("utf-8")
    if "new_text" in st.session_state:
        st.text_area("Preview", st.session_state["new_text"][:600] + "…",
                     height=180, disabled=True)

# ── Run diff ───────────────────────────────────────────────────────────────
if st.button("🚀 Extract & Compare Graphs", type="primary"):
    if "old_text" not in st.session_state or "new_text" not in st.session_state:
        st.warning("Please provide both documents first.")
        st.stop()

    with st.spinner("Extracting entities & relations from baseline document…"):
        old_data = extract_entities_and_relations(st.session_state["old_text"])

    with st.spinner("Extracting entities & relations from new document…"):
        new_data = extract_entities_and_relations(st.session_state["new_text"])

    # Compute diff
    diff = compute_diff(old_data, new_data)

    with st.spinner("Building graphs and generating diff image…"):
        old_graph = build_graph(old_data)
        new_graph = build_graph(new_data)
        img_bytes  = visualise_diff(old_graph, new_graph, diff)

    with st.spinner("Generating natural-language summary…"):
        summary = summarise_diff(diff)

    # ── Display results ────────────────────────────────────────────────────
    st.success("Done!")

    st.subheader("📊 Knowledge Graph Diff Visualisation")
    st.image(img_bytes, use_column_width=True)

    st.subheader("📝 Change Summary")
    st.info(summary)

    st.subheader("🔎 Detailed Diff")
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Added Entities",
        "➖ Removed Entities",
        "➕ Added Relations",
        "➖ Removed Relations",
    ])

    with tab1:
        if diff["added_entities"]:
            for e in diff["added_entities"]:
                st.markdown(f"- 🟢 **{e}**")
        else:
            st.write("No new entities.")

    with tab2:
        if diff["removed_entities"]:
            for e in diff["removed_entities"]:
                st.markdown(f"- 🔴 **{e}**")
        else:
            st.write("No removed entities.")

    with tab3:
        if diff["added_relations"]:
            for r in diff["added_relations"]:
                st.markdown(f"- 🟢 `{r[0]}` → **{r[1]}** → `{r[2]}`")
        else:
            st.write("No new relations.")

    with tab4:
        if diff["removed_relations"]:
            for r in diff["removed_relations"]:
                st.markdown(f"- 🔴 `{r[0]}` → **{r[1]}** → `{r[2]}`")
        else:
            st.write("No removed relations.")

    st.subheader("📦 Raw JSON")
    with st.expander("Old extraction"):
        st.json(old_data)
    with st.expander("New extraction"):
        st.json(new_data)
    with st.expander("Diff"):
        st.json(diff)
