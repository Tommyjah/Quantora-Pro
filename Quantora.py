import streamlit as st
import pandas as pd
import requests
import os
from crewai import Agent, Task, Crew, LLM

# --- CONFIGURATION ---
st.set_page_config(page_title="Quantora AI", page_icon="📈", layout="wide")

# Secret Keys (In a real app, we use 'st.secrets', but for now we'll use these)
ALPHA_VANTAGE_KEY = 'YOUR_ALPHA_VANTAGE_KEY'
os.environ["GROQ_API_KEY"] = "************************************"

# --- APP UI ---
st.title("🏹 Quantora")
st.markdown("### *AI-Powered Quantitative Stock Signals*")
st.divider()

symbol = st.text_input("Enter Ticker Symbol:", "AAPL").upper()

if st.button("Generate Signal Report"):
    with st.spinner(f"Quantora is analyzing {symbol}..."):
        try:
            # 1. Fetch Data
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}'
            response = requests.get(url)
            data = response.json()
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index').astype(float)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # 2. Calculate Math
            df['MA10'] = df['4. close'].rolling(window=10).mean()
            df['MA30'] = df['4. close'].rolling(window=30).mean()
            current_price = df['4. close'].iloc[-1]
            signal = "BUY" if df['MA10'].iloc[-1] > df['MA30'].iloc[-1] else "SELL"

            # 3. AI Analysis
            my_ai_brain = LLM(model="groq/llama-3.3-70b-versatile", api_key=os.environ["GROQ_API_KEY"])

            analyst = Agent(
                role='Senior Quant Researcher',
                goal=f'Explain why {symbol} has a {signal} signal.',
                backstory='You provide elite institutional-grade analysis.',
                llm=my_ai_brain,
                allow_delegation=False
            )

            job = Task(
                description=f"Price: ${current_price}. Signal: {signal}. Explain in 2 sentences for a premium subscriber.",
                expected_output="A professional 2-sentence summary.",
                agent=analyst
            )

            report = Crew(agents=[analyst], tasks=[job]).kickoff()

            # 4. Display Results
            col1, col2 = st.columns(2)
            col1.metric("Current Price", f"${current_price}")
            col2.metric("Signal", signal)

            st.success("**Quantora Intelligence Report:**")
            st.write(report.raw)

        except Exception as e:
            st.error(f"Quantora encountered an error: {e}")
