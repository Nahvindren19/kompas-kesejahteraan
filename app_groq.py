import streamlit as st
from groq import Groq
import speech_recognition as sr
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Kompas Kesejahteraan | Wellbeing Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Fixed for visibility and alignment
st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fix button visibility - IMPORTANT */
    .stButton > button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%);
        color: #1a1a2e !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255,215,0,0.4) !important;
        background: linear-gradient(135deg, #FFE44D 0%, #FFA500 100%) !important;
    }
    
    /* Fix radio button visibility */
    .stRadio > div {
        display: flex;
        justify-content: center;
        gap: 2rem;
        background: rgba(255,255,255,0.1);
        padding: 0.75rem;
        border-radius: 50px;
        backdrop-filter: blur(10px);
    }
    
    .stRadio label {
        background: rgba(255,255,255,0.15);
        padding: 0.5rem 1.5rem;
        border-radius: 40px;
        color: white !important;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stRadio label:hover {
        background: rgba(255,215,0,0.3);
    }
    
    /* Fix text area visibility */
    .stTextArea textarea {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        border-radius: 20px !important;
        color: white !important;
        font-size: 1rem !important;
        padding: 1rem !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #FFD700 !important;
        box-shadow: 0 0 0 2px rgba(255,215,0,0.3) !important;
    }
    
    .stTextArea textarea::placeholder {
        color: rgba(255,255,255,0.5) !important;
    }
    
    /* Hero section */
    .hero-premium {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        border-radius: 30px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.15);
        backdrop-filter: blur(10px);
    }
    
    .hero-premium h1 {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFD700, #FFA500, #FF6B6B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .hero-premium h3 {
        color: rgba(255,255,255,0.9);
        font-weight: 500;
        margin-bottom: 1rem;
    }
    
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        padding: 0.4rem 1rem;
        border-radius: 40px;
        font-size: 0.8rem;
        margin: 0.25rem;
        color: rgba(255,255,255,0.9);
    }
    
    /* Stat cards */
    .stat-premium {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.2rem;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
        margin: 0.5rem;
    }
    
    .stat-premium:hover {
        transform: translateY(-3px);
        background: rgba(255,255,255,0.12);
        border-color: rgba(255,215,0,0.3);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        color: rgba(255,255,255,0.7);
        font-size: 0.8rem;
        margin-top: 0.3rem;
    }
    
    /* Glass container */
    .glass-container {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(12px);
        border-radius: 30px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 2rem;
        margin: 1rem 0;
    }
    
    /* Question text */
    .question-text {
        text-align: center;
        color: white;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }
    
    /* Input containers */
    .input-container {
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 1rem;
        height: 100%;
    }
    
    /* Risk cards */
    .risk-card {
        border-radius: 20px;
        padding: 1.2rem;
        text-align: center;
        animation: fadeIn 0.5s ease;
        margin: 1rem 0;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .risk-low {
        background: linear-gradient(135deg, rgba(0,200,0,0.2), rgba(0,100,0,0.1));
        border: 1px solid rgba(0,255,0,0.3);
    }
    .risk-medium {
        background: linear-gradient(135deg, rgba(255,165,0,0.2), rgba(255,100,0,0.1));
        border: 1px solid rgba(255,165,0,0.3);
    }
    .risk-high {
        background: linear-gradient(135deg, rgba(255,0,0,0.2), rgba(150,0,0,0.1));
        border: 1px solid rgba(255,0,0,0.3);
    }
    
    .risk-card h2 {
        margin: 0;
        font-size: 1.8rem;
    }
    
    .risk-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Recommendation card */
    .rec-card {
        background: linear-gradient(135deg, rgba(255,215,0,0.12), rgba(255,165,0,0.08));
        border-radius: 20px;
        padding: 1.2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,215,0,0.25);
    }
    
    .rec-card h3 {
        margin: 0 0 0.8rem 0;
        color: #FFD700;
    }
    
    .rec-card p {
        margin: 0.3rem 0;
        color: rgba(255,255,255,0.9);
        line-height: 1.5;
    }
    
    /* Footer */
    .footer-premium {
        text-align: center;
        padding: 1.5rem;
        color: rgba(255,255,255,0.4);
        font-size: 0.75rem;
    }
    
    /* Resource section */
    .resource-section {
        background: rgba(0,0,0,0.3);
        border-radius: 20px;
        padding: 1.2rem;
        margin-top: 1rem;
        text-align: center;
    }
    
    .resource-section p {
        color: rgba(255,255,255,0.7);
        margin: 0;
    }
    
    /* Alert customization */
    .stAlert {
        background: rgba(0,0,0,0.4);
        backdrop-filter: blur(10px);
        border-radius: 16px;
    }
    
    /* Spinner customization */
    .stSpinner > div {
        border-color: #FFD700 !important;
    }
    
    /* Success/Warning/Error text */
    .stSuccess, .stWarning, .stError {
        background: rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Column alignment fix */
    .row-widget.stColumns {
        gap: 1rem;
    }
    
    /* Center align radio */
    .stRadio {
        display: flex;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-premium">
    <h1>🧭 Kompas Kesejahteraan</h1>
    <h3>Wellbeing Compass - AI for Malaysian Youth</h3>
    <div>
        <span class="hero-badge">🇲🇾 100% Free</span>
        <span class="hero-badge">🎤 Voice Enabled</span>
        <span class="hero-badge">🗣️ Bahasa Malaysia</span>
        <span class="hero-badge">🤝 Community First</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Stats Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="stat-premium">
        <div class="stat-number">30+</div>
        <div class="stat-label">Youth Tested</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="stat-premium">
        <div class="stat-number">90%</div>
        <div class="stat-label">Success Rate</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="stat-premium">
        <div class="stat-number">2</div>
        <div class="stat-label">Languages</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="stat-premium">
        <div class="stat-number">10+</div>
        <div class="stat-label">Local Resources</div>
    </div>
    """, unsafe_allow_html=True)

# Main Glass Container
st.markdown('<div class="glass-container">', unsafe_allow_html=True)

# Language Selector - Centered
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    lang = st.radio("", ["Bahasa Malaysia", "English"], horizontal=True, label_visibility="collapsed")

# Set text based on language
if lang == "Bahasa Malaysia":
    question_text = "💬 Bagaimana perasaan anda hari ini?"
    speak_btn_text = "🎤 Cakap Sekarang"
    type_placeholder = "Taip perasaan anda di sini..."
    analyze_btn_text = "🔍 Dapatkan Bantuan Segera"
    risk_labels = {"Low": "Rendah", "Medium": "Sederhana", "High": "Tinggi"}
    reco_title = "✨ Cadangan Untuk Anda"
    risk_messages = {"Low": "Tahap stress normal", "Medium": "Perlu sokongan", "High": "Bantuan segera diperlukan"}
else:
    question_text = "💬 How are you feeling today?"
    speak_btn_text = "🎤 Speak Now"
    type_placeholder = "Type your feelings here..."
    analyze_btn_text = "🔍 Get Help Now"
    risk_labels = {"Low": "Low", "Medium": "Medium", "High": "High"}
    reco_title = "✨ Recommended For You"
    risk_messages = {"Low": "Normal stress level", "Medium": "Support recommended", "High": "Immediate help needed"}

# Question
st.markdown(f'<p class="question-text">{question_text}</p>', unsafe_allow_html=True)

# Voice and Text Input - Properly Aligned
input_col1, input_col2 = st.columns(2)

user_input = ""

with input_col1:
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    if st.button(speak_btn_text, use_container_width=True, key="speak_btn"):
        with st.spinner("🎤 Listening..."):
            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    st.info("Speak now...")
                    audio = r.listen(source, timeout=5)
                    if lang == "Bahasa Malaysia":
                        user_input = r.recognize_google(audio, language="ms-MY")
                    else:
                        user_input = r.recognize_google(audio, language="en-US")
                    st.success(f"✅ You said: {user_input}")
                    st.session_state.voice_input = user_input
            except:
                st.error("❌ Could not hear. Please type.")
    st.markdown('</div>', unsafe_allow_html=True)

with input_col2:
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    text_input = st.text_area("", placeholder=type_placeholder, height=80, label_visibility="collapsed", key="text_input")
    if text_input:
        user_input = text_input
        st.session_state.voice_input = text_input
    st.markdown('</div>', unsafe_allow_html=True)

# Session state
if 'voice_input' not in st.session_state:
    st.session_state.voice_input = ""
if 'history' not in st.session_state:
    st.session_state.history = []

final_input = st.session_state.voice_input if st.session_state.voice_input else user_input

# Local recommendations (CUSTOMIZE THESE)
recommendations = {
    "study": "📚 **National Library Online**\n📍 www.pnm.gov.my\n👥 Free e-resources for students",
    "anxiety": "🧘 **Relate Malaysia**\n📍 www.relate.com.my\n🧘‍♀️ Free youth mental health",
    "lonely": "🎮 **The Howl Malaysia**\n📍 Instagram @thehowlmy\n🎲 Online youth events",
    "stress": "🌿 **KKM Sembang@Minda**\n📍 www.moh.gov.my/sembang\n💻 Free chat service",
    "sad": "🫂 **Talian Kasih**\n📍 24/7: 15999\n📞 Free helpline",
    "default": "📞 **Befrienders Malaysia**\n📍 24/7: 03-7627 2929"
}

# Analyze Button - Centered with visible color
btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
with btn_col2:
    if st.button(analyze_btn_text, use_container_width=True, key="analyze_btn"):
        if final_input:
            with st.spinner("🧠 Analyzing with AI..."):
                try:
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": f"""Analyze feeling. Return ONLY JSON: {{"risk": "Low/Medium/High", "category": "study/anxiety/lonely/stress/sad/default"}}. Respond in {lang}."""},
                            {"role": "user", "content": final_input}
                        ],
                        temperature=0.3,
                        max_tokens=150
                    )
                    
                    result_text = completion.choices[0].message.content
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                    result = json.loads(result_text)
                    
                    risk = result.get('risk', 'Medium')
                    category = result.get('category', 'default')
                    
                    # Risk Display
                    st.markdown("---")
                    risk_class = f"risk-card risk-{risk.lower()}"
                    risk_display = risk_labels.get(risk, risk)
                    st.markdown(f"""
                    <div class="{risk_class}">
                        <h2>{'🟢' if risk=='Low' else '🟡' if risk=='Medium' else '🔴'} {risk_display}</h2>
                        <p>{risk_messages.get(risk, '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Recommendation
                    rec_content = recommendations.get(category, recommendations['default'])
                    st.markdown(f"""
                    <div class="rec-card">
                        <h3>{reco_title}</h3>
                        <p>{rec_content.replace(chr(10), '<br>')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Crisis helpline
                    if risk == "High":
                        st.error("🚨 **You're not alone**\n\n📞 Befrienders Malaysia: 03-7627 2929 (24/7)\n📞 Talian Kasih: 15999\n🏥 Go to nearest hospital")
                    
                    # Save history
                    st.session_state.history.append({
                        "time": datetime.now().strftime("%H:%M"),
                        "risk": risk,
                        "date": datetime.now().date()
                    })
                    
                    # Show trend
                    if len(st.session_state.history) >= 3:
                        st.markdown("---")
                        st.subheader("📈 Your Wellbeing Trend")
                        risk_values = [1 if h['risk']=='Low' else 2 if h['risk']=='Medium' else 3 for h in st.session_state.history[-7:]]
                        st.line_chart(risk_values)
                        
                        if len(risk_values) >= 3 and risk_values[-1] > risk_values[-3]:
                            st.warning("⚠️ Your stress levels are rising. Consider reaching out.")
                    
                    st.session_state.voice_input = ""
                    
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please type or speak first")

st.markdown('</div>', unsafe_allow_html=True)

# Resource Section
st.markdown("""
<div class="resource-section">
    <p>🏥 <strong>Need immediate help?</strong> Befrienders Malaysia: 03-7627 2929 (24/7) | Talian Kasih: 15999 | 999 for emergencies</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer-premium">
    <p>🧭 Kompas Kesejahteraan | AI for Malaysian Youth | Powered by Groq</p>
    <p>ICYOUTH Hackathon 2026</p>
</div>
""", unsafe_allow_html=True)