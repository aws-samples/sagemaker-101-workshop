# Getting Started with Amazon SageMaker

This repository accompanies a hands-on training event to introduce data scientists (and ML-ready developers / technical leaders) to core model training and deployment workflows with [Amazon SageMaker](https://aws.amazon.com/sagemaker/).

## Agenda

Sessions in suggested order:

* [builtin_algorithm_hpo_tabular](builtin_algorithm_hpo_tabular): Demonstrating how to use (and tune the hyperparameters of) a **pre-built, SageMaker-provided algorithm** (Applying XGBoost to tabular data)
* (Optional) [custom_sklearn_rf](custom_sklearn_rf): Introductory example showing how to **bring your own algorithm**, using SageMaker's SKLearn container environment as a base (Predicting housing prices)
* [custom_tensorflow_keras_nlp](custom_tensorflow_keras_nlp): Demonstrating how to **bring your own algorithm**, using SageMaker's TensorFlow container environment as a base (Classifying news headline text)
* [migration_challenge_keras_image](migration_challenge_keras_image): A challenge to use what you've learned to **migrate an existing notebook** to SageMaker model training job and real-time inference endpoint deployment (Classifying MNIST DIGITS images)


## Deploying in Your Own Account

Our standard setup for this workshop is detailed in [.ee.tpl.yaml](.ee.tpl.yaml), a [CloudFormation template](https://aws.amazon.com/cloudformation/resources/templates/) file. You can deploy the same via the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/home).

If you've [onboarded to SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio-onboard.html) and would like to use that **instead** of a Notebook Instance, you'll need to take the following additional steps:

1. To download this repository, launch a **System terminal** (from the *Other* section of the launcher screen) and run `git clone https://github.com/apac-ml-tfc/sagemaker-workshop-101`.
1. You'll be asked to select a kernel when you first open each notebook, because the available kernels in Studio differ from those in Notebook Instances. Use **Python 3 (Data Science)** as standard and **Python 3 (TensorFlow CPU Optimized)** specifically for the 'local' notebooks in NLP and migration challenge folders (which fit TensorFlow models within the notebook itself).

You can refer to the [*"How Are Amazon SageMaker Studio Notebooks Different from Notebook Instances?"*](https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks-comparison.html) docs page for more details on differences between the Studio and Notebook Instance environments. As that page notes, SageMaker studio does not yet support [local mode](https://aws.amazon.com/blogs/machine-learning/use-the-amazon-sagemaker-local-mode-to-train-on-your-notebook-instance/): which we find can be useful to accelerate debugging in the migration challenge, and is one reason we typically run this session on Notebook Instances instead.


## Further Reading

One major focus of this workshop is how SageMaker helps us right-size and seggregate compute resources for different ML tasks, without sacrificing (but ideally accelerating!) data scientist productivity.

For more information on this topic, see this post on the AWS Machine Learning Blog: [Right-sizing resources and avoiding unnecessary costs in Amazon SageMaker](https://aws.amazon.com/blogs/machine-learning/right-sizing-resources-and-avoiding-unnecessary-costs-in-amazon-sagemaker/)
