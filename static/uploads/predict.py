import argparse
import numpy as np
import cv2
from keras.models import load_model

def predict(image_path):
    # loading the trained model from file
    model = load_model("pneumonia_cnn_model.h5")
    img_size = (150, 150)  # defining the expected image size

    # reading the image from disk
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image {image_path}")

    # resizing the image to match the model input
    img = cv2.resize(img, img_size)

    # normalizing the pixel values to [0–1]
    img = img.astype("float32") / 255.0

    # expanding the dimensions to simulate a batch of size 1
    img = np.expand_dims(img, axis=0)

    # predicting the class using the model
    pred = model.predict(img, verbose=0)[0][0]
    if pred > 0.5:
        return f"PNEUMONIA ({pred:.2f})"
    else:
        return f"NORMAL ({1 - pred:.2f})"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", required=True, help="Path to the image you want to predict")
    args = parser.parse_args()

    # calling the prediction function
    predict(args.image_path)
