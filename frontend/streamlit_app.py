from __future__ import annotations

import httpx
import streamlit as st

st.set_page_config(page_title="PaperLens", layout="wide")
st.title("📚 PaperLens — Research Paper Intelligence Aggregator")
st.caption("MVP UI: Streamlit dulu, React + Tailwind di v2.")

with st.sidebar:
    st.header("Filter")
    year = st.slider("Tahun", 2010, 2026, (2022, 2026))
    sources = st.multiselect(
        "Sumber",
        ["crossref", "openalex", "arxiv", "semantic_scholar", "pubmed", "doaj"],
        default=["crossref", "openalex", "arxiv", "semantic_scholar"],
    )
    oa_only = st.checkbox("Open Access only", value=False)
    min_cite = st.number_input("Minimal citation", 0, 10000, 0)

query = st.text_input("Cari paper", placeholder="contoh: graph neural network drug discovery")

if st.button("🔍 Search", type="primary") and query:
    payload = {
        "query": query,
        "filters": {
            "year_from": year[0],
            "year_to": year[1],
            "sources": sources,
            "open_access": oa_only,
            "min_citations": min_cite,
        },
        "limit": 25,
    }
    with st.spinner("Memanggil backend..."):
        try:
            response = httpx.post("http://localhost:8000/api/v1/search", json=payload, timeout=60)
            if response.status_code == 501:
                st.warning(response.json().get("detail", "Search belum diimplementasikan."))
            else:
                response.raise_for_status()
                data = response.json()
                st.success(f"Ditemukan {data['total']} paper dalam {data['latency_ms']} ms")
                for paper in data["results"]:
                    with st.container(border=True):
                        st.subheader(paper["title"])
                        st.caption(f"{paper.get('year') or '-'} · {paper.get('venue') or 'Unknown venue'}")
        except httpx.ConnectError:
            st.error("Backend belum berjalan. Jalankan: uv run uvicorn app.main:app --reload --port 8000")
        except httpx.HTTPError as exc:
            st.error(f"Request gagal: {exc}")
else:
    st.info("Jalankan backend, lalu masukkan query untuk mulai mencari paper.")
