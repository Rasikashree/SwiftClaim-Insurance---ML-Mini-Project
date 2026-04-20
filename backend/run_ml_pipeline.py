"""
SwiftClaim ML Pipeline Orchestrator
------------------------------------
One-command training pipeline: generate data → train → evaluate → save
"""

import sys
import argparse
from pathlib import Path

# Check TensorFlow availability
try:
    import tensorflow
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# Import custom modules
try:
    from dataset_generator import DatasetGenerator
    if TENSORFLOW_AVAILABLE:
        from train_model import ModelTrainer
except ImportError as e:
    print(f"[ERROR] Failed to import modules: {e}")
    sys.exit(1)


def run_pipeline(
    training_dir: str = None,
    models_dir: str = None,
    num_samples: int = 100,
    epochs: int = 20,
    finetune_epochs: int = 10,
    batch_size: int = 32,
    skip_generation: bool = False
):
    """
    Run complete ML pipeline.
    
    Args:
        training_dir: Directory for training data
        models_dir: Directory to save models
        num_samples: Samples per class
        epochs: Training epochs
        finetune_epochs: Fine-tuning epochs
        batch_size: Batch size for training
        skip_generation: Skip dataset generation if data exists
    """
    print("=" * 60)
    print("SwiftClaim ML Pipeline")
    print("=" * 60)
    
    # Step 1: Generate Dataset
    print("\n[STEP 1] Generating Synthetic Dataset")
    print("-" * 60)
    
    generator = DatasetGenerator(training_dir)
    
    # Check if data exists
    training_path = Path(training_dir or "training_data")
    data_exists = all((training_path / cls).exists() for cls in ["Minor", "Moderate", "Severe"])
    
    if skip_generation and data_exists:
        print(f"[INFO] Using existing dataset from {training_path}")
    else:
        print(f"[INFO] Generating {num_samples} samples per class...")
        generator.generate_dataset(samples_per_class=num_samples)
    
    # Step 2: Train Model
    if not TENSORFLOW_AVAILABLE:
        print("\n[ERROR] TensorFlow is required for model training!")
        print("[INFO] Install with: pip install tensorflow")
        return False
    
    print("\n[STEP 2] Building and Training Model")
    print("-" * 60)
    
    trainer = ModelTrainer(training_dir, models_dir)
    trainer.build_model()
    
    print(f"\n[INFO] Preparing data (batch_size={batch_size})...")
    train_gen, val_gen = trainer.prepare_data(batch_size=batch_size)
    
    print(f"\n[INFO] Training for {epochs} epochs...")
    trainer.train(train_gen, val_gen, epochs=epochs)
    
    # Step 3: Fine-tune
    print(f"\n[STEP 3] Fine-tuning Model")
    print("-" * 60)
    print(f"[INFO] Fine-tuning for {finetune_epochs} epochs...")
    trainer.unfreeze_and_finetune(train_gen, val_gen, epochs=finetune_epochs)
    
    # Step 4: Evaluate
    print(f"\n[STEP 4] Evaluating Model")
    print("-" * 60)
    metrics = trainer.evaluate(val_gen)
    
    # Step 5: Save
    print(f"\n[STEP 5] Saving Model")
    print("-" * 60)
    model_path = trainer.save_model()
    
    # Summary
    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print(f"\n✓ Model trained and saved to: {model_path}")
    print(f"\nFinal Metrics:")
    print(f"  - Accuracy: {metrics['accuracy']:.4f}")
    print(f"  - Loss: {metrics['loss']:.4f}")
    print(f"  - Precision: {metrics['precision']:.4f}")
    print(f"  - Recall: {metrics['recall']:.4f}")
    print(f"\nNext Steps:")
    print(f"  1. Start the API: python app.py")
    print(f"  2. Test the model: curl http://localhost:5001/api/model-info")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SwiftClaim ML Pipeline - Generate, Train, Evaluate, Save"
    )
    
    parser.add_argument(
        "--training-dir",
        type=str,
        default=None,
        help="Directory for training data"
    )
    
    parser.add_argument(
        "--models-dir",
        type=str,
        default=None,
        help="Directory to save models"
    )
    
    parser.add_argument(
        "--num-samples",
        type=int,
        default=100,
        help="Samples per class for dataset generation"
    )
    
    parser.add_argument(
        "--epochs",
        type=int,
        default=20,
        help="Number of training epochs"
    )
    
    parser.add_argument(
        "--finetune-epochs",
        type=int,
        default=10,
        help="Number of fine-tuning epochs"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for training"
    )
    
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip dataset generation if data exists"
    )
    
    args = parser.parse_args()
    
    success = run_pipeline(
        training_dir=args.training_dir,
        models_dir=args.models_dir,
        num_samples=args.num_samples,
        epochs=args.epochs,
        finetune_epochs=args.finetune_epochs,
        batch_size=args.batch_size,
        skip_generation=args.skip_generation
    )
    
    sys.exit(0 if success else 1)
