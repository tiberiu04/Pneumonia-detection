import argparse
import numpy as np
import cv2
from keras.models import load_model

def predict(image_path):
    model = load_model("pneumonia_cnn_model.h5")
    img_size = (150, 150)

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image {image_path}")
    img = cv2.resize(img, img_size)
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis = 0)

    pred = model.predict(img)[0][0]
    if pred > 0.5:
        print(f"{image_path}: PNEUMONIA ({pred:.2f})")
    else:
        print(f"{image_path}: NORMAL ({1 - pred:.2f})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", required = True, help = "Path to the image")
    args = parser.parse_args()

    predict(args.image_path)