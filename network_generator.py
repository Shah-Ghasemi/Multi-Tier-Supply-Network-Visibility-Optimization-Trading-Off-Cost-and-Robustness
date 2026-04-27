# Multi-Tier Supply Network Generator

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pickle

np.random.seed(42)

# 1. Network Structure

layer_sizes = [1, 5, 8, 6, 4]   # nodes per tier (Tier 0 to Tier 4)
num_tiers = len(layer_sizes)
G = nx.DiGraph()

# 2. Create Nodes

node_counter = 0
tier_nodes = []

for tier in range(num_tiers):
    nodes_in_tier = []
    for _ in range(layer_sizes[tier]):
        node_id = f"T{tier}_{node_counter}"
        G.add_node(node_id, tier=tier)
        nodes_in_tier.append(node_id)
        node_counter += 1
    tier_nodes.append(nodes_in_tier)

# 3. Add Edges (material flow: supplier -> customer)

for tier in range(1, num_tiers):
    suppliers = tier_nodes[tier]
    customers = tier_nodes[tier-1]
    for sup in suppliers:
        num_customers = np.random.randint(1, min(4, len(customers) + 1))
        targets = np.random.choice(customers, size=num_customers, replace=False)
        for cust in targets:
            G.add_edge(sup, cust)

# Ensure every Tier-1 node connects to the focal firm
for node in tier_nodes[1]:
    if G.out_degree(node) == 0:
        G.add_edge(node, tier_nodes[0][0])

# Ensure no orphan nodes in intermediate tiers
for tier in range(1, num_tiers-1):
    for node in tier_nodes[tier]:
        if G.out_degree(node) == 0:
            cust = np.random.choice(tier_nodes[tier-1])
            G.add_edge(node, cust)

# 4. Assign Node Attributes


for node in G.nodes:
    tier = G.nodes[node]['tier']
    G.nodes[node]['capacity'] = np.random.randint(50, 201) if tier > 0 else 0
    if tier == 0:
        G.nodes[node]['failure_prob'] = 0.0
    else:
        G.nodes[node]['failure_prob'] = round(np.random.uniform(0.02, 0.15), 3)

    if tier >= 2:
        G.nodes[node]['audit_cost'] = round(10 + 5 * (tier - 1) + np.random.uniform(0, 5), 2)
    else:
        G.nodes[node]['audit_cost'] = 0.0

# 5. Console Output & Sample Node

print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")

sample_node = None
for n in G.nodes:
    if G.nodes[n]['tier'] == 1:
        sample_node = n
        break
if sample_node is None:
    sample_node = list(G.nodes)[0]
print("Sample node (Tier 1):", sample_node)
print("Sample node attributes:", G.nodes[sample_node])

# 6. Visualization

pos = nx.multipartite_layout(G, subset_key='tier', align='horizontal', scale=2)
tier_colors = {0: 'gold', 1: 'lightblue', 2: 'lightgreen', 3: 'orange', 4: 'lightcoral'}
node_colors = [tier_colors[G.nodes[n]['tier']] for n in G.nodes]

plt.figure(figsize=(14, 8))
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=600, edgecolors='black', linewidths=0.8)
nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowstyle='-|>', arrowsize=12)
nx.draw_networkx_labels(G, pos, font_size=7, font_weight='bold')

legend_labels = {0: 'Focal Firm (Tier 0)', 1: 'Tier 1', 2: 'Tier 2 (hidden)', 3: 'Tier 3 (hidden)', 4: 'Tier 4 (hidden)'}
patches = [plt.Line2D([0],[0], marker='o', color='w', markerfacecolor=tier_colors[i], markersize=10, label=legend_labels[i]) for i in tier_colors]
plt.legend(handles=patches, loc='upper left', bbox_to_anchor=(1,1))
plt.title("Multi-Tier Supply Network (Corrected Flow Direction)", fontsize=14)
plt.axis('off')
plt.tight_layout()
plt.savefig("supply_network.png", dpi=150)
plt.show()

# 7. Save Network

with open('supply_network.pkl', 'wb') as f:
    pickle.dump(G, f)
print("Network saved to supply_network.pkl")