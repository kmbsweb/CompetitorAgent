import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class CompetitorAgent:
    def __init__(self, name, initial_price, probs_a, probs_not_a):
        self.name = name
        self.current_price = initial_price
        self.has_a_price = False
        self.prob_if_a_price = probs_a
        self.prob_if_not_a_price = probs_not_a

    def decide_price_change(self):
        probs = self.prob_if_a_price if self.has_a_price else self.prob_if_not_a_price
        action = np.random.choice(['increase', 'decrease', 'keep'], p=probs)
        adj = 0
        if action == 'increase': adj = np.random.uniform(0.01, 0.03)
        elif action == 'decrease': adj = -np.random.uniform(0.01, 0.05)
        self.current_price *= (1 + adj)
        return self.current_price

def run_scenario(
    market_duration,       # 1: 市場持続期間 (回数)
    high_share,            # 2: 最安値時のシェア (0.0~1.0)
    low_share,             # 2: 非最安値時のシェア (0.0~1.0)
    comp_probs_a,          # 3: 競合の確率(最安値時) [UP, DOWN, KEEP]
    comp_probs_not_a,      # 3: 競合の確率(非最安値時)
    comp_initial_prices,   # 4: 競合の初期価格リスト [p1, p2, ...]
    iterations=200
):
    prices_to_test = np.arange(70, 151, 5)
    results = []

    for lp in prices_to_test:
        trial_revs = []
        for _ in range(iterations):
            # 自社エージェント
            me = CompetitorAgent("My_Drug", lp, [0.05, 0.05, 0.90], [0.10, 0.30, 0.60])
            # 競合エージェント
            competitors = [me]
            for i, p_init in enumerate(comp_initial_prices):
                competitors.append(CompetitorAgent(f"Comp_{i}", p_init, comp_probs_a, comp_probs_not_a))
            
            total_rev = 0
            for _ in range(market_duration):
                prices = [c.current_price for c in competitors]
                min_p = min(prices)
                for c in competitors:
                    c.has_a_price = (c.current_price <= min_p * 1.001)
                    c.decide_price_change()
                    if c.name == "My_Drug":
                        share = high_share if c.has_a_price else low_share
                        total_rev += c.current_price * share
            trial_revs.append(total_rev)
        results.append(np.mean(trial_revs))
    
    return prices_to_test, results

# --- 実行とグラフ表示 ---
plt.figure(figsize=(12, 7))

# シナリオ設定例
# 1. 標準 (1年, シェア高, 競合穏やか, 初期値100/95)
p1, r1 = run_scenario(24, 0.6, 0.2, [0.05, 0.1, 0.85], [0.1, 0.4, 0.5], [100, 95])
plt.plot(p1, r1, label="Standard (1yr)", marker='o')

# 2. 悲観 (1年, シェア低, 競合攻撃的, 初期値95/90)
p2, r2 = run_scenario(24, 0.4, 0.1, [0.01, 0.5, 0.49], [0.01, 0.9, 0.09], [95, 90])
plt.plot(p2, r2, label="Aggressive Comp / Low Share", marker='s')

# 3. 長期 (3年=72回, シェア高)
p3, r3 = run_scenario(72, 0.6, 0.2, [0.05, 0.1, 0.85], [0.1, 0.4, 0.5], [100, 95])
plt.plot(p3, r3, label="Long-term (3yr)", marker='^')

plt.title('Sensitivity Analysis of Drug Launch Pricing')
plt.xlabel('Launch Price ($)')
plt.ylabel('Expected Revenue')
plt.legend()
plt.grid(True, linestyle='--')

# 結果の保存 (CSV)
df_out = pd.DataFrame({"Price": p1, "Standard": r1, "Aggressive": r2, "LongTerm": r3})
df_out.to_csv("simulation_results.csv", index=False)
print("CSV saved: simulation_results.csv")

plt.show()