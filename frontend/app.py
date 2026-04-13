import os
import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyMate",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.flashcard {
    background: #f8f9fa;
    color: #1a1a1a;
    border-left: 4px solid #4f8bf9;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.correct { color: #22c55e; font-weight: 600; }
.wrong   { color: #ef4444; font-weight: 600; }
.score-box {
    background: #f0fdf4;
    color: #1a1a1a;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def call_process(file_bytes: bytes, filename: str) -> dict | None:
    try:
        with httpx.Client(timeout=600) as client:
            r = client.post(
                f"{API_URL}/process",
                files={"file": (filename, file_bytes)},
            )
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error("Cannot connect to the backend. Make sure `uvicorn app.main:app` is running.")
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"Backend error: {detail}")
    return None


def fetch_sessions() -> list[dict]:
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(f"{API_URL}/sessions")
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def fetch_session(session_id: str) -> dict | None:
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(f"{API_URL}/sessions/{session_id}")
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def render_summary(summary: list[str]):
    if not summary:
        st.info("No summary generated.")
        return
    for point in summary:
        st.markdown(f"- {point}")


def render_flashcards(flashcards: list[dict]):
    if not flashcards:
        st.info("No flashcards generated.")
        return

    st.caption(f"{len(flashcards)} cards — click a card to reveal the answer")

    for i, card in enumerate(flashcards, 1):
        with st.expander(f"**Card {i}:** {card['question']}"):
            st.markdown(
                f'<div class="flashcard">{card["answer"]}</div>',
                unsafe_allow_html=True,
            )


def render_quiz(quiz: list[dict], key_prefix: str):
    if not quiz:
        st.info("No quiz generated.")
        return

    st.caption(f"{len(quiz)} questions — choose your answers then press **Submit**")

    answers: dict[int, int] = {}
    for i, q in enumerate(quiz):
        st.markdown(f"**{i + 1}. {q['question']}**")
        choice = st.radio(
            label="",
            options=q["options"],
            index=None,
            key=f"{key_prefix}_q{i}",
            label_visibility="collapsed",
        )
        if choice is not None:
            answers[i] = q["options"].index(choice)
        st.divider()

    if st.button("Submit quiz", key=f"{key_prefix}_submit"):
        if len(answers) < len(quiz):
            st.warning(f"Answer all {len(quiz)} questions before submitting.")
            return

        score = sum(1 for i, q in enumerate(quiz) if answers[i] == q["correct_index"])
        pct = int(score / len(quiz) * 100)
        emoji = "🏆" if pct >= 80 else "📈" if pct >= 50 else "📖"

        st.markdown(
            f'<div class="score-box"><h2>{emoji} {score}/{len(quiz)} ({pct}%)</h2></div>',
            unsafe_allow_html=True,
        )

        for i, q in enumerate(quiz):
            correct = answers[i] == q["correct_index"]
            label = "✅ Correct" if correct else "❌ Wrong"
            with st.expander(f'{label} — {q["question"]}'):
                for j, opt in enumerate(q["options"]):
                    if j == q["correct_index"]:
                        st.markdown(f'<span class="correct">✓ {opt}</span>', unsafe_allow_html=True)
                    elif j == answers[i]:
                        st.markdown(f'<span class="wrong">✗ {opt}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown(f"&nbsp;&nbsp;{opt}")
                st.info(q["explanation"])


# ── Sidebar: session history ──────────────────────────────────────────────────
with st.sidebar:
    st.title("📚 StudyMate")
    st.caption("AI study assistant")
    st.divider()

    st.subheader("History")
    sessions = fetch_sessions()

    if not sessions:
        st.caption("No past sessions yet.")
    else:
        for s in sessions:
            label = f"📄 {s['filename']}"
            ts = s["created_at"][:16].replace("T", " ")
            if st.button(label, key=s["session_id"], help=ts, use_container_width=True):
                st.session_state["loaded"] = fetch_session(s["session_id"])

    st.divider()
    st.caption(f"Backend: `{API_URL}`")


# ── Main area ─────────────────────────────────────────────────────────────────
st.header("Upload a lecture file")
st.caption("Supported formats: PDF, DOCX, TXT · Max 10 MB")

uploaded = st.file_uploader(
    label="",
    type=["pdf", "docx", "doc", "txt"],
    label_visibility="collapsed",
)

if uploaded:
    st.info(
        "⏱ Processing takes 1–3 minutes with a local LLM. "
        "If the page reloads during that time, find your result in the **History** sidebar — it's always saved to the database.",
        icon="ℹ️",
    )
    if st.button("✨ Generate summary, flashcards & quiz", type="primary"):
        with st.spinner(f"Processing **{uploaded.name}** — agents running in parallel..."):
            result = call_process(uploaded.getvalue(), uploaded.name)
        if result:
            st.session_state["loaded"] = result
            st.session_state["active_file"] = uploaded.name
            st.rerun()  # force a clean re-render so the results section draws fresh

# ── Results ───────────────────────────────────────────────────────────────────
data = st.session_state.get("loaded")

if data:
    fname = data.get("filename", "")
    sid = data.get("session_id", "")
    st.success(f"Results for **{fname}** · session `{sid[:8]}…`")

    tab_summary, tab_cards, tab_quiz = st.tabs(["📝 Summary", "🃏 Flashcards", "❓ Quiz"])

    with tab_summary:
        render_summary(data.get("summary", []))

    with tab_cards:
        render_flashcards(data.get("flashcards", []))

    with tab_quiz:
        render_quiz(data.get("quiz", []), key_prefix=sid[:8])

else:
    st.info("Upload a file above to get started.")
