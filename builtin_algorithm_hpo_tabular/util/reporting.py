# -*- coding: utf-8 -*-
"""Helper functions to generate classification model quality reports
"""

# Python Built-Ins:
import itertools
from typing import Iterable, Optional

# External Dependencies:
import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics


def plot_confusion_matrix(
    y_true,
    y_pred,
    class_names_list=["Class 0", "Class 1"],
    ax=None,
    normalize="true",
    title="Confusion matrix",
    cmap=plt.cm.Blues,
) -> plt.Axes:
    """Plot a confusion matrix

    Adds some extras vs vanilla sklearn.metrics.ConfusionMatrixDisplay.from_predictions(...)
    """
    new_figure = ax is None
    if new_figure:
        plt.figure()
        ax = plt.gca()

    # Calculate both raw and normalized confusion matrices:
    confusion_matrix = metrics.confusion_matrix(y_true, y_pred)
    confusion_matrix_norm = metrics.confusion_matrix(y_true, y_pred, normalize=normalize)

    # Use normalized values for colour, with absolute 0-100% scale:
    ax.imshow(confusion_matrix_norm, interpolation='nearest', cmap=cmap, vmin=0, vmax=1)

    # Add text detailing both absolute and normalized values per cell:
    for i, j in itertools.product(
        range(confusion_matrix.shape[0]),
        range(confusion_matrix.shape[1]),
    ):
        ax.text(
            j,
            i,
            f"{confusion_matrix[i, j]}\n({confusion_matrix_norm[i, j]:.2%})",
            horizontalalignment="center",
            color="white" if confusion_matrix_norm[i, j] > .5 else "black",
        )

    # Set up titles & axes:
    ax.set_title(title)
    tick_marks = np.arange(len(class_names_list))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(class_names_list, rotation=0)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(class_names_list)
    ax.set_ylabel("True label")
    ax.set_xlabel("Predicted label")
    ax.grid(False)

    if new_figure:
        plt.tight_layout()
        plt.show()
    return ax


def plot_precision_recall_curve(
    y_real: np.ndarray,
    y_predict: np.ndarray,
    ax: Optional[plt.Axes]=None,
) -> plt.Axes:
    """Plot a precision/recall curve from true and predicted (binary) classification labels"""
    new_figure = ax is None
    if new_figure:
        plt.figure()
        ax = plt.gca()

    metrics_P, metrics_R, _ = metrics.precision_recall_curve(y_real, y_predict)
    metrics_AP = metrics.average_precision_score(y_real, y_predict)

    ax.set_aspect(aspect=0.95)
    ax.step(metrics_R, metrics_P, color="b", where="post", linewidth=0.7)
    ax.fill_between(metrics_R, metrics_P, step="post", alpha=0.2, color="b")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_ylim([0.0, 1.05])
    ax.set_xlim([0.0, 1.05])
    ax.set_title(f"Precision-Recall curve: AP={metrics_AP:0.3f}")

    if new_figure:
        plt.tight_layout()
        plt.show()
    return ax


def plot_roc_curve(
    y_real: np.ndarray,
    y_predict: np.ndarray,
    ax: Optional[plt.Axes]=None,
) -> plt.Axes:
    """Plot a receiver operating characteristic from true and predicted (binary) class labels
    """
    new_figure = ax is None
    if new_figure:
        plt.figure()
        ax = plt.gca()

    metrics_FPR, metrics_TPR, _ = metrics.roc_curve(y_real, y_predict)
    metrics_AUC = metrics.roc_auc_score(y_real, y_predict)

    ax.set_aspect(aspect=0.95)
    ax.plot(metrics_FPR, metrics_TPR, color="b", linewidth=0.7)
    ax.fill_between(metrics_FPR, metrics_TPR, step="post", alpha=0.2, color="b")

    ax.plot([0, 1], [0, 1], color="k", linestyle="--", linewidth=1)
    ax.set_xlim([-0.05, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC curve: AUC={metrics_AUC:0.3f}")

    if new_figure:
        plt.tight_layout()
        plt.show()
    return ax


def plot_text(text: str, ax: plt.Axes=None) -> None:
    """Create a text-only plot
    """
    if ax is None:  # Create stand-alone figure if axes not provided
        plt.figure()
        ax = plt.gca()

    # set background white
    ax.set_axis_off()
    ax.set_frame_on(True)
    ax.grid(False)
    ax.text(
        x=0.8,
        y=1,
        s=text,
        horizontalalignment="right",
        verticalalignment="top",
        color="black",
    )


def sagemaker_binary_classification_report(
    y_real: np.ndarray,
    y_predict_proba: np.ndarray,
    y_predict_label: Optional[np.ndarray]=None,
) -> dict:
    """Create a binary classification model quality report compatible with SageMaker Model Monitor

    See: https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor-model-quality-metrics.html
        
    SageMaker Model Quality Monitor can create reports like this using the pre-built container
    without needing to maintain a utility function like this one, but this example uses this method
    instead because:
    
    - It avoids processing job spin-up time
    - We wanted to display custom model metrics in the notebook anyway
    - It's nice to show you can create Model Monitor-compatible reports with custom code too.

    Differences from the standard SageMaker Model Monitor quality bin cls report output include:

    - An additional binary_classification_metrics.assumed_threshold.{value, standard_deviation}
        metric is added, representing the F1-score-maximising decision threshold for the model.
    - In all metrics with `standard_deviation`, the metric is calculated only once on the entire
        dataset and stddev reported as "NaN", regardless of how many test data samples are given.

    Parameters
    ----------
    y_real :
        Actual class labels of test data points (assumed 1D numpy array of 0s and 1s)
    y_predict_proba :
        Positive class probability predictions from the model (1D numpy array of floats 0-1)
    y_predict_label :
        Optional assigned class labels from the model. If these are not provided, the
        assumed_threshold will be applied - **NOT** just 0.5!

    Returns
    -------
    report :
        A SageMaker Model Quality-like object describing binary classifier metrics. Dump this to
        JSON and save, to use as a model quality baseline.
    """
    # Validate inputs:
    n_classes = len(np.unique(y_real))
    if n_classes != 2:
        raise ValueError(
            f"y_real contains {n_classes} unique classes. Expected 2: Binary classification"
        )

    precision, recall, thresholds = metrics.precision_recall_curve(y_real, y_predict_proba)
    f1_scores = 2 * recall * precision / (recall + precision)
    best_f1 = np.nanmax(f1_scores)
    f1max_threshold = thresholds[np.nanargmax(f1_scores)]

    if y_predict_label is None:
        print("Using inferred F1-maximizing threshold for metrics")
        y_predict_label = (y_predict_proba >= f1max_threshold).astype(int)

    fpr, tpr, _ = metrics.roc_curve(y_real, y_predict_proba)
    confusion_matrix = metrics.confusion_matrix(y_real, y_predict_label)
    confusion_dict = {}  # Non-normalied dict e.g. { "0": { "1": [N_TRUE_0_PREDICTED_1] }}
    for i_true in range(confusion_matrix.shape[0]):
        confusion_entry = {}
        confusion_dict[str(i_true)] = confusion_entry
        for j_pred in range(confusion_matrix.shape[1]):
            confusion_entry[str(j_pred)] = int(confusion_matrix[i_true, j_pred])

    return {
        "binary_classification_metrics": {
            # Single standard metrics:
            "accuracy": {
                "value": metrics.accuracy_score(y_real, y_predict_label),
                "standard_deviation": "NaN",
            },
            "auc": {
                "value": metrics.roc_auc_score(y_real, y_predict_label),
                "standard_deviation": "NaN",
            },
            "f0_5": {
                "value": metrics.fbeta_score(y_real, y_predict_label, beta=0.5),
                "standard_deviation": "NaN",
            },
            "f1": {
                "value": metrics.f1_score(y_real, y_predict_label),
                "standard_deviation": "NaN",
            },
            "f2": {
                "value": metrics.fbeta_score(y_real, y_predict_label, beta=2),
                "standard_deviation": "NaN",
            },
            "false_negative_rate": {  # FP / N
                "value": confusion_matrix[0, 1] / sum(confusion_matrix[0]),
                "standard_deviation": "NaN",
            },
            "false_positive_rate": {  # FN / P
                "value": confusion_matrix[1, 0] / sum(confusion_matrix[1]),
                "standard_deviation": "NaN",
            },
            "precision": {
              "value": metrics.precision_score(y_real, y_predict_label),
              "standard_deviation": "NaN"
            },
            "recall": {
              "value": metrics.recall_score(y_real, y_predict_label),
              "standard_deviation": "NaN"
            },
            "true_negative_rate": {  # TN / N
                "value": confusion_matrix[0, 0] / sum(confusion_matrix[0]),
                "standard_deviation": "NaN",
            },
            "true_positive_rate": {  # TP / P
                "value": confusion_matrix[1, 1] / sum(confusion_matrix[1]),
                "standard_deviation": "NaN",
            },
            "confusion_matrix": confusion_dict,  # actual -> predicted -> count
            "precision_recall_curve": {
                "precisions": precision.tolist(),
                "recalls": recall.tolist(),
            },
            "receiver_operating_characteristic_curve": {
                "false_positive_rates": fpr.tolist(),
                "true_positive_rates": tpr.tolist(),
            },
            # Custom metrics:
            "assumed_threshold": {
                "value": f1max_threshold,
                "standard_deviation": "NaN",
            },
        },
    }


def generate_binary_classification_report(
    y_real: np.ndarray,
    y_predict_proba: np.ndarray,
    y_predict_label: Optional[np.ndarray] = None,
    decision_threshold: Optional[float] = None,
    class_names_list: Iterable[str] = ("Class 0", "Class 1"),
    title: str = "Model report",
    plot_style: Optional[str] = "ggplot",
) -> dict:
    """Generate a visual report for a binary classifier and return a SageMaker model quality dict

    Parameters
    ----------
    y_real :
        Actual class labels of test data points (assumed 1D numpy array of 0s and 1s)
    y_predict_proba :
        Positive class probability predictions from the model (1D numpy array of floats 0-1)
    y_predict_label :
        Optional assigned class labels from the model. If these are not provided, either
        `decision_threshold` will be used or a threshold inferred.
    decision_threshold :
        Optional confidence threshold above which to assign positive class label. This value is
        ignored if explicit `y_predict_label` labels are provided. If neither `y_predict_label` nor
        `decision_threshold` are provided, a threshold will be automatically selected to maximise
        the F1 score.
    class_names_list :
        Human-readable class names to tag in the graphical report (not used in SageMaker report)
    title :
        Title for the graphical report (not used in SageMaker report)
    plot_style :
        Optional pyplot style to enable (set `None` to avoid configuring this).

    Returns
    -------
    report :
        A SageMaker Model Quality-like object describing binary classifier metrics. See 
        sagemaker_binary_classification_report for details.
    """
    # Validate inputs:
    n_classes = len(np.unique(y_real))
    if n_classes != 2:
        raise ValueError(
            f"y_real contains {n_classes} unique classes. Expected 2: Binary classification"
        )

    if y_predict_label is None:
        if decision_threshold is not None:
            print(f"Applying decision threshold {decision_threshold}")
            y_predict_label = (y_predict_proba > decision_threshold).astype(int)
            label_source = "decision_threshold"
    else:
        label_source = "given labels"

    sagemaker_report = sagemaker_binary_classification_report(
        y_real,
        y_predict_proba,
        y_predict_label=y_predict_label,
    )
    assumed_thresh = sagemaker_report["binary_classification_metrics"]["assumed_threshold"]["value"]
    acc = sagemaker_report["binary_classification_metrics"]["accuracy"]["value"]
    f1 = sagemaker_report["binary_classification_metrics"]["f1"]["value"]
    if y_predict_label is None:
        y_predict_label = (y_predict_proba > assumed_thresh).astype(int)
        label_source = "max F1 threshold"

    # Build up text report:
    ml_report = f"Number of classes: {n_classes}\n"
    for i, class_name in enumerate(class_names_list):
        ml_report += f"{i}: {class_name}\n"

    if decision_threshold is not None:
        ml_report += f"\nDecision threshold: {decision_threshold}\n"
    else:
        ml_report += f"\nF1-maximizing decision threshold: {assumed_thresh:.5f}\n"
    ml_report += "\n---------------------Performance--------------------\n\n"
    metrics_report = metrics.classification_report(y_real, y_predict_label)
    metrics_report += f"\n Total accuracy = {acc:.2%}"
    metrics_report += f"\n F1 score (using {label_source}) = {f1:.2%}"
    ml_report += metrics_report

    # Generate graphs:
    if plot_style is not None:
        plt.style.use(plot_style)
    fig, ax = plt.subplots(2, 2, figsize=(12,9))
    plot_text(ml_report, ax=ax[0,0])
    plot_confusion_matrix(y_real, y_predict_label, class_names_list=class_names_list, ax=ax[0,1])
    plot_precision_recall_curve(y_real, y_predict_proba, ax=ax[1,0])
    plot_roc_curve(y_real, y_predict_proba, ax=ax[1,1])
    fig.suptitle(title, fontsize=15)
    fig.tight_layout()

    return sagemaker_report
