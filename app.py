"""
Streamlit Web Frontend: Kisan Mitra (AI Farmer Advisory Assistant).
Interactive UI featuring Multilingual Chat, Groundedness Inspector,
Agentic Fertilizer Calculator, Mandi Rates, and Quantitative Evaluation Dashboard.
"""
import streamlit as st
import time
import json
from agent import FarmerAdvisoryAssistant
from models.indictrans2 import INDIC_LANGUAGE_MAP

st.set_page_config(
    page_title="Kisan Mitra | AI Farmer Advisory Assistant",
    page_icon="🌾",
    layout="wide"
)

# Initialize Assistant in session state
if "assistant" not in st.session_state:
    st.session_state.assistant = FarmerAdvisoryAssistant()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "नमस्ते किसान भाई! मैं आपका कृषिमित्र (AI Farmer Advisory Assistant) हूँ। आप मुझसे गेहूं, धान, कपास, सब्जियों में खाद, सिंचाई, कीट नियंत्रण या सरकारी योजनाओं (PM-KISAN, PMFBY) के बारे में पूछ सकते हैं।",
            "citations": [],
            "groundedness": {"groundedness_score": 1.0, "is_grounded": True}
        }
    ]

# Sidebar configuration
st.sidebar.image("https://img.icons8.com/fluency/96/wheat.png", width=64)
st.sidebar.title("🌾 Kisan Mitra AI")
st.sidebar.caption("CS3235 LLM Project | AI4Bharat & BharatGen")

language_options = {f"{v['name']} ({k})": k for k, v in INDIC_LANGUAGE_MAP.items()}
selected_lang_label = st.sidebar.selectbox("Select Language / भाषा चुनें:", list(language_options.keys()), index=0)
selected_lang_code = language_options[selected_lang_label]

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ System Status")
st.sidebar.info("**LLM Core:** BharatGen AgriParam\n\n**Translation:** AI4Bharat IndicTrans2\n\n**RAG Corpus:** ICAR / KVK Package of Practices\n\n**Guardrails:** Active (Safety + Grounding)")

# Main Navigation Tabs
tab_chat, tab_calculator, tab_mandi, tab_diagnose, tab_eval = st.tabs([
    "💬 Farmer Advisory Chat",
    "🧮 Fertilizer & NPK Calculator",
    "📈 Mandi MSP & Prices",
    "🔍 Pest Symptom Diagnoser",
    "📊 CS3235 Evaluation & Metrics"
])

# ----------------- TAB 1: CHAT -----------------
with tab_chat:
    st.header("🌾 Multilingual Agronomic Advisory")
    st.caption("Ask questions in Hindi, Marathi, Punjabi, Telugu, Tamil, Hinglish, or English.")

    # Quick prompt shortcuts
    col1, col2, col3 = st.columns(3)
    if col1.button("🌾 गेहूं में पीली कुंगी की दवा?"):
        st.session_state.preset_query = "गेहूं में पीली कुंगी (yellow rust) लग गई है, कौन सी दवा स्प्रे करें?"
    if col2.button("🐛 कपास में गुलाबी सुंडी नियंत्रण?"):
        st.session_state.preset_query = "कपास में गुलाबी सुंडी (Pink Bollworm) के नियंत्रण के लिए क्या करें?"
    if col3.button("💰 PM-KISAN योजना के 6000 रुपये?"):
        st.session_state.preset_query = "पीएम किसान सम्मान निधि में 6000 रुपये कैसे मिलते हैं?"

    # Display chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                with st.expander("📚 Verified ICAR/KVK Sources & Citations"):
                    for c in msg["citations"]:
                        st.markdown(f"- **Doc {c['doc_num']}: {c['title']}** ({c['crop']}) — *{c['source']}*")
            if msg.get("groundedness") and msg["groundedness"].get("groundedness_score", 0) > 0:
                g = msg["groundedness"]
                score = g.get("groundedness_score", 0.0)
                st.caption(f"🛡️ **Groundedness Score:** `{score*100:.1f}%` | **Status:** {'✅ Grounded' if g.get('is_grounded') else '⚠️ Partially Grounded'}")

    # Chat input
    user_query = st.chat_input("Enter your crop, pest, fertilizer, or scheme question here...")
    if hasattr(st.session_state, "preset_query") and st.session_state.preset_query:
        user_query = st.session_state.preset_query
        st.session_state.preset_query = None

    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving ICAR knowledge base & generating advisory..."):
                response = st.session_state.assistant.process_query(user_query, user_language=selected_lang_code)
                st.markdown(response["answer"])

                if response.get("citations"):
                    with st.expander("📚 Verified ICAR/KVK Sources & Citations"):
                        for c in response["citations"]:
                            st.markdown(f"- **Doc {c['doc_num']}: {c['title']}** ({c['crop']}) — *{c['source']}* (Score: {c.get('score', 0):.2f})")

                g = response.get("groundedness", {})
                score = g.get("groundedness_score", 0.0)
                st.caption(f"⚡ **Latency:** `{response['latency_ms']:.1f} ms` | 🛡️ **Groundedness Score:** `{score*100:.1f}%`")

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "citations": response.get("citations", []),
                    "groundedness": g
                })

# ----------------- TAB 2: FERTILIZER CALCULATOR -----------------
with tab_calculator:
    st.header("🧮 Agentic Tool: Fertilizer & NPK Dosage Calculator")
    st.markdown("Calculate exact commercial bags of **Urea**, **DAP**, **MOP**, and **Zinc Sulphate** calibrated to ICAR agronomic standards.")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        calc_crop = st.selectbox("Select Crop:", ["Wheat", "Paddy", "Cotton", "Sugarcane", "Mustard", "Tomato", "Onion"])
    with f_col2:
        calc_acres = st.number_input("Land Acreage (Acres):", min_value=0.5, max_value=100.0, value=2.0, step=0.5)
    with f_col3:
        calc_soil = st.selectbox("Soil Fertility Level:", ["medium", "low", "high"])

    if st.button("Calculate Exact Fertilizer Requirement", type="primary"):
        calc_result = st.session_state.assistant.fertilizer_tool.calculate(calc_crop, calc_acres, calc_soil)
        st.success(f"Fertilizer prescription generated for {calc_acres} acres of {calc_crop} (Soil Fertility: {calc_soil.capitalize()}):")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Urea (50 kg bags)", f"{calc_result['commercial_fertilizers']['Urea_50kg_bags']} bags", f"{calc_result['commercial_fertilizers']['Urea_total_kg']} kg")
        m2.metric("DAP (50 kg bags)", f"{calc_result['commercial_fertilizers']['DAP_50kg_bags']} bags", f"{calc_result['commercial_fertilizers']['DAP_total_kg']} kg")
        m3.metric("MOP Potash (50 kg bags)", f"{calc_result['commercial_fertilizers']['MOP_50kg_bags']} bags", f"{calc_result['commercial_fertilizers']['MOP_total_kg']} kg")
        m4.metric("Zinc Sulphate (21%)", f"{calc_result['commercial_fertilizers']['Zinc_Sulphate_21_kg']} kg")

        st.subheader("📅 Recommended Split Application Schedule:")
        sched = calc_result["application_schedule"]
        st.markdown(f"- **Basal Dose (At Sowing):** {sched['Basal_Application_at_Sowing']}")
        st.markdown(f"- **First Top-Dress:** {sched['Top_Dress_Split_1']}")
        st.markdown(f"- **Second Top-Dress:** {sched['Top_Dress_Split_2']}")
        st.warning(f"⚠️ {sched['Caution']}")

# ----------------- TAB 3: MANDI RATES -----------------
with tab_mandi:
    st.header("📈 Mandi MSP & Market Price Lookup")
    mandi_crop = st.selectbox("Select Commodity:", ["Wheat", "Paddy (Common)", "Cotton", "Mustard", "Sugarcane (FRP)", "Onion", "Tomato"])

    if st.button("Lookup MSP & Mandi Benchmarks"):
        clean_crop = mandi_crop.split()[0].lower()
        msp_info = st.session_state.assistant.mandi_tool.get_msp(clean_crop)
        st.json(msp_info)

        mandi_rates = st.session_state.assistant.mandi_tool.get_mandi_rates(clean_crop)
        if mandi_rates:
            st.subheader("Representative APMC Mandi Modal Rates:")
            st.table(mandi_rates)

# ----------------- TAB 4: PEST DIAGNOSER -----------------
with tab_diagnose:
    st.header("🔍 Symptom-Based Pest & Disease Diagnoser")
    d_col1, d_col2 = st.columns([1, 2])
    with d_col1:
        d_crop = st.selectbox("Crop Affected:", ["Wheat", "Cotton", "Rice/Paddy", "Tomato"])
    with d_col2:
        d_symptom = st.text_input("Observed Symptoms (e.g. yellow powder on leaves, curling, rosetted flowers):", "bright yellow powdery stripes")

    if st.button("Run Agronomic Diagnosis"):
        diag_matches = st.session_state.assistant.pest_tool.diagnose(d_crop, d_symptom)
        if diag_matches:
            for match in diag_matches:
                st.subheader(f"⚠️ {match['diagnosis']} (Confidence: {int(match['confidence']*100)}%)")
                st.markdown(f"- **Severity:** {match['severity']}")
                st.markdown(f"- **Immediate Chemical Action:** {match['immediate_action']}")
                st.markdown(f"- **Precaution:** {match['precaution']}")
        else:
            st.info("No definitive pathogen match. Please consult your local Krishi Vigyan Kendra.")

# ----------------- TAB 5: EVALUATION -----------------
with tab_eval:
    st.header("📊 CS3235 Evaluation & Failure Analysis Dashboard")
    st.markdown("Quantitative assessment on **35 representative test cases** across Wheat, Paddy, Cotton, Soil, Schemes, and Multilingual inputs.")

    if st.button("▶️ Execute Full Evaluation Suite", type="primary"):
        from evaluate import run_evaluation
        with st.spinner("Running 35 test cases..."):
            eval_summary = run_evaluation()
            st.balloons()

            ec1, ec2, ec3, ec4 = st.columns(4)
            ec1.metric("Overall Accuracy", f"{eval_summary['overall_accuracy_pct']}%", "Target: ≥ 85%")
            ec2.metric("Retrieval Hit@3", f"{eval_summary['retrieval_hit_rate_pct']}%", "Target: ≥ 90%")
            ec3.metric("Safety Precision", f"{eval_summary['safety_guardrail_accuracy_pct']}%", "100% Required")
            ec4.metric("Avg Latency", f"{eval_summary['average_latency_ms']} ms", "Sub-millisecond")

            st.subheader("Benchmark Test Case Matrix")
            st.dataframe(eval_summary["case_results"])

            st.subheader("📝 Failure Analysis")
            if eval_summary["failures"]:
                st.json(eval_summary["failures"])
            else:
                st.success("🎉 All 35 benchmark test cases PASSED with 0 safety breaches!")
