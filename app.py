import streamlit as st
import requests
from streamlit_lottie import st_lottie

# Set page configuration
st.set_page_config(page_title="📈 Stock Trend App", layout="wide", page_icon="📊")

# Load Lottie animation
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load Lottie animation for the homepage
lottie_chart = load_lottie_url("https://assets1.lottiefiles.com/packages/lf20_ydo1amjm.json")

# Custom CSS for styling
st.markdown("""
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: 'Arial', sans-serif;
        }

        h1 {
            font-size: 3.5rem;
            color: #00ccff;
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }

        h2 {
            color: #00ccff;
            font-size: 2rem;
            text-align: center;
            margin-top: 1.5rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }

        .card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 2rem;
            margin: 2rem auto;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            max-width: 800px;
        }

        .footer-tip {
            text-align: center;
            font-size: 1.2rem;
            margin-top: 2rem;
            font-style: italic;
            color: #ffcc00;
        }

        .lottie-container {
            display: flex;
            justify-content: center;
            margin-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1>🏠 Welcome to the <span style='color:#00ccff;'>AI Stock Market Trend Analyzer</span></h1>", unsafe_allow_html=True)

# Centered Lottie Animation
st.markdown('<div class="lottie-container">', unsafe_allow_html=True)
st_lottie(lottie_chart, height=300, key="home-lottie")
st.markdown('</div>', unsafe_allow_html=True)

# What You Can Do Here Section
st.markdown("""
<div class="card">
    <h2>🌟 What You Can Do Here</h2>
    <ul>
        <li>📈 Get <b>AI-driven stock trend forecasts</b> using deep learning (LSTM)</li>
        <li>💬 Analyze <b>sentiments</b> from Reddit and news sources in real time</li>
        <li>📊 Explore interactive <b>financial visualizations</b> with Plotly</li>
        <li>🔍 Perform custom <b>stock ticker analysis</b> with insightful reasoning</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# How It Works Section
st.markdown("""
<div class="card">
    <h2>🚀 How It Works</h2>
    <ol>
        <li>Select a stock from the sidebar menu</li>
        <li>View AI-generated trend predictions and investment suggestions</li>
        <li>Understand market moods with sentiment breakdowns</li>
        <li>Use interactive charts to explore stock price patterns</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Tech Behind the Scenes Section
st.markdown("""
<div class="card">
    <h2>🧠 Tech Behind the Scenes</h2>
    <p>This app is powered by cutting-edge technologies:</p>
    <ul>
        <li>🧪 <b>Python</b>, <b>TensorFlow</b>, <b>Streamlit</b></li>
        <li>📰 Data from <b>Yahoo Finance</b>, <b>Reddit API</b>, and <b>News APIs</b></li>
        <li>🧠 AI Engine: <b>LSTM-based neural network</b></li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Footer Tip
st.markdown("""
<div class="footer-tip">
    📌 <b>Pro Tip:</b> Head to the<span style="color:#00ccff;">Dashboard</span> tab for real-time trend predictions and investment insights!
</div>
""", unsafe_allow_html=True)

# Floating Action Button (For fun)
st.markdown("""
    <div class="fab" style="position: fixed; bottom: 30px; right: 30px; background-color: #ff4b5c; color: white; padding: 15px; border-radius: 50%; font-size: 2rem; cursor: pointer; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); transition: transform 0.3s;">
        🔮
    </div>
""", unsafe_allow_html=True)

# Optional: Add functionality to the floating action button
if st.button("Click me for a surprise!"):
    st.balloons()  # This will show balloons when the button is clicked

# End of the Streamlit app