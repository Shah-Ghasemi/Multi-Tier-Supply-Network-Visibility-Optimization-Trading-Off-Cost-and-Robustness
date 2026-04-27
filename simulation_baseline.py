
# Monte Carlo Baseline Simulation – No Auditing

import pickle
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# 1. Load Network

with open('supply_network.pkl', 'rb') as f:
    G = pickle.load(f)

# 2. Prepare Tier Lookup

tiers = defaultdict(list)
for node in G.nodes:
    tiers[G.nodes[node]['tier']].append(node)

ordered_tiers = sorted(tiers.keys(), reverse=True)   # deepest tier first
focal_node = tiers[0][0]                             # sole Tier-0 node

# 3. Supply Propagation Function

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
                inflow = float('inf')         # raw material supplier (leaf node)
            else:
                inflow = sum(flow[s] for s in suppliers)
            
            capacity = G.nodes[node]['capacity']
            flow[node] = min(float(capacity), inflow)
    
    return sum(flow[pred] for pred in G.predecessors(focal_node))

# 4. Baseline (No Failures) Total Supply

baseline_total = compute_supply(set())
print(f"Maximum possible supply (no failures): {baseline_total:.2f}")

# 5. Monte Carlo Simulation

num_simulations = 1000
np.random.seed(123)

losses = []
for _ in range(num_simulations):
    failed = set()
    for node in G.nodes:
        if G.nodes[node]['tier'] == 0:
            continue
        if np.random.rand() < G.nodes[node]['failure_prob']:
            failed.add(node)
    supply = compute_supply(failed)
    losses.append(baseline_total - supply)

losses = np.array(losses)
print(f"Average Supply Loss: {losses.mean():.2f}")
print(f"Std Dev: {losses.std():.2f}")
print(f"Min Loss: {losses.min():.2f}, Max Loss: {losses.max():.2f}")

# 6. Plot Loss Distribution

plt.figure(figsize=(10,6))
plt.hist(losses, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
plt.axvline(losses.mean(), color='red', linestyle='dashed', linewidth=2, label=f'Mean Loss = {losses.mean():.2f}')
plt.xlabel('Supply Loss')
plt.ylabel('Frequency')
plt.title('Distribution of Supply Loss (Baseline: No Auditing)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('baseline_loss_distribution.png', dpi=150)
plt.show()

# 7. Save Results

with open('baseline_results.pkl', 'wb') as f:
    pickle.dump({'losses': losses, 'baseline_total': baseline_total}, f)
print("Results saved to baseline_results.pkl")