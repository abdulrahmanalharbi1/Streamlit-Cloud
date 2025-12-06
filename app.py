"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         Trading Dashboard                                      ║
║                       داش بورد توصيات التداول                                   ║
║                           Version 3.0                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta
import requests
import json
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient

# ═══════════════════════════════════════════════════════════════════════════════
# Page Configuration
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Trading Dashboard | داش بورد التداول",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants & Config
# ═══════════════════════════════════════════════════════════════════════════════
API_KEY = "PKQFABN4IQPP2AEIGHVPBPFRLI"
API_SECRET = "Ck15KLt7d51kmdSuuNniPB3P2xd7Y1GDnrRnMAvFsmtA"

# Telegram Config
TELEGRAM_TOKEN = "8464619215:AAGWJGQAOGISayId6d-JZRs63m0hnK5uwt8"
TELEGRAM_CHAT_ID = "328704848"

# Trades Database File
TRADES_FILE = "trades_history.json"

TRADING_CONFIG = {
    'initial_capital': 100000,
    'risk_per_trade': 0.02,
    'reward_ratio': 2.5,
    'max_position': 0.10
}

TOP_STOCKS = ['HOOD', 'ROKU', 'COIN', 'SHOP', 'TSLA', 'SNOW', 'MELI', 'DASH', 
              'AMD', 'NVDA', 'META', 'AAPL', 'MSFT', 'GOOGL', 'AMZN']

TRANSLATIONS = {
    'ar': {
        'app_title': 'لوحة تحكم التداول',
        'dashboard': 'الرئيسية',
        'signals': 'التوصيات',
        'history': 'سجل الصفقات',
        'analysis': 'التحليل',
        'settings': 'الإعدادات',
        'new_signals': 'إشارات جديدة',
        'open_positions': 'صفقات مفتوحة',
        'capital': 'رأس المال',
        'win_rate': 'نسبة النجاح',
        'buy': 'شراء',
        'sell': 'بيع',
        'entry_price': 'سعر الدخول',
        'stop_loss': 'وقف الخسارة',
        'target': 'الهدف',
        'strategy': 'الاستراتيجية',
        'timeframe': 'الإطار الزمني',
        'signal_strength': 'قوة الإشارة',
        'shares': 'الأسهم',
        'position_size': 'حجم الصفقة',
        'risk_per_trade': 'المخاطرة',
        'supporting_indicators': 'المؤشرات الداعمة',
        'volume': 'الحجم',
        'refresh': 'تحديث',
        'last_update': 'آخر تحديث',
        'no_signals': 'لا توجد إشارات حالياً',
        'loading': 'جاري التحميل...',
        'market_open': 'السوق مفتوح',
        'market_closed': 'السوق مغلق',
        'all': 'الكل',
        'stocks': 'الأسهم',
        'scan_now': 'مسح الآن',
        'server_status': 'حالة السيرفر',
        'connected': 'متصل',
        'disconnected': 'غير متصل',
        'error': 'خطأ',
        'total_trades': 'إجمالي الصفقات',
        'winning_trades': 'صفقات رابحة',
        'losing_trades': 'صفقات خاسرة',
        'total_profit': 'إجمالي الربح',
        'pending': 'معلقة',
        'closed': 'مغلقة',
        'status': 'الحالة',
        'result': 'النتيجة',
        'profit_loss': 'الربح/الخسارة',
        'close_trade': 'إغلاق الصفقة',
        'current_price': 'السعر الحالي'
    },
    'en': {
        'app_title': 'Trading Dashboard',
        'dashboard': 'Dashboard',
        'signals': 'Signals',
        'history': 'Trade History',
        'analysis': 'Analysis',
        'settings': 'Settings',
        'new_signals': 'New Signals',
        'open_positions': 'Open Positions',
        'capital': 'Capital',
        'win_rate': 'Win Rate',
        'buy': 'BUY',
        'sell': 'SELL',
        'entry_price': 'Entry Price',
        'stop_loss': 'Stop Loss',
        'target': 'Target',
        'strategy': 'Strategy',
        'timeframe': 'Timeframe',
        'signal_strength': 'Signal Strength',
        'shares': 'Shares',
        'position_size': 'Position Size',
        'risk_per_trade': 'Risk',
        'supporting_indicators': 'Supporting Indicators',
        'volume': 'Volume',
        'refresh': 'Refresh',
        'last_update': 'Last Update',
        'no_signals': 'No signals available',
        'loading': 'Loading...',
        'market_open': 'Market Open',
        'market_closed': 'Market Closed',
        'all': 'All',
        'stocks': 'Stocks',
        'scan_now': 'Scan Now',
        'server_status': 'Server Status',
        'connected': 'Connected',
        'disconnected': 'Disconnected',
        'error': 'Error',
        'total_trades': 'Total Trades',
        'winning_trades': 'Winning Trades',
        'losing_trades': 'Losing Trades',
        'total_profit': 'Total Profit',
        'pending': 'Pending',
        'closed': 'Closed',
        'status': 'Status',
        'result': 'Result',
        'profit_loss': 'P&L',
        'close_trade': 'Close Trade',
        'current_price': 'Current Price'
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# Custom CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .status-bar {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 100%);
        padding: 15px 25px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #333;
        flex-wrap: wrap;
        gap: 15px;
    }
    
    .live-clock {
        font-size: 1.8rem;
        font-weight: bold;
        color: #4CAF50;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
    }
    
    @keyframes blink-green {
        0%, 100% { opacity: 1; box-shadow: 0 0 15px #4CAF50, 0 0 30px #4CAF50; }
        50% { opacity: 0.6; box-shadow: 0 0 5px #4CAF50; }
    }
    
    @keyframes blink-yellow {
        0%, 100% { opacity: 1; box-shadow: 0 0 15px #FFC107, 0 0 30px #FFC107; }
        50% { opacity: 0.6; box-shadow: 0 0 5px #FFC107; }
    }
    
    @keyframes blink-red {
        0%, 100% { opacity: 1; box-shadow: 0 0 15px #f44336, 0 0 30px #f44336; }
        50% { opacity: 0.6; box-shadow: 0 0 5px #f44336; }
    }
    
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 15px;
        border-radius: 25px;
        background: rgba(0,0,0,0.3);
    }
    
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .status-dot.green { background: #4CAF50; animation: blink-green 1.5s infinite; }
    .status-dot.yellow { background: #FFC107; animation: blink-yellow 1s infinite; }
    .status-dot.red { background: #f44336; animation: blink-red 0.5s infinite; }
    
    .status-text { color: white; font-size: 0.95rem; font-weight: 500; }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        border-bottom: 3px solid #4CAF50;
    }
    
    .buy-badge { background: #4CAF50; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    .sell-badge { background: #f44336; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    .telegram-badge { background: #0088cc; color: white; padding: 3px 10px; border-radius: 10px; font-size: 0.75rem; margin-left: 10px; }
    
    .profit { color: #4CAF50; font-weight: bold; }
    .loss { color: #f44336; font-weight: bold; }
    
    .trade-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    
    .trade-card.closed-win { border-left-color: #4CAF50; }
    .trade-card.closed-loss { border-left-color: #f44336; }
    .trade-card.pending { border-left-color: #FFC107; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════════════════════════════════════
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'last_scan' not in st.session_state:
    st.session_state.last_scan = None
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'telegram_sent' not in st.session_state:
    st.session_state.telegram_sent = []
if 'startup_sent' not in st.session_state:
    st.session_state.startup_sent = False

def t(key):
    return TRANSLATIONS.get(st.session_state.lang, {}).get(key, key)

def get_stars(strength):
    return "⭐" * int(strength) + "☆" * (5 - int(strength))

# ═══════════════════════════════════════════════════════════════════════════════
# Trades Database Functions
# ═══════════════════════════════════════════════════════════════════════════════
def load_trades():
    """Load trades from JSON file"""
    try:
        if os.path.exists(TRADES_FILE):
            with open(TRADES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading trades: {e}")
    return []

def save_trades(trades):
    """Save trades to JSON file"""
    try:
        with open(TRADES_FILE, 'w', encoding='utf-8') as f:
            json.dump(trades, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Error saving trades: {e}")
        return False

def add_trade(signal):
    """Add a new trade from signal"""
    trades = load_trades()
    
    trade = {
        'id': len(trades) + 1,
        'symbol': signal['symbol'],
        'type': signal['type'],
        'strategy': signal['strategy'],
        'timeframe': signal['timeframe'],
        'entry_price': signal['price'],
        'stop_loss': signal['stop_loss'],
        'target1': signal['target1'],
        'target2': signal['target2'],
        'shares': signal['shares'],
        'position_value': signal['position_value'],
        'risk_amount': signal['risk_amount'],
        'strength': signal['strength'],
        'entry_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'pending',  # pending, closed_win, closed_loss
        'exit_price': None,
        'exit_date': None,
        'profit_loss': None,
        'profit_loss_pct': None,
        'notes': ''
    }
    
    trades.append(trade)
    save_trades(trades)
    return trade

def update_trade(trade_id, exit_price, status, notes=''):
    """Update trade with exit info"""
    trades = load_trades()
    
    for trade in trades:
        if trade['id'] == trade_id:
            trade['exit_price'] = exit_price
            trade['exit_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            trade['status'] = status
            trade['notes'] = notes
            
            # Calculate P&L
            if trade['type'] == 'BUY':
                trade['profit_loss'] = (exit_price - trade['entry_price']) * trade['shares']
                trade['profit_loss_pct'] = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
            else:
                trade['profit_loss'] = (trade['entry_price'] - exit_price) * trade['shares']
                trade['profit_loss_pct'] = ((trade['entry_price'] - exit_price) / trade['entry_price']) * 100
            
            break
    
    save_trades(trades)

def get_trade_stats():
    """Get trading statistics"""
    trades = load_trades()
    
    closed_trades = [t for t in trades if t['status'] != 'pending']
    pending_trades = [t for t in trades if t['status'] == 'pending']
    winning_trades = [t for t in closed_trades if t['status'] == 'closed_win']
    losing_trades = [t for t in closed_trades if t['status'] == 'closed_loss']
    
    total_profit = sum([t.get('profit_loss', 0) or 0 for t in closed_trades])
    
    win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
    
    return {
        'total': len(trades),
        'pending': len(pending_trades),
        'closed': len(closed_trades),
        'wins': len(winning_trades),
        'losses': len(losing_trades),
        'win_rate': round(win_rate, 1),
        'total_profit': round(total_profit, 2)
    }

# ═══════════════════════════════════════════════════════════════════════════════
# Telegram Functions
# ═══════════════════════════════════════════════════════════════════════════════
def send_telegram_message(message):
    """Send message to Telegram with detailed error handling"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=15)
        
        if response.status_code == 200:
            return True, "تم الإرسال بنجاح"
        else:
            result = response.json()
            error_msg = result.get('description', 'Unknown error')
            return False, f"خطأ: {error_msg}"
            
    except requests.exceptions.Timeout:
        return False, "انتهت مهلة الاتصال - تأكد من الإنترنت"
    except requests.exceptions.ConnectionError:
        return False, "فشل الاتصال - تحقق من الإنترنت"
    except Exception as e:
        return False, f"خطأ غير متوقع: {str(e)}"

def test_telegram():
    """Test Telegram connection with detailed feedback"""
    # Step 1: Test bot token
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return False, "❌ التوكن غير صحيح - تأكد من نسخه بشكل صحيح"
        
        bot_info = response.json()
        bot_name = bot_info.get('result', {}).get('username', 'Unknown')
        
    except Exception as e:
        return False, f"❌ فشل الاتصال: {str(e)}"
    
    # Step 2: Try to send message
    success, msg = send_telegram_message(f"✅ اختبار ناجح!\n\n🤖 البوت: @{bot_name}\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        return True, f"✅ نجح! البوت: @{bot_name}"
    else:
        if "chat not found" in msg.lower():
            return False, f"❌ لم تبدأ محادثة مع البوت.\n\n1️⃣ ابحث عن @{bot_name}\n2️⃣ اضغط Start\n3️⃣ جرب مرة أخرى"
        return False, msg

def send_signal_to_telegram(signal):
    """Format and send signal to Telegram"""
    is_buy = signal['type'] == 'BUY'
    emoji = "🟢" if is_buy else "🔴"
    signal_type = "شراء" if is_buy else "بيع"
    
    message = f"""
{emoji} <b>توصية جديدة - {signal_type}</b> {emoji}

📊 <b>السهم:</b> {signal['symbol']}
📈 <b>الاستراتيجية:</b> {signal['strategy']}
⏰ <b>الإطار الزمني:</b> {signal['timeframe']}
⭐ <b>القوة:</b> {get_stars(signal['strength'])}

💰 <b>سعر الدخول:</b> ${signal['price']:.2f}
🛑 <b>وقف الخسارة:</b> ${signal['stop_loss']:.2f} ({signal['stop_loss_pct']:.1f}%)
🎯 <b>الهدف 1:</b> ${signal['target1']:.2f} (+{signal['target1_pct']:.1f}%)
🎯 <b>الهدف 2:</b> ${signal['target2']:.2f} (+{signal['target2_pct']:.1f}%)

📦 <b>عدد الأسهم:</b> {signal['shares']}
💵 <b>حجم الصفقة:</b> ${signal['position_value']:,.0f}
⚠️ <b>المخاطرة:</b> ${signal['risk_amount']:.0f}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━
🤖 Trading Dashboard v3.0
"""
    success, msg = send_telegram_message(message)
    return success

def send_startup_message():
    """Send startup notification"""
    message = f"""
🚀 <b>تم تشغيل الداش بورد</b>

✅ السيرفر يعمل بنجاح
📊 الإصدار: 3.0
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━
🤖 Trading Dashboard
"""
    success, _ = send_telegram_message(message)
    return success

# Send startup message once
if not st.session_state.startup_sent:
    send_startup_message()
    st.session_state.startup_sent = True

# ═══════════════════════════════════════════════════════════════════════════════
# Data Fetcher
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_clients():
    try:
        data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
        trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        return data_client, trading_client, "connected"
    except Exception as e:
        return None, None, "error"

def check_server_status():
    try:
        data_client, trading_client, status = get_clients()
        if status == "error" or trading_client is None:
            return "red", t('error')
        clock = trading_client.get_clock()
        return "green", t('connected')
    except Exception as e:
        return "yellow", t('disconnected')

def get_historical_data(symbol, timeframe='1day', days=90):
    try:
        data_client, _, _ = get_clients()
        if data_client is None:
            return None
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        tf_map = {'1hour': TimeFrame.Hour, '4hour': TimeFrame.Hour, '1day': TimeFrame.Day}
        tf = tf_map.get(timeframe, TimeFrame.Day)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start_date,
            end=end_date
        )
        
        bars = data_client.get_stock_bars(request)
        df = bars.df
        
        if len(df) == 0:
            return None
        
        if isinstance(df.index, pd.MultiIndex):
            df = df.loc[symbol].reset_index()
        else:
            df = df.reset_index()
        
        df.columns = [c.lower() for c in df.columns]
        
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        if timeframe == '4hour':
            df = df.set_index('timestamp')
            df = df.resample('4H').agg({
                'open': 'first', 'high': 'max', 'low': 'min',
                'close': 'last', 'volume': 'sum'
            }).dropna().reset_index()
        
        return df
    except Exception as e:
        return None

def get_current_price(symbol):
    """Get current price for a symbol"""
    try:
        df = get_historical_data(symbol, '1day', 5)
        if df is not None and len(df) > 0:
            return df['close'].iloc[-1]
    except:
        pass
    return None

def get_account_info():
    try:
        _, trading_client, _ = get_clients()
        if trading_client is None:
            return None
        account = trading_client.get_account()
        return {
            'equity': float(account.equity),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power)
        }
    except:
        return None

def is_market_open():
    try:
        _, trading_client, _ = get_clients()
        if trading_client is None:
            return False
        clock = trading_client.get_clock()
        return clock.is_open
    except:
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# Signal Generator
# ═══════════════════════════════════════════════════════════════════════════════
def add_indicators(df):
    if len(df) < 50:
        return df
    
    for p in [10, 20, 30]:
        df[f'sma_{p}'] = ta.trend.sma_indicator(df['close'], window=p)
    
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()
    
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    
    df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    return df

def check_signals(df, symbol, timeframe):
    signals = []
    
    if len(df) < 35:
        return signals
    
    # MA Crossover
    fast_ma = df['close'].rolling(10).mean()
    slow_ma = df['close'].rolling(30).mean()
    if fast_ma.iloc[-1] > slow_ma.iloc[-1] and fast_ma.iloc[-2] <= slow_ma.iloc[-2]:
        signals.append({'type': 'BUY', 'strategy': 'MA Crossover', 'symbol': symbol, 'timeframe': timeframe})
    elif fast_ma.iloc[-1] < slow_ma.iloc[-1] and fast_ma.iloc[-2] >= slow_ma.iloc[-2]:
        signals.append({'type': 'SELL', 'strategy': 'MA Crossover', 'symbol': symbol, 'timeframe': timeframe})
    
    # MACD
    if 'macd' in df.columns and not pd.isna(df['macd'].iloc[-1]):
        if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1] and df['macd'].iloc[-2] <= df['macd_signal'].iloc[-2]:
            signals.append({'type': 'BUY', 'strategy': 'MACD', 'symbol': symbol, 'timeframe': timeframe})
        elif df['macd'].iloc[-1] < df['macd_signal'].iloc[-1] and df['macd'].iloc[-2] >= df['macd_signal'].iloc[-2]:
            signals.append({'type': 'SELL', 'strategy': 'MACD', 'symbol': symbol, 'timeframe': timeframe})
    
    # RSI
    if 'rsi' in df.columns and not pd.isna(df['rsi'].iloc[-1]):
        if df['rsi'].iloc[-1] > 30 and df['rsi'].iloc[-2] <= 30:
            signals.append({'type': 'BUY', 'strategy': 'RSI Reversal', 'symbol': symbol, 'timeframe': timeframe})
        elif df['rsi'].iloc[-1] < 70 and df['rsi'].iloc[-2] >= 70:
            signals.append({'type': 'SELL', 'strategy': 'RSI Reversal', 'symbol': symbol, 'timeframe': timeframe})
    
    # Stochastic
    if 'stoch_k' in df.columns and not pd.isna(df['stoch_k'].iloc[-1]):
        k, d = df['stoch_k'].iloc[-1], df['stoch_d'].iloc[-1]
        pk, pd_val = df['stoch_k'].iloc[-2], df['stoch_d'].iloc[-2]
        if k > d and pk <= pd_val and k < 35:
            signals.append({'type': 'BUY', 'strategy': 'Stochastic', 'symbol': symbol, 'timeframe': timeframe})
        elif k < d and pk >= pd_val and k > 65:
            signals.append({'type': 'SELL', 'strategy': 'Stochastic', 'symbol': symbol, 'timeframe': timeframe})
    
    # Bollinger Bounce
    if 'bb_lower' in df.columns and not pd.isna(df['bb_lower'].iloc[-1]):
        if df['low'].iloc[-1] <= df['bb_lower'].iloc[-1] and df['close'].iloc[-1] > df['open'].iloc[-1]:
            signals.append({'type': 'BUY', 'strategy': 'Bollinger Bounce', 'symbol': symbol, 'timeframe': timeframe})
        elif df['high'].iloc[-1] >= df['bb_upper'].iloc[-1] and df['close'].iloc[-1] < df['open'].iloc[-1]:
            signals.append({'type': 'SELL', 'strategy': 'Bollinger Bounce', 'symbol': symbol, 'timeframe': timeframe})
    
    # Add price and indicators to signals
    price = df['close'].iloc[-1]
    atr = df['atr'].iloc[-1] if 'atr' in df.columns and not pd.isna(df['atr'].iloc[-1]) else price * 0.02
    
    for sig in signals:
        sig['price'] = price
        sig['atr'] = atr
        sig['timestamp'] = datetime.now()
        
        if sig['type'] == 'BUY':
            sig['stop_loss'] = round(price - (2 * atr), 2)
            sig['target1'] = round(price + (3 * atr), 2)
            sig['target2'] = round(price + (5 * atr), 2)
        else:
            sig['stop_loss'] = round(price + (2 * atr), 2)
            sig['target1'] = round(price - (3 * atr), 2)
            sig['target2'] = round(price - (5 * atr), 2)
        
        sig['stop_loss_pct'] = round(abs(sig['stop_loss'] - price) / price * 100, 2)
        sig['target1_pct'] = round(abs(sig['target1'] - price) / price * 100, 2)
        sig['target2_pct'] = round(abs(sig['target2'] - price) / price * 100, 2)
        
        risk_amount = TRADING_CONFIG['initial_capital'] * TRADING_CONFIG['risk_per_trade']
        risk_per_share = abs(price - sig['stop_loss'])
        sig['shares'] = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        sig['position_value'] = round(sig['shares'] * price, 2)
        sig['risk_amount'] = round(risk_amount, 2)
        sig['risk_reward'] = round(TRADING_CONFIG['reward_ratio'], 1)
        
        strength = 3
        if 'rsi' in df.columns and not pd.isna(df['rsi'].iloc[-1]) and 40 < df['rsi'].iloc[-1] < 60:
            strength += 0.5
        if 'volume_ratio' in df.columns and not pd.isna(df['volume_ratio'].iloc[-1]) and df['volume_ratio'].iloc[-1] > 1.2:
            strength += 0.5
        if 'adx' in df.columns and not pd.isna(df['adx'].iloc[-1]) and df['adx'].iloc[-1] > 25:
            strength += 0.5
        sig['strength'] = min(5, int(strength))
        
        sig['indicators'] = {}
        if 'rsi' in df.columns and not pd.isna(df['rsi'].iloc[-1]):
            rsi = df['rsi'].iloc[-1]
            sig['indicators']['rsi'] = {'value': round(rsi, 1), 'status': 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'}
        if 'macd_hist' in df.columns and not pd.isna(df['macd_hist'].iloc[-1]):
            sig['indicators']['macd'] = {'value': round(df['macd_hist'].iloc[-1], 3), 'status': 'positive' if df['macd_hist'].iloc[-1] > 0 else 'negative'}
        if 'volume_ratio' in df.columns and not pd.isna(df['volume_ratio'].iloc[-1]):
            sig['indicators']['volume'] = {'value': round(df['volume_ratio'].iloc[-1], 2), 'status': 'high' if df['volume_ratio'].iloc[-1] > 1.2 else 'normal'}
        if 'adx' in df.columns and not pd.isna(df['adx'].iloc[-1]):
            sig['indicators']['adx'] = {'value': round(df['adx'].iloc[-1], 1), 'status': 'strong' if df['adx'].iloc[-1] > 25 else 'weak'}
    
    return signals

# ═══════════════════════════════════════════════════════════════════════════════
# Status Bar
# ═══════════════════════════════════════════════════════════════════════════════
def render_status_bar():
    status_color, status_text = check_server_status()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    market_open = is_market_open()
    market_color = "green" if market_open else "red"
    market_text = t('market_open') if market_open else t('market_closed')
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="live-clock">🕐 {current_time}</div>
        <div class="status-indicator">
            <span class="status-dot {status_color}"></span>
            <span class="status-text">{t('server_status')}: {status_text}</span>
        </div>
        <div class="status-indicator">
            <span class="status-dot {market_color}"></span>
            <span class="status-text">{market_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🇸🇦 عربي", use_container_width=True,
                     type="primary" if st.session_state.lang == 'ar' else "secondary"):
            st.session_state.lang = 'ar'
            st.rerun()
    with col2:
        if st.button("🇺🇸 EN", use_container_width=True,
                     type="primary" if st.session_state.lang == 'en' else "secondary"):
            st.session_state.lang = 'en'
            st.rerun()
    
    st.markdown("---")
    
    pages = {
        'dashboard': f"🏠 {t('dashboard')}",
        'signals': f"🔔 {t('signals')}",
        'history': f"📋 {t('history')}",
        'analysis': f"📊 {t('analysis')}",
        'settings': f"⚙️ {t('settings')}"
    }
    
    for key, label in pages.items():
        if st.button(label, use_container_width=True,
                     type="primary" if st.session_state.page == key else "secondary"):
            st.session_state.page = key
            st.rerun()
    
    st.markdown("---")
    
    if st.button(f"🔄 {t('refresh')}", use_container_width=True):
        st.session_state.signals = []
        st.session_state.last_scan = None
        st.cache_data.clear()
        st.rerun()
    
    if st.session_state.last_scan:
        st.caption(f"{t('last_update')}: {st.session_state.last_scan.strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    # Telegram Test
    if st.button("📱 Test Telegram", use_container_width=True):
        success, msg = test_telegram()
        if success:
            st.success(msg)
        else:
            st.error(msg)

# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_dashboard():
    render_status_bar()
    st.markdown(f'<div class="main-header">🎯 {t("app_title")}</div>', unsafe_allow_html=True)
    
    # Stats
    stats = get_trade_stats()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(f"🔔 {t('new_signals')}", len(st.session_state.signals))
    with col2:
        st.metric(f"📋 {t('total_trades')}", stats['total'])
    with col3:
        st.metric(f"⏳ {t('pending')}", stats['pending'])
    with col4:
        st.metric(f"🎯 {t('win_rate')}", f"{stats['win_rate']}%")
    with col5:
        profit_color = "normal" if stats['total_profit'] >= 0 else "inverse"
        st.metric(f"💰 {t('total_profit')}", f"${stats['total_profit']:,.0f}", delta_color=profit_color)
    
    st.markdown("---")
    
    # Scan Controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        scan_btn = st.button(f"🔍 {t('scan_now')}", use_container_width=True, type="primary")
    
    with col2:
        timeframes = st.multiselect(
            t('timeframe'),
            ['1hour', '4hour', '1day'],
            default=['1day'],
            format_func=lambda x: {'1hour': '1H', '4hour': '4H', '1day': 'Daily'}[x]
        )
    
    with col3:
        send_telegram = st.checkbox("📱 Telegram", value=True)
        save_trades_opt = st.checkbox("💾 حفظ", value=True)
    
    if scan_btn:
        with st.spinner(f"🔄 {t('loading')}"):
            signals = []
            progress = st.progress(0)
            
            for i, symbol in enumerate(TOP_STOCKS):
                for tf in timeframes:
                    try:
                        days = {'1hour': 30, '4hour': 60, '1day': 90}[tf]
                        df = get_historical_data(symbol, tf, days)
                        if df is not None and len(df) > 50:
                            df = add_indicators(df)
                            stock_signals = check_signals(df, symbol, tf)
                            signals.extend(stock_signals)
                    except:
                        continue
                progress.progress((i + 1) / len(TOP_STOCKS))
            
            telegram_count = 0
            saved_count = 0
            
            for sig in signals:
                sig_key = f"{sig['symbol']}_{sig['strategy']}_{sig['timeframe']}"
                
                # Save to database
                if save_trades_opt:
                    add_trade(sig)
                    saved_count += 1
                
                # Send to Telegram
                if send_telegram and sig_key not in st.session_state.telegram_sent:
                    if send_signal_to_telegram(sig):
                        st.session_state.telegram_sent.append(sig_key)
                        sig['telegram_sent'] = True
                        telegram_count += 1
            
            st.session_state.signals = signals
            st.session_state.last_scan = datetime.now()
            progress.empty()
            
            if signals:
                st.success(f"✅ {len(signals)} إشارة | 💾 {saved_count} محفوظ | 📱 {telegram_count} تيليجرام")
            st.rerun()
    
    st.markdown("---")
    st.subheader(f"🔔 {t('signals')}")
    
    if not st.session_state.signals:
        st.info(f"ℹ️ {t('no_signals')} - Press '{t('scan_now')}' to search")
    else:
        for sig in st.session_state.signals[:10]:
            render_signal_card(sig)

def render_signal_card(signal):
    is_buy = signal['type'] == 'BUY'
    emoji = '🟢' if is_buy else '🔴'
    badge = 'buy-badge' if is_buy else 'sell-badge'
    signal_text = t('buy') if is_buy else t('sell')
    
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            telegram_badge = '<span class="telegram-badge">📱 Sent</span>' if signal.get('telegram_sent') else ''
            st.markdown(f"### {emoji} {signal['symbol']} {telegram_badge}", unsafe_allow_html=True)
            st.markdown(f'<span class="{badge}">{signal_text}</span>', unsafe_allow_html=True)
            st.markdown(f"**{t('strategy')}:** {signal['strategy']}")
            st.markdown(f"**{t('signal_strength')}:** {get_stars(signal['strength'])}")
        
        with col2:
            st.markdown(f"""
            **{t('entry_price')}:** ${signal['price']:.2f}  
            **{t('stop_loss')}:** ${signal['stop_loss']:.2f} (-{signal['stop_loss_pct']:.1f}%)  
            **{t('target')} 1:** ${signal['target1']:.2f} (+{signal['target1_pct']:.1f}%)  
            **{t('target')} 2:** ${signal['target2']:.2f} (+{signal['target2_pct']:.1f}%)
            """)
        
        with col3:
            st.markdown(f"""
            **{t('shares')}:** {signal['shares']}  
            **{t('position_size')}:** ${signal['position_value']:,.0f}
            """)
        
        st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# Trade History Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_history():
    render_status_bar()
    st.title(f"📋 {t('history')}")
    
    trades = load_trades()
    stats = get_trade_stats()
    
    # Stats Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(t('total_trades'), stats['total'])
    col2.metric(t('pending'), stats['pending'])
    col3.metric(t('winning_trades'), stats['wins'])
    col4.metric(t('losing_trades'), stats['losses'])
    col5.metric(t('win_rate'), f"{stats['win_rate']}%")
    
    st.markdown("---")
    
    # Filter
    filter_status = st.selectbox(
        t('status'),
        ['all', 'pending', 'closed_win', 'closed_loss'],
        format_func=lambda x: t('all') if x == 'all' else t('pending') if x == 'pending' else '✅ ربح' if x == 'closed_win' else '❌ خسارة'
    )
    
    filtered_trades = trades
    if filter_status != 'all':
        filtered_trades = [t for t in trades if t['status'] == filter_status]
    
    # Display trades
    if not filtered_trades:
        st.info("لا توجد صفقات")
        return
    
    for trade in reversed(filtered_trades[-20:]):  # Last 20
        status_class = 'pending' if trade['status'] == 'pending' else 'closed-win' if trade['status'] == 'closed_win' else 'closed-loss'
        
        with st.expander(f"{'🟢' if trade['type'] == 'BUY' else '🔴'} {trade['symbol']} - {trade['strategy']} - {trade['entry_date'][:10]}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **{t('entry_price')}:** ${trade['entry_price']:.2f}  
                **{t('stop_loss')}:** ${trade['stop_loss']:.2f}  
                **{t('target')} 1:** ${trade['target1']:.2f}  
                **{t('shares')}:** {trade['shares']}
                """)
            
            with col2:
                if trade['status'] == 'pending':
                    current_price = get_current_price(trade['symbol'])
                    if current_price:
                        pnl = (current_price - trade['entry_price']) * trade['shares'] if trade['type'] == 'BUY' else (trade['entry_price'] - current_price) * trade['shares']
                        pnl_class = 'profit' if pnl >= 0 else 'loss'
                        st.markdown(f"**{t('current_price')}:** ${current_price:.2f}")
                        st.markdown(f"**P&L:** <span class='{pnl_class}'>${pnl:+,.2f}</span>", unsafe_allow_html=True)
                    st.markdown(f"**{t('status')}:** ⏳ {t('pending')}")
                else:
                    st.markdown(f"**Exit:** ${trade['exit_price']:.2f}")
                    pnl_class = 'profit' if trade['profit_loss'] >= 0 else 'loss'
                    st.markdown(f"**P&L:** <span class='{pnl_class}'>${trade['profit_loss']:+,.2f} ({trade['profit_loss_pct']:+.1f}%)</span>", unsafe_allow_html=True)
                    st.markdown(f"**{t('status')}:** {'✅ ربح' if trade['status'] == 'closed_win' else '❌ خسارة'}")
            
            with col3:
                if trade['status'] == 'pending':
                    exit_price = st.number_input(f"سعر الخروج", value=float(trade['entry_price']), key=f"exit_{trade['id']}")
                    
                    col_win, col_loss = st.columns(2)
                    with col_win:
                        if st.button("✅ ربح", key=f"win_{trade['id']}"):
                            update_trade(trade['id'], exit_price, 'closed_win')
                            st.rerun()
                    with col_loss:
                        if st.button("❌ خسارة", key=f"loss_{trade['id']}"):
                            update_trade(trade['id'], exit_price, 'closed_loss')
                            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# Signals Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_signals():
    render_status_bar()
    st.title(f"🔔 {t('signals')}")
    
    if not st.session_state.signals:
        st.info(t('no_signals'))
        return
    
    df = pd.DataFrame([{
        t('stocks'): s['symbol'],
        'Type': s['type'],
        t('strategy'): s['strategy'],
        t('entry_price'): f"${s['price']:.2f}",
        t('stop_loss'): f"${s['stop_loss']:.2f}",
        t('target'): f"${s['target1']:.2f}",
        t('signal_strength'): get_stars(s['strength'])
    } for s in st.session_state.signals])
    
    st.dataframe(df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_analysis():
    render_status_bar()
    st.title(f"📊 {t('analysis')}")
    
    trades = load_trades()
    closed_trades = [t for t in trades if t['status'] != 'pending']
    
    if closed_trades:
        # Performance by Strategy
        st.subheader("📈 أداء الاستراتيجيات")
        
        strategy_stats = {}
        for trade in closed_trades:
            strat = trade['strategy']
            if strat not in strategy_stats:
                strategy_stats[strat] = {'wins': 0, 'losses': 0, 'profit': 0}
            
            if trade['status'] == 'closed_win':
                strategy_stats[strat]['wins'] += 1
            else:
                strategy_stats[strat]['losses'] += 1
            strategy_stats[strat]['profit'] += trade.get('profit_loss', 0) or 0
        
        strat_df = pd.DataFrame([
            {
                'Strategy': k,
                'Wins': v['wins'],
                'Losses': v['losses'],
                'Win Rate': f"{v['wins']/(v['wins']+v['losses'])*100:.0f}%" if v['wins']+v['losses'] > 0 else "0%",
                'Profit': f"${v['profit']:,.0f}"
            }
            for k, v in strategy_stats.items()
        ])
        st.dataframe(strat_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("⭐ Top Stocks")
    st.write(", ".join(TOP_STOCKS))

# ═══════════════════════════════════════════════════════════════════════════════
# Settings Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_settings():
    render_status_bar()
    st.title(f"⚙️ {t('settings')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Trading")
        st.number_input(t('capital'), value=100000, min_value=1000, step=1000)
        st.slider(t('risk_per_trade'), 0.5, 5.0, 2.0, 0.5, format="%.1f%%")
    
    with col2:
        st.subheader("📱 Telegram Test")
        st.text_input("Token", value=TELEGRAM_TOKEN[:25] + "...", disabled=True)
        st.text_input("Chat ID", value=TELEGRAM_CHAT_ID, disabled=True)
        
        if st.button("🧪 اختبار كامل"):
            with st.spinner("جاري الاختبار..."):
                success, msg = test_telegram()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                    st.info("""
                    **خطوات إصلاح التيليجرام:**
                    1. افتح تيليجرام
                    2. ابحث عن البوت باستخدام التوكن
                    3. اضغط /start
                    4. جرب مرة أخرى
                    """)

# ═══════════════════════════════════════════════════════════════════════════════
# Main Router
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == 'dashboard':
    show_dashboard()
elif st.session_state.page == 'signals':
    show_signals()
elif st.session_state.page == 'history':
    show_history()
elif st.session_state.page == 'analysis':
    show_analysis()
elif st.session_state.page == 'settings':
    show_settings()

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666;'>"
    f"Trading Dashboard v3.0 | 🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    f"</div>",
    unsafe_allow_html=True
)
