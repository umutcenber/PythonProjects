
"""
WEEK 13 — SENTINEL
Intelligent Anomaly Detection Engine

Install:
    pip install numpy pandas scikit-learn matplotlib joblib

Run:
    python Week13_IntelligentAnomalyDetection.py

CSV mode:
    python Week13_IntelligentAnomalyDetection.py --csv data.csv

Example:
    python Week13_IntelligentAnomalyDetection.py --demo
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.preprocessing import StandardScaler


MODEL_FILE = Path("sentinel_model.joblib")
REPORT_FILE = Path("sentinel_report.json")
RESULT_FILE = Path("sentinel_results.csv")

RANDOM_STATE = 42

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("Sentinel")


class SentinelError(Exception):
    """Base exception for Sentinel."""


class DatasetError(SentinelError):
    """Raised when a dataset cannot be processed."""


class Sentinel:
    def __init__(self, contamination=0.05, random_state=RANDOM_STATE):
        if not 0.001 <= contamination <= 0.5:
            raise ValueError("Contamination must be between 0.001 and 0.5.")

        self.contamination = contamination
        self.random_state = random_state

        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=300,
            contamination=contamination,
            max_samples="auto",
            random_state=random_state,
            n_jobs=-1,
        )

        self.feature_columns = None
        self.is_trained = False
        self.training_timestamp = None

    # --------------------------------------------------
    # DATA PROCESSING
    # --------------------------------------------------

    @staticmethod
    def load_csv(path):
        path = Path(path)

        if not path.exists():
            raise DatasetError(f"File not found: {path}")

        try:
            dataframe = pd.read_csv(path)
        except Exception as error:
            raise DatasetError(f"Could not read CSV: {error}")

        if dataframe.empty:
            raise DatasetError("Dataset is empty.")

        return dataframe

    @staticmethod
    def prepare_features(dataframe):
        if not isinstance(dataframe, pd.DataFrame):
            raise DatasetError("Input must be a pandas DataFrame.")

        if dataframe.empty:
            raise DatasetError("Dataset is empty.")

        numeric = dataframe.select_dtypes(include=[np.number]).copy()

        if numeric.empty:
            raise DatasetError("No numeric features found.")

        numeric = numeric.replace([np.inf, -np.inf], np.nan)

        # Remove columns containing only missing values.
        numeric = numeric.dropna(axis=1, how="all")

        if numeric.empty:
            raise DatasetError("No usable numeric columns found.")

        # Median imputation.
        numeric = numeric.fillna(numeric.median())

        # Remove constant features.
        numeric = numeric.loc[:, numeric.nunique() > 1]

        if numeric.empty:
            raise DatasetError("All numeric columns are constant.")

        return numeric

    # --------------------------------------------------
    # TRAINING
    # --------------------------------------------------

    def fit(self, dataframe):
        features = self.prepare_features(dataframe)

        self.feature_columns = list(features.columns)

        scaled = self.scaler.fit_transform(features)

        self.model.fit(scaled)

        self.is_trained = True
        self.training_timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        logger.info(
            "Model trained on %s samples and %s features.",
            len(features),
            len(self.feature_columns),
        )

        return self

    # --------------------------------------------------
    # PREDICTION
    # --------------------------------------------------

    def predict(self, dataframe):
        self._check_trained()

        features = self.prepare_features(dataframe)

        missing = set(self.feature_columns) - set(features.columns)

        if missing:
            raise DatasetError(
                f"Missing required features: {sorted(missing)}"
            )

        features = features[self.feature_columns]

        scaled = self.scaler.transform(features)

        # Isolation Forest:
        # 1 = normal, -1 = anomaly.
        raw_predictions = self.model.predict(scaled)

        # Higher score means more unusual.
        anomaly_scores = -self.model.decision_function(scaled)

        results = dataframe.copy()

        results["sentinel_prediction"] = np.where(
            raw_predictions == -1,
            "ANOMALY",
            "NORMAL",
        )

        results["anomaly_score"] = anomaly_scores

        results["is_anomaly"] = raw_predictions == -1

        return results

    def _check_trained(self):
        if not self.is_trained:
            raise SentinelError("Train or load a model first.")

    # --------------------------------------------------
    # MODEL EVALUATION
    # --------------------------------------------------

    @staticmethod
    def evaluate(results, true_labels):
        """
        true_labels:
            1 = anomaly
            0 = normal
        """

        predictions = results["is_anomaly"].astype(int)

        if len(true_labels) != len(predictions):
            raise ValueError("Label count does not match predictions.")

        return {
            "precision": float(
                precision_score(
                    true_labels,
                    predictions,
                    zero_division=0,
                )
            ),
            "recall": float(
                recall_score(
                    true_labels,
                    predictions,
                    zero_division=0,
                )
            ),
            "f1_score": float(
                f1_score(
                    true_labels,
                    predictions,
                    zero_division=0,
                )
            ),
            "confusion_matrix": confusion_matrix(
                true_labels,
                predictions,
            ).tolist(),
            "classification_report": classification_report(
                true_labels,
                predictions,
                output_dict=True,
                zero_division=0,
            ),
        }

    # --------------------------------------------------
    # VISUALIZATION
    # --------------------------------------------------

    def visualize(self, results, show=True):
        self._check_trained()

        features = self.prepare_features(results)
        features = features[self.feature_columns]

        scaled = self.scaler.transform(features)

        if scaled.shape[1] < 2:
            logger.warning(
                "PCA visualization requires at least two features."
            )
            return

        pca = PCA(n_components=2, random_state=self.random_state)
        coordinates = pca.fit_transform(scaled)

        normal = ~results["is_anomaly"].to_numpy()
        anomaly = results["is_anomaly"].to_numpy()

        plt.figure(figsize=(11, 7))

        plt.scatter(
            coordinates[normal, 0],
            coordinates[normal, 1],
            alpha=0.55,
            label="Normal",
        )

        plt.scatter(
            coordinates[anomaly, 0],
            coordinates[anomaly, 1],
            alpha=0.85,
            marker="x",
            label="Anomaly",
        )

        plt.title("Sentinel — Anomaly Detection")
        plt.xlabel("Principal Component 1")
        plt.ylabel("Principal Component 2")
        plt.legend()
        plt.grid(alpha=0.2)
        plt.tight_layout()

        if show:
            plt.show()

    # --------------------------------------------------
    # REPORTING
    # --------------------------------------------------

    @staticmethod
    def generate_report(results):
        total = len(results)
        anomalies = int(results["is_anomaly"].sum())

        report = {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "total_records": total,
            "normal_records": total - anomalies,
            "anomalies": anomalies,
            "anomaly_percentage": round(
                anomalies / total * 100,
                2,
            ),
            "average_anomaly_score": float(
                results["anomaly_score"].mean()
            ),
            "highest_anomaly_scores": (
                results.nlargest(10, "anomaly_score")
                [["anomaly_score", "sentinel_prediction"]]
                .to_dict(orient="records")
            ),
        }

        return report

    @staticmethod
    def save_results(results, path=RESULT_FILE):
        results.to_csv(path, index=False)
        logger.info("Results saved to %s", path)

    @staticmethod
    def save_report(report, path=REPORT_FILE):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

        logger.info("Report saved to %s", path)

    # --------------------------------------------------
    # MODEL PERSISTENCE
    # --------------------------------------------------

    def save_model(self, path=MODEL_FILE):
        self._check_trained()

        payload = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_columns": self.feature_columns,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "training_timestamp": self.training_timestamp,
        }

        joblib.dump(payload, path)

        logger.info("Model saved to %s", path)

    @classmethod
    def load_model(cls, path=MODEL_FILE):
        path = Path(path)

        if not path.exists():
            raise SentinelError(f"Model file not found: {path}")

        payload = joblib.load(path)

        instance = cls(
            contamination=payload["contamination"],
            random_state=payload["random_state"],
        )

        instance.model = payload["model"]
        instance.scaler = payload["scaler"]
        instance.feature_columns = payload["feature_columns"]
        instance.training_timestamp = payload["training_timestamp"]
        instance.is_trained = True

        logger.info("Model loaded from %s", path)

        return instance


# ------------------------------------------------------
# DEMONSTRATION DATASET
# ------------------------------------------------------

def generate_demo_dataset(samples=1500, seed=42):
    rng = np.random.default_rng(seed)

    normal_count = int(samples * 0.95)
    anomaly_count = samples - normal_count

    normal = pd.DataFrame({
        "request_rate": rng.normal(100, 15, normal_count),
        "response_time": rng.normal(200, 30, normal_count),
        "cpu_usage": rng.normal(45, 10, normal_count),
        "memory_usage": rng.normal(60, 8, normal_count),
        "error_rate": rng.normal(2, 1, normal_count),
    })

    anomalies = pd.DataFrame({
        "request_rate": rng.normal(350, 45, anomaly_count),
        "response_time": rng.normal(900, 120, anomaly_count),
        "cpu_usage": rng.normal(95, 3, anomaly_count),
        "memory_usage": rng.normal(95, 3, anomaly_count),
        "error_rate": rng.normal(35, 8, anomaly_count),
    })

    dataset = pd.concat(
        [normal, anomalies],
        ignore_index=True,
    )

    labels = np.array(
        [0] * normal_count + [1] * anomaly_count
    )

    permutation = rng.permutation(len(dataset))

    return (
        dataset.iloc[permutation].reset_index(drop=True),
        labels[permutation],
    )


# ------------------------------------------------------
# TERMINAL INTERFACE
# ------------------------------------------------------

def print_report(report):
    print("\n" + "=" * 50)
    print("             SENTINEL ANALYSIS REPORT")
    print("=" * 50)

    print(f"Total records:          {report['total_records']}")
    print(f"Normal records:         {report['normal_records']}")
    print(f"Anomalies:              {report['anomalies']}")
    print(f"Anomaly percentage:     {report['anomaly_percentage']}%")
    print(
        "Average anomaly score: "
        f"{report['average_anomaly_score']:.5f}"
    )

    print("\nTop suspicious records:")

    for index, item in enumerate(
        report["highest_anomaly_scores"],
        start=1,
    ):
        print(
            f"{index:02d}. "
            f"Score: {item['anomaly_score']:.5f}"
        )

    print("=" * 50)


def run_pipeline(dataframe, contamination=0.05, labels=None):
    sentinel = Sentinel(contamination=contamination)

    sentinel.fit(dataframe)

    results = sentinel.predict(dataframe)

    report = sentinel.generate_report(results)

    print_report(report)

    sentinel.save_results(results)
    sentinel.save_report(report)
    sentinel.save_model()

    if labels is not None:
        evaluation = sentinel.evaluate(results, labels)

        print("\nMODEL EVALUATION")
        print("-" * 35)
        print(f"Precision: {evaluation['precision']:.4f}")
        print(f"Recall:    {evaluation['recall']:.4f}")
        print(f"F1 Score:  {evaluation['f1_score']:.4f}")
        print("\nConfusion Matrix:")
        print(np.array(evaluation["confusion_matrix"]))

    sentinel.visualize(results)

    return sentinel, results


def interactive_mode():
    parser = argparse.ArgumentParser(
        description="Sentinel Intelligent Anomaly Detection Engine"
    )

    parser.add_argument(
        "--csv",
        type=str,
        help="Path to a CSV dataset.",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the built-in demonstration dataset.",
    )

    parser.add_argument(
        "--contamination",
        type=float,
        default=0.05,
        help="Expected anomaly fraction (default: 0.05).",
    )

    parser.add_argument(
        "--predict",
        type=str,
        help="Predict anomalies using a previously saved model.",
    )

    args = parser.parse_args()

    try:
        if args.predict:
            sentinel = Sentinel.load_model()

            new_data = Sentinel.load_csv(args.predict)
            results = sentinel.predict(new_data)

            print_report(sentinel.generate_report(results))
            sentinel.save_results(results)
            sentinel.visualize(results)
            return

        if args.demo:
            print("\nGenerating synthetic monitoring dataset...")
            dataframe, labels = generate_demo_dataset()

            run_pipeline(
                dataframe,
                contamination=args.contamination,
                labels=labels,
            )
            return

        if args.csv:
            dataframe = Sentinel.load_csv(args.csv)

            run_pipeline(
                dataframe,
                contamination=args.contamination,
            )
            return

        print("\nSENTINEL — Intelligent Anomaly Detection")
        print("-----------------------------------------")
        print("1. Run demonstration")
        print("2. Analyze CSV dataset")
        print("3. Load saved model and predict")
        print("4. Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            dataframe, labels = generate_demo_dataset()
            run_pipeline(
                dataframe,
                contamination=args.contamination,
                labels=labels,
            )

        elif choice == "2":
            path = input("CSV file path: ").strip()
            dataframe = Sentinel.load_csv(path)

            run_pipeline(
                dataframe,
                contamination=args.contamination,
            )

        elif choice == "3":
            path = input("New CSV file path: ").strip()
            sentinel = Sentinel.load_model()
            dataframe = Sentinel.load_csv(path)

            results = sentinel.predict(dataframe)

            print_report(sentinel.generate_report(results))
            sentinel.save_results(results)
            sentinel.visualize(results)

        elif choice == "4":
            print("Sentinel shutting down.")

        else:
            print("Invalid option.")

    except (SentinelError, DatasetError, ValueError) as error:
        logger.error("%s", error)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")

    except Exception:
        logger.exception("Unexpected error occurred.")
        sys.exit(1)


if __name__ == "__main__":
    interactive_mode()
