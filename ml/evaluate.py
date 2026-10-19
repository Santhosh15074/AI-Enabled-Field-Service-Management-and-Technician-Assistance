"""Evaluates all four AI components and writes the results to docs/evaluation/.

Run after training both models (see README, setup step 6):

    python ml/evaluate.py

Each component is measured through the same code the app serves from, on data it never saw:
- Urgency classifier: the saved model on the training script's held-out 20% split, against a
  majority-class baseline.
- Failure model: the saved model on its held-out split, scored at the app's own risk thresholds.
- Troubleshooting assistant: hand-written customer complaints (ml/eval_data) against the seeded
  knowledge base, compared with a keyword (TF-IDF) baseline; off-topic queries check that
  MIN_SIMILARITY rejects them.
- Report extraction: hand-written technician reports with hand-labelled fields.
"""

import importlib.util
import json
import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    RocCurveDisplay,
    accuracy_score,
    average_precision_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

ML_DIR = Path(__file__).resolve().parent
ROOT = ML_DIR.parent
sys.path.insert(0, str(ROOT))

import train_failure_model  # noqa: E402
import train_urgency_classifier  # noqa: E402
from app.ml import failure, troubleshooting  # noqa: E402
from app.models import KnowledgeBaseEntry  # noqa: E402
from app.report_extraction import extract_fields  # noqa: E402

OUT_DIR = ROOT / "docs" / "evaluation"
EVAL_DATA = ML_DIR / "eval_data"


def _save(fig, name: str) -> str:
    fig.tight_layout()
    fig.savefig(OUT_DIR / name, dpi=120)
    plt.close(fig)
    return name


def evaluate_urgency() -> dict:
    text, label = train_urgency_classifier.load_training_data()
    x_train, x_test, y_train, y_test = train_test_split(
        text, label, test_size=0.2, random_state=42, stratify=label
    )
    model = joblib.load(train_urgency_classifier.MODEL_PATH)
    predicted = model.predict(x_test)
    baseline = DummyClassifier(strategy="most_frequent").fit(x_train, y_train).predict(x_test)

    labels = ["low", "medium", "high"]
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(y_test, predicted, labels=labels, ax=ax, colorbar=False)
    ax.set_title("Urgency classifier: confusion matrix")

    return {
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "accuracy": accuracy_score(y_test, predicted),
        "macro_f1": f1_score(y_test, predicted, average="macro"),
        "baseline_accuracy": accuracy_score(y_test, baseline),
        "baseline_macro_f1": f1_score(y_test, baseline, average="macro"),
        "high_recall": recall_score(y_test, predicted, labels=["high"], average="macro"),
        "report": classification_report(y_test, predicted, labels=labels, digits=3),
        "figure": _save(fig, "urgency_confusion_matrix.png"),
    }


def _risk_level(score: float) -> str:
    if score >= failure.CRITICAL_AT:
        return "critical"
    if score >= failure.MODERATE_AT:
        return "moderate"
    return "good"


def evaluate_failure() -> dict:
    features, label = train_failure_model.load_training_data()
    _, x_test, _, y_test = train_test_split(features, label, test_size=0.2, random_state=42, stratify=label)
    model = joblib.load(train_failure_model.MODEL_PATH)
    scores = model.predict_proba(x_test)[:, 1]
    y = y_test.to_numpy()

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    RocCurveDisplay.from_predictions(y, scores, ax=axes[0], name="Random forest")
    axes[0].set_title("ROC curve")
    PrecisionRecallDisplay.from_predictions(y, scores, ax=axes[1], name="Random forest")
    axes[1].set_title("Precision-recall curve")
    curves = _save(fig, "failure_roc_pr.png")

    classifier = model.named_steps["classifier"]
    names = [name.split("__", 1)[1] for name in model.named_steps["columns"].get_feature_names_out()]
    order = np.argsort(classifier.feature_importances_)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.barh(np.array(names)[order], classifier.feature_importances_[order])
    ax.set_title("Failure model: feature importance")
    importance = _save(fig, "failure_feature_importance.png")

    thresholds = []
    for threshold in [0.08, 0.15, 0.25, 0.35, 0.5]:
        flagged = scores >= threshold
        thresholds.append(
            {
                "threshold": threshold,
                "recall": recall_score(y, flagged, zero_division=0),
                "precision": precision_score(y, flagged, zero_division=0),
                "flagged_share": flagged.mean(),
            }
        )

    levels = np.array([_risk_level(score) for score in scores])
    buckets = {
        level: {
            "failures": int(((levels == level) & (y == 1)).sum()),
            "no_failures": int(((levels == level) & (y == 0)).sum()),
        }
        for level in ["good", "moderate", "critical"]
    }

    return {
        "test_rows": len(y),
        "test_failures": int(y.sum()),
        "roc_auc": roc_auc_score(y, scores),
        "average_precision": average_precision_score(y, scores),
        "moderate_at": failure.MODERATE_AT,
        "critical_at": failure.CRITICAL_AT,
        "thresholds": thresholds,
        "buckets": buckets,
        "figures": [curves, importance],
    }


def _seeded_knowledge_base() -> list[KnowledgeBaseEntry]:
    path = next((ROOT / "alembic" / "versions").glob("*_seed_knowledge_base.py"))
    spec = importlib.util.spec_from_file_location("seed_knowledge_base", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [
        KnowledgeBaseEntry(id=index, equipment_type=equipment_type, issue_pattern=issue, suggested_fix=fix)
        for index, (_, equipment_type, issue, fix) in enumerate(module.ENTRIES, start=1)
    ]


class _StubSession:
    """Just enough of a Session for suggest_fixes, which only ever lists the knowledge base."""

    def __init__(self, entries):
        self._entries = entries

    def scalars(self, _statement):
        return self

    def all(self):
        return self._entries


def _ranking_metrics(score_matrix: np.ndarray, expected: list[int]) -> dict:
    ranks = [int((row > row[target]).sum()) + 1 for row, target in zip(score_matrix, expected)]
    return {
        "top1": float(np.mean([rank == 1 for rank in ranks])),
        "top3": float(np.mean([rank <= 3 for rank in ranks])),
        "mrr": float(np.mean([1 / rank for rank in ranks])),
    }


def evaluate_troubleshooting() -> dict:
    data = json.loads((EVAL_DATA / "troubleshooting_queries.json").read_text(encoding="utf-8"))
    entries = _seeded_knowledge_base()
    patterns = [entry.issue_pattern for entry in entries]
    queries = [item["query"] for item in data["matching"]]
    expected = [patterns.index(item["expected"]) for item in data["matching"]]

    model = troubleshooting._model()
    corpus = model.encode(patterns, normalize_embeddings=True)
    semantic = model.encode(queries, normalize_embeddings=True) @ corpus.T

    vectorizer = TfidfVectorizer(stop_words="english").fit(patterns + queries)
    keyword = (vectorizer.transform(queries) @ vectorizer.transform(patterns).T).toarray()

    # App-level behaviour: what a user actually sees, MIN_SIMILARITY cut-off included.
    session = _StubSession(entries)
    shown = [troubleshooting.suggest_fixes(session, query) for query in queries]
    answered = [bool(suggestions) for suggestions in shown]
    hit_in_shown = [
        any(entry.issue_pattern == patterns[target] for entry, _ in suggestions)
        for suggestions, target in zip(shown, expected)
    ]
    off_topic_rejected = [not troubleshooting.suggest_fixes(session, query) for query in data["off_topic"]]

    correct_scores = semantic[np.arange(len(expected)), expected]
    off_topic_best = (model.encode(data["off_topic"], normalize_embeddings=True) @ corpus.T).max(axis=1)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bins = np.linspace(0, 1, 21)
    ax.hist(correct_scores, bins=bins, alpha=0.7, label="Matching complaint vs correct entry")
    ax.hist(off_topic_best, bins=bins, alpha=0.7, label="Off-topic query vs best entry")
    ax.axvline(troubleshooting.MIN_SIMILARITY, color="black", linestyle="--", label="MIN_SIMILARITY")
    ax.set_xlabel("Cosine similarity")
    ax.set_ylabel("Queries")
    ax.set_title("Troubleshooting: similarity scores")
    ax.legend(fontsize=8)

    return {
        "knowledge_base_entries": len(entries),
        "matching_queries": len(queries),
        "off_topic_queries": len(data["off_topic"]),
        "semantic": _ranking_metrics(semantic, expected),
        "keyword": _ranking_metrics(keyword, expected),
        "min_similarity": troubleshooting.MIN_SIMILARITY,
        "answered_rate": float(np.mean(answered)),
        "shown_hit_rate": float(np.mean(hit_in_shown)),
        "off_topic_rejection_rate": float(np.mean(off_topic_rejected)),
        "figure": _save(fig, "troubleshooting_similarity.png"),
    }


def _contains(haystack: str | None, needle: str) -> bool:
    return haystack is not None and needle.lower() in haystack.lower()


def evaluate_report_extraction() -> dict:
    cases = json.loads((EVAL_DATA / "service_reports.json").read_text(encoding="utf-8"))
    issue_ok, action_ok, time_ok = [], [], []
    true_parts = predicted_parts = matched_parts = 0
    failures, issue_misses = [], []

    for case in cases:
        fields = extract_fields(case["report"])
        issue_ok.append(_contains(fields.issue, case["issue"]))
        if not issue_ok[-1]:
            issue_misses.append({"report": case["report"], "expected": case["issue"], "extracted": fields.issue})
        action_ok.append(all(_contains(fields.action_taken, phrase) for phrase in case["action"]))
        time_ok.append(fields.time_spent_minutes == case["minutes"])

        predicted = [part.strip().lower() for part in (fields.parts_used or "").split(",") if part.strip()]
        expected = [part.lower() for part in case["parts"]]
        true_parts += len(expected)
        predicted_parts += len(predicted)
        matched_parts += sum(any(want in got for got in predicted) for want in expected)
        if set(expected) != set(predicted):
            failures.append({"report": case["report"], "expected_parts": expected, "extracted_parts": predicted})

    precision = matched_parts / predicted_parts if predicted_parts else 0.0
    recall = matched_parts / true_parts if true_parts else 0.0
    return {
        "reports": len(cases),
        "issue_accuracy": float(np.mean(issue_ok)),
        "action_accuracy": float(np.mean(action_ok)),
        "time_accuracy": float(np.mean(time_ok)),
        "parts_precision": precision,
        "parts_recall": recall,
        "parts_mismatches": failures,
        "issue_misses": issue_misses,
    }


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_markdown(results: dict) -> str:
    u, f, t, r = results["urgency"], results["failure"], results["troubleshooting"], results["report_extraction"]
    lines = [
        "# Evaluation results",
        "",
        "Generated by `python ml/evaluate.py`; do not edit by hand. See `docs/evaluation.md` for discussion.",
        "",
        "## 1. Urgency classifier",
        "",
        f"TF-IDF + logistic regression, {u['train_rows']:,} training / {u['test_rows']:,} held-out English tickets.",
        "",
        "| Model | Accuracy | Macro F1 |",
        "|---|---|---|",
        f"| Majority-class baseline | {_pct(u['baseline_accuracy'])} | {u['baseline_macro_f1']:.3f} |",
        f"| Urgency classifier | {_pct(u['accuracy'])} | {u['macro_f1']:.3f} |",
        "",
        f"Recall on **high** urgency: {_pct(u['high_recall'])}.",
        "",
        "```",
        u["report"].rstrip(),
        "```",
        "",
        f"![Urgency confusion matrix]({u['figure']})",
        "",
        "## 2. Failure prediction",
        "",
        f"Random forest, {f['test_rows']:,} held-out readings ({f['test_failures']} real failures).",
        "",
        f"- ROC-AUC: **{f['roc_auc']:.3f}**",
        f"- Average precision (PR-AUC): **{f['average_precision']:.3f}** (a random model scores "
        f"{f['test_failures'] / f['test_rows']:.3f})",
        "",
        "Recall and precision of the *failure* class if every reading at or above the threshold is flagged:",
        "",
        "| Threshold | Recall | Precision | Readings flagged |",
        "|---|---|---|---|",
    ]
    for row in f["thresholds"]:
        marker = ""
        if row["threshold"] == f["moderate_at"]:
            marker = " (app: moderate)"
        elif row["threshold"] == f["critical_at"]:
            marker = " (app: critical)"
        lines.append(
            f"| {row['threshold']:.2f}{marker} | {_pct(row['recall'])} | {_pct(row['precision'])} | "
            f"{_pct(row['flagged_share'])} |"
        )
    lines += [
        "",
        "How the app's three risk levels split the test set:",
        "",
        "| Risk level | Real failures | No failure |",
        "|---|---|---|",
    ]
    for level, counts in f["buckets"].items():
        lines.append(f"| {level} | {counts['failures']} | {counts['no_failures']} |")
    lines += [""] + [f"![Failure model]({name})" for name in f["figures"]]
    lines += [
        "",
        "## 3. Troubleshooting assistant",
        "",
        f"{t['matching_queries']} hand-written complaints against the {t['knowledge_base_entries']} seeded "
        f"knowledge-base entries, plus {t['off_topic_queries']} off-topic queries.",
        "",
        "| Method | Top-1 | Top-3 | MRR |",
        "|---|---|---|---|",
        f"| Keyword baseline (TF-IDF) | {_pct(t['keyword']['top1'])} | {_pct(t['keyword']['top3'])} | "
        f"{t['keyword']['mrr']:.3f} |",
        f"| Semantic search (all-MiniLM-L6-v2) | {_pct(t['semantic']['top1'])} | {_pct(t['semantic']['top3'])} | "
        f"{t['semantic']['mrr']:.3f} |",
        "",
        f"With the app's MIN_SIMILARITY = {t['min_similarity']} cut-off:",
        "",
        f"- Complaints that get at least one suggestion: {_pct(t['answered_rate'])}",
        f"- Complaints whose correct fix is among the suggestions shown: {_pct(t['shown_hit_rate'])}",
        f"- Off-topic queries correctly given no suggestion: {_pct(t['off_topic_rejection_rate'])}",
        "",
        f"![Similarity distribution]({t['figure']})",
        "",
        "## 4. Report extraction",
        "",
        f"{r['reports']} hand-written technician reports with hand-labelled fields.",
        "",
        "| Field | Score |",
        "|---|---|",
        f"| Issue | {_pct(r['issue_accuracy'])} accuracy |",
        f"| Action taken | {_pct(r['action_accuracy'])} accuracy |",
        f"| Time spent | {_pct(r['time_accuracy'])} accuracy |",
        f"| Parts used | {_pct(r['parts_precision'])} precision, {_pct(r['parts_recall'])} recall |",
        "",
    ]
    if r["issue_misses"]:
        lines += ["Reports where the extracted issue misses the labelled cause:", ""]
        for miss in r["issue_misses"]:
            lines.append(f"- \"{miss['report']}\" — expected \"{miss['expected']}\", extracted \"{miss['extracted']}\"")
        lines.append("")
    if r["parts_mismatches"]:
        lines += ["Reports where the extracted parts differ from the labels:", ""]
        for miss in r["parts_mismatches"]:
            lines.append(
                f"- \"{miss['report']}\" — expected {miss['expected_parts']}, extracted {miss['extracted_parts']}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {
        "urgency": evaluate_urgency(),
        "failure": evaluate_failure(),
        "troubleshooting": evaluate_troubleshooting(),
        "report_extraction": evaluate_report_extraction(),
    }
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")
    (OUT_DIR / "results.md").write_text(write_markdown(results), encoding="utf-8")
    print(f"Wrote {OUT_DIR / 'results.md'}")


if __name__ == "__main__":
    main()
