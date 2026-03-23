import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- 共通シミュレーション関数 (US糖尿病市場カスタマイズ) ---
def calculate_market_share(my_price, comp_prices, max_s, min_s, sensitivity):
    avg_comp_price = np.mean(comp_prices)
    price_ratio = my_price / avg_comp_price
    # 糖尿病薬はスイッチングコストがある程度あるが、PBMの介入(価格)に敏感
    relative_share = 1 / (1 + np.exp(sensitivity * (price_ratio - 1.05))) # 5%程度のプレミアムなら維持できる想定
    return min_s + (max_s - min_s) * relative_share

def run_diabetes_simulation(launch_price_range, comp_prices, max_share, min_share, sensitivity, cogs):
    iterations = 200
    market_duration = 36 # 3年間の推移を想定
    results = []

    for lp in launch_price_range:
        trial_profits = []
        for _ in range(iterations):
            my_price = lp
            current_comp_prices = list(comp_prices)
            total_profit = 0
            
            for _ in range(market_duration):
                # 論文にある「A-price（最安値）への執着」を競合の動きに反映
                for i in range(len(current_comp_prices)):
                    if current_comp_prices[i] > my_price: # 自社が最安値なら競合は値下げ
                        current_comp_prices[i] *= np.random.uniform(0.97, 1.0)
                    else: # 競合が安ければ現状維持または微増
                        current_comp_prices[i] *= np.random.uniform(1.0, 1.03)
                
                share = calculate_market_share(my_price, current_comp_prices, max_share, min_share, sensitivity)
                # 糖尿病薬はリベート(GTN)が大きいため、cogsを「売上の50%」などの変数として扱うことも多いが、今回は固定
                total_profit += (my_price - cogs) * share
            
            trial_profits.append(total_profit)
        results.append(np.mean(trial_profits))
    return results

# --- 設定値 ---
test_prices = np.arange(10000, 25001, 500)
cogs_diabetes = 6000 # 高額なリベートや製造コストを合算

# シナリオ1: Me-too薬（既存薬と大差ない新薬）
# PBMの交渉力が強く、価格が高くなると即座にフォーミュラリーから外される
res_std = run_diabetes_simulation(
    test_prices, comp_prices=[15000], 
    max_share=0.4, min_share=0.02, sensitivity=10.0 # 感受性が高い
    , cogs=cogs_diabetes
)

# シナリオ2: 画期的な新薬（心血管イベント抑制データなど圧倒的な臨床的優位性）
# 医師の選好が強く、PBMも外しにくい。高値でも一定のシェアを維持。
res_high_val = run_diabetes_simulation(
    test_prices, comp_prices=[15000], 
    max_share=0.7, min_share=0.25, sensitivity=4.5 # 感受性が低い
    , cogs=cogs_diabetes
)

# --- 可視化 ---
plt.figure(figsize=(12, 7))
plt.plot(test_prices, res_std, label="Standard Diabetes Drug (Me-too)", color='royalblue', lw=2)
plt.plot(test_prices, res_high_val, label="Next-Gen Breakthrough (High Value)", color='crimson', lw=2)

# 最適解（ピーク）の強調
for res, label, col in zip([res_std, res_high_val], ["Standard", "High Value"], ['royalblue', 'crimson']):
    idx = np.argmax(res)
    plt.annotate(f'Best {label}: ${test_prices[idx]}', (test_prices[idx], res[idx]), 
                 xytext=(test_prices[idx]-2000, res[idx]*1.05), arrowprops=dict(arrowstyle='->', color=col))

plt.title('Diabetes Market: Launch Price vs 3yr Expected Profit', fontsize=14)
plt.xlabel('Launch Price (Annual WAC $)', fontsize=12)
plt.ylabel('Expected Cumulative Profit', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()