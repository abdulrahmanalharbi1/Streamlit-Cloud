"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         Trading Dashboard                                      ║
║                       داش بورد توصيات التداول                                   ║
║                           Version 1.0                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
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
        'scan_now': 'مسح الآن'
    },
    'en': {
        'app_title': 'Trading Dashboard',
        'dashboard': 'Dashboard',
        'signals': 'Signals',
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
        'scan_now': 'Scan Now'
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# Custom CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
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
    .buy-badge {
        background: #4CAF50;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    .sell-badge {
        background: #f44336;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
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

def t(key):
    return TRANSLATIONS.get(st.session_state.lang, {}).get(key, key)

def get_stars(strength):
    return "⭐" * int(strength) + "☆" * (5 - int(strength))

# ═══════════════════════════════════════════════════════════════════════════════
# Data Fetcher
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_clients():
    data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
    trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
    return data_client, trading_client

def get_historical_data(symbol, timeframe='1day', days=90):
    try:
        data_client, _ = get_clients()
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

def get_account_info():
    try:
        _, trading_client = get_clients()
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
        _, trading_client = get_clients()
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
    if 'macd' in df.columns:
        if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1] and df['macd'].iloc[-2] <= df['macd_signal'].iloc[-2]:
            signals.append({'type': 'BUY', 'strategy': 'MACD', 'symbol': symbol, 'timeframe': timeframe})
        elif df['macd'].iloc[-1] < df['macd_signal'].iloc[-1] and df['macd'].iloc[-2] >= df['macd_signal'].iloc[-2]:
            signals.append({'type': 'SELL', 'strategy': 'MACD', 'symbol': symbol, 'timeframe': timeframe})
    
    # RSI
    if 'rsi' in df.columns:
        if df['rsi'].iloc[-1] > 30 and df['rsi'].iloc[-2] <= 30:
            signals.append({'type': 'BUY', 'strategy': 'RSI Reversal', 'symbol': symbol, 'timeframe': timeframe})
        elif df['rsi'].iloc[-1] < 70 and df['rsi'].iloc[-2] >= 70:
            signals.append({'type': 'SELL', 'strategy': 'RSI Reversal', 'symbol': symbol, 'timeframe': timeframe})
    
    # Stochastic
    if 'stoch_k' in df.columns:
        k, d = df['stoch_k'].iloc[-1], df['stoch_d'].iloc[-1]
        pk, pd_val = df['stoch_k'].iloc[-2], df['stoch_d'].iloc[-2]
        if k > d and pk <= pd_val and k < 35:
            signals.append({'type': 'BUY', 'strategy': 'Stochastic', 'symbol': symbol, 'timeframe': timeframe})
        elif k < d and pk >= pd_val and k > 65:
            signals.append({'type': 'SELL', 'strategy': 'Stochastic', 'symbol': symbol, 'timeframe': timeframe})
    
    # Bollinger Bounce
    if 'bb_lower' in df.columns:
        if df['low'].iloc[-1] <= df['bb_lower'].iloc[-1] and df['close'].iloc[-1] > df['open'].iloc[-1]:
            signals.append({'type': 'BUY', 'strategy': 'Bollinger Bounce', 'symbol': symbol, 'timeframe': timeframe})
        elif df['high'].iloc[-1] >= df['bb_upper'].iloc[-1] and df['close'].iloc[-1] < df['open'].iloc[-1]:
            signals.append({'type': 'SELL', 'strategy': 'Bollinger Bounce', 'symbol': symbol, 'timeframe': timeframe})
    
    # Add price and indicators to signals
    price = df['close'].iloc[-1]
    atr = df['atr'].iloc[-1] if 'atr' in df.columns else price * 0.02
    
    for sig in signals:
        sig['price'] = price
        sig['atr'] = atr
        sig['timestamp'] = datetime.now()
        
        # Calculate targets
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
        
        # Position sizing
        risk_amount = TRADING_CONFIG['initial_capital'] * TRADING_CONFIG['risk_per_trade']
        risk_per_share = abs(price - sig['stop_loss'])
        sig['shares'] = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        sig['position_value'] = round(sig['shares'] * price, 2)
        sig['risk_amount'] = round(risk_amount, 2)
        sig['risk_reward'] = round(TRADING_CONFIG['reward_ratio'], 1)
        
        # Strength
        strength = 3
        if 'rsi' in df.columns and 40 < df['rsi'].iloc[-1] < 60:
            strength += 0.5
        if 'volume_ratio' in df.columns and df['volume_ratio'].iloc[-1] > 1.2:
            strength += 0.5
        if 'adx' in df.columns and df['adx'].iloc[-1] > 25:
            strength += 0.5
        sig['strength'] = min(5, int(strength))
        
        # Indicators status
        sig['indicators'] = {}
        if 'rsi' in df.columns:
            rsi = df['rsi'].iloc[-1]
            sig['indicators']['rsi'] = {'value': round(rsi, 1), 'status': 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'}
        if 'macd_hist' in df.columns:
            sig['indicators']['macd'] = {'value': round(df['macd_hist'].iloc[-1], 3), 'status': 'positive' if df['macd_hist'].iloc[-1] > 0 else 'negative'}
        if 'volume_ratio' in df.columns:
            sig['indicators']['volume'] = {'value': round(df['volume_ratio'].iloc[-1], 2), 'status': 'high' if df['volume_ratio'].iloc[-1] > 1.2 else 'normal'}
        if 'adx' in df.columns:
            sig['indicators']['adx'] = {'value': round(df['adx'].iloc[-1], 1), 'status': 'strong' if df['adx'].iloc[-1] > 25 else 'weak'}
    
    return signals

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
    
    st.markdown(f"### 📍 {t('dashboard')}")
    
    pages = {
        'dashboard': f"🏠 {t('dashboard')}",
        'signals': f"🔔 {t('signals')}",
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
    
    if is_market_open():
        st.success(f"🟢 {t('market_open')}")
    else:
        st.warning(f"🔴 {t('market_closed')}")

# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_dashboard():
    st.markdown(f'<div class="main-header">🎯 {t("app_title")}</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(f"🔔 {t('new_signals')}", len(st.session_state.signals))
    
    with col2:
        st.metric(f"📈 {t('open_positions')}", 0)
    
    with col3:
        account = get_account_info()
        if account:
            st.metric(f"💰 {t('capital')}", f"${account['equity']:,.0f}")
        else:
            st.metric(f"💰 {t('capital')}", "$100,000")
    
    with col4:
        st.metric(f"🎯 {t('win_rate')}", "--")
    
    st.markdown("---")
    
    # Scan Controls
    col1, col2 = st.columns([1, 2])
    
    with col1:
        scan_btn = st.button(f"🔍 {t('scan_now')}", use_container_width=True, type="primary")
    
    with col2:
        timeframes = st.multiselect(
            t('timeframe'),
            ['1hour', '4hour', '1day'],
            default=['1day'],
            format_func=lambda x: {'1hour': '1H', '4hour': '4H', '1day': 'Daily'}[x]
        )
    
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
            
            st.session_state.signals = signals
            st.session_state.last_scan = datetime.now()
            progress.empty()
            st.rerun()
    
    st.markdown("---")
    st.subheader(f"🔔 {t('signals')}")
    
    if not st.session_state.signals:
        st.info(f"ℹ️ {t('no_signals')} - Press '{t('scan_now')}' to search")
    else:
        buy_signals = [s for s in st.session_state.signals if s['type'] == 'BUY']
        sell_signals = [s for s in st.session_state.signals if s['type'] == 'SELL']
        
        tab1, tab2, tab3 = st.tabs([f"🟢 {t('buy')} ({len(buy_signals)})", 
                                     f"🔴 {t('sell')} ({len(sell_signals)})",
                                     f"📋 {t('all')} ({len(st.session_state.signals)})"])
        
        with tab1:
            for sig in buy_signals[:10]:
                render_signal_card(sig)
        
        with tab2:
            for sig in sell_signals[:10]:
                render_signal_card(sig)
        
        with tab3:
            for sig in st.session_state.signals[:15]:
                render_signal_card(sig)

def render_signal_card(signal):
    is_buy = signal['type'] == 'BUY'
    emoji = '🟢' if is_buy else '🔴'
    badge = 'buy-badge' if is_buy else 'sell-badge'
    signal_text = t('buy') if is_buy else t('sell')
    
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"### {emoji} {signal['symbol']}")
            st.markdown(f'<span class="{badge}">{signal_text}</span>', unsafe_allow_html=True)
            st.markdown(f"**{t('strategy')}:** {signal['strategy']}")
            st.markdown(f"**{t('timeframe')}:** {signal['timeframe']}")
            st.markdown(f"**{t('signal_strength')}:** {get_stars(signal['strength'])}")
        
        with col2:
            st.markdown(f"""
            **{t('entry_price')}:** ${signal['price']:.2f}  
            **{t('stop_loss')}:** ${signal['stop_loss']:.2f} (-{signal['stop_loss_pct']:.1f}%)  
            **{t('target')} 1:** ${signal['target1']:.2f} (+{signal['target1_pct']:.1f}%)  
            **{t('target')} 2:** ${signal['target2']:.2f} (+{signal['target2_pct']:.1f}%)  
            **R:R:** 1:{signal['risk_reward']:.1f}
            """)
        
        with col3:
            st.markdown(f"""
            **{t('shares')}:** {signal['shares']}  
            **{t('position_size')}:** ${signal['position_value']:,.0f}  
            **{t('risk_per_trade')}:** ${signal['risk_amount']:.0f}
            """)
        
        with st.expander(f"📊 {t('supporting_indicators')}"):
            ind = signal.get('indicators', {})
            cols = st.columns(4)
            if 'rsi' in ind:
                cols[0].metric("RSI", ind['rsi']['value'], ind['rsi']['status'])
            if 'macd' in ind:
                cols[1].metric("MACD", ind['macd']['value'], ind['macd']['status'])
            if 'volume' in ind:
                cols[2].metric(t('volume'), ind['volume']['value'], ind['volume']['status'])
            if 'adx' in ind:
                cols[3].metric("ADX", ind['adx']['value'], ind['adx']['status'])
        
        st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# Signals Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_signals():
    st.title(f"🔔 {t('signals')}")
    
    if not st.session_state.signals:
        st.info(t('no_signals'))
        return
    
    # Table view
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
    
    st.markdown("---")
    for sig in st.session_state.signals:
        render_signal_card(sig)

# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_analysis():
    st.title(f"📊 {t('analysis')}")
    
    st.subheader("⭐ Top Stocks")
    st.write(", ".join(TOP_STOCKS))
    
    st.markdown("---")
    
    st.subheader("📈 Strategies")
    strategies = [
        {'Strategy': 'MA Crossover', 'Win Rate': '55%', 'Avg Return': '7.5%'},
        {'Strategy': 'MACD', 'Win Rate': '52%', 'Avg Return': '5.5%'},
        {'Strategy': 'RSI Reversal', 'Win Rate': '50%', 'Avg Return': '5.0%'},
        {'Strategy': 'Stochastic', 'Win Rate': '53%', 'Avg Return': '6.0%'},
        {'Strategy': 'Bollinger Bounce', 'Win Rate': '48%', 'Avg Return': '4.5%'}
    ]
    st.dataframe(pd.DataFrame(strategies), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Settings Page
# ═══════════════════════════════════════════════════════════════════════════════
def show_settings():
    st.title(f"⚙️ {t('settings')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"💰 {t('capital')}")
        st.number_input(t('capital'), value=100000, min_value=1000, max_value=10000000, step=1000)
        st.slider(t('risk_per_trade'), 0.5, 5.0, 2.0, 0.5, format="%.1f%%")
        st.slider("Reward:Risk", 1.0, 5.0, 2.5, 0.5)
    
    with col2:
        st.subheader(f"📊 {t('timeframe')}")
        st.checkbox("1 Hour", value=True)
        st.checkbox("4 Hours", value=True)
        st.checkbox("Daily", value=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Main Router
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == 'dashboard':
    show_dashboard()
elif st.session_state.page == 'signals':
    show_signals()
elif st.session_state.page == 'analysis':
    show_analysis()
elif st.session_state.page == 'settings':
    show_settings()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Trading Dashboard v1.0 | ⚠️ للأغراض التعليمية فقط"
    "</div>",
    unsafe_allow_html=True
)
