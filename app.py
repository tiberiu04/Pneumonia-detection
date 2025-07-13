from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
from predict import predict

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    uploaded_image = None  # ✅ inițializezi aici

    if request.method == "POST":
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Capturăm output-ul de la predict()
            result = predict(filepath)
            uploaded_image = filepath  # ✅ setezi doar dacă ai uploadat

    return render_template("index.html", result=result, uploaded_image=uploaded_image)


if __name__ == "__main__":
    app.run(debug=True)
