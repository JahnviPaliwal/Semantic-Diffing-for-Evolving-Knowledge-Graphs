# Evaluation & Ablation Benchmark Results

> **Note:** Ground truth gold pairs marked *needs human review*.

## Overall Ablation Comparison

| Metric | With Entity Resolution (Hybrid) | Without Resolution (Naive Diff) | Improvement |
| :--- | :---: | :---: | :---: |
| **Entity Diff F1** | **89.91%** | 87.32% | +2.59% |
| **False Add/Remove Pairs** | **0** | 2 | -2 false pairs eliminated |

## Per-Pair Benchmark Breakdown

| Benchmark Pair | Status | Entity F1 (Semantic) | Entity F1 (Naive) | Rel F1 (Semantic) | False Pairs Eliminated |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `synthetic_v1_v2` | needs human review | 94.74% | 86.95% | 81.48% | **2** |
| `synthetic_v2_v3` | needs human review | 75.00% | 75.00% | 58.83% | **0** |
| `real_policy_v1_v2` | needs human review | 100.00% | 100.00% | 85.71% | **0** |
