# Visibility Portfolio Optimization (Benefit Estimation + Knapsack ILP)

import pickle
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import pulp

# 1. Load Data

with open('supply_network.pkl', 'rb') as f:
    G = pickle.load(f)

with open('baseline_results.pkl', 'rb') as f:
    baseline_data = pickle.load(f)

baseline_losses = baseline_data['losses']
baseline_expected_loss = np.mean(baseline_losses)
print(f"Baseline Expected Loss: {baseline_expected_loss:.2f}")

# 2. Parameters and Helpers

alpha = 0.5                     # failure probability multiplier if audited
num_sim_estimation = 500        # simulations per hidden node for benefit estimation

tiers = defaultdict(list)
for node in G.nodes:
    tiers[G.nodes[node]['tier']].append(node)
ordered_tiers = sorted(tiers.keys(), reverse=True)
focal_node = tiers[0][0]

def compute_supply(failed_set):
    """Compute total supply delivered to focal firm given a set of failed nodes."""
    flow = {}
    for tier in ordered_tiers:
        for node in tiers[tier]:
            if node in failed_set:
                flow[node] = 0.0
                continue
            if tier == 0:
                flow[node] = 0.0
                continue
            suppliers = list(G.predecessors(node))
            if not suppliers:
                inflow = float('inf')
            else:
                inflow = sum(flow[s] for s in suppliers)
            capacity = G.nodes[node]['capacity']
            flow[node] = min(float(capacity), inflow)
    return sum(flow[pred] for pred in G.predecessors(focal_node))

max_supply = compute_supply(set())

# 3. Estimate Benefit of Auditing Each Hidden Node

hidden_nodes = [n for n in G.nodes if G.nodes[n]['tier'] >= 2]
benefit = {}
cost = {}

for node in hidden_nodes:
    orig_prob = G.nodes[node]['failure_prob']
    reduced_prob = orig_prob * alpha
    
    losses_reduced = []
    np.random.seed(777)
    for _ in range(num_sim_estimation):
        failed = set()
        for n in G.nodes:
            if G.nodes[n]['tier'] == 0:
                continue
            prob = reduced_prob if n == node else G.nodes[n]['failure_prob']
            if np.random.rand() < prob:
                failed.add(n)
        supply = compute_supply(failed)
        losses_reduced.append(max_supply - supply)
    
    expected_loss_audited = np.mean(losses_reduced)
    benefit[node] = baseline_expected_loss - expected_loss_audited
    cost[node] = G.nodes[node]['audit_cost']
    print(f"Node {node}: cost={cost[node]:.2f}, benefit={benefit[node]:.4f}")


# 4. Knapsack Optimization for Various Budgets

budgets = [10, 20, 30, 50, 75, 100]
results = []

for B in budgets:
    prob = pulp.LpProblem("Visibility_Optimization", pulp.LpMaximize)
    
    x = {n: pulp.LpVariable(f"x_{n}", cat='Binary') for n in hidden_nodes}
    
    prob += pulp.lpSum(benefit[n] * x[n] for n in hidden_nodes)
    prob += pulp.lpSum(cost[n] * x[n] for n in hidden_nodes) <= B
    
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    selected = [n for n in hidden_nodes if pulp.value(x[n]) == 1]
    total_cost = sum(cost[n] for n in selected)
    total_benefit = sum(benefit[n] for n in selected)
    expected_loss_after = baseline_expected_loss - total_benefit
    
    results.append({
        'budget': B,
        'selected': selected,
        'total_cost': total_cost,
        'total_benefit': total_benefit,
        'expected_loss': expected_loss_after
    })
    
    print(f"\nBudget {B}: selected {len(selected)} nodes, "
          f"cost={total_cost:.2f}, benefit={total_benefit:.4f}, "
          f"expected loss={expected_loss_after:.2f}")

# 5. Visualizations

# Cost-Robustness Trade-off
budget_vals = [r['budget'] for r in results]
loss_vals = [r['expected_loss'] for r in results]

plt.figure(figsize=(10,6))
plt.plot(budget_vals, loss_vals, marker='o', linestyle='-', color='darkblue')
plt.axhline(y=baseline_expected_loss, color='red', linestyle='--', 
            label=f'Baseline Loss = {baseline_expected_loss:.2f}')
plt.xlabel('Auditing Budget')
plt.ylabel('Expected Supply Loss')
plt.title('Cost-Robustness Trade-off: Visibility Investment vs. Expected Loss')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('cost_robustness_tradeoff.png', dpi=150)
plt.show()

# Node Selection Frequency
node_selection_count = defaultdict(int)
for r in results:
    for n in r['selected']:
        node_selection_count[n] += 1
        
if node_selection_count:
    nodes_sorted = sorted(node_selection_count, key=node_selection_count.get, reverse=True)
    counts = [node_selection_count[n] for n in nodes_sorted]
    plt.figure(figsize=(12,6))
    plt.bar(nodes_sorted, counts, color='lightcoral')
    plt.xlabel('Hidden Node')
    plt.ylabel('Times Selected (across budgets)')
    plt.title('Frequency of Node Selection in Optimal Portfolios')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('node_selection_frequency.png', dpi=150)
    plt.show()

# 6. Save Optimization Results

with open('optimization_results.pkl', 'wb') as f:
    pickle.dump({'results': results, 'benefit': benefit, 
                 'cost': cost, 'baseline_expected_loss': baseline_expected_loss}, f)
print("\nOptimization results saved to optimization_results.pkl")