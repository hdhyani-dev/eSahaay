"""Evaluation harness for running validation sets and hidden-set protocols.
Reference: Section 10.2, FR-8.1, FR-8.2
"""
import json
import time
from typing import List, Dict, Any, Optional
from sahaay.triage.pipeline import run_triage_pipeline
from sahaay.evaluation.metrics import compute_triage_metrics
from sahaay.evaluation.datasets import VALIDATION_DATASET, HIDDEN_STYLE_DATASET

def evaluate_dataset(dataset: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Run pipeline on labelled validation set and compute safety metrics.
    """
    dataset = dataset or VALIDATION_DATASET
    eval_records = []
    
    for item in dataset:
        res = run_triage_pipeline(item["raw_text"], call_id=item["id"])
        
        record = {
            "id": item["id"],
            "raw_text": item["raw_text"],
            "true_urgency": item.get("true_urgency"),
            "pred_urgency": res["urgency"],
            "true_threat": item.get("true_threat"),
            "pred_threats": res["threat_types"],
            "true_routes": item.get("true_routes", []),
            "pred_routes": res["routes"],
            "true_location": item.get("true_location"),
            "pred_locations": res["location"],
            "is_covert": item.get("is_covert", False),
            "pred_flags": res["flags"],
            "pred_covert_detected": "COVERT_SIGNAL" in res["flags"],
            "confidence": res["confidence"],
            "latency_ms": res["latency_ms"],
            "requires_verification": res["requires_verification"]
        }
        eval_records.append(record)
        
    metrics = compute_triage_metrics(eval_records)
    return {
        "metrics": metrics,
        "records": eval_records,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "dataset_name": "Sahaay Validation Split (15 cases)"
    }

def run_hidden_set_protocol(hidden_records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Hidden-set protocol: runs triage pipeline WITHOUT reading or exposing true labels.
    Outputs submission predictions format according to PRD FR-8.2.
    """
    hidden_records = hidden_records or HIDDEN_STYLE_DATASET
    predictions = []
    
    for rec in hidden_records:
        res = run_triage_pipeline(rec["raw_text"], call_id=rec["id"])
        predictions.append({
            "id": rec["id"],
            "predicted_urgency": res["urgency"],
            "confidence": res["confidence"],
            "predicted_threats": [t["type"] for t in res["threat_types"]],
            "predicted_routes": res["routes"],
            "extracted_locations": [l["text"] for l in res["location"]],
            "flags": res["flags"],
            "latency_ms": res["latency_ms"]
        })
        
    return {
        "metadata": {
            "protocol": "Hidden-Set Prediction Protocol",
            "model_version": "sahaay-hybrid-v1.0",
            "total_evaluated": len(predictions),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        },
        "predictions": predictions
    }

def export_evaluation_html_report(eval_summary: Dict[str, Any]) -> str:
    """Generate professional HTML evaluation report for judges and audit review."""
    metrics = eval_summary.get("metrics", {})
    records = eval_summary.get("records", [])
    
    ci_low, ci_high = metrics.get("urgent_recall_ci", (0.0, 0.0))
    
    cm = metrics.get("confusion_matrix", [[0]*4 for _ in range(4)])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sahaay Model Evaluation Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #F3F5F7; color: #253445; margin: 30px; }}
            .card {{ background: #FFFFFF; border: 1px solid #E8EDF2; border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            h1, h2, h3 {{ color: #173B57; }}
            .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px; }}
            .metric {{ background: #F8FAFC; border-left: 4px solid #173B57; padding: 12px; border-radius: 4px; }}
            .metric-val {{ font-size: 24px; font-weight: bold; color: #173B57; }}
            .metric-lbl {{ font-size: 13px; color: #526171; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ padding: 10px; border: 1px solid #E8EDF2; text-align: left; }}
            th {{ background: #173B57; color: #FFFFFF; }}
            .badge-p0 {{ background: #B42318; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
            .badge-p1 {{ background: #A15C00; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
            .badge-p2 {{ background: #286A8A; color: white; padding: 3px 8px; border-radius: 4px; }}
            .badge-p3 {{ background: #187347; color: white; padding: 3px 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h1>🛡️ Sahaay — Emergency Response Evaluation Report</h1>
        <p>Generated: {eval_summary.get('timestamp')} | Model: sahaay-hybrid-v1.0</p>
        
        <div class="card">
            <h2>Safety Evaluation Targets vs Measured Results</h2>
            <div class="grid">
                <div class="metric">
                    <div class="metric-val">{metrics.get('urgent_recall', 0.0):.1%}</div>
                    <div class="metric-lbl">Urgent Recall (P0/P1) [Target &ge;98%]<br>95% CI: [{ci_low:.1%}, {ci_high:.1%}]</div>
                </div>
                <div class="metric">
                    <div class="metric-val" style="color: {'#187347' if metrics.get('severe_under_triage_rate', 0) == 0 else '#B42318'};">
                        {metrics.get('severe_under_triage_rate', 0.0):.1%}
                    </div>
                    <div class="metric-lbl">Severe Under-Triage (&ge;2 levels)<br>[Target &lt;0.5%]</div>
                </div>
                <div class="metric">
                    <div class="metric-val">{metrics.get('routing_macro_f1', 0.0):.2f}</div>
                    <div class="metric-lbl">Routing Macro-F1<br>[Target &ge;0.85]</div>
                </div>
                <div class="metric">
                    <div class="metric-val">{metrics.get('covert_recall', 0.0):.1%}</div>
                    <div class="metric-lbl">Covert-Signal Recall<br>[Target &ge;90%]</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Confusion Matrix (Rows: Ground Truth, Cols: Prediction)</h2>
            <table>
                <tr><th>Truth \\ Pred</th><th>P0 (Critical)</th><th>P1 (High)</th><th>P2 (Medium)</th><th>P3 (Low)</th></tr>
                <tr><td><b>P0 (Critical)</b></td><td>{cm[0][0]}</td><td>{cm[0][1]}</td><td>{cm[0][2]}</td><td>{cm[0][3]}</td></tr>
                <tr><td><b>P1 (High)</b></td><td>{cm[1][0]}</td><td>{cm[1][1]}</td><td>{cm[1][2]}</td><td>{cm[1][3]}</td></tr>
                <tr><td><b>P2 (Medium)</b></td><td>{cm[2][0]}</td><td>{cm[2][1]}</td><td>{cm[2][2]}</td><td>{cm[2][3]}</td></tr>
                <tr><td><b>P3 (Low)</b></td><td>{cm[3][0]}</td><td>{cm[3][1]}</td><td>{cm[3][2]}</td><td>{cm[3][3]}</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>Evaluated Cases & Predictions</h2>
            <table>
                <tr><th>ID</th><th>Transcript</th><th>Ground Truth</th><th>Predicted</th><th>Routes</th><th>Latency</th></tr>
    """
    for r in records:
        html += f"""
                <tr>
                    <td><b>{r['id']}</b></td>
                    <td>{r['raw_text']}</td>
                    <td><span class='badge-{r['true_urgency'].lower()}'>{r['true_urgency']}</span></td>
                    <td><span class='badge-{r['pred_urgency'].lower()}'>{r['pred_urgency']}</span></td>
                    <td>{', '.join(r['pred_routes'])}</td>
                    <td>{r['latency_ms']} ms</td>
                </tr>
        """
    html += """
            </table>
        </div>
    </body>
    </html>
    """
    return html
