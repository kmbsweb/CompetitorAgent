import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import gaussian_kde

# --- ページ設定 ---
st.set_page_config(page_title="Pharma Strategic Pricing Optimizer", layout="wide")

# タイトルを最上部に表示
st.title("Pharma Strategic Pricing Optimizer")

# ==========================================
# 1. データベース層 (Navlin Mock Data)
# ==========================================
@st.cache_resource
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.execute("CREATE TABLE navlin (drug TEXT, date DATE, price REAL)")
    
    drugs = ['Enhertu-like', 'Opdivo-like', 'Cyramza-like', 'Generic-A']
    data = []
    dates = pd.date_range(start='2024-01-01', periods=24, freq='ME')
    
    for d in drugs:
        base_p = 21000 if 'Enhertu' in d else 18500 if 'Opdivo' in d else 14500 if 'Cyramza' in d else 3500
        current_p = base_p
        for dt in dates:
            if np.random.rand() < 0.15: # 過去の不定期な値下げイベント
                current_p *= np.random.uniform(0.96, 0.99)
            data.append((d, dt.date(), round(current_p, 2)))
            
    conn.executemany("INSERT INTO navlin VALUES (?,?,?)", data)
    return conn

conn = init_db()

# ==========================================
# 2. KDE計算 & ABMシミュレーション・エンジン
# ==========================================
def get_kde_from_history(drug_name):
    df = pd.read_sql(f"SELECT price FROM navlin WHERE drug='{drug_name}' ORDER BY date", conn)
    pct_changes = df['price'].pct_change().dropna()
    changes = pct_changes[pct_changes != 0]
    
    if len(changes) < 2:
        return lambda: -np.random.uniform(0.01, 0.04) # デフォルト
    
    kde = gaussian_kde(changes)
    return lambda: kde.resample(1)[0][0]

def run_abm_simulation(test_prices, market_size, cogs, duration, n_trials, our_cfg, c1_cfg, c2_cfg):
    results = []
    kde_func1 = get_kde_from_history(c1_cfg['name'])
    kde_func2 = get_kde_from_history(c2_cfg['name'])

    for lp in test_prices:
        trial_profits = []
        for _ in range(n_trials):
            p_self = lp
            p_c1, p_c2 = c1_cfg['start_p'], c2_cfg['start_p']
            total_profit = 0
            
            for m in range(duration):
                # 競合エージェントの行動ルール
                if p_c1 > min(p_self, p_c2): # NA-price
                    if np.random.rand() < 0.35: p_c1 *= (1 + kde_func1())
                elif np.random.rand() < 0.05: p_c1 *= (1 + kde_func1())
                
                if p_c2 > min(p_self, p_c1): # NA-price
                    if np.random.rand() < 0.35: p_c2 *= (1 + kde_func2())
                elif np.random.rand() < 0.05: p_c2 *= (1 + kde_func2())

                # 市場シェア計算 (Sigmoid)
                min_comp_p = min(p_c1, p_c2)
                ratio = p_self / min_comp_p
                base_s = 1 / (1 + np.exp(our_cfg['k'] * (ratio - 1.05)))
                share = our_cfg['min_s'] + (our_cfg['max_s'] - our_cfg['min_s']) * base_s
                
                total_profit += (p_self - cogs) * (share * market_size)
            
            trial_profits.append(total_profit)
        results.append({
            'LaunchPrice': lp,
            'ExpectedProfit': np.mean(trial_profits),
            'LowerCI': np.percentile(trial_profits, 2.5),
            'UpperCI': np.percentile(trial_profits, 97.5)
        })
    return pd.DataFrame(results)

# ==========================================
# 3. UI 構成
# ==========================================
# --- Sidebar ---
with st.sidebar:
    st.header("🌐 Global Configuration")
    sim_duration = st.slider("Simulate Duration (Months)", 12, 60, 24, help="発売からシミュレーションを終了するまでの月数です。")
    market_size = st.number_input("Market Size (Patients)", value=10000, help="対象となる市場の総患者数（ポテンシャル）です。")
    unit_cogs = st.number_input("Unit COGS / Net Rebate ($)", value=5000, help="1単位あたりの製造原価および平均的なリベートを差し引いた実質単価です。")
    mc_trials = st.slider("Monte Carlo Trials", 50, 500, 100, help="競合の反応パターンの試行回数です。多いほど精度が上がりますが計算時間がかかります。")

tab1, tab2, tab3 = st.tabs(["🚀 Simulator", "📊 Data Explorer", "📚 Methodology"])

# 最新価格データの取得
df_latest = pd.read_sql("SELECT drug, price FROM navlin GROUP BY drug HAVING date = MAX(date)", conn)
drug_list = df_latest['drug'].tolist()
price_map = df_latest.set_index('drug')['price'].to_dict()

# --- Tab 1: Simulator ---
with tab1:
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("Our Drug")
        p_min = st.number_input("Launch Price Min ($)", value=5000, help="シミュレーションを開始する最低価格。")
        p_max = st.number_input("Launch Price Max ($)", value=40000, help="シミュレーションを終了する最高価格。")
        p_step = st.number_input("Price Increment Step ($)", value=2000, help="価格帯を刻む間隔。小さいほどグラフが滑らかになります。")
        s_max = st.slider("Max Share", 0.0, 1.0, 0.4, key="smax", help="自社が最安値で市場を圧倒した場合に獲得できるシェアの上限値です。")
        s_min = st.slider("Min Share", 0.0, 0.5, 0.05, key="smin", help="自社が高値であっても、ブランド選好により維持できる最低限のシェアです。")
        s_k = st.slider("Sensitivity (k)", 1.0, 20.0, 8.0, key="sk", help="価格差に対する市場の敏感度。高いほど価格差でシェアが急変します。")

    with c2:
        st.subheader("Comp Drug 1")
        comp1_name = st.selectbox("Select Benchmark Drug 1", drug_list, index=0, help="比較対象とする競合薬剤を選択します。")
        comp1_p = st.number_input("Current WAC ($) - C1", value=price_map[comp1_name], key="cp1", help="競合薬1の現在の公定価格です。")
        c1_max = st.slider("Max Share (C1)", 0.0, 1.0, 0.3, key="c1max", help="競合1が市場で持ちうる最大の影響力です。")
        c1_k = st.slider("Sensitivity (C1)", 1.0, 20.0, 8.0, key="c1k", help="競合1の顧客がどれだけ価格で他剤へ流出しやすいかを示します。")

    with c3:
        st.subheader("Comp Drug 2")
        comp2_name = st.selectbox("Select Benchmark Drug 2", drug_list, index=1, help="2つ目の比較対象薬剤を選択します。")
        comp2_p = st.number_input("Current WAC ($) - C2", value=price_map[comp2_name], key="cp2", help="競合薬2の現在の公定価格です。")
        c2_max = st.slider("Max Share (C2)", 0.0, 1.0, 0.3, key="c2max", help="競合2が市場で持ちうる最大の影響力です。")
        c2_k = st.slider("Sensitivity (C2)", 1.0, 20.0, 8.0, key="c2k", help="競合2の顧客の価格感受性です。")

    st.divider()
    
    if st.button("🔥 Run Strategic Simulation", use_container_width=True):
        test_prices = np.arange(p_min, p_max + 1, p_step)
        our_cfg = {'max_s': s_max, 'min_s': s_min, 'k': s_k}
        c1_cfg = {'name': comp1_name, 'start_p': comp1_p}
        c2_cfg = {'name': comp2_name, 'start_p': comp2_p}
        
        with st.spinner("Analyzing competitive response via KDE..."):
            df_res = run_abm_simulation(test_prices, market_size, unit_cogs, sim_duration, mc_trials, our_cfg, c1_cfg, c2_cfg)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_res['LaunchPrice'], y=df_res['UpperCI'], line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=df_res['LaunchPrice'], y=df_res['LowerCI'], fill='tonexty', fillcolor='rgba(0,255,150,0.1)', line=dict(width=0), name='95% Confidence Interval'))
        fig.add_trace(go.Scatter(x=df_res['LaunchPrice'], y=df_res['ExpectedProfit'], line=dict(color='#00FF96', width=4), mode='lines+markers', name='Expected Cumulative Profit'))
        
        fig.update_layout(title="Risk-Adjusted Profit Optimization Curve", xaxis_title="Our Launch Price (WAC $)", yaxis_title="Expected Total Profit ($)", height=700, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        csv = df_res.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results (CSV)", data=csv, file_name="pricing_analysis.csv", mime="text/csv")

# --- Tab 2: Data Explorer ---
with tab2:
    st.header("Navlin Historical Price Trends")
    sel_drug = st.selectbox("Select Drug to Inspect", drug_list)
    df_hist = pd.read_sql(f"SELECT * FROM navlin WHERE drug='{sel_drug}'", conn)
    fig_h = px.line(df_hist, x='date', y='price', title=f"WAC Trend: {sel_drug}", markers=True, height=500)
    fig_h.update_layout(template="plotly_dark")
    st.plotly_chart(fig_h, use_container_width=True)
    st.dataframe(df_hist, use_container_width=True)

# --- Tab 3: Methodology ---
with tab3:
    st.header("Methodology & User Guide")
    st.info("""
    ### 📝 シミュレーターの正しい使い方・ワークフロー
    このツールは、自社のローンチ価格が市場全体の価格競争をどう引き起こすかを予測します。
    1. **市場背景の確認 (Tab 2)**: 競合の過去の値下げ頻度を確認。
    2. **基本条件の設定 (Sidebar)**: 市場規模や期間を定義。
    3. **シナリオ設定 (Tab 1)**: 自社(Our Drug)の目標値と、競合(Comp Drug 1/2)の現況を入力。
    4. **実行と判断**: 頂点（期待値最大）かつ影の幅（リスク）が小さい価格を特定します。
    """)
    st.markdown("""
    ### 🔬 ABM計算原理
    - **エージェント行動**: 競合薬は「最安値」を奪われると35%の確率で反撃（値下げ）を行います。
    - **KDEロジック**: 値下げ幅は、Tab 2の過去データから抽出された確率密度関数に基づき決定されます。
    - **シグモイドシェア関数**: 価格差に対するシェアの移動を数理的にモデル化しています。
    """)