import streamlit as st
import pdfplumber
from dotenv import load_dotenv
import os
import json
import re
import requests

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Analyzer AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Load Environment Variables ──────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ─────────────────────────────────────────── */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 40%, #16213e 100%);
        font-family: 'Inter', sans-serif;
    }

    /* ── Header ─────────────────────────────────────────── */
    .hero-header {
        text-align: center;
        padding: 2.5rem 1rem 1rem;
    }
    .hero-header h1 {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa, #818cf8, #6366f1, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        letter-spacing: -1px;
    }
    .hero-header p {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 300;
    }

    /* ── Glass Card ─────────────────────────────────────── */
    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99,102,241,0.15);
    }

    /* ── Score Ring ──────────────────────────────────────── */
    .score-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
    }
    .score-ring {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        font-weight: 800;
        color: #fff;
        position: relative;
        margin-bottom: 1rem;
    }
    .score-ring::before {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        padding: 4px;
        background: conic-gradient(from 0deg, #6366f1, #a78bfa, #c084fc, #6366f1);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        animation: spin 4s linear infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .score-label {
        font-size: 1rem;
        color: #94a3b8;
        font-weight: 500;
    }

    /* ── Section Headers ────────────────────────────────── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 1rem;
    }
    .section-header .icon {
        font-size: 1.5rem;
    }
    .section-header h3 {
        font-size: 1.25rem;
        font-weight: 700;
        color: #e2e8f0;
        margin: 0;
    }

    /* ── List Items ─────────────────────────────────────── */
    .item-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .item-list li {
        padding: 0.65rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 10px;
        font-size: 0.95rem;
        color: #cbd5e1;
        line-height: 1.5;
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
    }
    .item-list li .bullet {
        flex-shrink: 0;
        margin-top: 2px;
    }
    .strength-item  { background: rgba(34,197,94,0.08);  border-left: 3px solid #22c55e; }
    .weakness-item  { background: rgba(239,68,68,0.08);  border-left: 3px solid #ef4444; }
    .keyword-item   { background: rgba(234,179,8,0.08);  border-left: 3px solid #eab308; }
    .suggest-item   { background: rgba(59,130,246,0.08); border-left: 3px solid #3b82f6; }

    /* ── Job Role Pills ─────────────────────────────────── */
    .role-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .role-pill {
        background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,139,250,0.2));
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 999px;
        padding: 0.5rem 1.2rem;
        color: #c4b5fd;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .role-pill:hover {
        background: linear-gradient(135deg, rgba(99,102,241,0.4), rgba(168,139,250,0.4));
        transform: scale(1.05);
    }

    /* ── Upload Area ────────────────────────────────────── */
    .upload-area {
        background: rgba(255,255,255,0.03);
        border: 2px dashed rgba(99,102,241,0.3);
        border-radius: 16px;
        padding: 3rem 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .upload-area:hover {
        border-color: rgba(99,102,241,0.6);
        background: rgba(99,102,241,0.05);
    }
    .upload-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .upload-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.3rem;
    }
    .upload-sub {
        color: #64748b;
        font-size: 0.9rem;
    }

    /* ── Streamlit Overrides ────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2.5rem !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(99,102,241,0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(99,102,241,0.45) !important;
    }
    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.03);
        border: 2px dashed rgba(99,102,241,0.25);
        border-radius: 16px;
        padding: 1rem;
    }
    .stSpinner > div {
        border-top-color: #6366f1 !important;
    }
    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_file) -> str:
    """Extract all text from an uploaded PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def analyze_resume_with_gemini(resume_text: str) -> dict:
    """Send resume text to Gemini REST API and return structured analysis."""
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
You are an expert resume analyst and career coach. Analyze the following resume text 
and provide a detailed evaluation. Return your response as a valid JSON object with 
exactly these keys (no markdown, no code fences, just raw JSON):

{{
  "overall_score": <number from 1 to 10>,
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1", "weakness 2", ...],
  "missing_keywords": ["keyword 1", "keyword 2", ...],
  "suggestions": ["suggestion 1", "suggestion 2", ...],
  "best_matching_job_roles": ["role 1", "role 2", ...]
}}

Evaluation criteria:
- Overall Score: Rate the resume from 1-10 based on formatting, content quality, 
  relevance, and completeness.
- Strengths: Highlight what the candidate does well (skills, experience, presentation).
- Weaknesses: Identify areas that hurt the resume's impact.
- Missing Keywords: Industry-standard keywords or skills that are absent but commonly 
  expected for the candidate's apparent field.
- Suggestions: Actionable recommendations to improve the resume.
- Best Matching Job Roles: Roles the candidate is most suited for based on their 
  profile.

RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(endpoint, json=payload)
    response.raise_for_status()  # raises HTTPError with full message on failure

    data = response.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


def render_score(score: int):
    """Render the animated score ring."""
    color = "#22c55e" if score >= 7 else "#eab308" if score >= 5 else "#ef4444"
    st.markdown(f"""
    <div class="score-container">
        <div class="score-ring" style="background: radial-gradient(circle, {color}22 0%, transparent 70%);">
            {score}/10
        </div>
        <div class="score-label">Overall Resume Score</div>
    </div>
    """, unsafe_allow_html=True)


def render_list(items: list, css_class: str, bullet: str):
    """Render a styled list of items."""
    li_items = "".join(
        f'<li class="{css_class}"><span class="bullet">{bullet}</span>{item}</li>'
        for item in items
    )
    st.markdown(f'<ul class="item-list">{li_items}</ul>', unsafe_allow_html=True)


def render_pills(items: list):
    """Render job roles as pill badges."""
    pills = "".join(f'<span class="role-pill">{item}</span>' for item in items)
    st.markdown(f'<div class="role-pills">{pills}</div>', unsafe_allow_html=True)


# ─── Main Application ───────────────────────────────────────────────────────

def main():
    # Hero Header
    st.markdown("""
    <div class="hero-header">
        <h1>📄 Resume Analyzer AI</h1>
        <p>Upload your resume and get instant AI-powered feedback to land your dream job.</p>
    </div>
    """, unsafe_allow_html=True)

    # Check API key
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        st.warning(
            "⚠️ **Gemini API key not configured.** "
            "Please add your API key to the `.env` file:\n\n"
            "```\nGEMINI_API_KEY=your_actual_key_here\n```"
        )
        st.stop()

    # Upload Section
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown("""
        <div class="upload-area">
            <div class="upload-icon">☁️</div>
            <div class="upload-title">Upload Your Resume</div>
            <div class="upload-sub">Supports PDF files up to 10 MB</div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload PDF Resume",
            type=["pdf"],
            label_visibility="collapsed",
        )

    if uploaded_file is not None:
        # Extract text
        with st.spinner("📖 Extracting text from PDF…"):
            resume_text = extract_text_from_pdf(uploaded_file)

        if not resume_text:
            st.error("❌ Could not extract any text from the PDF. Please upload a text-based resume (not a scanned image).")
            st.stop()

        # Show extracted text in expander
        with st.expander("📝 View Extracted Resume Text", expanded=False):
            st.text(resume_text[:3000] + ("…" if len(resume_text) > 3000 else ""))

        # Analyze button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            analyze_clicked = st.button("🚀 Analyze My Resume", use_container_width=True)

        if analyze_clicked:
            with st.spinner("🤖 AI is analyzing your resume… This may take a moment."):
                try:
                    result = analyze_resume_with_gemini(resume_text)
                except requests.exceptions.HTTPError as e:
                    st.error(f"❌ API Error {e.response.status_code}: {e.response.text}")
                    st.stop()
                except json.JSONDecodeError:
                    st.error("❌ Failed to parse AI response. Please try again.")
                    st.stop()
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    st.stop()

            st.markdown("---")

            # ── Score ────────────────────────────────────────
            score = result.get("overall_score", 0)
            render_score(score)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Strengths & Weaknesses ───────────────────────
            col_s, col_w = st.columns(2)

            with col_s:
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <span class="icon">💪</span>
                        <h3>Strengths</h3>
                    </div>
                """, unsafe_allow_html=True)
                render_list(result.get("strengths", []), "strength-item", "✅")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_w:
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <span class="icon">⚠️</span>
                        <h3>Weaknesses</h3>
                    </div>
                """, unsafe_allow_html=True)
                render_list(result.get("weaknesses", []), "weakness-item", "🔴")
                st.markdown("</div>", unsafe_allow_html=True)

            # ── Missing Keywords & Suggestions ───────────────
            col_k, col_sg = st.columns(2)

            with col_k:
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <span class="icon">🔑</span>
                        <h3>Missing Keywords</h3>
                    </div>
                """, unsafe_allow_html=True)
                render_list(result.get("missing_keywords", []), "keyword-item", "🏷️")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_sg:
                st.markdown("""
                <div class="glass-card">
                    <div class="section-header">
                        <span class="icon">💡</span>
                        <h3>Suggestions to Improve</h3>
                    </div>
                """, unsafe_allow_html=True)
                render_list(result.get("suggestions", []), "suggest-item", "📌")
                st.markdown("</div>", unsafe_allow_html=True)

            # ── Best Matching Job Roles ──────────────────────
            st.markdown("""
            <div class="glass-card">
                <div class="section-header">
                    <span class="icon">🎯</span>
                    <h3>Best Matching Job Roles</h3>
                </div>
            """, unsafe_allow_html=True)
            render_pills(result.get("best_matching_job_roles", []))
            st.markdown("</div>", unsafe_allow_html=True)

            # ── Footer ──────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; color:#475569; font-size:0.85rem; padding-bottom:2rem;">
                Powered by <strong style="color:#a78bfa;">Google Gemini 2.5 Flash</strong> · 
                Built with <strong style="color:#ef4444;">♥</strong> using Streamlit
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
