"""CNN-based image classification on SageMaker with TensorFlow and Keras

(Complete me with help from Local Notebook.ipynb, and the NLP example's src/main.py!)
"""

# Dependencies:
import argparse
# TODO: Others?

def parse_args():
    # TODO: Standard pattern for loading parameters in from SageMaker

# TODO: Other function definitions, if you'd like to break up your code into functions?

# Training script:
if __name__ == "__main__":
    # Load arguments from CLI / environment variables:
    args, unknown = parse_args()

    # TODO: Load images from container filesystem into training / test data sets?

    # TODO: Create the Keras model?

    # Fit the Keras model:
    model.fit(
        ?
    )

    # TODO: Evaluate model quality and log metrics?

    # TODO: Save outputs (trained model) to specified folder?
    model.save(
        ?
    )
