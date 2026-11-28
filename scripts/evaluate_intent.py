"""Compare two intent baselines using the same reviewed train and test splits."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from time import perf_counter

from app.ai.intent import Intent
from app.preprocessing import clean_text

LabeledMessage = tuple[str, str]
# The team's temporary dataset uses this offline label for mixed cases.
EVALUATION_LABELS = {intent.value for intent in Intent} | {"lainnya"}


def _read_split(path: Path) -> dict[str, LabeledMessage]:
    rows: dict[str, LabeledMessage] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"text", "intent"} <= set(reader.fieldnames or ()):
            raise ValueError(f"{path.name} must contain text and intent columns.")
        for line, row in enumerate(reader, start=2):
            message = row.get("text") or ""
            label = (row.get("intent") or "").strip()
            normalized = clean_text(message)
            if not normalized or label not in EVALUATION_LABELS:
                raise ValueError(
                    f"{path.name}:{line} contains an empty message or unknown intent."
                )
            if normalized in rows:
                raise ValueError(f"{path.name}:{line} duplicates a normalized message.")
            rows[normalized] = (message, label)
    return rows


def load_intent_splits(
    train_path: Path, test_path: Path
) -> tuple[list[LabeledMessage], list[LabeledMessage]]:
    """Load labeled splits, rejecting duplicate messages and label mismatches."""
    train, test = _read_split(train_path), _read_split(test_path)
    if train.keys() & test.keys():
        raise ValueError("The training and test splits overlap after normalization.")
    train_labels = {label for _, label in train.values()}
    test_labels = {label for _, label in test.values()}
    if len(train_labels) < 2 or train_labels != test_labels:
        raise ValueError(
            "Train and test need the same labels, with at least two intents."
        )
    return list(train.values()), list(test.values())


def compare_models(
    train: list[LabeledMessage], test: list[LabeledMessage]
) -> dict[str, object]:
    """Fit fresh pipelines on train and report held-out metrics for each model."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.pipeline import make_pipeline
    from sklearn.svm import LinearSVC

    train_messages, train_intents = zip(*train, strict=True)
    test_messages, test_intents = zip(*test, strict=True)
    labels = sorted(set(train_intents))
    candidates = {
        "tfidf_logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
        "tfidf_linear_svm": LinearSVC(random_state=42),
    }
    scores = {}
    for name, classifier in candidates.items():
        pipeline = make_pipeline(
            TfidfVectorizer(preprocessor=clean_text, ngram_range=(1, 2)),
            classifier,
        )
        pipeline.fit(train_messages, train_intents)
        start = perf_counter()
        predictions = pipeline.predict(test_messages)
        inference_ms = (perf_counter() - start) * 1000 / len(test_messages)
        scores[name] = {
            "classification": classification_report(
                test_intents,
                predictions,
                labels=labels,
                output_dict=True,
                zero_division=0,
            ),
            "confusion_matrix": confusion_matrix(
                test_intents, predictions, labels=labels
            ).tolist(),
            "mean_inference_ms": round(inference_ms, 3),
        }
    return {
        "labels": labels,
        "train_classes": dict(sorted(Counter(train_intents).items())),
        "test_classes": dict(sorted(Counter(test_intents).items())),
        "models": scores,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()
    try:
        train, test = load_intent_splits(args.train, args.test)
        report = compare_models(train, test)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    except ModuleNotFoundError as exc:
        if exc.name != "sklearn":
            raise
        parser.error("Install the optional packages from requirements-eval.txt.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
