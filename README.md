# **AI-Powered Market Navigator**

## **Project Overview**

AI-Powered Market Navigator is a comprehensive solution that leverages machine learning to predict stock market trends and provide real-time insights. The system fetches stock data from Yahoo Finance, analyzes trends using advanced ML models, and provides users with visual and actionable insights through an interactive Streamlit interface.

The project consists of multiple components including data fetching, training machine learning models, real-time predictions, and a frontend dashboard for visualization.

---

## **Features**

- **Real-Time Stock Trend Analysis**: Predict stock price movements based on historical data.
- **Sentiment Analysis**: Gather insights from Reddit discussions using the Reddit API (via PRAW).
- **Data Visualization**: Interactive plots using Plotly, Matplotlib, and Seaborn to visualize stock trends, predictions, and market insights.
- **AI-Driven Recommendations**: Predict future trends based on technical indicators like RSI, SMA, MACD, and Bollinger Bands.
- **Interactive Frontend**: Built using Streamlit for a smooth, user-friendly interface to display data and insights in real time.

---

## **Technology Stack**

### **Backend & Data Processing**
- **Programming Language**: Python
- **Machine Learning Framework**: TensorFlow / Keras, Scikit-Learn
- **Data Processing**: Pandas, NumPy
- **Data Fetching**: Reddit API (via PRAW), Yahoo Finance API
- **Data Visualization**: Matplotlib, Seaborn, Plotly

### **Frontend**
- **Web Framework**: Streamlit
- **Model Deployment**: Streamlit (for frontend and real-time predictions)

### **Version Control**
- **Version Control System**: Git
- **Repository Hosting**: GitHub / GitLab

### **Hosting & Deployment**
- **Deployment Platforms**: Streamlit Cloud, AWS, Google Cloud, Heroku (optional)
- **Containerization**: Docker (optional)

---

## **Installation & Setup**

1. **Clone the Repository**  
   Clone the repository to your local machine:

   ```bash
   git clone https://github.com/yourusername/your-ai-powered-market-navigator.git
   cd your-ai-powered-market-navigator
   
2. **Create a Virtual Environment (optional but recommended)**
  Create and activate a virtual environment to manage dependencies:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use venv\Scripts\activate
    
3. **Install Required Dependencies**
    Install all necessary Python libraries using pip:
   
    ```bash
    pip install -r requirements.txt
4. **API Keys **
   Set up API keys for Reddit (via PRAW) and Yahoo Finance to access data. You can store them in a .env file or environment variables.
   
6. **Run the Application**
   Start the Streamlit app for the frontend:

    ```bash
    streamlit run app.py

7. **Access the Application**
    After running the app, open the browser and navigate to http://localhost:8501 to interact with the app.
