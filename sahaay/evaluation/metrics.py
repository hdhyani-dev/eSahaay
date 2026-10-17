"""Safety-first evaluation metrics calculation.
Reference: Section 1.5, Section 10.1
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics import confusion_matrix, f1_score
from rapidfuzz import fuzz
from sahaay.config import settings

URGENCY_MAP = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

def compute_urgent_recall_ci(y_true: List[str], y_pred: List[str], n_bootstraps: int = 500) -> Tuple[float, float, float]:
    """
    Calculate Urgent Recall (share of true P0/P1 placed in P0/P1) with 95% Bootstrap CI.
    """
    true_urgent_indices = [i for i, yt in enumerate(y_true) if yt in ["P0", "P1"]]
    if not true_urgent_indices:
        return 1.0, 1.0, 1.0
        
    y_true_arr = np.array([1 if y_true[i] in ["P0", "P1"] else 0 for i in true_urgent_indices])
    y_pred_arr = np.array([1 if y_pred[i] in ["P0", "P1"] else 0 for i in true_urgent_indices])
    
    base_recall = float(np.mean(y_pred_arr == 1))
    
    # Bootstrap CI
    rng = np.random.default_rng(seed=42)
    boot_recalls = []
    n = len(y_pred_arr)
    for _ in range(n_bootstraps):
        sample_idx = rng.integers(0, n, size=n)
        boot_recalls.append(float(np.mean(y_pred_arr[sample_idx] == 1)))
        
    ci_lower = float(np.percentile(boot_recalls, 2.5))
    ci_upper = float(np.percentile(boot_recalls, 97.5))
    return round(base_recall, 4), round(ci_lower, 4), round(ci_upper, 4)

def compute_triage_metrics(
    eval_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute comprehensive safety and triage metrics over evaluated dataset.
    """
    y_true = [r["true_urgency"] for r in eval_results]
    y_pred = [r["pred_urgency"] for r in eval_results]
    
    n_total = len(eval_results)
    if n_total == 0:
        return {}
        
    # 1. Urgent Recall & CI
    urgent_recall, ci_low, ci_high = compute_urgent_recall_ci(y_true, y_pred)
    
    # 2. Under-triage and Over-triage rates
    under_triage_count = 0
    severe_under_triage_count = 0 # 2+ levels below
    over_triage_count = 0
    total_cost = 0.0
    cost_matrix = settings.cost_matrix
    
    cm = [[0]*4 for _ in range(4)]
    
    for yt, yp in zip(y_true, y_pred):
        idx_t = URGENCY_MAP[yt]
        idx_p = URGENCY_MAP[yp]
        cm[idx_t][idx_p] += 1
        
        # In URGENCY_MAP, lower number means higher urgency (0=P0, 3=P3)
        # Under-triage: pred > true (e.g. true=P0 (0), pred=P2 (2) -> diff = 2)
        diff = idx_p - idx_t
        if diff >= 2:
            severe_under_triage_count += 1
        if diff >= 1:
            under_triage_count += 1
        elif diff <= -1:
            over_triage_count += 1
            
        # Asymmetric cost
        c = cost_matrix.get(yt, {}).get(yp, 0)
        total_cost += c

    severe_under_triage_rate = round(severe_under_triage_count / n_total, 4)
    under_triage_rate = round(under_triage_count / n_total, 4)
    over_triage_rate = round(over_triage_count / n_total, 4)
    avg_cost_score = round(total_cost / n_total, 3)

    # 3. Multi-label Routing Accuracy & Macro-F1
    all_services = ["police", "medical", "shelter", "legal"]
    service_f1s = {}
    for s in all_services:
        s_true = [1 if s in r.get("true_routes", []) else 0 for r in eval_results]
        s_pred = [1 if s in r.get("pred_routes", []) else 0 for r in eval_results]
        if sum(s_true) > 0 or sum(s_pred) > 0:
            service_f1s[s] = round(f1_score(s_true, s_pred, zero_division=0), 3)
        else:
            service_f1s[s] = 1.0
            
    routing_macro_f1 = round(float(np.mean(list(service_f1s.values()))), 3)

    # 4. Location Extraction Partial-Match F1
    loc_matches = 0
    loc_evaluable = 0
    for r in eval_results:
        true_loc = r.get("true_location")
        if true_loc:
            loc_evaluable += 1
            pred_locs = [l.get("text", "") for l in r.get("pred_locations", [])]
            matched = any(fuzz.partial_ratio(true_loc.lower(), pl.lower()) >= 80 for pl in pred_locs)
            if matched:
                loc_matches += 1
    loc_f1 = round(loc_matches / max(1, loc_evaluable), 3)

    # 5. Covert-Signal Recall
    covert_cases = [r for r in eval_results if r.get("is_covert")]
    covert_detected = [r for r in covert_cases if "COVERT_SIGNAL" in r.get("pred_flags", []) or r.get("pred_covert_detected")]
    covert_recall = round(len(covert_detected) / max(1, len(covert_cases)), 3)

    # 6. Latency percentiles
    latencies = [r.get("latency_ms", 0.0) for r in eval_results]
    p50_latency = round(float(np.percentile(latencies, 50)), 1)
    p95_latency = round(float(np.percentile(latencies, 95)), 1)

    return {
        "n_samples": n_total,
        "urgent_recall": urgent_recall,
        "urgent_recall_ci": (ci_low, ci_high),
        "under_triage_rate": under_triage_rate,
        "severe_under_triage_rate": severe_under_triage_rate,
        "over_triage_rate": over_triage_rate,
        "avg_cost_score": avg_cost_score,
        "routing_macro_f1": routing_macro_f1,
        "service_f1s": service_f1s,
        "location_f1": loc_f1,
        "covert_recall": covert_recall,
        "p50_latency_ms": p50_latency,
        "p95_latency_ms": p95_latency,
        "confusion_matrix": cm,
        "labels": ["P0", "P1", "P2", "P3"]
    }
