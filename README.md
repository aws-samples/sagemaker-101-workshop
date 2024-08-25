# Getting Started with "Amazon SageMaker 101"

This repository accompanies a hands-on training event to introduce data scientists (and ML-ready developers / technical leaders) to core model training and deployment workflows with [Amazon SageMaker](https://aws.amazon.com/sagemaker/).

Like a "101" course in [the academic sense](https://en.wikipedia.org/wiki/101_(topic)), this will likely **not** be the simplest introduction to SageMaker you can find; nor the fastest way to get started with advanced features like [optimized SageMaker Distributed training](https://docs.aws.amazon.com/sagemaker/latest/dg/distributed-training.html) or [SageMaker Clarify for bias and explainability analyses](https://aws.amazon.com/sagemaker/clarify/).

Instead, these exercises are chosen to demonstrate some core build/train/deploy patterns that we've found help new users to first get productive with SageMaker - and to later understand how the more advanced features fit in.

## Agenda

An interactive walkthrough of the content with screenshots is available at:

> **[https://sagemaker-101-workshop.workshop.aws/](https://sagemaker-101-workshop.workshop.aws/)**

Sessions in suggested order:

1. [builtin_algorithm_hpo_tabular](builtin_algorithm_hpo_tabular): Explore some **pre-built algorithms** and tools for tabular data, including [SageMaker Canvas](https://aws.amazon.com/sagemaker/canvas/), [SageMaker AutoML APIs](https://docs.aws.amazon.com/sagemaker/latest/dg/use-auto-ml.html), the [XGBoost built-in algorithm](https://docs.aws.amazon.com/sagemaker/latest/dg/xgboost.html), and [automatic hyperparameter tuning](https://docs.aws.amazon.com/sagemaker/latest/dg/automatic-model-tuning.html)
    - This module also includes a quick initial look at [SageMaker Feature Store](https://docs.aws.amazon.com/sagemaker/latest/dg/feature-store.html), [SageMaker Model Registry](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html), and the [AutoGluon built-in algorithm](https://docs.aws.amazon.com/sagemaker/latest/dg/autogluon-tabular.html) - but you don't need to dive deep on these topics.
1. [custom_script_demos](custom_script_demos): See how you can train and deploy your own models on SageMaker with **custom Python scripts** and the pre-built framework containers
    - (Optional) Start with [sklearn_reg](custom_script_demos/sklearn_reg) for an introduction if you're new to deep learning but familiar with Scikit-Learn
    - See [huggingface_nlp](custom_script_demos/sklearn_reg) (preferred) for a side-by-side comparison of in-notebook versus on-SageMaker model training and inference for text classification - or alternatively the custom CNN-based [keras_nlp](custom_script_demos/keras_nlp) or [pytorch_nlp](custom_script_demos/pytorch_nlp) examples.
1. [migration_challenge](migration_challenge): **Apply** what you learned to port an in-notebook workflow to a SageMaker training job + endpoint deployment on your own
    - Choose the [sklearn_cls](migration_challenge/sklearn_cls), [keras_mnist](migration_challenge/keras_mnist) or [pytorch_mnist](migration_challenge/pytorch_mnist) challenge, depending which ML framework you're most comfortable with.


## Deploying in Your Own Account

The recommended way to explore these exercises is to **[onboard to SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio-onboard.html)**. Once you've done this, you can download this repository by launching a **System terminal** (From the "Utilities and files" section of the launcher screen inside Studio) and running `git clone https://github.com/aws-samples/sagemaker-101-workshop`.

If you prefer to use classic [SageMaker Notebook Instances](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html), you can find a [CloudFormation template](https://aws.amazon.com/cloudformation/resources/templates/) defining a simple setup at [.simple.cf.yaml](.simple.cf.yaml). This can be deployed via the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/home).

You can refer to the [*"How Are Amazon SageMaker Studio Notebooks Different from Notebook Instances?"*](https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks-comparison.html) docs page for more details on differences between the Studio and Notebook Instance environments.

Depending on your setup, you may be asked to **choose a kernel** when opening some notebooks. There should be guidance at the top of each notebook on suggested kernel types, but if you can't find any, `Data Science 3.0 (Python 3)` (on Studio) or `conda_python3` (on Notebook Instances) are likely good options.

### Setting up widgets and code completion (JupyterLab extensions)

Some of the examples depend on [ipywidgets](@jupyter-widgets/jupyterlab-manager) and [ipycanvas](https://ipycanvas.readthedocs.io/en/latest/) for interactive inference demo widgets (but do provide code-only alternatives).

We also usually enable some additional JupyterLab extensions powered by [jupyterlab-lsp](https://github.com/jupyter-lsp/jupyterlab-lsp#readme) and [jupyterlab-s3-browser](https://github.com/IBM/jupyterlab-s3-browser#readme) to improve user experience. You can find more information about these extensions in [this AWS ML blog post](https://aws.amazon.com/blogs/machine-learning/amazon-sagemaker-studio-and-sagemaker-notebook-instance-now-come-with-jupyterlab-3-notebooks-to-boost-developer-productivity/)

`ipywidgets` should be available by default on SageMaker Studio, but not on Notebook Instances when we last tested. The other extensions require installation.

To see how we automate these extra setup steps for AWS-run events, you can refer to the **lifecycle configuration scripts** in our CloudFormation templates. For a [Notebook Instance LCC](https://docs.amazonaws.cn/en_us/sagemaker/latest/dg/notebook-lifecycle-config.html), see the `AWS::SageMaker::NotebookInstanceLifecycleConfig` in [.simple.cf.yaml](.simple.cf.yaml). For a [SageMaker Studio LCC](https://docs.amazonaws.cn/en_us/sagemaker/latest/dg/studio-lcc-create.html), see the `Custom::StudioLifecycleConfig` in [.infrastructure/template.sam.yaml](.infrastructure/template.sam.yaml).


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.


## License

This library is licensed under the MIT-0 License. See the LICENSE file.


## Further Reading

One major focus of this workshop is how SageMaker helps us right-size and segregate compute resources for different ML tasks, without sacrificing (and ideally accelerating!) data scientist productivity. For more information on this topic, see this post on the AWS Machine Learning Blog: [Right-sizing resources and avoiding unnecessary costs in Amazon SageMaker](https://aws.amazon.com/blogs/machine-learning/right-sizing-resources-and-avoiding-unnecessary-costs-in-amazon-sagemaker/)

For a workshop that starts with a similar migration-based approach, but dives further into automated pipelines and CI/CD, check out [aws-samples/amazon-sagemaker-from-idea-to-production](https://github.com/aws-samples/amazon-sagemaker-from-idea-to-production).

As you continue to explore Amazon SageMaker, you'll also find many more useful resources in:

- The official **[Amazon SageMaker Examples repository](https://github.com/aws/amazon-sagemaker-examples)**: with a broad range of code samples covering SageMaker use cases from beginner to expert.
- The **[documentation](https://sagemaker.readthedocs.io/en/stable/)** (and maybe even the [source code](https://github.com/aws/sagemaker-python-sdk)) for the **SageMaker Python SDK**: The high-level, open-source [PyPI library](https://pypi.org/project/sagemaker/) we use when we `import sagemaker`.
- The **[Amazon SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html)**: documenting the SageMaker service itself.
    - Built-in Algorithms **[Docker Registry Paths](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-algo-docker-registry-paths.html)**
    - Built-in Algorithms data formats for **[training](https://docs.aws.amazon.com/sagemaker/latest/dg/cdf-training.html)** and **[inference](https://docs.aws.amazon.com/sagemaker/latest/dg/cdf-inference.html)**

More advanced users may also find it helpful to refer to:

- The **[boto3 reference for SageMaker](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html)** and the **[SageMaker API reference](https://docs.aws.amazon.com/sagemaker/latest/APIReference/Welcome.html)**: in case you have use cases for SageMaker where you want (or need) to use low-level APIs directly, instead of through the `sagemaker` library.
- The **[AWS Deep Learning Containers](https://github.com/aws/deep-learning-containers)** and **[SageMaker Scikit-Learn Containers](https://github.com/aws/sagemaker-scikit-learn-container)** **source code**: For a deeper understanding of the framework container environments.
