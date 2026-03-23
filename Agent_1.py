import numpy as np
import pandas as pd

class CompetitorAgent:
    def __init__(self, name, size, initial_price):
        self.name = name
        self.size = size  # 'Large', 'Medium', 'Small' [cite: 938]
        self.current_price = initial_price
        self.has_a_price = False  # 最安値（A-price）を保持しているか [cite: 585]
        
        # 論文に基づいた行動確率の設定（例示） [cite: 586, 588]
        # [価格を上げる, 下げる, 維持する] の確率
        if size == 'Large':
            self.prob_if_a_price = [0.05, 0.05, 0.90]  # 大手は価格を維持しやすい [cite: 558]
            self.prob_if_not_a_price = [0.10, 0.40, 0.50]
        else:
            self.prob_if_a_price = [0.10, 0.50, 0.40]  # 小規模はシェア奪取のため下げやすい [cite: 556]
            self.prob_if_not_a_price = [0.05, 0.70, 0.25]

    def decide_price_change(self):
        # 現在のステータスに応じてアクションを選択 [cite: 605]
        probs = self.prob_if_a_price if self.has_a_price else self.prob_if_not_a_price
        action = np.random.choice(['increase', 'decrease', 'keep'], p=probs)
        
        # 変動幅の決定（論文ではカーネル密度推定等を使用） [cite: 590]
        adjustment = 0
        if action == 'increase':
            adjustment = np.random.uniform(0.01, 0.05) # 1-5%上昇
        elif action == 'decrease':
            adjustment = -np.random.uniform(0.01, 0.10) # 1-10%下落
            
        self.current_price *= (1 + adjustment)
        return self.current_price

class MarketEnvironment:
    def __init__(self, competitors):
        self.competitors = competitors

    def update_market_status(self):
        # 市場での最安値（A-price）を特定し、各エージェントのステータスを更新 [cite: 605]
        prices = [c.current_price for c in self.competitors]
        min_price = min(prices)
        for c in self.competitors:
            c.has_a_price = (c.current_price == min_price)

# --- シミュレーションの実行 ---
# 1. 競合エージェントの初期化
comp1 = CompetitorAgent("Comp_Large", "Large", 100)
comp2 = CompetitorAgent("Comp_Small", "Small", 95)
market = MarketEnvironment([comp1, comp2])

# 2. 12ヶ月分（24隔週）のシミュレーション
history = []
for step in range(24):
    market.update_market_status()
    current_prices = {c.name: c.decide_price_change() for c in market.competitors}
    history.append(current_prices)

df_res = pd.DataFrame(history)
print(df_res.head())