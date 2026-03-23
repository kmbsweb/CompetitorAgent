import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_generalized_simulation(
    test_prices,        # 検証する価格帯 (list/array)
    comp_prices,        # 競合他社の現在価格 (list)
    max_share,          # 最安値時の到達可能シェア上限
    min_share,          # 高価格時の維持可能シェア下限
    sensitivity,        # 価格感受性 (K値: 高いほど価格でシェアが動く)
    cogs,               # 実質単価コスト (製造 + リベート)
    market_duration=24, # 期間 (月次想定)
    iterations=100      # 試行回数
):
    results = []

    for lp in test_prices:
        trial_profits = []
        for _ in range(iterations):
            my_p = lp
            c_prices = list(comp_prices)
            total_profit = 0
            
            for _ in range(market_duration):
                # 論文の知見: 競合の動的反応 (A-price獲得状況による変動)
                avg_comp = np.mean(c_prices)
                for i in range(len(c_prices)):
                    # 競合は最安値を奪われていると値下げ確率が上がる(論文ロジック)
                    if c_prices[i] > my_p:
                        c_prices[i] *= np.random.uniform(0.98, 1.0)
                    else:
                        c_prices[i] *= np.random.uniform(1.0, 1.02)
                
                # シェア計算: シグモイド関数による滑らかな遷移
                price_ratio = my_p / np.mean(c_prices)
                rel_s = 1 / (1 + np.exp(sensitivity * (price_ratio - 1.05)))
                share = min_share + (max_share - min_share) * rel_s
                
                # 累積利益の加算
                total_profit += (my_p - cogs) * share
                
            trial_profits.append(total_profit)
        results.append(np.mean(trial_profits))
    
    return results

# --- シミュレーション実行と複数ケース比較 ---
test_range = np.arange(5000, 20001, 500)

# Case A: 生活習慣病薬 (高競争・高リベート・高感受性)
res_a = run_generalized_simulation(test_range, [12000], 0.40, 0.02, 12.0, 6000)

# Case B: スペシャリティ/希少疾患 (低競争・低リベート・低感受性)
res_b = run_generalized_simulation(test_range, [12000], 0.70, 0.25, 4.0, 2000)

# Case C: バイオシミラー (価格破壊・高シェア狙い)
res_c = run_generalized_simulation(test_range, [12000], 0.85, 0.00, 15.0, 1000)

# --- 可視化 ---
plt.figure(figsize=(10, 6))
plt.plot(test_range, res_a, label="Case A: Mass Market", lw=2)
plt.plot(test_range, res_b, label="Case B: Specialty/Rare", lw=2)
plt.plot(test_range, res_c, label="Case C: Biosimilar", lw=2)

plt.title("Generalized Drug Pricing Optimizer", fontsize=14)
plt.xlabel("Launch Price ($)")
plt.ylabel("Expected Cumulative Profit")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()