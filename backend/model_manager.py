"""
SwiftClaim ML Model Manager
----------------------------
Manages model lifecycle: loading, inference, and fallback handling.
"""

import os
import numpy as np
from pathlib import Path

try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


class ModelManager:
    """Handles ML model operations with graceful fallback."""
    
    def __init__(self, models_dir: str = None):
        """
        Initialize the model manager.
        
        Args:
            models_dir: Directory containing saved models
        """
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "models")
        
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.model_path = self.models_dir / "damage_severity_model.h5"
        self.available = TENSORFLOW_AVAILABLE
        
        if self.available:
            self._load_model()
    
    def _load_model(self):
        """Load model from disk if it exists."""
        try:
            if self.model_path.exists():
                self.model = load_model(str(self.model_path))
                print(f"[ModelManager] Loaded model from {self.model_path}")
            else:
                print(f"[ModelManager] No model found at {self.model_path}")
                self.model = None
        except Exception as e:
            print(f"[ModelManager] Error loading model: {e}")
            self.model = None
    
    def is_model_available(self) -> bool:
        """Check if model is available for inference."""
        return self.available and self.model is not None
    
    def predict(self, image_array: np.ndarray, confidence_threshold: float = 0.5) -> dict:
        """
        Run inference on an image.
        
        Args:
            image_array: Input image (H×W×3)
            confidence_threshold: Minimum confidence to return prediction
            
        Returns:
            Dict with severity, confidence, and classes
        """
        if not self.is_model_available():
            return {
                "available": False,
                "error": "Model not available for inference",
                "severity": None,
                "confidence": None
            }
        
        try:
            # Preprocess image
            processed = self._preprocess_image(image_array)
            
            # Get predictions
            predictions = self.model.predict(processed, verbose=0)
            class_scores = predictions[0]
            
            # Get class labels
            class_names = ["Minor", "Moderate", "Severe"]
            predicted_class_idx = np.argmax(class_scores)
            predicted_class = class_names[predicted_class_idx]
            confidence = float(class_scores[predicted_class_idx])
            
            if confidence < confidence_threshold:
                return {
                    "available": True,
                    "error": f"Confidence {confidence:.3f} below threshold {confidence_threshold}",
                    "severity": None,
                    "confidence": confidence,
                    "all_scores": {name: float(score) for name, score in zip(class_names, class_scores)}
                }
            
            return {
                "available": True,
                "error": None,
                "severity": predicted_class,
                "confidence": confidence,
                "all_scores": {name: float(score) for name, score in zip(class_names, class_scores)}
            }
        
        except Exception as e:
            return {
                "available": True,
                "error": f"Inference failed: {str(e)}",
                "severity": None,
                "confidence": None
            }
    
    def _preprocess_image(self, image_array: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model input.
        
        Args:
            image_array: Input image (H×W×3 in BGR)
            
        Returns:
            Preprocessed image ready for model (1×224×224×3 in RGB)
        """
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        
        # Ensure it's a numpy array
        if not isinstance(image_array, np.ndarray):
            image_array = np.array(image_array)
        
        # Resize to 224x224 (MobileNetV2 input size)
        if image_array.shape[:2] != (224, 224):
            import cv2
            image_array = cv2.resize(image_array, (224, 224))
        
        # Convert BGR to RGB if needed
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        # Preprocess (normalize)
        image_array = preprocess_input(image_array)
        
        return image_array
    
    def save_model(self, model):
        """Save model to disk."""
        try:
            model.save(str(self.model_path))
            print(f"[ModelManager] Model saved to {self.model_path}")
            self.model = model
            return True
        except Exception as e:
            print(f"[ModelManager] Error saving model: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        info = {
            "tensorflow_available": TENSORFLOW_AVAILABLE,
            "model_loaded": self.model is not None,
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists()
        }
        
        if self.model is not None:
            try:
                info["model_summary"] = {
                    "parameters": int(self.model.count_params()),
                    "layers": len(self.model.layers),
                    "input_shape": list(self.model.input_shape),
                    "output_shape": list(self.model.output_shape)
                }
            except Exception as e:
                info["model_summary_error"] = str(e)
        
        return info


# Global model manager instance
_model_manager = None

def get_model_manager(models_dir: str = None) -> ModelManager:
    """Get or create the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager(models_dir)
    return _model_manager
