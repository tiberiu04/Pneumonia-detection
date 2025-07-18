
import unittest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the application
try:
    from app import app, predict_image, allowed_file, MODEL_METRICS
    from config import Config, DevelopmentConfig, ProductionConfig
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running tests from the project root directory")
    sys.exit(1)


class TestPneumoniaDetectionApp(unittest.TestCase):    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.test_dir
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI Pneumonia Detection System', response.data)
    
    def test_predictions_page_get(self):
        response = self.client.get('/predictions')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI-Powered Chest X-Ray Analysis', response.data)
    
    def test_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About Our AI System', response.data)
    
    def test_settings_page(self):
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
    
    def test_api_health_endpoint(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_api_metrics_endpoint(self):
        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('accuracy', data)
        self.assertIn('precision', data)
        self.assertIn('recall', data)
        self.assertIn('f1_score', data)
    
    def test_allowed_file_function(self):
        # Test valid file extensions
        self.assertTrue(allowed_file('test.jpg'))
        self.assertTrue(allowed_file('test.jpeg'))
        self.assertTrue(allowed_file('test.png'))
        self.assertTrue(allowed_file('TEST.JPG'))  # Case insensitive
        
        # Test invalid file extensions
        self.assertFalse(allowed_file('test.gif'))
        self.assertFalse(allowed_file('test.txt'))
        self.assertFalse(allowed_file('test.pdf'))
        self.assertFalse(allowed_file('test'))  # No extension
    
    def test_api_predict_no_file(self):
        response = self.client.post('/api/predict')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_predict_invalid_file_type(self):
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'This is not an image')
            temp_file = f.name
        
        try:
            with open(temp_file, 'rb') as f:
                response = self.client.post('/api/predict', 
                                        data={'image': (f, 'test.txt')})
            
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertIn('error', data)
        finally:
            os.unlink(temp_file)
    
    def test_404_error_handler(self):
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    @patch('app.model', None)
    def test_prediction_with_no_model(self):
        # Create a dummy image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            temp_file = f.name
        
        try:
            with self.assertRaises(Exception) as context:
                predict_image(temp_file)
            
            self.assertIn('Model not loaded', str(context.exception))
        finally:
            os.unlink(temp_file)


class TestConfiguration(unittest.TestCase):    
    def test_base_config(self):
        config = Config()
        self.assertEqual(config.MAX_CONTENT_LENGTH, 16 * 1024 * 1024)
        self.assertEqual(config.UPLOAD_FOLDER, 'static/uploads')
        self.assertIn('png', config.ALLOWED_EXTENSIONS)
        self.assertIn('jpg', config.ALLOWED_EXTENSIONS)
        self.assertIn('jpeg', config.ALLOWED_EXTENSIONS)
    
    def test_development_config(self):
        config = DevelopmentConfig()
        self.assertTrue(config.DEBUG)
        self.assertFalse(config.TESTING)
        self.assertEqual(config.LOG_LEVEL, 'DEBUG')
    
    def test_production_config(self):
        # Mock environment variable
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            config = ProductionConfig()
            self.assertFalse(config.DEBUG)
            self.assertFalse(config.TESTING)
            self.assertEqual(config.LOG_LEVEL, 'WARNING')
            self.assertEqual(config.SECRET_KEY, 'test-secret-key')
    
    def test_model_metrics_structure(self):
        self.assertIn('accuracy', MODEL_METRICS)
        self.assertIn('precision', MODEL_METRICS)
        self.assertIn('recall', MODEL_METRICS)
        self.assertIn('f1_score', MODEL_METRICS)
        self.assertIn('training_samples', MODEL_METRICS)
        
        # Check that metrics are reasonable values
        self.assertGreaterEqual(MODEL_METRICS['accuracy'], 0)
        self.assertLessEqual(MODEL_METRICS['accuracy'], 100)


class TestUtilityFunctions(unittest.TestCase):    
    def test_file_extension_validation(self):
        # Test files with multiple dots
        self.assertTrue(allowed_file('my.image.jpg'))
        self.assertFalse(allowed_file('my.image.txt'))
        
        # Test files with no extension
        self.assertFalse(allowed_file('filename'))
        
        # Test empty filename
        self.assertFalse(allowed_file(''))
        
        # Test filename with just extension
        self.assertTrue(allowed_file('.jpg'))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)