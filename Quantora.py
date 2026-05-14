import streamlit as st
import pandas as pd
import requests
import os
import smtplib
from email.message import EmailMessage
import plotly.graph_objects as go
from crewai import Agent, Task, Crew, LLM
from PIL import Image

# 1. PAGE CONFIGURATION (Must be the ABSOLUTE FIRST Streamlit command)
st.set_page_config(
    page_title="Quantora Pro",
    page_icon="Quantora.jpg",  # Sets your clean logo as the browser favicon
    layout="wide"
)

# 2. LOAD & DISPLAY BRAND ASSETS
try:
    # Synchronized to your renamed asset file
    logo = Image.open("Quantora.jpg")
    st.sidebar.image(logo, use_container_width=True)
except Exception:
    # Safe fallback wrapper so your app won't crash if git tracking has a delay
    st.sidebar.warning("🏹 Quantora Pro Asset Loading...")

# FinTech UI CSS Injection (Bento Box / SaaS Style)
st.markdown("""
    <style>
    /* Main App Background - Clean Slate */
    .stApp { background-color: #F4F7F9; }
    
    /* Card Styling (Bento Box) */
    div[data-testid="stMetricValue"] {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 24px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #E1E8ED;
        color: #0066FF !important;
        font-weight: 700;
    }

    /* Sidebar - Clean & Professional */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E1E8ED;
    }

    /* Gradient Title */
    .main-title {
        background: linear-gradient(90deg, #0066FF, #00D084);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Info Box Styling */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    </style>
    """, unsafe_allow_html=True)

# --- NOTIFICATION LOGIC ---
def send_telegram(msg, token, chat_id):
    if token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            params = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
            requests.get(url, params=params)
        except Exception as e:
            st.sidebar.error(f"Telegram failed: {e}")

# REPLACE YOUR OLD EMAIL FUNCTION WITH THIS ONE:
def send_email(msg_content, recipient):
    if recipient:
        try:
            # Safely pull your system email and app password from Streamlit Secrets
            sender_email = st.secrets.get("SYSTEM_EMAIL")
            sender_password = st.secrets.get("EMAIL_APP_PASSWORD")

            if not sender_email or not sender_password:
                st.sidebar.warning("⚠️ Email system configuration missing from Secrets.")
                return False

            msg = EmailMessage()
            msg.set_content(msg_content)
            msg['Subject'] = "🏹 Quantora Pro: Trade Signal Detected"
            msg['From'] = f"Quantora Alerts <{sender_email}>"
            msg['To'] = recipient

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)
            return True
        except Exception as e:
            st.sidebar.error(f"Email system offline: {e}")
            return False

# --- CONFIGURATION KEYS ---
# Safe fallback if you don't use streamlit secrets locally yet
ALPHA_VANTAGE_KEY = st.secrets.get("ALPHA_VANTAGE_KEY", "YOUR_ALPHA_VANTAGE_KEY")
os.environ["GROQ_API_KEY"] = st.secrets.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")

# --- UI LAYOUT ---
st.markdown('<h1 class="main-title">Quantora Pro</h1>', unsafe_allow_html=True)

# SaaS Control Center in Sidebar
with st.sidebar:
    st.markdown("### 🏹 Quantora Control Center")
    st.info("Configure your notification uplinks below to receive real-time trade signals.")
    
    # Hides technical credentials smoothly inside a dropdown panel
    with st.expander("🔔 Notification Settings", expanded=False):
        st.write("Enter your credentials to enable multi-channel alerts.")
        email_user = st.text_input("Personal Email", placeholder="email@example.com")
        
        st.divider()
        st.markdown("**Telegram Integration**")
        tg_token = st.text_input("Bot Token", type="password", help="Get this from @BotFather on Telegram")
        tg_id = st.text_input("Chat ID", help="Get this from @userinfobot on Telegram")
    
    st.divider()
    
    if st.button("System Health Check", use_container_width=True):
        st.success("Quantora Core: Operational")
        st.toast("All systems synchronized.")
        
    st.caption("Quantora Pro Engine v2.1 | © 2026")

# Main Interface Content Area
col_input, _ = st.columns([2, 1])
with col_input:
    symbol = st.text_input("Select Asset Ticker:", "AAPL").upper()

if st.button("RUN QUANT ANALYSIS", use_container_width=True):
    with st.spinner("Synchronizing with Market Nodes..."):
        try:
            # 1. Fetching Market Data
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}'
            data = requests.get(url).json()
            
            # Extract and form clean historical pricing dataframe
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index').astype(float)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index().tail(60) # Frame lookback window to last 60 periods

            # 2. Moving Average Intersection Formulas
            df['MA10'] = df['4. close'].rolling(window=10).mean()
            df['MA30'] = df['4. close'].rolling(window=30).mean()
            current_price = df['4. close'].iloc[-1]
            signal = "BUY" if df['MA10'].iloc[-1] > df['MA30'].iloc[-1] else "SELL"

            # 3. Clean Interactive Candlestick/Trend Vector Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['4. close'], name='Price Trace', line=dict(color='#0066FF', width=3)))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA10'], name='10D Fast MA', line=dict(color='#00D084', dash='dot')))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA30'], name='30D Slow MA', line=dict(color='#FF4B4B')))
            
            fig.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F2F6')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F2F6')
            st.plotly_chart(fig, use_container_width=True)

            # 4. Metric Windows (Bento Box grid)
            c1, c2, c3 = st.columns(3)
            c1.metric("Market Price", f"${current_price:,.2f}")
            c2.metric("Bot Signal", signal, delta=signal if signal == "BUY" else f"-{signal}")
            c3.metric("Status", "Active")

            # 5. Parallel Dispatch Notification Pipeline
            alert_msg = f"🏹 *Quantora Pro System Alert*\n\nAsset Matrix: *{symbol}*\nEngine Execution: *{signal}*\nSpot Value: *${current_price:,.2f}*"
            send_telegram(alert_msg, tg_token, tg_id)
            send_email(alert_msg, email_user)
            st.toast("Alert payloads routed successfully!")

            # 6. Deep Neural Market Analysis Core
            my_ai_brain = LLM(model="groq/llama-3.3-70b-versatile")
            
            analyst = Agent(
                role='Senior Crypto & Equity Strategist', 
                goal=f'Provide professional structural trend context for {symbol}', 
                backstory='You are a world-class system strategist with decades of quantitative fund experience. You process mathematical technical indicator values and map them into ultra-dense, executive briefs.',
                llm=my_ai_brain
            )
            
            task = Task(
                description=f"Analyze the structural {signal} breakout condition tracking {symbol} at current settlement pricing of ${current_price}. Formulate structural context around the 10-day crossing the 30-day structural line.", 
                expected_output="A concise, high-signal 2-sentence market intelligence brief.", 
                agent=analyst
            )
            
         report = Crew(agents=[analyst], tasks=[task]).kickoff()
            
            st.subheader("💡 Strategist Intelligence")
            
            # --- CLEAN SQUISHED TEXT RENDERING ---
            # Cast raw crew output to a string and clean formatting gaps
            raw_text = str(report.raw)
            cleaned_brief = raw_text.replace("._", ". ").replace("_", " ").replace(".T", ". T").replace("..", ".")
            
            # Display the polished text on your UI
            st.info(cleaned_brief)

        except Exception as e:
            st.error(f"Analysis Pipeline Interrupted: {e}")