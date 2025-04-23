import streamlit as st
import yfinance as yf
from demo1 import get_stock_data, preprocess_data, RealTimeData, generate_intelligent_reasoning
from tensorflow.keras.models import load_model
import pandas as pd
import numpy as np

# Load the pre-trained LSTM model
model = load_model("model3.h5")

# List of stock symbols to analyze (can be customized)
stock_symbols = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "INTC", "AMD", "ADBE",
    "JPM", "BAC", "GS", "C", "WFC", "MA", "V", "PYPL", "AXP", "BLK",
    "JNJ", "PFE", "MRK", "ABBV", "UNH", "BMY", "GILD", "AMGN", "CVS", "MDT",
    "PG", "KO", "PEP", "NKE", "MCD", "SBUX", "COST", "WMT", "TGT", "DIS",
    "BA", "CAT", "GE", "HON", "MMM", "UPS", "FDX", "RTX", "LMT", "DE",
    "XOM", "CVX", "COP", "SLB", "EOG", "PSX", "VLO", "MPC", "OXY", "DVN",
    "SPY", "QQQ", "DIA", "VTI", "IVV", "IWM", "GLD", "TLT", "EEM", "ARKK",
    # Indian Stocks...
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    "RELIANCE.NS", "ONGC.NS", "GAIL.NS", "IOC.NS", "BPCL.NS",
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "BIOCON.NS",
    "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS",
    "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS",
    "LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "ACC.NS", "JSWSTEEL.NS"
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "INDUSINDBK.NS", "BANDHANBNK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS",
    "HDFCLIFE.NS", "SBILIFE.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS",
    "MUTHOOTFIN.NS", "RECLTD.NS", "PFC.NS", "LICHSGFIN.NS",
    
    # Information Technology
    "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    "LTIM.NS", "MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS", "OFSS.NS",
    
    # Oil & Gas/Energy
    "RELIANCE.NS", "ONGC.NS", "GAIL.NS", "IOC.NS", "BPCL.NS",
    "HINDPETRO.NS", "PETRONET.NS", "GUJGASLTD.NS", "MGL.NS",
    "ADANIGREEN.NS", "TATAPOWER.NS", "NTPC.NS", "POWERGRID.NS",
    
    # Pharmaceuticals & Healthcare
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "BIOCON.NS",
    "LUPIN.NS", "AUROPHARMA.NS", "GLENMARK.NS", "TORNTPHARM.NS", "ALKEM.NS",
    "LAURUSLABS.NS", "METROPOLIS.NS", "FORTIS.NS", "APOLLOHOSP.NS",
    
    # Automobiles & Ancillaries
    "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS",
    "ASHOKLEY.NS", "BOSCHLTD.NS", "TVSMOTOR.NS", "EXIDEIND.NS", "MOTHERSON.NS",
    "BHARATFORG.NS", "AMARAJABAT.NS", "MRF.NS", "CEAT.NS",
    
    # FMCG & Consumer Goods
    "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS",
    "GODREJCP.NS", "COLPAL.NS", "MARICO.NS", "RADICO.NS", "UBL.NS",
    "TATACONSUM.NS", "EMAMILTD.NS", "BATAINDIA.NS", "VBL.NS",
    
    # Infrastructure & Construction
    "LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "ACC.NS", "AMBUJACEM.NS",
    "SHREECEM.NS", "GRASIM.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "SAIL.NS",
    "HINDALCO.NS", "VEDL.NS", "JINDALSTEL.NS",
    
    # Chemicals & Fertilizers
    "UPL.NS", "PIIND.NS", "SRF.NS", "TATACHEM.NS", "GNFC.NS",
    "FACT.NS", "GSFC.NS", "DEEPAKNTR.NS", "NAVINFLUOR.NS", "AARTIIND.NS",
    
    # Retail & E-commerce
    "TITAN.NS", "TRENT.NS", "V-MART.NS", "APOLLOTYRE.NS", "ZOMATO.NS",
    "NAUKRI.NS", "JUBLFOOD.NS", "WESTLIFE.NS", "DELHIVERY.NS",
    
    # Specialized Sectors
    "IRCTC.NS",      # Railways
    "IRFC.NS",       # Railway Finance
    "RVNL.NS",       # Rail Infrastructure
    "HAL.NS",        # Defense
    "BEL.NS",        # Defense Electronics
    "NHPC.NS",       # Hydro Power
    "SJVN.NS",       # Renewable Energy
    "IREDA.NS",      # Renewable Energy Financing
    "POLICYBZR.NS",  # Insurance Tech
    "PAYTM.NS",      # Fintech
    "AFFLE.NS",      # Mobile Marketing
    "MAPMYINDIA.NS", # Digital Mapping
    
    # Emerging Companies
    "LATENTVIEW.NS", # Analytics
    "TANLA.NS",      # Cloud Communications
    "CDSL.NS",       # Depository Services
    "CAMS.NS",       # Mutual Fund Services
    "PRIVISCL.NS",   # Plastic Products
    "ROUTE.NS",      # Fiber Networks
    "KAYNES.NS",     # Electronics Manufacturing
    "DATAPATTNS.NS", # AI/ML Solutions
    
    # PSUs (Public Sector Undertakings)
    "COALINDIA.NS", "NMDC.NS", "BHEL.NS", "HUDCO.NS", "NBCC.NS",
    "GAIL.NS", "ONGC.NS", "OIL.NS", "CONCOR.NS", "STLTECH.NS",
    
    # International Companies (Indian Operations)
    "HONDAPOWER.NS", # Honda
    "SIEMENS.NS",    # Siemens India
    "ABB.NS",        # ABB India
    "SCHNEIDER.NS",  # Schneider Electric
    "WHIRLPOOL.NS",  # Whirlpool India
    "COLPAL.NS",     # Colgate-Palmolive
    "HINDCOPPER.NS", # Hindustan Copper
    "HSCL.NS"        # Hindustan Sanitaryware
   
    # United States (NYSE/NASDAQ)
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",  # Tech Giants
    "META", "NVDA", "INTC", "AMD", "QCOM",    # Semiconductor/Social Media
    "JPM", "BAC", "GS", "C", "MS",            # Financial Services
    "WMT", "TGT", "COST", "HD", "LOW",        # Retail
    "XOM", "CVX", "COP", "SLB", "EOG",        # Energy
    "JNJ", "PFE", "MRK", "ABBV", "GILD",      # Healthcare
    "KO", "PEP", "PG", "UL", "MO",            # Consumer Staples
    "BA", "CAT", "HON", "MMM", "GE",          # Industrials
    "SPY", "QQQ", "DIA", "IWM", "VOO",        # ETFs (Market Indices)

    # Europe
    ## UK (LSE)
    "HSBA.L", "BP.L", "GSK.L", "RIO.L", "AZN.L",  # FTSE 100
    "ULVR.L", "DGE.L", "RDSA.L", "TSCO.L", "BATS.L",
    
    ## Germany (XETRA)
    "SAP.DE", "SIE.DE", "DTE.DE", "ALV.DE", "DBK.DE",  # DAX
    "BMW.DE", "VOW3.DE", "BAS.DE", "BAYN.DE", "MRK.DE",
    
    ## France (Euronext Paris)
    "AIR.PA", "TOT.PA", "SAN.PA", "BNP.PA", "MC.PA",   # CAC 40
    "OR.PA", "UG.PA", "CAP.PA", "AI.PA", "DG.PA",
    
    ## Pan-European
    "ASML.AS", "ULVR.AS", "INGA.AS",  # Netherlands
    "NESN.SW", "ROG.SW", "NOVN.SW",   # Switzerland
    "ENEL.MI", "ENI.MI", "STM.MI",    # Italy

    # Asia-Pacific
    ## Japan (Tokyo)
    "7203.T", "9984.T", "9433.T", "6861.T", "9983.T",  # Toyota, SoftBank, KDDI, Keyence, Fast Retailing
    "6758.T", "7267.T", "6954.T", "4568.T", "6098.T",  # Sony, Honda, Fanuc, Daiichi Sankyo, Recruit
    
    ## Hong Kong
    "0700.HK", "9988.HK", "3690.HK", "1810.HK", "2318.HK",  # Tencent, Alibaba, Meituan, Xiaomi, Ping An
    
    ## China (US ADRs)
    "BABA", "PDD", "JD", "BIDU", "TCOM",                 # E-commerce
    "NIO", "XPEV", "LI", "BZUN", "TIGR",                 # EVs/Fintech
    
    ## South Korea
    "005930.KS", "000660.KS", "035420.KS","051910.KS",  # Samsung, SK Hynix, Naver, LG Chem
    "068270.KS", "035720.KS", "207940.KS",               # Celltrion, Kakao, SK Bioscience
    
    ## Australia
    "BHP.AX", "RIO.AX", "CBA.AX", "CSL.AX", "WES.AX",    # Mining/Banking
    "TLS.AX", "WOW.AX", "FMG.AX", "GMG.AX", "ALL.AX",    # Telstra, Woolworths, Fortescue

    # Emerging Markets
    ## Brazil
    "VALE", "PBR", "ITUB", "BBD", "ERJ",                 # Vale, Petrobras, Itau, Banco Bradesco, Embraer
    
    ## Russia (US ADRs)
    "SBRCY", "LUKOY", "OGZPY", "MTLR", "NILSY",          # Sberbank, Lukoil, Gazprom, Mechel, Nornickel
    
    ## South Africa
    "NPN.JO", "BGA.JO", "ANG.JO", "SOL.JO", "MTN.JO",    # Naspers, Barclays Africa, AngloGold, Sasol, MTN
    
    ## Mexico
    "AMX", "GGAL", "CX", "ASR", "VIST",                  # America Movil, Grupo Financiero, Cemex, Grupo Aeroportuario
    
    ## Middle East
    "SABIC.TA", "ARAMCO.SE", "QNBK.QA", "DPW.DU",        # Saudi Basic, Saudi Aramco, Qatar National Bank, DP World

    # Sector-Specific Global Leaders
    ## Semiconductors
    "TSM", "ASML", "AVGO", "TXN", "MU",
    
    ## Automotive
    "VWAGY", "TM", "HMC", "STLA", "RACE.MI",
    
    ## Luxury Goods
    "LVMUY", "CFR.SW", "KER.PA", "TIF", 
    
    ## Aerospace/Defense
    "LMT", "RTX", "BA", "AIR.PA", "HEI",
    
    ## Renewable Energy
    "NEE", "ENPH", "PLUG", "FSLR", "SEDG",
    
    ## Cryptocurrency/Blockchain
    "COIN", "MSTR", "RIOT", "MARA", "SQ",
    
    ## Space Exploration
    "SPCE", "RKLB", "ASTS", "AJRD", "MAXR",
    
    ## Global ETFs
    "EEM",  # Emerging Markets
    "VGK",  # Europe
    "EWJ",  # Japan
    "FXI",  # China
    "EWZ",  # Brazil
    "EWY",  # South Korea
    "EWC",  # Canada
    "EWA",  # Australia
    "EWG",  # Germany
    "EWU"   # UK
    # Add more stocks as needed
]

# --- Function to Get Predictions for Multiple Stocks ---
def get_buy_recommendations(stocks):
    recommendations = []
    
    for ticker in stocks:
        try:
            # Fetch stock data
            data = get_stock_data(ticker)
            if data.empty:
                continue  # Skip if no data is available

            # Process data and get prediction
            X, scaler, feature_columns = preprocess_data(data)
            prediction = model.predict(X)
            close_idx = list(feature_columns).index('Close')
            last_row = X[0, -1, :].copy()
            last_row[close_idx] = prediction[0, 0]
            predicted_price = scaler.inverse_transform([last_row])[0, close_idx]

            # Get current price
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")["Close"].iloc[-1]

            # Calculate price difference
            price_difference = predicted_price - current_price
            recommendations.append({
                "ticker": ticker,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "price_difference": price_difference
            })
        
        except Exception as e:
            continue  # Skip if any error occurs for a stock
    
    # Convert recommendations to DataFrame
    recommendations_df = pd.DataFrame(recommendations)
    
    # Sort by price difference (highest predicted increase)
    top_recommendations = recommendations_df[recommendations_df["price_difference"] > 0].sort_values(
        by="price_difference", ascending=False
    ).head(5)
    
    return top_recommendations

# --- Streamlit Dashboard for "Buy Recommendations" Page ---
# --- Streamlit Dashboard for "Buy Recommendations" Page ---
st.set_page_config(page_title="🛒 Best Stocks to Buy", layout="wide", page_icon="💰")

# Display header
st.markdown("""
    <h1 style='text-align: center;'>💰 Top 5 Best Stocks to Buy</h1>
    <h4 style='text-align: center;'>Based on AI predictions and market trends</h4>
""", unsafe_allow_html=True)

# Check if recommendations already exist in session state
if "top_buy_stocks" not in st.session_state:
    with st.spinner("🔍 Analyzing market data..."):
        st.session_state.top_buy_stocks = get_buy_recommendations(stock_symbols)

top_buy_stocks = st.session_state.top_buy_stocks

# Display results
if not top_buy_stocks.empty:
    st.markdown("### 🏆 Top 5 Stocks Recommended for Buying")
    st.dataframe(
        top_buy_stocks[['ticker', 'current_price', 'predicted_price', 'price_difference']],
        use_container_width=True
    )
else:
    st.info("🔍 No stocks recommended for buying at the moment.")

if st.button("🔄 Refresh Recommendations"):
    with st.spinner("Re-analyzing..."):
        st.session_state.top_buy_stocks = get_buy_recommendations(stock_symbols)
