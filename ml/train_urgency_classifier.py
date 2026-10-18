"""Trains the urgency classifier served by app.ml.urgency.predict_urgency.

Run after scripts/download_datasets.py:

    python ml/train_urgency_classifier.py

Labels come straight from the ticket dataset's own "priority" column (low/medium/high) — exactly
Urgency's three values, so no remapping is needed. Only English rows are used: German is roughly
43% of the dataset, and handling it would mean either a second model or a translation step, which
is future work rather than Phase 3. Text is the subject and body joined together.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

RAW_CSV = (
    Path(__file__).resolve().parent
    / "data"
    / "raw"
    / "customer_support_tickets"
    / "aa_dataset-tickets-multi-lang-5-2-50-version.csv"
)
MODEL_PATH = Path(__file__).resolve().parent / "models" / "urgency_classifier.joblib"


def load_training_data() -> tuple[pd.Series, pd.Series]:
    df = pd.read_csv(RAW_CSV)
    df = df[df["language"] == "en"].dropna(subset=["body", "priority"])
    text = (df["subject"].fillna("") + " " + df["body"]).str.strip()
    return text, df["priority"]


def main() -> None:
    text, label = load_training_data()
    x_train, x_test, y_train, y_test = train_test_split(
        text, label, test_size=0.2, random_state=42, stratify=label
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=20_000, ngram_range=(1, 2), min_df=2, stop_words="english")),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    pipeline.fit(x_train, y_train)

    print(classification_report(y_test, pipeline.predict(x_test)))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
