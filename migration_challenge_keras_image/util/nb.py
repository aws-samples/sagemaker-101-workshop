"""Utility functions for data science in Jupyter/JupyterLab notebooks"""

# Python Built-Ins:
import os
import subprocess
import threading
import time

# External Dependencies:
import boto3
from IPython.display import display, HTML
import ipywidgets as widgets

s3 = boto3.client("s3")

def upload_in_background(local_path: str, s3_uri: str, n_procs: int=0):
    """Utility function to asynchronously upload (many) files to S3 in a notebook

    Must be run in Jupyter, or in JupyterLab with @jupyter-widgets/jupyterlab-manager extension
    installed, for output to display correctly.

    Uploads use the AWS CLI for speed and are optionally parallelized across n_procs processes by sharding
    the *lowest-level folders*: Which of course will only help when uploading folders with subfolders.
    """
    if not s3_uri.lower().startswith("s3://"):
        raise ValueError(
            f"s3_uri must be a URI string like 's3://BUCKETNAME/FOLDERS': Got '{s3_uri}'"
        )
    # Normalize inputs to no trailing slash:
    if local_path.endswith("/"):
        local_path = local_path[:-1]
    if s3_uri.endswith("/"):
        s3_uri = s3_uri[:-1]

    # Validate the bucket exists and we have access
    # (Because for some reason NoSuchBucket errors keep not surfacing in the subprocess call later)
    s3_bucket, _, S3_key = s3_uri[len("s3://"):].partition("/")
    try:
        s3.head_bucket(Bucket=s3_bucket)
    except s3.exceptions.ClientError as e:
        errcode = e.response.get("Error", {}).get("Code")
        if errcode in (404, "404"):
            raise ValueError(f"No such bucket {s3_bucket} (from s3_uri {s3_uri})") from e
        elif errcode in (403, "403"):
            raise ValueError(f"No permission to access {s3_bucket} (from s3_uri {s3_uri})") from e
        else:
            raise e

    # We can directly "capture" a function's console output with an IPyWidgets output, but it seems
    # to disconnect after a long period of silence - so we also pass the widget in to the function
    # and use append_stdout() to be safe:
    out = widgets.Output()
    @out.capture()
    def upload_data(out):
        out.append_stdout(
            f"Uploading files from {local_path} to {s3_uri} in the background...\n"
        )
        if n_procs:
            # Retrieve the list of lowest-level subfolders in the input:
            proc_folders = []
            for currpath, dirs, files in os.walk(local_path):
                if len(dirs) == 0:
                    # Exclude the root path from the results:
                    proc_folders.append(currpath[len(local_path):])
            if len(proc_folders) <= 1:
                out.append_stdout(
                    "WARNING: n_procs parallelism only available for local_paths with subfolders.\n"
                )
                proc_folders = None
        else:
            proc_folders = None
            
        t0 = time.time()

        if proc_folders:
            # Spawn the parallel processor:
            out.append_stdout(
                "WARNING: Uploading in parallel mode can cause some error messages not to show.\n"
            )
            proc = subprocess.Popen(
                [
                    # xargs distributes null-separated stdin inputs to n_procs, replacing the token '{}':
                    "xargs", "-n1", "-0", f"-P{n_procs}", "-I", "{}",
                    # Each process is an s3 cp command for the given subfolder:
                    "aws", "s3", "cp", "--recursive", "--quiet", local_path+"{}/", s3_uri+"{}/",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            # Submit the list of subdirectories:
            proc.stdin.write("\0".join(proc_folders).encode("UTF-8"))
            proc.stdin.close()
        else:
            # Spawn the standard single-process uploader:
            proc = subprocess.Popen(
                ["aws", "s3", "sync", "--quiet", "--delete", local_path, s3_uri],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        # Unfortunately for some reason NoSuchBucket errors don't seem to show up in the logs
        # however I try to collect them (tried communicate, separate stderr streams, etc)... There are
        # probably some other errors that get hidden too.
        # TODO: Better error diagnostics
        for line in proc.stdout:
            out.append_stdout(line.decode("UTF-8"))

        retcode = proc.wait()
        if retcode:
            raise RuntimeError(
                f"Failed to complete upload: S3 Sync Exit code {retcode}... Check your bucket?"
            )
        else:
            t1 = time.time()
            mins, secs = divmod((t1 - t0), 60)
            out.append_stdout(f"Done in {int(mins)} mins {int(secs)} secs")

    display(out)
    threading.Thread(target=upload_data,args=(out,)).start()
