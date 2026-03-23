import numpy as np
import pandas as pd

class CompetitorAgent:
    def __init__(self, name, size, initial_price):
        self.name = name
        self.size = size  # 'Large' or 'Small'
        self.current_price = initial_price
        self.has_a_price = False  # 市場最安値を保持しているか
        
        # 論文の知見に基づいた行動確率の設定
        # [価格を上げる, 価格を下げる, 維持する]
        if size == 'Large':
            # 大手は価格を維持する傾向が強く、下げる場合は慎重
            self.prob_if_a_price = [0.05, 0.05, 0.90]
            self.prob_if_not_a_price = [0.10, 0.40, 0.50]
        else:
            # 小規模はシェア奪取のため、最安値でない場合に激しく価格を下げる
            self.prob_if_a_price = [0.10, 0.50, 0.40]
            self.prob_if_not_a_price = [0.05, 0.70, 0.25]

    def decide_price_change(self):
        # 現在のステータスに応じて次の行動を選択
        probs = self.prob_if_a_price if self.has_a_price else self.prob_if_not_a_price
        action = np.random.choice(['increase', 'decrease', 'keep'], p=probs)
        
        adjustment = 0
        if action == 'increase':
            adjustment = np.random.uniform(0.01, 0.03) # 1-3%上昇
        elif action == 'decrease':
            adjustment = -np.random.uniform(0.01, 0.05) # 1-5%下落
            
        self.current_price *= (1 + adjustment)
        return self.current_price

class MarketEnvironment:
    def __init__(self, competitors):
        self.competitors = competitors

    def update_market_status(self):
        # 市場での最安値を特定し、各エージェントのステータスを更新
        prices = [c.current_price for c in self.competitors]
        min_price = min(prices)
        for c in self.competitors:
            # 誤差を考慮して最安値を判定
            c.has_a_price = (c.current_price <= min_price * 1.001)

def objective_function(launch_price, iterations=100):
    """
    特定のローンチ価格を設定した際の、期待収益をシミュレーションする
    """
    total_revenues = []
    
    for _ in range(iterations):
        # 毎回市場を初期化
        me = CompetitorAgent("My_Drug", "Large", launch_price)
        comp1 = CompetitorAgent("Comp_A", "Large", 100) # 既存大手
        comp2 = CompetitorAgent("Comp_B", "Small", 95)  # 既存小規模
        
        market = MarketEnvironment([me, comp1, comp2])
        
        step_revenue = 0
        # 24期間（例：2週間×24＝約1年間）のシミュレーション
        for _ in range(24):
            market.update_market_status()
            for c in market.competitors:
                c.decide_price_change()
                
                # 自社製品（My_Drug）の収益計算
                if c.name == "My_Drug":
                    # 簡易的なシェアモデル：最安値ならシェア60%、そうでなければ20%
                    share = 0.6 if c.has_a_price else 0.2
                    step_revenue += c.current_price * share
        
        total_revenues.append(step_revenue)
    
    return np.mean(total_revenues)

# --- メイン実行部分 ---
if __name__ == "__main__":
    print("--- 薬価ローンチ戦略シミュレーション開始 ---")
    print("各ローンチ価格における1年間の期待累積収益を計算します...\n")
    
    results = []
    # 90ドルから130ドルまで10ドル刻みで検証
    test_prices = [90, 100, 110, 120, 130]
    
    for p in test_prices:
        rev = objective_function(p, iterations=200) # 精度のため200回試行
        results.append({"Launch Price": p, "Expected Revenue": rev})
        print(f"検証中: ローンチ価格 ${p} -> 期待収益: {rev:.2f}")

    # 結果をデータフレームで表示
    df_results = pd.DataFrame(results)
    best_strategy = df_results.loc[df_results['Expected Revenue'].idxmax()]
    
    print("\n--- シミュレーション結果まとめ ---")
    print(df_results.to_string(index=False))
    print(f"\n推奨戦略: ローンチ価格 ${best_strategy['Launch Price']} (最大収益: {best_strategy['Expected Revenue']:.2f})")