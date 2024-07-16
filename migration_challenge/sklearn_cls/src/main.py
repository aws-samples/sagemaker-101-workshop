"""SageMaker combined training/inference script for Scikit Learn random forest classifier"""
# TODO: Add any other libraries you need below
# Python Built-Ins:
import argparse
import json
import os

# External Dependencies:
import joblib  # Utilities for saving and re-loading models
import numpy as np  # Matrix/vector math tools
import pandas as pd  # DataFrame (tablular data) utilities
from sklearn.ensemble import RandomForestClassifier


# Helper Functions

def load_csvs_from_folder(folder_name: str) -> pd.DataFrame:
    """Read .csv files directly under folder_name (no nesting) into a combined dataframe"""
    filenames = [f for f in os.listdir(folder_name) if f.lower().endswith(".csv")]
    if len(filenames) == 0:
        raise ValueError(f"No CSV files found in folder! {folder_name}")
    dfs = []
    for f in filenames:
        print(f"Reading {f}")
        dfs.append(pd.read_csv(os.path.join(folder_name, f)))
    return pd.concat(dfs, axis=0, ignore_index=True)


# Main training script block:
if __name__ == "__main__":
    # Parse input parameters from command line and environment variables:
    print("Parsing training arguments")
    parser = argparse.ArgumentParser()
    print("Parsing training arguments")
    parser = argparse.ArgumentParser()

    # TODO: Load RandomForest hyperparameters
    parser.add_argument("--n_estimators", type=int, default=10)
    parser.add_argument("--min_samples_leaf", type=int, default=3)

    # TODO: Find data, model, and output directories from CLI/env vars
    parser.add_argument("--model_dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN"))
    parser.add_argument("--test", type=str, default=os.environ.get("SM_CHANNEL_TEST"))
    parser.add_argument("--class_names", type=lambda s: s.split(","))
    parser.add_argument("--target_variable", type=str, default="label")

    args, _ = parser.parse_known_args()

    # TODO: Parse class names to Id mappings:
    label2idx = {name: ix for ix, name in enumerate(args.class_names)}
    idx2label = {ix: name for ix, name in enumerate(args.class_names)}

    # TODO: Load your data (both training and test) from container filesystem
    # (split into training and test datasets and identify correct features/labels)
    print("Reading data")
    train_df = load_csvs_from_folder(args.train)
    test_df = load_csvs_from_folder(args.test)
    print(train_df.head())
    X_train = train_df[(col for col in train_df.columns if col != args.target_variable)]
    X_test = test_df[(col for col in test_df.columns if col != args.target_variable)]
    y_train = train_df[args.target_variable].map(label2idx)
    y_test = test_df[args.target_variable].map(label2idx)

    # TODO: Fit the random forest model
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        min_samples_leaf=args.min_samples_leaf,
    )
    model.fit(X_train, y_train)

    # TODO: Save the model to the location specified by args.model_dir, using the joblib
    with open(os.path.join(args.model_dir, "class_names.json"), "w") as f:
        json.dump(args.class_names, f)
    path = os.path.join(args.model_dir, "model.joblib")
    joblib.dump(model, path)
    print(f"model saved at {path}")

    # BONUS: Evaluate against the test set and print out some metrics:
    print("Testing model")
    print(f"Test-Accuracy: {model.score(X_test, y_test):.4%}")


# TODO: Function to load the trained model at inference time
def model_fn(model_dir):
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    return model

# TODO: (Bonus!) Custom inference output_fn to return string labels instead of numeric class IDs
