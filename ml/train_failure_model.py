"""Trains the equipment failure-risk model served by app.ml.failure.predict_risk.

Run after scripts/download_datasets.py:

    python ml/train_failure_model.py

Uses the AI4I 2020 predictive-maintenance dataset, whose five sensor columns and "Type" column
are exactly what Equipment stores per visit (see the comment on Equipment in app/models.py) —
there's no domain mismatch to work around here, unlike Phases 3 and 4. The label is "Machine
failure" (a 1 for an imminent failure), and it's rare (~3.4% of rows), so the model is a random
forest with balanced class weights and is judged on recall for that class, not raw accuracy — a
missed real failure is far more costly than a false alarm the technician double-checks.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

RAW_CSV = Path(__file__).resolve().parent / "data" / "raw" / "ai4i2020.csv"
MODEL_PATH = Path(__file__).resolve().parent / "models" / "failure_model.joblib"

# Equipment's column names -> the dataset's. Keeping Equipment's names as the pipeline's feature
# names means app.ml.failure can hand it a DataFrame shaped just like the ORM row.
COLUMNS = {
    "Type": "quality_grade",
    "Air temperature [K]": "air_temperature_k",
    "Process temperature [K]": "process_temperature_k",
    "Rotational speed [rpm]": "rotational_speed_rpm",
    "Torque [Nm]": "torque_nm",
    "Tool wear [min]": "tool_wear_min",
}
NUMERIC_FEATURES = [name for name in COLUMNS.values() if name != "quality_grade"]


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(RAW_CSV).rename(columns=COLUMNS)
    return df[list(COLUMNS.values())], df["Machine failure"]


def main() -> None:
    features, label = load_training_data()
    x_train, x_test, y_train, y_test = train_test_split(
        features, label, test_size=0.2, random_state=42, stratify=label
    )

    pipeline = Pipeline(
        [
            (
                "columns",
                ColumnTransformer(
                    [
                        ("grade", OneHotEncoder(handle_unknown="ignore"), ["quality_grade"]),
                        ("numeric", "passthrough", NUMERIC_FEATURES),
                    ]
                ),
            ),
            ("classifier", RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42)),
        ]
    )
    pipeline.fit(x_train, y_train)

    predicted = pipeline.predict(x_test)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    print(classification_report(y_test, predicted, target_names=["no failure", "failure"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, probabilities):.3f}")
    print("Predicted failure-probability percentiles (test set):")
    print(pd.Series(probabilities).describe(percentiles=[0.5, 0.9, 0.95, 0.99]))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
