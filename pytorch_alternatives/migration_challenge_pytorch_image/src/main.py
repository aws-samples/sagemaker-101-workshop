"""CNN-based image classification on SageMaker with PyTorch

(Complete me with help from Local Notebook.ipynb, and the NLP example's src/main.py!)
"""

# Dependencies:
import argparse
# TODO: Others?

def parse_args():
    # TODO: Standard pattern for loading parameters in from SageMaker

def model_fn(model_dir):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.jit.load(os.path.join(model_dir, 'model.pth'))
    return model

# TODO: Other function definitions, if you'd like to break up your code into functions?

# Training script:
if __name__ == "__main__":
    # TODO: Load arguments from CLI / environment variables?
    args, _ = parse_args()

    # TODO: Load images from container filesystem into training / test data sets?
    
    # TODO: Load dataset into a PyTorch Data Loader with correct batch size

    # TODO: Fit the PyTorch model?
    model = ?
        
    # TODO: Save outputs (trained model) to specified folder?