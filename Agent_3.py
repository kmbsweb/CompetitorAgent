import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- 前述の Agentクラスと Environmentクラスは同じ ---
class CompetitorAgent:
    def __init__(self, name, size, initial_price, probs_a=None, probs_not_a=None):
        self.name = name
        self.current_price = initial_price
        self.has_a_price = False
        # 引数で行動確率をカスタマイズ可能に
        self.prob_if_a_price = probs_a or ([0.05, 0.05, 0.90] if size == 'Large' else [0.10, 0.50, 0.40])
        self.prob_if_not_a_price = probs_not_a or ([0.10, 0.40, 0.50] if size == 'Large' else [0.05, 0.70, 0.25])

    def decide_price_change(self):
        probs = self.prob_if_a_price if self.has_a_price else self.prob_if_not_a_price
        action = np.random.choice(['increase', 'decrease', 'keep'], p=probs)
        adj = 0
        if action == 'increase': adj = np.random.uniform(0.01, 0.03)
        elif action == 'decrease': adj = -np.random.uniform(0.01, 0.05)
        self.current_price *= (1 + adj)
        return self.current_price

class MarketEnvironment:
    def __init__(self, competitors):
        self.competitors = competitors
    def update_market_status(self):
        min_p = min([c.current_price for c in self.competitors])
        for c in self.competitors:
            c.has_a_price = (c.current_price <= min_p * 1.001)

# --- 収益計算関数（引数を追加） ---
def simulate_revenue(launch_price, iterations=100, market_duration=24, high_share=0.6, low_share=0.2):
    total_revenues = []
    for _ in range(iterations):
        me = CompetitorAgent("My_Drug", "Large", launch_price)
        comp1 = CompetitorAgent("Comp_A", "Large", 100)
        comp2 = CompetitorAgent("Comp_B", "Small", 95)
        market = MarketEnvironment([me, comp1, comp2])
        
        step_rev = 0
        for _ in range(market_duration):
            market.update_market_status()
            for c in market.competitors:
                c.decide_price_change()
                if c.name == "My_Drug":
                    share = high_share if c.has_a_price else low_share
                    step_rev += c.current_price * share
        total_revenues.append(step_rev)
    return np.mean(total_revenues)

# --- 実行と可視化 ---
def run_analysis():
    # ユーザーが変更可能なパラメータ
    prices_to_test = np.arange(80, 151, 5) # 80ドルから150ドルまで5ドル刻み
    num_iter = 200                         # 試行回数
    
    print(f"シミュレーション実行中（試行回数: {num_iter}）...")
    results = []
    for p in prices_to_test:
        avg_rev = simulate_revenue(p, iterations=num_iter)
        results.append(avg_rev)
    
    # グラフ表示
    plt.figure(figsize=(10, 6))
    plt.plot(prices_to_test, results, marker='o', linestyle='-', color='b')
    plt.title('Launch Price vs. Expected 1yr Revenue', fontsize=14)
    plt.xlabel('Launch Price ($)', fontsize=12)
    plt.ylabel('Expected Cumulative Revenue', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 最大値の強調
    max_rev = max(results)
    best_p = prices_to_test[results.index(max_rev)]
    plt.annotate(f'Optimal: ${best_p}\nRev: {max_rev:.1f}', 
                 xy=(best_p, max_rev), xytext=(best_p+10, max_rev-10),
                 arrowprops=dict(facecolor='red', shrink=0.05))
    
    plt.show()

if __name__ == "__main__":
    run_analysis()