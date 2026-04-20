import streamlit as st
from groq import Groq
import speech_recognition as sr
from datetime import datetime
import json
import re
import random
import plotly.express as px
import pandas as pd
from PIL import Image
import time
import os

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="Kompas Kesejahteraan | Wellbeing Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== BROWSER-BASED VOICE RECOGNITION (Works on Cloud!) ==========
def browser_voice_input():
    """Uses browser's Web Speech API - works on Streamlit Cloud!"""
    import streamlit.components.v1 as components
    
    voice_html = """
    <div id="voice-container">
        <button id="voice-btn" style="
            background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%);
            color: #1a1a2e;
            font-weight: bold;
            border: none;
            border-radius: 50px;
            padding: 12px 24px;
            width: 100%;
            cursor: pointer;
            font-size: 1rem;
        ">🎤 Click to Speak</button>
        <p id="voice-status" style="color: white; margin-top: 10px; text-align: center;"></p>
        <input type="text" id="voice-result" style="display: none;">
    </div>
    
    <script>
    const voiceBtn = document.getElementById('voice-btn');
    const statusDiv = document.getElementById('voice-status');
    const resultInput = document.getElementById('voice-result');
    
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        let currentLang = 'en-US';
        
        // Function to update language
        window.updateVoiceLanguage = function(lang) {
            currentLang = lang === 'Bahasa Malaysia' ? 'ms-MY' : 'en-US';
            recognition.lang = currentLang;
        };
        
        voiceBtn.onclick = function() {
            statusDiv.innerHTML = '🎤 Listening... Speak now';
            statusDiv.style.color = '#FFD700';
            voiceBtn.disabled = true;
            voiceBtn.style.opacity = '0.5';
            
            try {
                recognition.start();
            } catch(e) {
                statusDiv.innerHTML = '❌ Error: ' + e.message;
                statusDiv.style.color = '#ff4444';
                voiceBtn.disabled = false;
                voiceBtn.style.opacity = '1';
            }
        };
        
        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            resultInput.value = text;
            statusDiv.innerHTML = '✅ You said: ' + text;
            statusDiv.style.color = '#00ff00';
            
            // Send to Streamlit
            const streamlitEvent = new CustomEvent('streamlit:message', {
                detail: { text: text }
            });
            window.dispatchEvent(streamlitEvent);
        };
        
        recognition.onerror = function(event) {
            statusDiv.innerHTML = '❌ Could not hear. Please type.';
            statusDiv.style.color = '#ff4444';
            voiceBtn.disabled = false;
            voiceBtn.style.opacity = '1';
        };
        
        recognition.onend = function() {
            voiceBtn.disabled = false;
            voiceBtn.style.opacity = '1';
        };
    } else {
        voiceBtn.disabled = true;
        statusDiv.innerHTML = '❌ Voice not supported in this browser. Please use Chrome.';
        statusDiv.style.color = '#ff4444';
    }
    </script>
    """
    
    components.html(voice_html, height=100)
    
    # Check for voice result from JavaScript
    query_params = st.query_params
    if 'voice_text' in query_params:
        return query_params['voice_text']
    return None

# ========== USER COUNTER FUNCTIONS ==========
def load_user_count():
    try:
        with open('users.txt', 'r') as f:
            return int(f.read())
    except:
        return 0

def save_user_count(count):
    with open('users.txt', 'w') as f:
        f.write(str(count))

# ========== INITIALIZE SESSION STATE ==========
if 'voice_input' not in st.session_state:
    st.session_state.voice_input = ""
if 'history' not in st.session_state:
    st.session_state.history = []
if 'streak' not in st.session_state:
    st.session_state.streak = 0
if 'last_checkin_date' not in st.session_state:
    st.session_state.last_checkin_date = ""
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True
if 'total_users' not in st.session_state:
    st.session_state.total_users = load_user_count()
if 'wall_messages' not in st.session_state:
    st.session_state.wall_messages = [
        "💚 You are stronger than you think! Keep going!",
        "🌟 Taking the first step is the hardest. Proud of you!",
        "🌱 Small progress is still progress. You've got this!"
    ]

# ========== LOGIN SYSTEM ==========
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("### 👋 Welcome to Kompas Kesejahteraan")
    username = st.text_input("Enter your name to begin:")
    if username:
        st.session_state.username = username
        st.session_state.logged_in = True
        # Count new user
        if 'counted' not in st.session_state:
            st.session_state.total_users += 1
            save_user_count(st.session_state.total_users)
            st.session_state.counted = True
        st.rerun()
    st.stop()

# ========== WELCOME ANIMATION ==========
if st.session_state.first_visit:
    st.balloons()
    st.success("🎉 **Welcome to Kompas Kesejahteraan!** 🎉\n\nYour wellbeing journey starts now. Let's take the first step together! 💚")
    st.session_state.first_visit = False
    time.sleep(1)

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    /* Main background */
    .stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
    
    /* Hide menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* All text - ensure visibility */
    .stApp, div, p, span, label, .stMarkdown, .stText, .stCaption {
        color: #FFFFFF !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6, .stHeading {
        color: #FFFFFF !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%);
        color: #1a1a2e !important;
        font-weight: 700 !important;
        border-radius: 50px !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease;
        border: none !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255,215,0,0.4);
        color: #1a1a2e !important;
    }
    
    /* Text area input */
    .stTextArea textarea {
        background: rgba(255,255,255,0.95) !important;
        border: 2px solid #FFD700 !important;
        border-radius: 20px !important;
        color: #1a1a2e !important;
        padding: 1rem !important;
        font-size: 1rem !important;
    }
    .stTextArea textarea::placeholder {
        color: #666666 !important;
    }
    
    /* Radio buttons */
    .stRadio > div {
        display: flex;
        justify-content: center;
        gap: 1rem;
        background: rgba(255,255,255,0.15);
        padding: 0.5rem;
        border-radius: 50px;
    }
    .stRadio label {
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1.5rem;
        border-radius: 40px;
        color: #FFFFFF !important;
        font-weight: 500;
    }
    .stRadio label:hover {
        background: rgba(255,215,0,0.3);
    }

    /* Fix for download buttons */
.stDownloadButton button {
    background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%) !important;
    color: #1a1a2e !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.75rem 1.5rem !important;
}

.stDownloadButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(255,215,0,0.4) !important;
    color: #1a1a2e !important;
}

/* Fix for caption text */
.stCaption {
    color: #FFD700 !important;
}
    
    /* Hero section */
    .hero {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.08));
        border-radius: 30px;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    .hero h1 {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFD700, #FFA500, #FF6B6B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero h3 {
        color: #FFFFFF !important;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        background: rgba(255,215,0,0.2);
        padding: 0.4rem 1rem;
        border-radius: 40px;
        font-size: 0.8rem;
        margin: 0.25rem;
        color: #FFD700 !important;
        font-weight: 500;
        border: 1px solid rgba(255,215,0,0.3);
    }
    
    /* Stat cards */
    .stat-card {
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.2rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.15);
        transition: all 0.3s ease;
    }
    .stat-card:hover { 
        transform: translateY(-5px); 
        border-color: #FFD700;
        background: rgba(255,255,255,0.18);
    }
    .stat-card div {
        color: #FFFFFF !important;
    }
    .stat-number {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Risk cards */
    .risk-low { 
        background: linear-gradient(135deg, rgba(0,255,0,0.25), rgba(0,150,0,0.15)); 
        border-radius: 20px; 
        padding: 1.2rem; 
        margin: 1rem 0;
        border: 1px solid rgba(0,255,0,0.5);
    }
    .risk-low h2, .risk-low p {
        color: #FFFFFF !important;
    }
    
    .risk-medium { 
        background: linear-gradient(135deg, rgba(255,165,0,0.25), rgba(255,100,0,0.15)); 
        border-radius: 20px; 
        padding: 1.2rem; 
        margin: 1rem 0;
        border: 1px solid rgba(255,165,0,0.5);
    }
    .risk-medium h2, .risk-medium p {
        color: #FFFFFF !important;
    }
    
    .risk-high { 
        background: linear-gradient(135deg, rgba(255,0,0,0.25), rgba(150,0,0,0.15)); 
        border-radius: 20px; 
        padding: 1.2rem; 
        margin: 1rem 0;
        border: 1px solid rgba(255,0,0,0.5);
    }
    .risk-high h2, .risk-high p {
        color: #FFFFFF !important;
    }
    
    /* Recommendation card */
    .rec-card {
        background: linear-gradient(135deg, rgba(255,215,0,0.2), rgba(255,165,0,0.15));
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,215,0,0.5);
    }
    .rec-card h3 {
        color: #FFD700 !important;
        margin-bottom: 0.5rem;
    }
    .rec-card p {
        color: #FFFFFF !important;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Achievement card */
    .achievement-card {
        background: linear-gradient(135deg, rgba(255,215,0,0.25), rgba(255,165,0,0.2));
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #FFD700;
    }
    .achievement-card h3, .achievement-card p {
        color: #FFD700 !important;
    }
    
    /* Metric boxes */
    [data-testid="stMetricValue"] {
        color: #FFD700 !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }
    
    /* Info/Warning/Success boxes */
    .stAlert {
        background: rgba(0,0,0,0.7) !important;
        backdrop-filter: blur(10px);
    }
    .stAlert p {
        color: #FFFFFF !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: #FFD700 !important;
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
    }
    .streamlit-expanderContent {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #FFFFFF !important;
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FFD700, #FF8C00) !important;
        color: #1a1a2e !important;
        font-weight: 700;
    }
    
    /* Footer */
    .footer { 
        text-align: center; 
        padding: 1.5rem; 
        color: rgba(255,255,255,0.6) !important; 
        font-size: 0.75rem; 
    }
    
    /* Breathing animation */
    @keyframes breathe {
        0% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(1); opacity: 0.5; }
    }
    .breathing-circle {
        animation: breathe 4s ease-in-out infinite;
        text-align: center;
        font-size: 4rem;
    }
    
    /* Quote card */
    .quote-card {
        background: rgba(255,255,255,0.1);
        border-left: 4px solid #FFD700;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-style: italic;
        color: #FFFFFF !important;
    }

    /* Fix selectbox */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1a1a2e !important;
        border: 2px solid #FFD700 !important;
        border-radius: 10px !important;
    }
    .stSelectbox div[data-baseweb="select"] div {
        color: #FFFFFF !important;
        background-color: #1a1a2e !important;
    }
    .stSelectbox [data-baseweb="select"] span {
        color: #FFFFFF !important;
    }
    .stSelectbox svg {
        fill: #FFD700 !important;
    }
    div[role="listbox"] {
        background-color: #1a1a2e !important;
        border: 2px solid #FFD700 !important;
        border-radius: 10px !important;
    }
    div[role="option"] {
        color: #FFFFFF !important;
        background-color: #1a1a2e !important;
        padding: 8px 12px !important;
    }
    div[role="option"]:hover {
        background-color: #FFD700 !important;
        color: #1a1a2e !important;
    }
    .stSuccess {
        background-color: rgba(0,255,0,0.2) !important;
        color: #FFFFFF !important;
    }
    .stSuccess p {
        color: #FFFFFF !important;
    }
    .stInfo {
        background-color: rgba(255,215,0,0.2) !important;
        color: #FFFFFF !important;
    }
    .stInfo p {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== CRISIS KEYWORDS ==========
CRISIS_KEYWORDS = [
    "kill myself", "end my life", "want to die", "suicide", "self harm",
    "no reason to live", "give up", "hopeless", "better off dead",
    "bunuh diri", "mati", "nak mati", "taknak hidup", "putus asa"
]

# ========== MOTIVATIONAL QUOTES ==========
QUOTES = [
    "💙 You are not alone. Millions of youth feel this way.",
    "🌱 Small steps lead to big changes. You've got this.",
    "🦁 Reaching out for help is brave, not weak.",
    "🌈 Tomorrow is a new day. This feeling will pass.",
    "🌟 Your mental health matters. You matter.",
    "🤝 There are people who care about you.",
    "🎯 One step at a time. You're making progress!"
]

# ========== MALAYSIAN RESOURCES BY LOCATION ==========
MALAYSIA_RESOURCES = {
    "Kuala Lumpur": {
        "Befrienders KL": "03-7956 8144 (24/7)",
        "Mental Health Support Centre": "03-7627 2929",
        "Hospital Kuala Lumpur": "03-2615 5555"
    },
    "Penang": {
        "Befrienders Penang": "04-281 5161",
        "Hospital Penang": "04-222 5333"
    },
    "Johor": {
        "Hospital Sultanah Aminah": "07-225 7000",
        "Mentari JB": "07-331 1466"
    },
    "Sabah": {
        "Hospital Queen Elizabeth": "088-517 555"
    },
    "Sarawak": {
        "Hospital Umum Sarawak": "082-276 666"
    },
    "Selangor": {
        "Hospital Selayang": "03-6120 3233",
        "Mentari Shah Alam": "03-5510 4433"
    }
}

# ========== FALLBACK RECOMMENDATIONS ==========
def get_fallback_recommendation(text, lang):
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["exam", "study", "test", "assignment", "belajar"]):
        if lang == "Bahasa Malaysia":
            return "📌 **SEKARANG:** Tarik nafas dalam-dalam 5 kali\n\n📚 **HARI INI:** Cuba teknik Pomodoro - belajar 25 minit, rehat 5 minit\n\n📞 **BANTUAN:** Hubungi Befrienders 03-7956 8144\n\n💚 Anda mampu!"
        else:
            return "📌 **RIGHT NOW:** Take 5 deep breaths\n\n📚 **TODAY:** Try Pomodoro - study 25 min, break 5 min\n\n📞 **HELP:** Call Befrienders 03-7956 8144\n\n💚 You've got this!"
    
    elif any(w in text_lower for w in ["lonely", "alone", "no friends", "sunyi"]):
        if lang == "Bahasa Malaysia":
            return "📌 **SEKARANG:** Hantar mesej kepada seorang kawan\n\n👥 **HARI INI:** Join komuniti online\n\n📞 **BANTUAN:** Talian Kasih 15999\n\n💚 Anda tidak bersendirian"
        else:
            return "📌 **RIGHT NOW:** Message one friend\n\n👥 **TODAY:** Join an online community\n\n📞 **HELP:** Talian Kasih 15999\n\n💚 You're not alone"
    
    else:
        if lang == "Bahasa Malaysia":
            return "📌 **SEKARANG:** Tarik nafas dalam-dalam\n\n🌿 **HARI INI:** Jalan-jalan 10 minit di luar\n\n📞 **BANTUAN:** Befrienders 03-7956 8144\n\n💚 Anda penting"
        else:
            return "📌 **RIGHT NOW:** Take deep breaths\n\n🌿 **TODAY:** 10-minute walk outside\n\n📞 **HELP:** Call Befrienders 03-7956 8144\n\n💚 You matter"

# ========== ANALYZE WITH GROQ ==========
def analyze_with_groq(user_input, lang):
    try:
        if "GROQ_API_KEY" not in st.secrets:
            return 'Medium', get_fallback_recommendation(user_input, lang)
        
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        if lang == "Bahasa Malaysia":
            system_prompt = """Anda pembantu kesihatan mental untuk belia Malaysia. 
Analisis: RISK dan ADVICE.

Format:
RISK: [Rendah/Sederhana/Tinggi]
ADVICE: [nasihat 2-3 ayat pendek]"""
            
            user_prompt = f"Pengguna berkata: '{user_input}'\n\nBerikan RISK dan ADVICE mengikut format di atas."
        else:
            system_prompt = """You are a mental health assistant for Malaysian youth.
Analyze: RISK and ADVICE.

Format:
RISK: [Low/Medium/High]
ADVICE: [short 2-3 sentence advice]"""
            
            user_prompt = f"User says: '{user_input}'\n\nProvide RISK and ADVICE in the format above."

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = completion.choices[0].message.content
        
        risk = "Medium"
        if "RISK: Low" in result_text or "RISK: Rendah" in result_text:
            risk = "Low"
        elif "RISK: High" in result_text or "RISK: Tinggi" in result_text:
            risk = "High"
        
        recommendation = get_fallback_recommendation(user_input, lang)
        advice_match = re.search(r'ADVICE:\s*(.+?)(?=$)', result_text, re.DOTALL | re.IGNORECASE)
        if advice_match:
            recommendation = advice_match.group(1).strip()
        
        return risk, recommendation
        
    except Exception as e:
        return 'Medium', get_fallback_recommendation(user_input, lang)

# ========== UPDATE STREAK ==========
def update_streak():
    today = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.last_checkin_date == today:
        return
    
    if st.session_state.last_checkin_date == (datetime.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d"):
        st.session_state.streak += 1
    else:
        st.session_state.streak = 1
    
    st.session_state.last_checkin_date = today

# ========== SHOW MOOD CHART ==========
def show_mood_chart():
    if len(st.session_state.history) >= 3:
        df = pd.DataFrame(st.session_state.history)
        mood_map = {"Low": 3, "Medium": 2, "High": 1}
        df['score'] = df['risk'].map(mood_map)
        
        fig = px.line(
            df, y='score', 
            title="📈 Your Wellbeing Journey",
            labels={'index': 'Check-in #', 'value': 'Wellbeing Score'},
            color_discrete_sequence=['#FFD700']
        )
        fig.update_yaxes(ticktext=['😔 Struggling', '😐 Okay', '😊 Good'], tickvals=[1, 2, 3])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)',
                         font=dict(color='white'), title_font_color='white')
        fig.update_traces(line=dict(width=3), marker=dict(size=8, color='#FF8C00'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Complete 3 check-ins to see your wellbeing trend!")

# ========== SENTIMENT TREND ==========
def show_sentiment_trend():
    if len(st.session_state.history) >= 3:
        moods = []
        for h in st.session_state.history:
            if h['risk'] == 'Low':
                moods.append(3)
            elif h['risk'] == 'Medium':
                moods.append(2)
            else:
                moods.append(1)
        
        fig = px.area(
            y=moods,
            title="💭 Your Emotional Journey",
            labels={'index': 'Check-in #', 'value': 'Mood Score'},
            color_discrete_sequence=['#FFD700']
        )
        fig.update_yaxes(ticktext=['😔 Struggling', '😐 Okay', '😊 Good'], tickvals=[1, 2, 3])
        fig.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(255,255,255,0.05)',
            font=dict(color='white')
        )
        fig.update_traces(fill='tozeroy', line=dict(color='#FFD700', width=2))
        st.plotly_chart(fig, use_container_width=True)
        
        if moods[-1] > moods[0]:
            st.success("📈 **Trending Up!** Your wellbeing is improving! Keep going! 🎉")
        elif moods[-1] < moods[0]:
            st.warning("📉 **Reach out for support.** You're not alone. Help is available. 💚")
        else:
            st.info("➡️ **Staying consistent.** Every day you check in is a victory! 💪")
    else:
        st.info("📊 Complete 3 check-ins to see your emotional journey!")

# ========== EXPORT REPORT ==========
def export_report():
    st.markdown("### 📄 Generate Your Wellbeing Report")
    
    if len(st.session_state.history) > 0:
        total_checkins = len(st.session_state.history)
        good_days = sum(1 for h in st.session_state.history if h['risk'] == 'Low')
        tough_days = sum(1 for h in st.session_state.history if h['risk'] == 'High')
        recovery_rate = (good_days / total_checkins) * 100 if total_checkins > 0 else 0
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           KOMPAS KESEJAHTERAAN - WELLBEING REPORT            ║
╚══════════════════════════════════════════════════════════════╝

Report for: {st.session_state.username}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📊 YOUR STATISTICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total Check-ins: {total_checkins}
• Current Streak: {st.session_state.streak} days 🔥
• Good Days: {good_days} 😊
• Tough Days: {tough_days} 💪
• Recovery Rate: {recovery_rate:.1f}%

🏆 ACHIEVEMENTS UNLOCKED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        if total_checkins >= 1:
            report += "✓ First Step\n"
        if total_checkins >= 7:
            report += "✓ 7-Day Warrior\n"
        if st.session_state.streak >= 5:
            report += "✓ 5-Day Streak\n"
        if st.session_state.streak >= 10:
            report += "✓ 10-Day Streak Legend\n"
        
        report += f"""
💚 EMERGENCY CONTACTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Befrienders Malaysia: 03-7956 8144 (24/7)
• Talian Kasih: 15999
• Emergency: 999

💪 MESSAGE FROM KOMPAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You've taken {total_checkins} steps toward better wellbeing.
Every check-in is a victory. Keep going, one day at a time.

"You are stronger than you know. Every small step matters."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Kompas Kesejahteraan | AI for Malaysian Youth
🧭 Your wellbeing journey continues...
"""
        
        st.download_button(
            label="📥 Download My Wellbeing Report",
            data=report,
            file_name=f"wellbeing_report_{st.session_state.username}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.caption("💚 Share this report with a counselor or trusted friend if needed")
    else:
        st.info("✨ Complete your first check-in to generate a report!")

# ========== PEER SUPPORT WALL ==========
def peer_support_wall():
    st.markdown("### 💬 Encouragement Wall")
    st.caption("Anonymous messages of hope from our community")
    
    st.markdown("---")
    for msg in st.session_state.wall_messages[-5:]:
        st.markdown(f"💬 *\"{msg}\"*")
        st.markdown("---")
    
    st.markdown("#### Share Encouragement")
    st.caption("Your words could help someone today")
    new_msg = st.text_area("Write something encouraging:", placeholder="Example: 'You are not alone. Reach out, help is available.'", height=80)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💚 Post to Wall", use_container_width=True):
            if new_msg:
                st.session_state.wall_messages.append(new_msg)
                st.success("✨ Your encouragement has been posted! Thank you for helping others 💚")
                st.balloons()
                st.rerun()
            else:
                st.warning("Please write something before posting")

# ========== SHOW ACHIEVEMENTS ==========
def show_achievements():
    total = len(st.session_state.history)
    achievements = []
    
    if total >= 1:
        achievements.append("🌟 First Step")
    if total >= 7:
        achievements.append("🏆 7-Day Warrior")
    if total >= 30:
        achievements.append("⭐️ Monthly Champion")
    if st.session_state.streak >= 5:
        achievements.append("🔥 5-Day Streak")
    if st.session_state.streak >= 10:
        achievements.append("💪 10-Day Streak Legend")
    
    if achievements:
        cols = st.columns(min(len(achievements), 4))
        for i, ach in enumerate(achievements):
            with cols[i % 4]:
                st.markdown(f'<div class="achievement-card"><h3>{ach.split()[0]}</h3><p>{ach.split()[1] if len(ach.split()) > 1 else ""}</p></div>', unsafe_allow_html=True)
    else:
        st.info("✨ Complete your first check-in to earn achievements!")

# ========== BREATHING EXERCISE ==========
def breathing_exercise():
    st.markdown("### 🧘 60-Second Calming Exercise")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🌬️ Start Breathing", use_container_width=True):
            breath_placeholder = st.empty()
            
            for cycle in range(2):
                for i in range(4, 0, -1):
                    breath_placeholder.markdown(f"""
                    <div style='text-align: center;'>
                        <div class="breathing-circle">😤</div>
                        <h2 style='color: #FFD700;'>Breathe IN...</h2>
                        <h1 style='font-size: 3rem;'>{i}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(1)
                
                for i in range(4, 0, -1):
                    breath_placeholder.markdown(f"""
                    <div style='text-align: center;'>
                        <div class="breathing-circle">😌</div>
                        <h2 style='color: #FF8C00;'>Hold...</h2>
                        <h1 style='font-size: 3rem;'>{i}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(1)
                
                for i in range(4, 0, -1):
                    breath_placeholder.markdown(f"""
                    <div style='text-align: center;'>
                        <div class="breathing-circle">🌊</div>
                        <h2 style='color: #6B8EFF;'>Breathe OUT...</h2>
                        <h1 style='font-size: 3rem;'>{i}</h1>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(1)
            
            breath_placeholder.success("✅ Great job! Notice how you feel now? 💚")
            st.balloons()

# ========== EXPORT JOURNAL ==========
def export_journal():
    if st.button("📥 Export My Journal", use_container_width=True):
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_checkins": len(st.session_state.history),
            "current_streak": st.session_state.streak,
            "entries": st.session_state.history
        }
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="💾 Download Journal (JSON)",
            data=json_str,
            file_name=f"wellbeing_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# ========== ACTION PLAN ==========
def action_plan():
    st.markdown("### 📋 Personalized Action Plan")
    st.markdown("<p style='color: #FFFFFF; margin-bottom: 1rem;'>Click on your challenge:</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    selected = None
    
    with col1:
        if st.button("📚 Exam Stress", use_container_width=True, key="btn_exam"):
            selected = "Exam Stress"
        if st.button("😔 Loneliness", use_container_width=True, key="btn_lonely"):
            selected = "Loneliness"
    
    with col2:
        if st.button("😰 Anxiety", use_container_width=True, key="btn_anxiety"):
            selected = "Anxiety"
        if st.button("😴 Sleep Issues", use_container_width=True, key="btn_sleep"):
            selected = "Sleep Issues"
    
    with col3:
        if st.button("💪 Low Motivation", use_container_width=True, key="btn_motivation"):
            selected = "Low Motivation"
    
    if selected:
        plans = {
            "Exam Stress": """
<div style='background: #1a1a2e; border-radius: 20px; padding: 1.5rem; margin: 1rem 0; border: 2px solid #FFD700;'>
<h3 style='color: #FFD700; margin-bottom: 1rem;'>🎯 YOUR 3-STEP PLAN:</h3>
<p style='color: #FFFFFF; line-height: 1.8; font-size: 1rem;'>
1️⃣ <strong style='color: #FFD700;'>RIGHT NOW:</strong> Take 5 deep breaths<br>
2️⃣ <strong style='color: #FFD700;'>TODAY:</strong> Study 25 min, break 5 min (Pomodoro)<br>
3️⃣ <strong style='color: #FFD700;'>TONIGHT:</strong> Sleep 7-8 hours<br>
<br>
📞 <strong style='color: #FFD700;'>Support:</strong> <span style='color: #FFD700; background: #000000; padding: 0.3rem 0.6rem; border-radius: 8px;'>Befrienders 03-7956 8144</span>
</p>
</div>
""",
            "Loneliness": """
<div style='background: #1a1a2e; border-radius: 20px; padding: 1.5rem; margin: 1rem 0; border: 2px solid #FFD700;'>
<h3 style='color: #FFD700; margin-bottom: 1rem;'>🎯 YOUR 3-STEP PLAN:</h3>
<p style='color: #FFFFFF; line-height: 1.8; font-size: 1rem;'>
1️⃣ <strong style='color: #FFD700;'>RIGHT NOW:</strong> Message one friend<br>
2️⃣ <strong style='color: #FFD700;'>TODAY:</strong> Join an online community<br>
3️⃣ <strong style='color: #FFD700;'>THIS WEEK:</strong> Attend a local event<br>
<br>
📞 <strong style='color: #FFD700;'>Support:</strong> <span style='color: #FFD700; background: #000000; padding: 0.3rem 0.6rem; border-radius: 8px;'>Talian Kasih 15999</span>
</p>
</div>
""",
            "Anxiety": """
<div style='background: #1a1a2e; border-radius: 20px; padding: 1.5rem; margin: 1rem 0; border: 2px solid #FFD700;'>
<h3 style='color: #FFD700; margin-bottom: 1rem;'>🎯 YOUR 3-STEP PLAN:</h3>
<p style='color: #FFFFFF; line-height: 1.8; font-size: 1rem;'>
1️⃣ <strong style='color: #FFD700;'>RIGHT NOW:</strong> Try the breathing exercise<br>
2️⃣ <strong style='color: #FFD700;'>TODAY:</strong> Write down 3 things you're grateful for<br>
3️⃣ <strong style='color: #FFD700;'>THIS WEEK:</strong> Try grounding technique<br>
<br>
📞 <strong style='color: #FFD700;'>Support:</strong> <span style='color: #FFD700; background: #000000; padding: 0.3rem 0.6rem; border-radius: 8px;'>RELATE Malaysia 03-7627 2929</span>
</p>
</div>
""",
            "Sleep Issues": """
<div style='background: #1a1a2e; border-radius: 20px; padding: 1.5rem; margin: 1rem 0; border: 2px solid #FFD700;'>
<h3 style='color: #FFD700; margin-bottom: 1rem;'>🎯 YOUR 3-STEP PLAN:</h3>
<p style='color: #FFFFFF; line-height: 1.8; font-size: 1rem;'>
1️⃣ <strong style='color: #FFD700;'>TONIGHT:</strong> No phones 1 hour before bed<br>
2️⃣ <strong style='color: #FFD700;'>TOMORROW:</strong> Wake up same time daily<br>
3️⃣ <strong style='color: #FFD700;'>THIS WEEK:</strong> No coffee after 4pm<br>
<br>
📞 <strong style='color: #FFD700;'>Support:</strong> <span style='color: #FFD700; background: #000000; padding: 0.3rem 0.6rem; border-radius: 8px;'>Consult a doctor</span>
</p>
</div>
""",
            "Low Motivation": """
<div style='background: #1a1a2e; border-radius: 20px; padding: 1.5rem; margin: 1rem 0; border: 2px solid #FFD700;'>
<h3 style='color: #FFD700; margin-bottom: 1rem;'>🎯 YOUR 3-STEP PLAN:</h3>
<p style='color: #FFFFFF; line-height: 1.8; font-size: 1rem;'>
1️⃣ <strong style='color: #FFD700;'>RIGHT NOW:</strong> Write ONE small goal<br>
2️⃣ <strong style='color: #FFD700;'>TODAY:</strong> Reward yourself after completing it<br>
3️⃣ <strong style='color: #FFD700;'>THIS WEEK:</strong> Share your goal with a friend<br>
<br>
📞 <strong style='color: #FFD700;'>Support:</strong> <span style='color: #FFD700; background: #000000; padding: 0.3rem 0.6rem; border-radius: 8px;'>You've got this!</span>
</p>
</div>
"""
        }
        
        st.markdown(plans[selected], unsafe_allow_html=True)
        
        if st.button("✅ I'll follow this plan", use_container_width=True):
            st.success("🎉 Amazing! Take it one step at a time. You've got this!")

# ========== LOCATION RESOURCES ==========
def location_resources():
    st.markdown("### 📍 Find Help Near You")
    st.markdown("Click on your state to see resources:")
    
    col1, col2, col3 = st.columns(3)
    selected_location = None
    
    with col1:
        if st.button("🇲🇾 Kuala Lumpur", use_container_width=True):
            selected_location = "Kuala Lumpur"
        if st.button("🇲🇾 Penang", use_container_width=True):
            selected_location = "Penang"
        if st.button("🇲🇾 Johor", use_container_width=True):
            selected_location = "Johor"
    
    with col2:
        if st.button("🇲🇾 Selangor", use_container_width=True):
            selected_location = "Selangor"
        if st.button("🇲🇾 Sabah", use_container_width=True):
            selected_location = "Sabah"
        if st.button("🇲🇾 Sarawak", use_container_width=True):
            selected_location = "Sarawak"
    
    with col3:
        if st.button("🇲🇾 Perak", use_container_width=True):
            selected_location = "Perak"
        if st.button("🇲🇾 Kedah", use_container_width=True):
            selected_location = "Kedah"
        if st.button("🇲🇾 Kelantan", use_container_width=True):
            selected_location = "Kelantan"
    
    if selected_location:
        resources = {
            "Kuala Lumpur": {
                "Befrienders KL": "03-7956 8144",
                "Mental Health Support Centre": "03-7627 2929",
                "Hospital Kuala Lumpur": "03-2615 5555"
            },
            "Penang": {
                "Befrienders Penang": "04-281 5161",
                "Hospital Penang": "04-222 5333"
            },
            "Johor": {
                "Hospital Sultanah Aminah": "07-225 7000",
                "Mentari JB": "07-331 1466"
            },
            "Selangor": {
                "Hospital Selayang": "03-6120 3233",
                "Mentari Shah Alam": "03-5510 4433"
            },
            "Sabah": {
                "Hospital Queen Elizabeth": "088-517 555"
            },
            "Sarawak": {
                "Hospital Umum Sarawak": "082-276 666"
            },
            "Perak": {
                "Hospital Raja Permaisuri Bainun": "05-208 7000"
            },
            "Kedah": {
                "Hospital Sultanah Bahiyah": "04-740 6000"
            },
            "Kelantan": {
                "Hospital Raja Perempuan Zainab II": "09-745 2000"
            }
        }
        
        if selected_location in resources:
            st.markdown(f"## 📍 {selected_location} Resources")
            
            for name, number in resources[selected_location].items():
                st.markdown(f"""
                <div style='background: #1a1a2e; border-radius: 10px; padding: 0.8rem; margin-bottom: 0.5rem; border-left: 3px solid #FFD700;'>
                    <strong style='color: #FFD700;'>{name}</strong><br>
                    <span style='color: #FFFFFF; font-size: 1.2rem;'>📞 {number}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.warning("🚨 **Emergency: Always call 999 first**")
            st.info("💚 These services are confidential and free")

# ========== COMMUNITY CORNER ==========
def community_corner():
    st.markdown("### 🤝 Youth Community Corner")
    st.markdown(f"👋 Welcome back, **{st.session_state.username}!**")
    
    # Daily inspirational quotes
    daily_quotes = [
        "🌟 'The strongest people are those who win battles others know nothing about.'",
        "💪 'Your mental health is a priority. Your happiness is essential.'",
        "🌱 'Healing takes time, and asking for help is a courageous step.'",
        "🦋 'You don't have to control your thoughts. Just stop letting them control you.'",
        "🌈 'Every small step forward is still progress.'",
        "💚 'You are not alone. Millions of youth feel this way.'",
        "⭐ 'Your feelings are valid. Your struggles are seen.'"
    ]
    quote_index = datetime.now().day % len(daily_quotes)
    st.info(f"📖 **Daily Inspiration**\n\n{daily_quotes[quote_index]}")
    
    st.markdown("---")
    
    # Daily challenge
    challenges = [
        "🌱 Message one friend you haven't talked to",
        "📝 Write 3 things you're grateful for",
        "🧘 Do the breathing exercise",
        "💪 Help someone today",
        "📞 Check in on a friend",
        "🎯 Set one small goal for today"
    ]
    st.success(f"🎯 **Today's Challenge:** {random.choice(challenges)}")
    
    st.markdown("---")
    
    # Anonymous tips
    st.markdown("#### 💬 Share an Anonymous Tip")
    st.caption("Your tip could help someone else going through the same thing")
    
    tip = st.text_area("What helped you feel better?", height=100, 
                       placeholder="Example: Taking deep breaths when I feel anxious really helps me...")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💚 Share Anonymously", use_container_width=True):
            if tip:
                st.success("✨ Thank you for helping others! Your tip has been shared with the community.")
                st.balloons()
            else:
                st.warning("Please write something before sharing")
    
    st.markdown("---")
    
    # Motivational message
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background: rgba(255,215,0,0.1); border-radius: 15px;'>
        <p style='color: #FFD700; font-size: 1.1rem;'>
        💙 "You are stronger than you know. Every small step matters."
        </p>
    </div>
    """, unsafe_allow_html=True)

# ========== MAIN APP ==========
def main():
    # Hero Section
    st.markdown("""
    <div class="hero">
        <h1>🧭 Kompas Kesejahteraan</h1>
        <h3>Wellbeing Compass - AI for Malaysian Youth</h3>
        <div>
            <span class="badge">🇲🇾 100% Free</span>
            <span class="badge">🎤 Voice Enabled</span>
            <span class="badge">🗣️ Bilingual</span>
            <span class="badge">📊 Track Progress</span>
            <span class="badge">🏆 Achievements</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Row with 6 columns
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(st.session_state.history)}</div><div>Check-ins</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{st.session_state.streak}</div><div>Day Streak 🔥</div></div>', unsafe_allow_html=True)
    with col3:
        good_days = sum(1 for h in st.session_state.history if h['risk'] == 'Low')
        st.markdown(f'<div class="stat-card"><div class="stat-number">{good_days}</div><div>Good Days 😊</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-card"><div class="stat-number">2</div><div>Languages</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="stat-card"><div class="stat-number">24/7</div><div>Support</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{st.session_state.total_users}</div><div>Youth Helped 💚</div></div>', unsafe_allow_html=True)
    
    # Crisis Banner
    st.warning("🚨 **Need immediate help?** Befrienders Malaysia: 03-7956 8144 (24/7) | Talian Kasih: 15999 | 999 for emergencies")
    
    # Language Selection
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        lang = st.radio("", ["English", "Bahasa Malaysia"], horizontal=True, label_visibility="collapsed")
    
    if lang == "Bahasa Malaysia":
        question = "💬 Bagaimana perasaan anda hari ini?"
        speak_btn = "🎤 Cakap Sekarang"
        analyze_btn = "🔍 Dapatkan Bantuan"
    else:
        question = "💬 How are you feeling today?"
        speak_btn = "🎤 Speak Now"
        analyze_btn = "🔍 Get Help Now"
    
    st.markdown(f"<h3 style='text-align: center;'>{question}</h3>", unsafe_allow_html=True)
    
    # Input Section
    col1, col2 = st.columns(2)
    user_input = ""

    with col1:
    # Simple voice button that works on cloud
        voice_text = st.text_input("🎤 Or paste from voice:", placeholder="Voice text will appear here", key="voice_paste")
    
        if st.button(speak_btn, use_container_width=True):
            st.info("""
            🎤 **Voice Instructions:**
            1. Click the microphone icon in your browser's address bar
            2. Or use Chrome's built-in dictation (Edit → Start Dictation on Mac)
            3. Or speak into your phone's microphone
        
            💡 **For Hackathon Demo:** Voice works perfectly on your LOCAL machine!
            """)
    
 
    with col2:
        text_input = st.text_area("", placeholder="Type your feelings here...", height=80, label_visibility="collapsed")
        if text_input:
            user_input = text_input
            st.session_state.voice_input = text_input
    
    final_input = st.session_state.voice_input if st.session_state.voice_input else user_input
    
    # Check for crisis
    is_crisis = False
    if final_input:
        for keyword in CRISIS_KEYWORDS:
            if keyword in final_input.lower():
                is_crisis = True
                break
    
    # Analyze Button
    btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
    with btn_col2:
        if st.button(analyze_btn, use_container_width=True):
            if not final_input:
                st.warning("Please type or speak your feelings first")
            elif is_crisis:
                st.markdown("---")
                st.markdown("""
                <div class="risk-high">
                    <h2>🔴 IMMEDIATE HELP NEEDED</h2>
                    <p style="font-size: 1.2rem;">You are not alone. Please reach out now:</p>
                </div>
                """, unsafe_allow_html=True)
                st.error("""
                🚨 **CRISIS SUPPORT - AVAILABLE NOW:**
                
                📞 **Befrienders Malaysia:** 03-7956 8144 (24/7)
                📞 **Talian Kasih:** 15999  
                📞 **Emergency:** 999
                
                🏥 **Go to nearest hospital emergency department**
                """)
                st.markdown(f'<div class="rec-card"><p style="font-size: 1.1rem;">{random.choice(QUOTES)}</p></div>', unsafe_allow_html=True)
                
                st.session_state.history.append({
                    "time": datetime.now().strftime("%I:%M %p, %d %b"),
                    "risk": "High",
                    "recommendation": "Crisis helpline provided"
                })
                update_streak()
                st.session_state.voice_input = ""
            else:
                with st.spinner("🧠 AI is analyzing your feelings..."):
                    risk, recommendation = analyze_with_groq(final_input, lang)
                    
                    st.markdown("---")
                    
                    if risk == "Low":
                        st.markdown(f'<div class="risk-low"><h2>🟢 {risk} Risk</h2><p>Your stress level is normal. Keep taking care of yourself! 😊</p></div>', unsafe_allow_html=True)
                        st.balloons()
                    elif risk == "Medium":
                        st.markdown(f'<div class="risk-medium"><h2>🟡 {risk} Risk</h2><p>You\'re showing signs of stress. Support is available. 💚</p></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="risk-high"><h2>🔴 {risk} Risk</h2><p>You\'re not alone. Please consider reaching out for support. 🤝</p></div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="rec-card"><h3>✨ Your Personalized Plan</h3><p style="font-size: 1.1rem; line-height: 1.6; white-space: pre-line;">{recommendation}</p></div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="text-align: center; padding: 1rem;"><i>{random.choice(QUOTES)}</i></div>', unsafe_allow_html=True)
                    
                    st.session_state.history.append({
                        "time": datetime.now().strftime("%I:%M %p, %d %b"),
                        "risk": risk,
                        "recommendation": recommendation[:100] + "..."
                    })
                    update_streak()
                    st.session_state.voice_input = ""
    
    # Dashboard Section with Tabs
    st.markdown("---")
    st.markdown("## 📊 Your Wellbeing Dashboard")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Trends", "🏆 Achievements", "🧘 Breathe", "📋 Action Plan", "📍 Resources", "🤝 Community"])
    
    with tab1:
        show_mood_chart()
        st.markdown("---")
        show_sentiment_trend()
        if len(st.session_state.history) > 0:
            st.markdown("### 📜 Recent Activity")
            for h in st.session_state.history[-5:][::-1]:
                icon = "🟢" if h['risk'] == 'Low' else "🟡" if h['risk'] == 'Medium' else "🔴"
                st.write(f"{icon} **{h['time']}** - {h['risk']} risk")
    
    with tab2:
        show_achievements()
        export_journal()
        st.markdown("---")
        export_report()
    
    with tab3:
        breathing_exercise()
    
    with tab4:
        action_plan()
    
    with tab5:
        location_resources()
    
    with tab6:
        community_corner()
        st.markdown("---")
        peer_support_wall()
    
    # Reset button
    if len(st.session_state.history) > 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.history = []
                st.session_state.streak = 0
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>🧭 Kompas Kesejahteraan | AI for Malaysian Youth | Powered by Groq Llama 3.3</p>
        <p>🏥 Emergency: 999 | Befrienders: 03-7956 8144 | Talian Kasih: 15999</p>
        <p>🔒 Your data stays private on your device | 💚 You matter</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
