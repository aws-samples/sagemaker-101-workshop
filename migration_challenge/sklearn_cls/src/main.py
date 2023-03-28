"""SageMaker combined training/inference script for Scikit Learn random forest classifier"""
# TODO: Add any other libraries you need below
# Python Built-Ins:
import argparse
import os

# External Dependencies:
import joblib  # Utilities for saving and re-loading models


# Helper Functions


# Main training script block:
if __name__ == "__main__":
    # Parse input parameters from command line and environment variables:
    print("Parsing training arguments")
    parser = argparse.ArgumentParser()

    # TODO: Load RandomForest hyperparameters
    # TODO: Find data, model, and output directories from CLI/env vars

    args, _ = parser.parse_known_args()

    # TODO: Parse class names to Id mappings:

    # TODO: Load your data (both training and test) from container filesystem
    # (split into training and test datasets and identify correct features/labels)

    # TODO: Fit the random forest model

    # TODO: Save the model to the location specified by args.model_dir, using the joblib


# TODO: Function to load the trained model at inference time


# TODO: (Bonus!) Custom inference output_fn to return string labels instead of numeric class IDs
