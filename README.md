# Getting Started with "Amazon SageMaker 101"

This repository accompanies a hands-on training event to introduce data scientists (and ML-ready developers / technical leaders) to core model training and deployment workflows with [Amazon SageMaker](https://aws.amazon.com/sagemaker/).

Like a "101" course in [the academic sense](https://en.wikipedia.org/wiki/101_(topic)), this will likely **not** be the simplest introduction to SageMaker you can find; nor the fastest way to get started with advanced features like [optimized SageMaker Distributed training](https://docs.aws.amazon.com/sagemaker/latest/dg/distributed-training.html) or [SageMaker Clarify for bias and explainability analyses](https://aws.amazon.com/sagemaker/clarify/).

Instead, these exercises are chosen to demonstrate some core build/train/deploy patterns that we've found help new users to first get productive with SageMaker - and to later understand how the more advanced features fit in.

## Agenda

Sessions in suggested order:

* [builtin_algorithm_hpo_tabular](builtin_algorithm_hpo_tabular): Demonstrating how to use (and tune the hyperparameters of) a **pre-built, SageMaker-provided algorithm** (Applying XGBoost to tabular data)
* (Optional) [custom_sklearn_rf](custom_sklearn_rf): Introductory example showing how to **bring your own algorithm**, using SageMaker's Scikit-Learn container environment as a base (Predicting housing prices)
* [custom_tensorflow_keras_nlp](custom_tensorflow_keras_nlp): Demonstrating how to **bring your own algorithm**, using SageMaker's TensorFlow container environment as a base (Classifying news headline text)
* [migration_challenge_keras_image](migration_challenge_keras_image): A challenge to use what you've learned to **migrate an existing TensorFlow notebook** to SageMaker model training job and real-time inference endpoint deployment (Classifying MNIST DIGITS images)

While the deep learning exercises above are presented in TensorFlow+Keras by default, PyTorch users can explore the [pytorch_alternatives folder](pytorch_alternatives) instead.


## Deploying in Your Own Account

If you've [onboarded to SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio-onboard.html), you can download this repository by launching a **System terminal** (From the "Utilities and files" section of the launcher screen) and running `git clone https://github.com/aws-samples/sagemaker-101-workshop`.

If you prefer to use classic [SageMaker Notebook Instances](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html), you can find a [CloudFormation template](https://aws.amazon.com/cloudformation/resources/templates/) defining the standard setup at [.ee.tpl.yaml](.ee.tpl.yaml). This can be deployed via the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/home).

> **Note:** Some of the examples depend on [ipywidgets](@jupyter-widgets/jupyterlab-manager) for interactive inference demos, which should be installed by default in SageMaker Studio but requires additional setup on a classic Notebook Instance. See the CloudFormation template for an example installing the required libraries via Lifecycle Configuration script.

Depending on your setup, you may be asked to **choose a kernel** when opening some notebooks. There should be guidance at the top of each notebook on suggested kernel types, but if you can't find any, `Python 3 (Data Science)` (on Studio) or `conda_python3` (on Notebook Instances) are likely good options.

You can refer to the [*"How Are Amazon SageMaker Studio Notebooks Different from Notebook Instances?"*](https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks-comparison.html) docs page for more details on differences between the Studio and Notebook Instance environments. As that page notes, SageMaker studio does not yet support [local mode](https://aws.amazon.com/blogs/machine-learning/use-the-amazon-sagemaker-local-mode-to-train-on-your-notebook-instance/): which we find can be useful to accelerate debugging in the migration challenge.


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.


## License

This library is licensed under the MIT-0 License. See the LICENSE file.


## Further Reading

One major focus of this workshop is how SageMaker helps us right-size and seggregate compute resources for different ML tasks, without sacrificing (but ideally accelerating!) data scientist productivity. For more information on this topic, see this post on the AWS Machine Learning Blog: [Right-sizing resources and avoiding unnecessary costs in Amazon SageMaker](https://aws.amazon.com/blogs/machine-learning/right-sizing-resources-and-avoiding-unnecessary-costs-in-amazon-sagemaker/)

As you continue to explore Amazon SageMaker, you'll also find many more useful resources in:

- The official **[Amazon SageMaker Examples repository](https://github.com/aws/amazon-sagemaker-examples)**: with a broad range of code samples covering SageMaker use cases from beginner to expert.
- The **[documentation](https://sagemaker.readthedocs.io/en/stable/)** (and maybe even the [source code](https://github.com/aws/sagemaker-python-sdk)) for the **SageMaker Python SDK**: The high-level, open-source [PyPI library](https://pypi.org/project/sagemaker/) we use when we `import sagemaker`.
- The **[Amazon SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html)**: documenting the SageMaker service itself.

More advanced users may also find it helpful to refer to:

- The **[boto3 reference for SageMaker](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html)** and the **[SageMaker API reference](https://docs.aws.amazon.com/sagemaker/latest/APIReference/Welcome.html)**: in case you have use cases for SageMaker where you want (or need) to use low-level APIs directly, instead of through the `sagemaker` library.
- The **[AWS Deep Learning Containers](https://github.com/aws/deep-learning-containers)** and **[SageMaker Scikit-Learn Containers](https://github.com/aws/sagemaker-scikit-learn-container)** **source code**: For a deeper understanding of the framework container environments.
