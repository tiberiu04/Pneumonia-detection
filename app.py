from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import smtplib
from email.message import EmailMessage
from keras.models import load_model
import numpy as np
import cv2
import os
import logging
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import json
from functools import wraps
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static/logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/logs', exist_ok=True)

# Load model with error handling
try:
    model = load_model("pneumonia_cnn_model.h5")
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    model = None

IMG_SIZE = (150, 150)

# Model performance metrics (you can update these with actual values)
MODEL_METRICS = {
    'accuracy': 95.2,
    'precision': 94.8,
    'recall': 96.1,
    'f1_score': 95.4,
    'training_samples': 5856,
    'validation_samples': 624,
    'test_samples': 624
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_prediction(image_path, prediction, confidence, processing_time):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'image_path': image_path,
        'prediction': prediction,
        'confidence': confidence,
        'processing_time': processing_time,
        'model_version': '1.0'
    }
    
    try:
        with open('static/logs/predictions.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"Failed to log prediction: {str(e)}")

def get_natural_remedies(prediction, confidence):
    remedies = {
        'general': [
            "🫖 Drink plenty of warm fluids (herbal teas, warm water with honey)",
            "🍯 Honey has natural antibacterial properties - take 1-2 teaspoons daily",
            "🧄 Garlic contains allicin, which has antimicrobial effects",
            "🫁 Practice deep breathing exercises to improve lung function",
            "😴 Get adequate rest to support immune system recovery",
            "🌿 Ginger tea can help reduce inflammation and boost immunity"
        ],
        'mild': [
            "🌿 Drink eucalyptus tea or inhale eucalyptus steam",
            "🍋 Warm lemon water with honey to soothe throat and boost vitamin C",
            "🥣 Chicken soup provides hydration and nutrients for recovery",
            "🌱 Turmeric milk (golden milk) has anti-inflammatory properties",
            "🫖 Thyme tea has natural expectorant properties",
            "🧘 Light yoga or stretching to maintain circulation"
        ],
        'moderate': [
            "🫖 Oregano oil (diluted) has strong antimicrobial properties",
            "🍄 Mushroom broths (shiitake, reishi) support immune function",
            "🌿 Fenugreek tea helps break down mucus and reduce inflammation",
            "🫁 Steam inhalation with salt water 2-3 times daily",
            "🥄 Apple cider vinegar diluted in water may help alkalinize the body",
            "🌱 Elderberry syrup supports immune system function"
        ],
        'severe': [
            "⚠️ SEEK IMMEDIATE MEDICAL ATTENTION - These are supportive measures only",
            "🏥 Contact healthcare provider or emergency services immediately",
            "💊 Natural remedies should complement, not replace, medical treatment",
            "🫁 Maintain upright position to ease breathing",
            "💧 Stay hydrated with small, frequent sips of water",
            "🌡️ Monitor temperature and breathing rate closely"
        ]
    }
    
    if prediction == "NORMAL":
        return {
            'severity': 'none',
            'message': '✅ No pneumonia detected. Maintain good respiratory health with these preventive measures:',
            'remedies': [
                "🫁 Practice regular deep breathing exercises",
                "🏃 Regular exercise to strengthen respiratory system",
                "🥗 Maintain a balanced diet rich in vitamins C and D",
                "💧 Stay well-hydrated throughout the day",
                "😴 Get 7-9 hours of quality sleep",
                "🚭 Avoid smoking and secondhand smoke"
            ]
        }
    
    # Determine severity based on confidence
    if confidence < 0.65:
        severity = 'mild'
        message = '🟡 Mild pneumonia indicators detected. Consider these natural supportive measures:'
    elif confidence < 0.85:
        severity = 'moderate'
        message = '🟠 Moderate pneumonia indicators detected. Use these remedies alongside medical consultation:'
    else:
        severity = 'severe'
        message = '🔴 Strong pneumonia indicators detected. SEEK IMMEDIATE MEDICAL ATTENTION:'
    
    selected_remedies = remedies['general'][:3] + remedies[severity]
    
    return {
        'severity': severity,
        'message': message,
        'remedies': selected_remedies
    }

def predict_image(image_path):
    if model is None:
        raise Exception("Model not loaded")
    
    start_time = time.time()
    
    try:
        # Load and preprocess image
        img = cv2.imread(image_path)
        if img is None:
            raise Exception("Could not load image")
        
        img = cv2.resize(img, IMG_SIZE)
        img = img.astype("float32") / 255.0
        img = np.expand_dims(img, axis=0)
        
        # Make prediction
        pred = model.predict(img)[0][0]
        processing_time = time.time() - start_time
        
        # Determine result
        if pred > 0.5:
            result = "PNEUMONIA"
            confidence = float(pred)
        else:
            result = "NORMAL"
            confidence = float(1 - pred)
        
        # Get natural remedies
        remedies = get_natural_remedies(result, confidence)
        
        # Log prediction
        log_prediction(image_path, result, confidence, processing_time)
        
        return {
            'prediction': result,
            'confidence': confidence,
            'processing_time': processing_time,
            'remedies': remedies
        }
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise

def rate_limit(max_requests=10, window=60):
    requests = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            now = time.time()
            
            # Clean old requests
            if client_ip in requests:
                requests[client_ip] = [req_time for req_time in requests[client_ip] if now - req_time < window]
            else:
                requests[client_ip] = []
            
            # Check rate limit
            if len(requests[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            requests[client_ip].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route("/")
def home():
    return render_template("index.html", metrics=MODEL_METRICS)

@app.route("/predictions", methods=["GET", "POST"])
def predictions():
    result = None
    uploaded_image = None
    error_message = None
    
    if request.method == "POST":
        try:
            # Check if file was uploaded
            if 'image' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['image']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # Secure filename and save
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                # Make prediction
                prediction_result = predict_image(filepath)
                
                result = {
                    'prediction': prediction_result['prediction'],
                    'confidence': prediction_result['confidence'],
                    'processing_time': prediction_result['processing_time']
                }
                uploaded_image = filepath
                
                flash(f'Analysis complete! Prediction: {result["prediction"]} (Confidence: {result["confidence"]:.1%})', 'success')
                
            else:
                flash('Invalid file type. Please upload PNG, JPG, or JPEG files only.', 'error')
                
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            error_message = "An error occurred during analysis. Please try again."
            flash(error_message, 'error')
    
    return render_template("predictions.html", 
                         result=result, 
                         uploaded_image=uploaded_image,
                         error_message=error_message)

@app.route("/api/predict", methods=["POST"])
@rate_limit(max_requests=20, window=60)
def api_predict():
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Use PNG, JPG, or JPEG'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        unique_filename = f"api_{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        try:
            # Make prediction
            prediction_result = predict_image(filepath)
            
            return jsonify({
                'success': True,
                'prediction': prediction_result['prediction'],
                'confidence': prediction_result['confidence'],
                'processing_time': prediction_result['processing_time'],
                'model_version': '1.0'
            })
            
        finally:
            # Clean up temporary file
            try:
                os.remove(filepath)
            except:
                pass
                
    except Exception as e:
        logger.error(f"API prediction error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route("/api/health")
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route("/api/metrics")
def get_metrics():
    """Get model performance metrics"""
    return jsonify(MODEL_METRICS)

@app.route("/settings")
def settings():
    return render_template("settings.html", metrics=MODEL_METRICS)

@app.route("/about")
def about():
    return render_template("about.html")

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

if __name__ == "__main__":
    logger.info("Starting Pneumonia Detection Application")
    app.run(debug=True, host='0.0.0.0', port=5000)
