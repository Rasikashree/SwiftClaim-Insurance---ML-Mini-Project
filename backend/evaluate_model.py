"""
SwiftClaim Model Evaluation
----------------------------
Evaluate trained model performance on test data.
"""

import os
import sys
import numpy as np
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
    from sklearn.preprocessing import label_binarize
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import load_img, img_to_array
    REQUIRED_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Missing required package: {e}")
    REQUIRED_AVAILABLE = False


class ModelEvaluator:
    """Evaluate model performance."""
    
    def __init__(self, model_path: str = None, training_dir: str = None):
        """
        Initialize evaluator.
        
        Args:
            model_path: Path to trained model
            training_dir: Directory containing training data
        """
        if not REQUIRED_AVAILABLE:
            raise ImportError("scikit-learn and matplotlib required for evaluation")
        
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "models", "damage_severity_model.h5")
        if training_dir is None:
            training_dir = os.path.join(os.path.dirname(__file__), "training_data")
        
        self.model_path = Path(model_path)
        self.training_dir = Path(training_dir)
        
        try:
            self.model = tf.keras.models.load_model(str(self.model_path))
        except Exception as e:
            raise Exception(f"Failed to load model: {e}")
        
        self.class_names = ["Minor", "Moderate", "Severe"]
        self.true_labels = []
        self.predictions = []
    
    def load_and_predict(self, image_size: tuple = (224, 224)):
        """
        Load images and generate predictions.
        
        Args:
            image_size: Size to resize images to
        """
        print("[ModelEvaluator] Loading images and generating predictions...")
        
        for class_idx, class_name in enumerate(self.class_names):
            class_dir = self.training_dir / class_name
            if not class_dir.exists():
                print(f"[WARNING] Class directory not found: {class_dir}")
                continue
            
            image_files = list(class_dir.glob("*.jpg"))
            print(f"  {class_name}: {len(image_files)} images")
            
            for img_file in image_files[:50]:  # Limit to 50 per class for speed
                try:
                    # Load and preprocess image
                    img = load_img(str(img_file), target_size=image_size)
                    img_array = img_to_array(img)
                    img_array = np.expand_dims(img_array, axis=0)
                    
                    # Preprocess (normalize)
                    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
                    img_array = preprocess_input(img_array)
                    
                    # Get prediction
                    prediction = self.model.predict(img_array, verbose=0)
                    predicted_class = np.argmax(prediction[0])
                    
                    self.true_labels.append(class_idx)
                    self.predictions.append(predicted_class)
                
                except Exception as e:
                    print(f"[ERROR] Failed to process {img_file}: {e}")
        
        print(f"[ModelEvaluator] Loaded {len(self.true_labels)} images total")
    
    def print_classification_report(self):
        """Print detailed classification metrics."""
        if not self.true_labels:
            print("[ERROR] No predictions loaded")
            return
        
        print("\n" + "=" * 60)
        print("Classification Report")
        print("=" * 60)
        
        report = classification_report(
            self.true_labels,
            self.predictions,
            target_names=self.class_names
        )
        print(report)
    
    def print_confusion_matrix(self):
        """Print confusion matrix."""
        if not self.true_labels:
            print("[ERROR] No predictions loaded")
            return
        
        print("\nConfusion Matrix:")
        cm = confusion_matrix(self.true_labels, self.predictions)
        
        # Format nicely
        print("     " + "  ".join(f"{name:>8}" for name in self.class_names))
        for i, row in enumerate(cm):
            print(f"{self.class_names[i]:>4} " + "  ".join(f"{val:>8}" for val in row))
    
    def plot_confusion_matrix(self, save_path: str = None):
        """Plot confusion matrix heatmap."""
        if not self.true_labels:
            print("[ERROR] No predictions loaded")
            return
        
        cm = confusion_matrix(self.true_labels, self.predictions)
        
        plt.figure(figsize=(8, 6))
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title('Confusion Matrix')
        plt.colorbar()
        
        tick_marks = np.arange(len(self.class_names))
        plt.xticks(tick_marks, self.class_names, rotation=45)
        plt.yticks(tick_marks, self.class_names)
        
        # Add text annotations
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(j, i, str(cm[i, j]), ha='center', va='center', color='white' if cm[i, j] > cm.max() / 2 else 'black')
        
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"[INFO] Confusion matrix plot saved to {save_path}")
        else:
            plt.show()
    
    def get_accuracy(self) -> float:
        """Get overall accuracy."""
        if not self.true_labels:
            return 0.0
        return np.mean(np.array(self.true_labels) == np.array(self.predictions))
    
    def print_summary(self):
        """Print evaluation summary."""
        accuracy = self.get_accuracy()
        
        print("\n" + "=" * 60)
        print("Evaluation Summary")
        print("=" * 60)
        print(f"Model: {self.model_path}")
        print(f"Total Samples: {len(self.true_labels)}")
        print(f"Overall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print("=" * 60)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate damage severity model")
    parser.add_argument("--model-path", type=str, default=None, help="Path to model")
    parser.add_argument("--training-dir", type=str, default=None, help="Training data directory")
    parser.add_argument("--plot", action="store_true", help="Save confusion matrix plot")
    
    args = parser.parse_args()
    
    try:
        evaluator = ModelEvaluator(args.model_path, args.training_dir)
        evaluator.load_and_predict()
        evaluator.print_summary()
        evaluator.print_classification_report()
        evaluator.print_confusion_matrix()
        
        if args.plot:
            output_dir = Path(args.model_path or "models").parent
            plot_path = output_dir / "confusion_matrix.png"
            evaluator.plot_confusion_matrix(str(plot_path))
    
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
