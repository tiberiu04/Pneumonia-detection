from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import smtplib
from email.message import EmailMessage
from keras.models import load_model
import numpy as np
import cv2
import os
import logging
from datetime import datetime, timedelta
import uuid
from werkzeug.utils import secure_filename
import json
from functools import wraps
import time
import threading
from cryptography.fernet import Fernet
import base64
import hashlib

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

# Settings Management
class SettingsManager:
    def __init__(self):
        self.settings_file = 'static/logs/user_settings.json'
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_or_create_encryption_key(self):
        """Get or create encryption key for data encryption"""
        key_file = 'static/logs/encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def get_user_settings(self, user_id=None):
        """Get user settings with defaults"""
        if user_id is None:
            user_id = session.get('user_id', 'anonymous')
            
        default_settings = {
            'enableSoundAlerts': True,
            'enableEmailNotifications': False,
            'enableProgressUpdates': True,
            'enableAutoSave': True,
            'enableDataEncryption': True,
            'enableAutoDelete': True,
            'enableAnalytics': False,
            'enableSessionLogging': False,
            'email': '',
            'confidenceThreshold': 0.5
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    all_settings = json.load(f)
                    user_settings = all_settings.get(user_id, default_settings)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_settings.items():
                        if key not in user_settings:
                            user_settings[key] = value
                    return user_settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            
        return default_settings
    
    def save_user_settings(self, settings, user_id=None):
        """Save user settings"""
        if user_id is None:
            user_id = session.get('user_id', 'anonymous')
            
        try:
            all_settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    all_settings = json.load(f)
            
            all_settings[user_id] = settings
            
            with open(self.settings_file, 'w') as f:
                json.dump(all_settings, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def encrypt_file(self, file_path):
        """Encrypt a file"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = self.cipher.encrypt(file_data)
            encrypted_path = file_path + '.encrypted'
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
                
            return encrypted_path
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
            return None
    
    def decrypt_file(self, encrypted_path):
        """Decrypt a file"""
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            original_path = encrypted_path.replace('.encrypted', '')
            
            with open(original_path, 'wb') as f:
                f.write(decrypted_data)
                
            return original_path
        except Exception as e:
            logger.error(f"Error decrypting file: {e}")
            return None

# Initialize settings manager
settings_manager = SettingsManager()

# Session management
def init_session():
    """Initialize user session"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['session_start'] = datetime.now().isoformat()
    
    # Log session activity if enabled
    user_settings = settings_manager.get_user_settings()
    if user_settings.get('enableSessionLogging', False):
        log_session_activity('session_init', {
            'user_id': session['user_id'],
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })

def log_session_activity(action, data):
    """Log session activity"""
    try:
        log_entry = {
            'action': action,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('static/logs/session_activity.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"Error logging session activity: {e}")

# Email notification system
def send_email_notification(to_email, subject, body):
    """Send email notification"""
    try:
        # Configure with your email settings
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        if not all([smtp_username, smtp_password]):
            logger.warning("Email credentials not configured")
            return False
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg.set_content(body)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def send_analysis_completion_email(user_email, prediction_result):
    """Send analysis completion email"""
    subject = "🩺 Pneumonia Analysis Complete"
    
    body = f"""
    Your chest X-ray analysis has been completed.
    
    Results:
    - Prediction: {prediction_result['prediction']}
    - Confidence: {prediction_result['confidence']:.1%}
    - Processing Time: {prediction_result['processing_time']:.2f} seconds
    
    Please log in to view detailed results and recommendations.
    
    Best regards,
    Pneumonia AI Team
    """
    
    return send_email_notification(user_email, subject, body)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_prediction(image_path, prediction, confidence, processing_time, remedies=None):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'image_path': image_path,
        'prediction': prediction,
        'confidence': confidence,
        'processing_time': processing_time,
        'model_version': '1.0',
        'remedies': remedies
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
    user_settings = settings_manager.get_user_settings()
    
    try:
        # Encrypt image if encryption is enabled
        if user_settings.get('enableDataEncryption', True):
            encrypted_path = settings_manager.encrypt_file(image_path)
            if encrypted_path:
                logger.info(f"Image encrypted: {encrypted_path}")
        
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
        
        prediction_result = {
            'prediction': result,
            'confidence': confidence,
            'processing_time': processing_time,
            'remedies': remedies
        }
        
        # Log prediction if auto-save is enabled
        if user_settings.get('enableAutoSave', True):
            log_prediction(image_path, result, confidence, processing_time, remedies)
        
        # Send email notification if enabled
        if user_settings.get('enableEmailNotifications', False) and user_settings.get('email'):
            threading.Thread(
                target=send_analysis_completion_email,
                args=(user_settings['email'], prediction_result)
            ).start()
        
        # Auto-delete image if enabled
        if user_settings.get('enableAutoDelete', True):
            try:
                os.remove(image_path)
                logger.info(f"Image auto-deleted: {image_path}")
            except Exception as e:
                logger.error(f"Error auto-deleting image: {e}")
        
        return prediction_result
        
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

@app.before_request
def before_request():
    """Initialize session before each request"""
    init_session()

@app.route("/")
def home():
    user_settings = settings_manager.get_user_settings()
    return render_template("index.html", metrics=MODEL_METRICS, settings=user_settings)

@app.route("/predictions", methods=["GET", "POST"])
def predictions():
    result = None
    uploaded_image = None
    error_message = None
    user_settings = settings_manager.get_user_settings()
    
    if request.method == "POST":
        try:
            # Log upload attempt if session logging is enabled
            if user_settings.get('enableSessionLogging', False):
                log_session_activity('image_upload_attempt', {
                    'user_id': session.get('user_id'),
                    'timestamp': datetime.now().isoformat(),
                    'ip_address': request.remote_addr
                })
            
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
                
                # Log successful upload if session logging is enabled
                if user_settings.get('enableSessionLogging', False):
                    log_session_activity('image_uploaded', {
                        'user_id': session.get('user_id'),
                        'timestamp': datetime.now().isoformat(),
                        'filename': filename,
                        'file_size': os.path.getsize(filepath)
                    })
                
                # Make prediction
                prediction_result = predict_image(filepath)
                
                result = {
                    'prediction': prediction_result['prediction'],
                    'confidence': prediction_result['confidence'],
                    'processing_time': prediction_result['processing_time'],
                    'remedies': prediction_result['remedies']
                }
                
                # Set uploaded_image path only if auto-delete is disabled
                if not user_settings.get('enableAutoDelete', True):
                    uploaded_image = filepath
                
                flash(f'Analysis complete! Prediction: {result["prediction"]} (Confidence: {result["confidence"]:.1%})', 'success')
                
                # Log successful analysis if session logging is enabled
                if user_settings.get('enableSessionLogging', False):
                    log_session_activity('analysis_completed', {
                        'user_id': session.get('user_id'),
                        'timestamp': datetime.now().isoformat(),
                        'prediction': result['prediction'],
                        'confidence': result['confidence']
                    })
                
            else:
                flash('Invalid file type. Please upload PNG, JPG, or JPEG files only.', 'error')
                
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            error_message = "An error occurred during analysis. Please try again."
            flash(error_message, 'error')
            
            # Log error if session logging is enabled
            if user_settings.get('enableSessionLogging', False):
                log_session_activity('analysis_error', {
                    'user_id': session.get('user_id'),
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })
    
    return render_template("predictions.html", 
                         result=result, 
                         uploaded_image=uploaded_image,
                         error_message=error_message,
                         settings=user_settings)

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

@app.route("/api/predictions/export/<format>")
def export_predictions(format):
    """Export prediction history in JSON or CSV format"""
    try:
        predictions = []
        
        # Read predictions from log file
        if os.path.exists('static/logs/predictions.json'):
            with open('static/logs/predictions.json', 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            predictions.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        
        if format.lower() == 'json':
            from flask import make_response
            response = make_response(json.dumps(predictions, indent=2))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=predictions_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            return response
            
        elif format.lower() == 'csv':
            import csv
            import io
            from flask import make_response
            
            output = io.StringIO()
            if predictions:
                # Flatten the data for CSV
                flattened_predictions = []
                for pred in predictions:
                    flattened = {
                        'timestamp': pred.get('timestamp', ''),
                        'image_path': pred.get('image_path', ''),
                        'prediction': pred.get('prediction', ''),
                        'confidence': pred.get('confidence', ''),
                        'processing_time': pred.get('processing_time', ''),
                        'model_version': pred.get('model_version', ''),
                        'remedies_severity': pred.get('remedies', {}).get('severity', '') if pred.get('remedies') else '',
                        'remedies_message': pred.get('remedies', {}).get('message', '') if pred.get('remedies') else '',
                        'remedies_count': len(pred.get('remedies', {}).get('remedies', [])) if pred.get('remedies') else 0
                    }
                    flattened_predictions.append(flattened)
                
                fieldnames = flattened_predictions[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_predictions)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=predictions_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response
            
        else:
            return jsonify({'error': 'Invalid format. Use json or csv'}), 400
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': 'Failed to export predictions'}), 500

@app.route("/api/predictions/history")
def get_prediction_history():
    """Get prediction history with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        predictions = []
        
        # Read predictions from log file
        if os.path.exists('static/logs/predictions.json'):
            with open('static/logs/predictions.json', 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            predictions.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        
        # Sort by timestamp (newest first)
        predictions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_predictions = predictions[start:end]
        
        return jsonify({
            'predictions': paginated_predictions,
            'total': len(predictions),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(predictions) + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"History error: {str(e)}")
        return jsonify({'error': 'Failed to get prediction history'}), 500

@app.route("/api/progress/<task_id>")
def get_progress(task_id):
    """Get progress updates for a specific task"""
    try:
        progress_file = f'static/logs/progress_{task_id}.json'
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            return jsonify(progress_data)
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        logger.error(f"Progress error: {str(e)}")
        return jsonify({'error': 'Failed to get progress'}), 500

@app.route("/api/session/activity")
def get_session_activity():
    """Get session activity logs"""
    try:
        user_settings = settings_manager.get_user_settings()
        if not user_settings.get('enableSessionLogging', False):
            return jsonify({'error': 'Session logging is disabled'}), 403
        
        activities = []
        if os.path.exists('static/logs/session_activity.json'):
            with open('static/logs/session_activity.json', 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            activity = json.loads(line.strip())
                            if activity.get('data', {}).get('user_id') == session.get('user_id'):
                                activities.append(activity)
                        except json.JSONDecodeError:
                            continue
        
        # Sort by timestamp (newest first)
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'activities': activities[:50],  # Limit to 50 most recent
            'total': len(activities)
        })
        
    except Exception as e:
        logger.error(f"Session activity error: {str(e)}")
        return jsonify({'error': 'Failed to get session activity'}), 500

@app.route("/settings")
def settings():
    user_settings = settings_manager.get_user_settings()
    return render_template("settings.html", metrics=MODEL_METRICS, settings=user_settings)

@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """API endpoint for managing user settings"""
    if request.method == "GET":
        settings = settings_manager.get_user_settings()
        return jsonify(settings)
    
    elif request.method == "POST":
        try:
            new_settings = request.json
            if settings_manager.save_user_settings(new_settings):
                
                # Log settings change if session logging is enabled
                if new_settings.get('enableSessionLogging', False):
                    log_session_activity('settings_updated', {
                        'user_id': session.get('user_id'),
                        'timestamp': datetime.now().isoformat(),
                        'settings_changed': list(new_settings.keys())
                    })
                
                return jsonify({'success': True, 'message': 'Settings saved successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to save settings'}), 500
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return jsonify({'success': False, 'message': 'Invalid settings data'}), 400

@app.route("/history")
def history():
    """Display prediction history page"""
    return render_template("history.html", metrics=MODEL_METRICS)

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
