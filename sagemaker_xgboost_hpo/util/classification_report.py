# -*- coding: utf-8 -*-
"""
Set of helper functions to generate classification reports.
"""



import numpy as np
import matplotlib.pyplot as plt
import itertools
from sklearn import metrics




# Function to plot a nice comfusion matrix
def plot_confusion_matrix(confusion_matrix, 
                          class_names_list=['Class1', 'Class2'],
                          axis=None,
                          title='Confusion matrix',
                          plot_style='ggplot',
                          colormap=plt.cm.Blues):

    if axis is None:  # for standalone plot
        plt.figure()
        ax = plt.gca()
    else:  # for plots inside a subplot
        ax = axis
 
    plt.style.use(plot_style)
    
    # normalizing matrix to [0,100%]
    confusion_matrix_norm = (confusion_matrix.astype('float') / 
                             confusion_matrix.sum(axis=1)[:, np.newaxis])
    confusion_matrix_norm = np.round(100 * confusion_matrix_norm, 2)

    ax.imshow(confusion_matrix_norm,
              interpolation='nearest',
              cmap=colormap,
              vmin=0,  # to make sure colors are scaled between [0,100%]
              vmax=100)
 
    ax.set_title(title)
    tick_marks = np.arange(len(class_names_list))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(class_names_list, rotation=0)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(class_names_list)
    
    for i, j in itertools.product(range(confusion_matrix.shape[0]), 
                                  range(confusion_matrix.shape[1])):
        ax.text(j, i, 
                 str(confusion_matrix[i, j])+'\n('+str(confusion_matrix_norm[i,j])+'%)',
                 horizontalalignment="center",
                 color="white" if confusion_matrix_norm[i, j] > 50 else "black")

    ax.set_ylabel('True label')
    ax.set_xlabel('Predicted label')
    ax.grid(False)
    
    if axis is None:  # for standalone plots
        plt.tight_layout()
        plt.show()




# Function to plot a nice preceision/recall curve for a binary classification model
def plot_precision_recall_curve(y_real,
                                y_predict,
                                axis=None,
                                plot_style='ggplot'):
    
    if axis is None:  # for standalone plot
        plt.figure()
        ax = plt.gca()
    else:  # for plots inside a subplot
        ax = axis

    plt.style.use(plot_style)
    
    metrics_P, metrics_R, _ = metrics.precision_recall_curve(y_real, y_predict)
    metrics_AP = metrics.average_precision_score(y_real, y_predict)
    
    ax.set_aspect(aspect=0.95)
    ax.step(metrics_R, metrics_P, color='b', where='post', linewidth=0.7)
    ax.fill_between(metrics_R, metrics_P, step='post', alpha=0.2, color='b')
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_ylim([0.0, 1.05])
    ax.set_xlim([0.0, 1.05])
    ax.set_title('Precision-Recall curve: AP={0:0.3f}'.format(metrics_AP))
    
    if axis is None:  # for standalone plots
        plt.tight_layout()
        plt.show()




# Function to plot a nice ROC curve for a binary classification model
def plot_roc_curve(y_real,
                   y_predict,
                   axis=None,
                   plot_style='ggplot'):
    
    if axis is None:  # for standalone plot
        plt.figure()
        ax = plt.gca()
    else:  # for plots inside a subplot
        ax = axis
    
    plt.style.use(plot_style)
    
    metrics_FPR, metrics_TPR, _ = metrics.roc_curve(y_real, y_predict)
    metrics_AUC = metrics.roc_auc_score(y_real, y_predict)
    
    ax.set_aspect(aspect=0.95)
    ax.plot(metrics_FPR,
             metrics_TPR,
             color='b',
             linewidth=0.7)
    
    ax.fill_between(metrics_FPR,
                     metrics_TPR,
                     step='post',
                     alpha=0.2,
                     color='b')
    
    ax.plot([0, 1], [0, 1], color='k', linestyle='--', linewidth=1)
    ax.set_xlim([-0.05, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC curve: AUC={0:0.3f}'.format(metrics_AUC))
    
    if axis is None:  # for standalone plots
        plt.tight_layout()
        plt.show()




# Function to plot text inside an image
def plot_text(text, axis=None):

    if axis is None:  # for standalone plot
        plt.figure()
        ax = plt.gca()
    else:  # for plots inside a subplot
        ax = axis
        
    # set background white
    ax.set_axis_off()
    ax.set_frame_on(True)
    ax.grid(False)
    
    ax.text(x=0.8,
            y=0, 
            s=text,
            horizontalalignment="right",
            color="black")




# Function to generate a complete classification report
def generate_classification_report(y_real, 
                                   y_predict_proba, 
                                   decision_threshold=0.5, 
                                   class_names_list=None,
                                   title='Model report',
                                   plot_style='ggplot'):
    
    plt.style.use(plot_style)
    
    if class_names_list is None:
        class_names_list = ['Class 0', 'Class 1']
    
    # find out how many classes we have in the test set
    number_of_classes = len(np.unique(y_real))

    ml_report = 'Number of classes: ' + str(number_of_classes) + '\n'
    
    for i,class_name in enumerate(class_names_list):
        ml_report += str(i) + ': ' + str(class_name) + '\n'
        
    ml_report += '\nDecision threshold: ' + str(decision_threshold) + '\n'

    ml_report += '\n---------------------Performance--------------------\n\n'

    y_decision = y_predict_proba.copy()
    y_decision[y_decision>decision_threshold] = 1
    y_decision[y_decision<1] = 0
    y_decision = y_decision.astype(bool)

    # get initial classification report and more text in it
    metrics_report = metrics.classification_report(y_real, y_decision)
    metrics_ACC = metrics.accuracy_score(y_real, y_decision)
    metrics_report += ('\n Total accuracy = ' + 
                       str(round(metrics_ACC*100,2)) + '%')
    ml_report += metrics_report
    ml_report += '\n\n\n\n\n'

    # generate graphs
    fig, ax = plt.subplots(2, 2, figsize=(12,9))
    plot_text(ml_report, axis=ax[0,0])
    plot_confusion_matrix(metrics.confusion_matrix(y_real, y_decision),
                          class_names_list=class_names_list, axis=ax[0,1])
    plot_precision_recall_curve(y_real, y_predict_proba, axis=ax[1,0])
    plot_roc_curve(y_real, y_predict_proba, axis=ax[1,1])
    fig.suptitle(title, fontsize=15)
    fig.tight_layout()