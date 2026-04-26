"""
SwiftClaim Model Training Pipeline
-----------------------------------
Trains CNN model with MobileNetV2 backbone for damage severity classification.
"""

import os
import sys
import numpy as np
from pathlib import Path
from typing import Tuple

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("[ERROR] TensorFlow is required for model training!")
    print("[INFO] Install with: pip install tensorflow")


class ModelTrainer:
    """Train CNN model for damage severity classification."""

    " Training data path and Model save path "
    def __init__(self, training_dir: str = None, models_dir: str = None):
        """
        Initialize trainer.
        
        Args:
            training_dir: Directory containing training data
            models_dir: Directory to save trained models
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required")
        
        #" Set default paths if not provided "
        if training_dir is None:
            training_dir = os.path.join(os.path.dirname(__file__), "training_data")
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "models")
        
        #" Create directories if they don't exist "
        self.training_dir = Path(training_dir)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        " Initialize model and history "
        self.model = None
        self.history = None
    
    " Build transfer learning model with MobileNetV2 backbone "
    # Input shape: (224 size, 224 size, 3 color channels) for RGB images, Output classes: 3 (No Damage, Minor, Severe) 
    
    def build_model(self, input_shape: Tuple[int, int, int] = (224, 224, 3), num_classes: int = 3):
        """
        Build transfer learning model using MobileNetV2.
        
        Args:
            input_shape: Input image shape
            num_classes: Number of output classes
            
        Returns:
            Compiled Keras model
        """
        print("[ModelTrainer] Building transfer learning model...")
        
        # Load pre-trained MobileNetV2 (ImageNet weights)
        # Removes original classification layer and uses ImageNet weights for feature extraction
        base_model = MobileNetV2(
            input_shape=input_shape,
            include_top=False,
            weights='imagenet'
        )
        
        # Freeze base model weights and prevents retraining
        base_model.trainable = False
        
        # Build custom top layers or build custom model
        model = keras.Sequential([
            layers.Input(shape=input_shape), # Input layer image
            base_model, #extract features from base model
            layers.GlobalAveragePooling2D(), #converts feature maps to a single vector
            layers.Dense(256, activation='relu'), # learns feature
            layers.Dropout(0.5), # overfitting
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3), # learning + regularization
            layers.Dense(num_classes, activation='softmax') # 3 classes probabilities
        ])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-4), # adam for effective training
            loss='categorical_crossentropy', # multi-class classification 
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()] # performance metrics for evaluation
        )
        
        print(f"[ModelTrainer] Model built successfully!")
        print(f"[ModelTrainer] Total parameters: {model.count_params():,}") # trainable + non-trainable parameters
        print(f"[ModelTrainer] Trainable parameters: {sum([tf.keras.backend.count_params(w) for w in model.trainable_weights]):,}") # trainable parameters        
        self.model = model # stores model and return
        return model
    
    def prepare_data(self, batch_size: int = 32, image_size: Tuple[int, int] = (224, 224)):
        """
        Prepare training and validation data.
        
        Args:
            batch_size: Batch size for training
            image_size: Size to resize images to
            
        Returns:
            Tuple of (train_generator, validation_generator)
        """
        print(f"[ModelTrainer] Preparing data from {self.training_dir}...")
        
        # Data augmentation
        train_datagen = ImageDataGenerator( # creates data generator for training
            rescale=1./255, # normalizes pixel
            rotation_range=20, 
            width_shift_range=0.2,
            height_shift_range=0.2, # random transformations
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest',
            validation_split=0.2  # 20% for validation
        )
        
        # Load training data
        train_generator = train_datagen.flow_from_directory( # reads image from folders
            str(self.training_dir),
            target_size=image_size,
            batch_size=batch_size,
            class_mode='categorical',
            subset='training', # uses only 80% of data for training
            seed=42
        )
        
        # Load validation data
        validation_generator = train_datagen.flow_from_directory(
            str(self.training_dir),
            target_size=image_size,
            batch_size=batch_size,
            class_mode='categorical',
            subset='validation', # uses remaining 20% for validation
            seed=42
        )
        
        print(f"[ModelTrainer] Training samples: {train_generator.samples}") # images used for training the model (minor, moderate, severe)
        print(f"[ModelTrainer] Validation samples: {validation_generator.samples}") # images used for checking model performance during training
        print(f"[ModelTrainer] Classes: {list(train_generator.class_indices.keys())}") # minor, moderate, severe 
        
        return train_generator, validation_generator
    
    def train(self, train_generator, validation_generator, epochs: int = 20, verbose: int = 1):
        """
        Train the model.
        
        Args:
            train_generator: Training data generator
            validation_generator: Validation data generator
            epochs: Number of training epochs
            verbose: Verbosity level
            
        Returns:
            Training history
        """
        if self.model is None: # ensures model exists before training
            raise ValueError("Model not built. Call build_model() first.")
        
        print(f"\n[ModelTrainer] Starting training for {epochs} epochs...")
        
        # Callbacks - smart training tool
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5, # stops if there is no improvement
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5, # reduces learning rate if no improvement
                patience=3,
                min_lr=1e-7,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                str(self.models_dir / "best_model.h5"),
                monitor='val_accuracy',
                save_best_only=True, # saves the best model based on validation accuracy    
                verbose=0
            )
        ]
        
        # Train model
        history = self.model.fit( # start training process
            train_generator,
            epochs=epochs,
            validation_data=validation_generator, # using the validation data
            callbacks=callbacks,
            verbose=verbose
        )
        
        self.history = history
        return history # saves the training results
    
    def unfreeze_and_finetune(self, train_generator, validation_generator, epochs: int = 10):
        """
        Unfreeze base model and fine-tune.
        
        Args:
            train_generator: Training data generator
            validation_generator: Validation data generator
            epochs: Number of fine-tuning epochs
        """
        if self.model is None:
            raise ValueError("Model not built.")
        
        print("\n[ModelTrainer] Unfreezing base model for fine-tuning...")
        
        # Find the base model (MobileNetV2) - it's the layer with 'layers' attribute
        base_model = None
        for layer in self.model.layers:
            if hasattr(layer, 'layers'):  # Check if it's a model/functional layer
                base_model = layer
                break
        
        if base_model is None:
            print("[WARNING] Could not find base model for fine-tuning. Skipping fine-tuning phase.")
            return None
        
        base_model.trainable = True # unfreezes model
        
        # Freeze early layers (keep features learned from ImageNet)
        for layer in base_model.layers[:-30]:
            layer.trainable = False
        
        # Recompile with lower learning rate and all metrics
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-5), # lower learning rate
            loss='categorical_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        # Fine-tune
        print(f"[ModelTrainer] Fine-tuning for {epochs} epochs...")
        history = self.model.fit(
            train_generator,
            epochs=epochs,
            validation_data=validation_generator,
            verbose=1
        )
        
        return history
    
    def save_model(self, filename: str = "damage_severity_model.h5"):
        """
        Save trained model.
        
        Args:
            filename: Model filename
            
        Returns:
            Path to saved model
        """
        if self.model is None:
            raise ValueError("No model to save.")
        
        filepath = self.models_dir / filename
        self.model.save(str(filepath)) # save the trained model
        print(f"[ModelTrainer] Model saved to {filepath}")
        return filepath
    
    def evaluate(self, validation_generator):
        """
        Evaluate model on validation data.
        
        Args:
            validation_generator: Validation data generator
            
        Returns:
            Evaluation metrics
        """
        if self.model is None:
            raise ValueError("No model to evaluate.")
        
        print("\n[ModelTrainer] Evaluating model...")
        results = self.model.evaluate(validation_generator, verbose=0) # test the model
        
        # Handle variable number of metrics returned
        # Results format: [loss, metric1, metric2, ...]
        metrics = { # extract metrics from results
            'loss': results[0],
            'accuracy': results[1] if len(results) > 1 else 0.0,
            'precision': results[2] if len(results) > 2 else 0.0,
            'recall': results[3] if len(results) > 3 else 0.0
        }
        
        print(f"  Loss: {metrics['loss']:.4f}")
        print(f"  Accuracy: {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall: {metrics['recall']:.4f}")
        
        return metrics


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train damage severity model")
    parser.add_argument("--training-dir", type=str, default=None, help="Training data directory")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--finetune-epochs", type=int, default=10, help="Fine-tuning epochs")
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(args.training_dir)
    trainer.build_model()
    train_gen, val_gen = trainer.prepare_data(batch_size=args.batch_size)
    trainer.train(train_gen, val_gen, epochs=args.epochs)
    trainer.unfreeze_and_finetune(train_gen, val_gen, epochs=args.finetune_epochs)
    trainer.evaluate(val_gen)
    trainer.save_model()
