"""Utility functions for data science in Jupyter/JupyterLab notebooks"""

# Python Built-Ins:
import subprocess
import threading
import time

# External Dependencies:
from IPython.display import display, HTML
import ipywidgets as widgets

def upload_in_background(local_path: str, s3_uri: str):
    """Utility function to asynchronously upload (many) files to S3 in a notebook

    Must be run in Jupyter, or in JupyterLab with @jupyter-widgets/jupyterlab-manager extension
    installed, for output to display correctly
    """
    if not s3_uri.lower().startswith("s3://"):
        raise ValueError(
            f"s3_uri must be a URI string like 's3://BUCKETNAME/FOLDERS': Got '{s3_uri}'"
        )

    # We can directly "capture" a function's console output with an IPyWidgets output, but it seems
    # to disconnect after a long period of silence - so we also pass the widget in to the function
    # and use append_stdout() to be safe:
    out = widgets.Output()
    @out.capture()
    def upload_data(out):
        out.append_stdout(
            f"Uploading files from {local_path} to {s3_uri} in the background...\n"
        )
        t0 = time.time()
        proc = subprocess.Popen(
            ["aws", "s3", "sync", "--quiet", "--delete", local_path, s3_uri],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        # Unfortunately for some reason NoSuchBucket errors don't seem to show up in the logs
        # however I try to collect them (tried communicate, separate stderr streams, etc)
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
