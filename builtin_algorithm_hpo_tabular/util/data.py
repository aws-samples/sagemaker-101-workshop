# Python Built-Ins:
from io import BytesIO
import os
from time import sleep
from typing import Callable, Dict, Iterable, Optional
from urllib.request import urlopen
from zipfile import ZipFile

# Local Dependencies:
import botocore
import numpy as np
import pandas as pd
import sagemaker
from sagemaker.feature_store.feature_definition import FeatureDefinition
from sagemaker.feature_store.feature_group import FeatureGroup, FeatureParameter


def fetch_sample_data(
    zip_url: str = "https://sagemaker-sample-data-us-west-2.s3-us-west-2.amazonaws.com/autopilot/direct_marketing/bank-additional.zip",
    local_folder: str = "data",
    target_file: str = "bank-additional/bank-additional-full.csv",
) -> str:
    """Fetch the raw sample dataset, download and extract it locally, and return the local file path
    """
    target_file_path = os.path.join(local_folder, target_file)

    if os.path.isdir(local_folder) and os.path.isfile(target_file_path):
        print(f"Skipping download - file already exists {target_file_path}")
    else:
        print(f"Downloading zip data...\n{zip_url}")
        with urlopen(zip_url) as resp:
            with ZipFile(BytesIO(resp.read())) as zip_file:
                print(f"Extracting to {local_folder}...")
                zip_file.extractall(local_folder)

    return target_file_path
    


def transform_df(df: pd.DataFrame) -> pd.DataFrame:
    # Indicator variable to capture when pdays takes a value of 999
    df["no_previous_contact"] = np.where(df["pdays"] == 999, 1, 0)

    # Indicator for individuals not actively employed
    df["not_working"] = np.where(
        np.in1d(df["job"], ["student", "retired", "unemployed"]), 1, 0
    )

    # df = pd.get_dummies(df)  # Convert categorical variables to sets of indicators

    # Replace "y_no" and "y_yes" with a single label column, and bring it to the front:
    # df_model_data = pd.concat(
    #     [
    #         df_model_data["y_yes"].rename("y"),
    #         df_model_data.drop(["y_no", "y_yes"], axis=1),
    #     ],
    #     axis=1,
    # )
    
    # Encode 'y' to numeric so AutoGluon-Tabular predictions can be mapped to labels:
    assert "yes" in df["y"].unique(), "Expected 'y' column to contain 'yes' and 'no'"
    df["y"] = df["y"].apply(lambda y: int(y == "yes"))

    # Move 'y' to front:
    df = df.loc[:, ["y"] + [col for col in df.columns if col != "y"]]

    # Add record identifier and event timestamp fields required for SageMaker Feature Store:
    df["customer_id"] = df.index.to_series().apply(lambda num: f"C-{num:08}")
    df["event_time"] = (pd.Timestamp.utcnow() - pd.DateOffset(years=1)).timestamp()

    return df


def load_sample_data(
    raw_file_path: str,
    fg_s3_uri: str,
    ignore_cols: Iterable[str] = (
        "duration", "emp.var.rate", "cons.price.idx", "cons.conf.idx", "euribor3m", "nr.employed"
    ),
    transform_fn: Callable[[pd.DataFrame], pd.DataFrame] = transform_df,
    feature_group_name: str = "sm101-direct-marketing",
    feature_group_description: str = (
        "Demo Bank Marketing dataset for 'SageMaker 101' workshop, based on "
        "http://archive.ics.uci.edu/ml/datasets/Bank+Marketing"
        # "Demo Bank marketing dataset for 'SageMaker 101' introductory workshop.\n\n"
        # "This is a transformed version of the 'Bank Marketing' UCI dataset for research. Please "
        # "cite: S. Moro, P. Cortez and P. Rita. A Data-Driven Approach to Predict the Success of "
        # "Bank Telemarketing. Decision Support Systems, In press, "
        # "http://dx.doi.org/10.1016/j.dss.2014.03.001\n\n"
        # "Data description at: http://archive.ics.uci.edu/ml/datasets/Bank+Marketing"
    ),
    feature_descriptions: Dict[str, str] = {
        "customer_id": (
            "Unique customer identifier (dummy added for purpose of SageMaker Feature Store)"
        ),
        "event_time": "Event/update timestamp (dummy added for purpose of SageMaker Feature Store)",
        "y": (
            "Has the client subscribed a term deposit? (binary: 0/1). This is the target variable "
            "for our direct marketing example."
        ),
        ## Bank client data:
        "age": "Client's age in years",
        "job": (
            'Type of job (categorical: "admin.","blue-collar","entrepreneur","housemaid",'
            '"management","retired","self-employed","services","student","technician","unemployed",'
            '"unknown")'
        ),
        "marital": (
            'Marital status (categorical: "divorced","married","single","unknown"; note: '
            '"divorced" means divorced or widowed)'
        ),
        "education": (
            'Highest education (categorical: "basic.4y","basic.6y","basic.9y","high.school",'
            '"illiterate","professional.course","university.degree","unknown")'
        ),
        "default": 'Has credit in default? (categorical: "no","yes","unknown")',
        "housing": 'Has housing loan? (categorical: "no","yes","unknown")',
        "loan": 'Has personal loan? (categorical: "no","yes","unknown")',
        ## Related with last contact of current campaign:
        "contact": 'Contact communication type (categorical: "cellular","telephone")',
        "day_of_week": 'Last contact day of the week (categorical: "mon","tue","wed","thu","fri")',
        # "duration": (
        #     'Last contact duration, in seconds (numeric). Important note:  this attribute highly '
        #     'affects the output target (e.g., if duration=0 then y="no"). Yet, the duration is not '
        #     'known before a call is performed. Also, after the end of the call y is obviously '
        #     'known. Thus, this input should only be included for benchmark purposes and should be '
        #     'discarded if the intention is to have a realistic predictive model.'
        # ),
        ## Other attributes:
        "campaign": (
            "Number of contacts performed during this campaign and for this client (numeric, "
            "includes last contact)"
        ),
        "pdays": (
            "Number of days that passed by after the client was last contacted from a previous "
            "campaign (numeric; 999 means client was not previously contacted)"
        ),
        "previous": (
            "Number of contacts performed before this campaign and for this client (numeric)"
        ),
        "poutcome": (
            'Outcome of the previous marketing campaign (categorical: "failure","nonexistent",'
            '"success")'
        ),
        ## Social and economic context attributes:
        # "emp.var.rate": "Employment variation rate - quarterly indicator (numeric)",
        # "cons.price.idx": "Consumer price index - monthly indicator (numeric)",
        # "cons.conf.idx": "Consumer confidence index - monthly indicator (numeric)",
        # "euribor3m": "EURIBOR 3 month rate - daily indicator (numeric)",
        # "nr.employed": "Number of employees - quarterly indicator (numeric)",
        ## Synthetics from transform_fn:
        "no_previous_contact": (
            "Boolean indicator for clients not previously contacted (pdays=999)"
        ),
        "not_working": "Boolean indicator for individuals not actively employed",
    },
    feature_parameters: Dict[str, Dict[str, str]] = {
        "Source": {
            "bank-client": ["age", "job", "marital", "education", "default", "housing", "loan"],
            "last-contact": ["contact", "day_of_week"],
            "other": ["campaign", "pdays", "previous", "poutcome"],
            "subscriptions": ["y"],
            "transforms": ["no_previous_contact", "not_working"],
        },
    },
    fg_record_identifier_field: str = "customer_id",
    fg_event_timestamp_field: str = "event_time",
    sagemaker_session: Optional[sagemaker.Session] = None,
) -> None:
    print(f"Loading {raw_file_path}...")
    df = pd.read_csv(raw_file_path)
    print("Transforming dataframe...")
    df.drop(columns=[col for col in ignore_cols], inplace=True)
    df = transform_fn(df)

    print(f"Setting up SageMaker Feature Store feature group: {feature_group_name}")
    if not sagemaker_session:
        sagemaker_session = sagemaker.Session()
    feature_group = FeatureGroup(name=feature_group_name, sagemaker_session=sagemaker_session)

    # Pandas defaults string fields to 'object' dtype, which FS type inference doesn't like:
    for col in df:
        if pd.api.types.is_object_dtype(df[col].dtype):
            df[col] = df[col].astype(pd.StringDtype())

    #print(df.info())
    feature_group.load_feature_definitions(data_frame=df)

    feature_group.create(
        s3_uri=fg_s3_uri,
        record_identifier_name=fg_record_identifier_field,
        event_time_feature_name=fg_event_timestamp_field,
        role_arn=sagemaker.get_execution_role(sagemaker_session),
        enable_online_store=True,
        description=feature_group_description,
    )
    wait_for_fg_creation(feature_group)

    ingestion_manager = feature_group.ingest(data_frame=df, max_processes=16, wait=False)

    print("Configuring feature metadata...")
    update_meta_calls = {}
    for feature_name, desc in feature_descriptions.items():
        update_meta_calls[feature_name] = {"description": desc}
    for param_name, spec in feature_parameters.items():
        for param_value, features in spec.items():
            for feature_name in features:
                if feature_name not in update_meta_calls:
                    update_meta_calls[feature_name] = {}
                feature_spec = update_meta_calls[feature_name]
                if param_value is None:
                    if "parameter_removals" not in feature_spec:
                        feature_spec["parameter_removals"] = [param_name]
                    else:
                        feature_spec["parameter_removals"].append(param_name)
                else:
                    if "parameter_additions" not in feature_spec:
                        feature_spec["parameter_additions"] = [
                            FeatureParameter(key=param_name, value=param_value),
                        ]
                    else:
                        feature_spec["parameter_additions"].append(
                            FeatureParameter(key=param_name, value=param_value),
                        )
    for feature_name, feature_spec in update_meta_calls.items():
        feature_group.update_feature_metadata(feature_name, **feature_spec)
        sleep(2)

    print("Ingesting data to SageMaker Feature Store...")
    ingestion_manager.wait()
    ingest_timestamp = pd.Timestamp.now()


    print("Waiting for propagation to offline Feature Store...")
    ingest_wait_period = pd.DateOffset(
        minutes=5,  # Technically can take 15mins, but who has time for that
    )
    sleep(((ingest_timestamp + ingest_wait_period) - pd.Timestamp.now()).seconds)

    print("Done!")
    return feature_group_name


def describe_fg_if_exists(feature_group: FeatureGroup) -> Optional[dict]:
    try:
        return feature_group.describe()
    except botocore.exceptions.ClientError as e:
        if "Not Found" in e.response["Error"]["Message"]:
            return None
        else:
            raise e


def wait_for_fg_creation(feature_group):
    status = feature_group.describe().get("FeatureGroupStatus")
    print(
        f"Waiting for creation of Feature Group {feature_group.name} (Initial status {status})",
        end="",
    )
    while status == "Creating":
        print(".", end="")
        sleep(5)
        status = feature_group.describe().get("FeatureGroupStatus")
    print()
    if status != "Created":
        raise RuntimeError(f"Failed to create feature group {feature_group.name}: {status}")
    print(f"Feature Group {feature_group.name} successfully created.")