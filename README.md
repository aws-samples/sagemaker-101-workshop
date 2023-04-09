# "Amazon SageMaker 101" 시작하기

이 리포지토리는 데이터 과학자 (혹은 ML 개발자/테크니컬 리더) 에게 [Amazon SageMaker] (https://aws.amazon.com/sagemaker/) 를 사용한 핵심 모델 학습 및 배포 워크플로를 소개하는 실습 교육 이벤트입니다.

[학문적 의미] (https://en.wikipedia.org/wiki/101_(topic)) 의 “101” 강좌처럼, 이 강좌는 아마도 가장 간단한 SageMaker 입문 과정이 **아니고**, [최적화된 SageMaker 분산 교육] (https://docs.aws.amazon.com/sagemaker/latest/dg/distributed-training.html) 또는 [편향 및 설명 가능성 분석을 위한 SageMaker Clarify] (https://aws.amazon.com/sagemaker/clarify/) 와 같은 고급 기능을 시작하는 가장 빠른 방법도 아닐 것입니다.

대신 이 워크샾은 신규 사용자가 SageMaker 를 사용하여 생산성을 높이고 나중에 고급 기능이 어떻게 적용되는지 이해하는 데 도움이 되는 몇 가지 핵심 기능등, 빌드 -> 트레이닝 -> 배포 패턴을 보여주기 위해 선택되었습니다.

## 자세한 내용

스크린샷이 포함된 인터렉티브한 컨텐츠는 다음에서 확인할 수 있습니다:

> **[https://sagemaker-101-workshop.workshop.aws/](https://sagemaker-101-workshop.workshop.aws/)**


이 세션의 제안된 순서:

1.[builtin_algorithm_hpo_tabular] (builtin_algorithm_hpo_tabular): [SageMaker Autopilot AutoML] (https://aws.amazon.com/sagemaker/autopilot/), [XGBoost 내장 알고리즘] (https://docs.aws.amazon.com/sagemaker/latest/dg/xgboost.html), [자동 하이퍼파라미터 조정] (https://docs.aws.amazon.com/sagemaker/latest/dg/automatic-model-tuning.html) 등 테이블 형식 데이터를 위한 몇 가지 **사전 빌드된 알고리즘** 및 도구를 살펴보세요.
    - 이 모듈에는 [SageMaker Feature Store] (https://docs.aws.amazon.com/sagemaker/latest/dg/feature-store.html), [SageMaker 모델 레지스트리] (https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html) 및 [AutoGluon 내장 알고리즘] (https://docs.aws.amazon.com/sagemaker/latest/dg/autogluon-tabular.html) 에 대한 간략한 초기 설명도 포함되어 있지만 이러한 주제에 대해 자세히 알아볼 필요는 없습니다.
1.[custom_script_demos] (custom_script_demos): **사용자 지정 Python 스크립트** 및 사전 빌드된 프레임워크 컨테이너를 사용하여 SageMaker 에서 자체 모델을 학습하고 배포하는 방법을 알아보십시오.
    - (선택 사항) 딥 러닝은 처음이지만 Scikit-Learn 에 익숙하다면 [sklearn_reg] (custom_script_demos/sklearn_reg) 로 시작하십시오.
    - 텍스트 분류를 위한 노트북 내 모델 학습과 On-SageMaker 모델 학습 및 추론을 나란히 비교하려면 [huggingface_nlp] (custom_script_demos/huggingface_nlp) (권장) 또는 사용자 지정 CNN 기반 [keras_nlp] (custom_script_demos/keras_nlp) 또는 [pytorch_nlp] (custom_script_nlp) 를 참조하십시오. pt_demos/pytorch_nlp) 예제.
1.[마이그레이션_챌린지] (migration_challenge): **노트북 내 워크플로를 SageMaker 학습 작업+엔드포인트 배포에 직접 이식하기 위해 배운 내용을 적용**
 - 가장 편한 ML 프레임워크에 따라 [sklearn_cls] (migration_challenge/sklearn_cls), [keras_mnist] (마이그레이션_챌린지/keras_mnist) 또는 [pytorch_mnist] (migration_challenge/pytorch_mnist) 챌린지를 선택하세요.


## 계정에 배포하기

이러한 연습을 살펴보는 데 권장되는 방법은** [SageMaker Studio 로의 온보딩] (https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio-onboard.html) **을 사용하는 것입니다.이 작업을 완료했으면, **시스템 터미널** (Studio 내부 런처 화면의 “유틸리티 및 파일” 섹션에서) 을 실행하고 `git clone https://github.com/aws-samples/sagemaker-101-workshop` 을 실행하여 이 리포지토리를 다운로드할 수 있습니다.

클래식 [SageMaker 노트북 인스턴스] (https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html) 를 사용하고 싶다면 [.simple.cf.yaml] (.simple.cf.yaml) 에서 간단한 설정을 정의하는 [클라우드포메이션 템플릿] (https://aws.amazon.com/cloudformation/resources/templates/) 을 찾을 수 있습니다. 이는 [AWS 클라우드포메이션 콘솔] (https://console.aws.amazon.com/cloudformation/home) 을 통해 배포할 수 있습니다.

[*"Amazon SageMaker 스튜디오 노트북은 노트북 인스턴스와 어떻게 다릅니까?” 를 참조하십시오.*] (https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks-comparison.html) 문서 페이지에서 Studio 와 노트북 인스턴스 환경 간의 차이점에 대한 자세한 내용을 볼 수 있습니다.

설정에 따라 일부 노트북을 열 때 **커널을 선택**하라는 메시지가 표시될 수 있습니다. 각 노트북 상단에 제안된 커널 유형에 대한 지침이 있어야 하지만, 찾을 수 없다면 `데이터 과학 3.0 (Python 3)` (Studio) 또는 `conda_python3` (노트북 인스턴스) 이 좋은 옵션일 것입니다.


### 위젯 설정 및 코드 완성 (JupyterLab 확장 프로그램)

일부 예제는 인터렉티브한 추론 데모 위젯 [ipywidgets] (@jupyter -widgets/jupyterlab-manager) 및 [ipycanvas] (https://ipycanvas.readthedocs.io/en/latest/) 에 의존합니다 (하지만 코드 역시 제공함).

또한, 사용자 경험을 개선하기 위해 [jupyterlab-lsp] (https://github.com/jupyter-lsp/jupyterlab-lsp#readme) 및 [jupyterlab-s3-browser] (https://github.com/IBM/jupyterlab-s3-browser#readme) 에서 제공하는 일부 추가 JupyterLab 확장 프로그램을 활성화합니다. 이러한 확장 프로그램에 대한 자세한 내용은 [이 AWS ML 블로그 게시물] (https://aws.amazon.com/blogs/machine-learning/amazon-sagemaker-studio-and-sagemaker-notebook-instance-now-come-with-jupyterlab-3-notebooks-to-boost-developer-productivity/) 에서 확인할 수 있습니다.

`ipywidgets` 은 SageMaker Studio 에서 설치가 필요합니다.

AWS-Run 이벤트에 대한 이러한 추가 설정 단계를 자동화하는 방법을 알아보려면 CloudFormation 템플릿의 **라이프사이클 구성 스크립트**를 참조하십시오.[노트북 인스턴스 LCC] (https://docs.amazonaws.cn/en_us/sagemaker/latest/dg/notebook-lifecycle-config.html) 에 대해서는 [.simple.cf.yaml] (.simple.cf.yaml) 에 있는 `AWS::SageMaker::NotebookInstanceLifecycleConfig` 을 참조하십시오.[SageMaker Studio LCC] (https://docs.amazonaws.cn/en_us/sagemaker/latest/dg/studio-lcc-create.html) 의 경우 [.infrastructure/template.sam.yaml] (.infrastructure/template.sam.yaml) 에 있는 `Custom::StudioLifecycleConfig` 을 참조하십시오.


## 보안

이 곳 [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) 을 참조하세요.


## 라이센스

이 라이브러리는 MIT-0 License 에 속해 있습니다. LICENSE 를 참조하세요.


## Further Reading

이 워크숍의 주요 초점 중 하나는 SageMaker 를 통해 어떻게 다른 ML워크로드에 맞게 컴퓨팅 리소스의 크기를 조정하고 분리하여 성능 저하 없이 (이상적으로는 가속화를 기대) 할 수 있는가 입니다. 데이터 과학자의 생산성 주제에 대한 자세한 내용은 AWS 기계 학습 블로그의 다음 게시물을 참조하십시오. [Amazon SageMaker의 리소스 크기 조정 및 불필요한 비용 방지] (https://aws.amazon.com/blogs/machine-learning/right-sizing-resources-and-avoiding-unnecessary-costs-in-amazon-sagemaker/)

이와 유사한 마이그레이션 기반 접근 방식으로 시작하지만 자동화된 파이프라인 및 CI/CD 에 대해 더 자세히 알아보는 워크샾을 보려면 [aws-samples/amazon-sagemaker-from-idea-production] (https://github.com/aws-samples/amazon-sagemaker-from-idea-to-production) 을 참조하십시오.

Amazon SageMaker 를 계속 사용하면서 다음에서도 유용한 리소스를 많이 찾을 수 있습니다:

- 공식** [Amazon SageMaker 예제 리포지토리] (https://github.com/aws/amazon-sagemaker-examples) **: 초보자부터 전문가까지 SageMaker 사용 사례를 다루는 광범위한 코드 샘플이 포함되어 있습니다.
- **SageMaker Python SDK**의 ** [문서] (https://sagemaker.readthedocs.io/en/stable/) ** (그리고 아마도 [소스 코드] (https://github.com/aws/sagemaker-python-sdk)): `import sagemaker` 할 때 사용하는 고급 오픈 소스 [PyPI 라이브러리] (https://pypi.org/project/sagemaker/) 입니다.
- ** [Amazon SageMaker 개발자 가이드] (https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html) **: SageMaker 서비스 자체를 문서화합니다.

고급 사용자는 다음을 참조하는 것도 도움이 될 수 있습니다:

- ** [SageMaker용 boto3 레퍼런스] (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html) ** 및 ** [SageMaker API 레퍼런스] (https://docs.aws.amazon.com/sagemaker/latest/APIReference/Welcome.html) **: `sagemaker` 라이브러리 대신 API를 직접 사용하려는 (또는 필요한) SageMaker의 사용 사례가 있는 경우
- ** [AWS 딥 러닝 컨테이너] (https://github.com/aws/deep-learning-containers) ** 및 ** [SageMaker Scikit-Learn Containers] (https://github.com/aws/sagemaker-scikit-learn-container) ** **소스 코드**: 프레임워크 컨테이너 환경에 대한 심층적인 이해를 위한 것입니다.
