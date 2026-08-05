
import os
import json
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow import keras
from flask import Flask, request, jsonify
from config import Config

# Initialize Flask app for Model Service
model_app = Flask(__name__)
model_app.config.from_object(Config)

# Global variables for model
model = None
class_indices = None
index_to_class = None
model_metadata = None

# FIX: Patch InputLayer to handle 'batch_shape' compatibility issue
# Verify if InputLayer exists in keras.layers
if hasattr(keras.layers, 'InputLayer'):
    # We define a custom InputLayer class that handles 'batch_shape'
    class PatchedInputLayer(keras.layers.InputLayer):
        def __init__(self, *args, **kwargs):
            if 'batch_shape' in kwargs:
                # 'batch_shape' is deprecated/unsupported in newer Keras InputLayer
                # It expects 'batch_input_shape'
                kwargs['batch_input_shape'] = kwargs.pop('batch_shape')
            super().__init__(*args, **kwargs)
else:
    PatchedInputLayer = None

# FIX: Patch DTypePolicy for Keras 3 compatibility
class DTypePolicy(tf.keras.mixed_precision.Policy):
    def __init__(self, name=None, **kwargs):
        super().__init__(name=name or "float32")
    
    def get_config(self):
        return {"name": self.name}


def log(msg):
    try:
        with open('model_service.log', 'a', encoding='utf-8') as f:
            f.write(str(msg) + '\n')
        print(msg)
    except Exception as e:
        print(f"Logging error: {e}")

def load_model_resources():
    global model, class_indices, index_to_class, model_metadata
    
    log("="*50)
    log("Loading Model Resources...")
    log("="*50)
    
    model_path = model_app.config['MODEL_PATH']
    log(f"Model Path: {model_path}")

    # Load Model
    if os.path.exists(model_path):
        try:
            # Prepare custom objects
            custom_objects = {}
            if 'PatchedInputLayer' in globals() and PatchedInputLayer:
                custom_objects['InputLayer'] = PatchedInputLayer
            
            # Register DTypePolicy
            if 'DTypePolicy' in globals():
                custom_objects['DTypePolicy'] = DTypePolicy
                
            model = keras.models.load_model(model_path, custom_objects=custom_objects, compile=False)
            log(" Model loaded successfully!")  # Removed emoji to be safe
        except Exception as e:
            log(f" Error loading model: {e}") # Removed emoji
            import traceback
            try:
                with open('model_service.log', 'a', encoding='utf-8') as f:
                    traceback.print_exc(file=f)
            except:
                traceback.print_exc()
            return False
    else:
        log(f" Model file not found at: {model_path}") # Removed emoji
        return False
        
    # Load Class Indices
    if os.path.exists(model_app.config['CLASS_INDICES_PATH']):
        try:
            with open(model_app.config['CLASS_INDICES_PATH'], 'r') as f:
                class_indices = json.load(f)
            index_to_class = {v: k for k, v in class_indices.items()}
            log(f" Class indices loaded: {len(class_indices)} classes")
        except Exception as e:
            log(f" Error loading class indices: {e}")
    
    # Load Metadata
    if os.path.exists(model_app.config['METADATA_PATH']):
        try:
            with open(model_app.config['METADATA_PATH'], 'r') as f:
                model_metadata = json.load(f)
            log(" Metadata loaded")
        except Exception as e:
            log(f" Error loading metadata: {e}")
            
    return True

# Initialize resources
try:
    with open('model_service.log', 'w', encoding='utf-8') as f:
        f.write("Starting model service...\n")
    load_model_resources()
except Exception as e:
    with open('model_service.log', 'a', encoding='utf-8') as f:
        f.write(f"CRITICAL ERROR: {e}\n")
        import traceback
        traceback.print_exc(file=f)



# Helper Functions
def preprocess_image(image_file):
    try:
        img = Image.open(image_file).convert('RGB')
        img = img.resize((model_app.config['IMG_SIZE'], model_app.config['IMG_SIZE']))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def determine_severity(confidence, prediction_class):
    if prediction_class == 'no_damage':
        return 'none'
    
    for severity, thresholds in model_app.config['SEVERITY_MAPPING'].items():
        if confidence >= thresholds['min']:
            return severity
    return 'low'

def determine_damage_type(prediction_class, confidence):
    if prediction_class == 'no_damage':
        return 'No Damage Detected'
    
    if confidence >= 0.95:
        return 'Severe Road Damage - Immediate Attention Required'
    elif confidence >= 0.85:
        return 'Significant Road Damage - High Priority'
    elif confidence >= 0.70:
        return 'Moderate Road Damage - Maintenance Recommended'
    else:
        return 'Minor Road Damage - Monitor Condition'

@model_app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503
        
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    
    try:
        img_array = preprocess_image(file)
        if img_array is None:
            return jsonify({'error': 'Invalid image'}), 400
            
        predictions = model.predict(img_array, verbose=0)
        predicted_index = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_index])
        
        predicted_class = index_to_class[predicted_index] if index_to_class else str(predicted_index)
        
        severity = determine_severity(confidence, predicted_class)
        damage_type = determine_damage_type(predicted_class, confidence)
        
        return jsonify({
            'success': True,
            'prediction_class': predicted_class,
            'confidence': confidence,
            'severity': severity,
            'damage_type': damage_type
        })
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@model_app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'model_loaded': model is not None
    })

if __name__ == '__main__':
    print("Starting Model Service on port 5001...")
    model_app.run(host='0.0.0.0', port=5001)
