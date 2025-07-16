from flask import Flask, render_template, request
from keras.models import load_model
import numpy as np
import cv2
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model = load_model("pneumonia_cnn_model.h5")

IMG_SIZE = (150, 150)

def predict_image(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, IMG_SIZE)
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)
    pred = model.predict(img)[0][0]
    if pred > 0.5:
        return f"PNEUMONIA ({pred:.2f})"
    else:
        return f"NORMAL ({1 - pred:.2f})"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predictions", methods=["GET", "POST"])
def predictions():
    result = None
    uploaded_image = None
    if request.method == "POST":
        file = request.files["image"]
        if file:
            path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(path)
            result = predict_image(path)
            uploaded_image = path
    return render_template("predictions.html", result=result, uploaded_image=uploaded_image)


@app.route("/settings")
def settings():
    return render_template("settings.html")


if __name__ == "__main__":
    app.run(debug=True)
