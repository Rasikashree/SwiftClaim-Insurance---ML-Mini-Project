"""
SwiftClaim Synthetic Dataset Generator
---------------------------------------
Generates synthetic training data for damage severity classification.
Creates Minor, Moderate, and Severe damage examples.
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple


class DatasetGenerator:
    """Generate synthetic training data for damage severity classification."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize dataset generator.
        
        Args:
            output_dir: Directory to save generated datasets
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "training_data")
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create class directories
        self.classes = ["Minor", "Moderate", "Severe"]
        self.class_dirs = {}
        for cls in self.classes:
            cls_dir = self.output_dir / cls
            cls_dir.mkdir(exist_ok=True)
            self.class_dirs[cls] = cls_dir
    
    def generate_dataset(self, samples_per_class: int = 100, image_size: Tuple[int, int] = (224, 224)):
        """
        Generate synthetic dataset.
        
        Args:
            samples_per_class: Number of images per severity class
            image_size: Size of generated images (H, W)
        """
        print(f"[DatasetGenerator] Generating {samples_per_class} samples per class...")
        
        for cls_idx, cls_name in enumerate(self.classes):
            print(f"  Generating {cls_name} ({cls_idx + 1}/{len(self.classes)})...")
            
            for i in range(samples_per_class):
                if cls_name == "Minor":
                    img = self._generate_minor_damage(image_size)
                elif cls_name == "Moderate":
                    img = self._generate_moderate_damage(image_size)
                else:  # Severe
                    img = self._generate_severe_damage(image_size)
                
                # Save image
                filename = f"{cls_name.lower()}_{i:04d}.jpg"
                filepath = self.class_dirs[cls_name] / filename
                cv2.imwrite(str(filepath), img)
        
        print(f"[DatasetGenerator] Dataset generation complete!")
        self._print_dataset_summary()
    
    def _generate_minor_damage(self, size: Tuple[int, int]) -> np.ndarray:
        """Generate image with minor damage (scratches/paint damage)."""
        # Start with a uniform colored background (car part)
        img = np.ones((*size, 3), dtype=np.uint8)
        img[:] = self._random_color()  # Random car paint color
        
        # Add subtle texture
        noise = np.random.randint(0, 20, size + (3,), dtype=np.uint8)
        img = cv2.add(img, noise)
        
        # Add light scratches
        num_scratches = np.random.randint(3, 8)
        for _ in range(num_scratches):
            x1, y1 = np.random.randint(0, size[1], 2)
            x2, y2 = np.random.randint(0, size[1], 2)
            thickness = np.random.randint(1, 3)
            color = self._scratch_color()
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)
        
        # Add small scuffs
        num_scuffs = np.random.randint(2, 5)
        for _ in range(num_scuffs):
            x, y = np.random.randint(0, size[1], 2)
            radius = np.random.randint(2, 5)
            color = self._scratch_color()
            cv2.circle(img, (x, y), radius, color, -1)
        
        return img
    
    def _generate_moderate_damage(self, size: Tuple[int, int]) -> np.ndarray:
        """Generate image with moderate damage (visible deformation)."""
        img = np.ones((*size, 3), dtype=np.uint8)
        img[:] = self._random_color()
        
        # Add texture
        noise = np.random.randint(0, 30, size + (3,), dtype=np.uint8)
        img = cv2.add(img, noise)
        
        # Create dent effect with gradient
        center_x, center_y = np.random.randint(size[1] // 4, 3 * size[1] // 4, 2)
        for r in range(30, 5, -2):
            alpha = 0.3 + 0.7 * (30 - r) / 25
            color = tuple(int(c * (1 - alpha)) for c in self._random_color())
            cv2.circle(img, (center_x, center_y), r, color, -1)
        
        # Add multiple damage areas
        for _ in range(2):
            x, y = np.random.randint(0, size[1], 2)
            cv2.circle(img, (x, y), np.random.randint(20, 40), (50, 50, 50), -1)
        
        # Add gouges/scratches
        for _ in range(8):
            x1, y1 = np.random.randint(0, size[1], 2)
            x2, y2 = np.random.randint(0, size[1], 2)
            thickness = np.random.randint(2, 5)
            color = self._damage_color()
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)
        
        return img
    
    def _generate_severe_damage(self, size: Tuple[int, int]) -> np.ndarray:
        """Generate image with severe damage (structural damage)."""
        img = np.zeros((*size, 3), dtype=np.uint8)
        
        # Heavy damage base
        img[:] = (40, 40, 40)  # Dark base
        
        # Add large damaged regions
        for _ in range(3):
            x, y = np.random.randint(0, size[1], 2)
            radius = np.random.randint(40, 80)
            color = (30, 30, 30)
            cv2.circle(img, (x, y), radius, color, -1)
        
        # Severe cracks/breaks
        for _ in range(5):
            x1, y1 = np.random.randint(0, size[1], 2)
            x2, y2 = np.random.randint(0, size[1], 2)
            thickness = np.random.randint(3, 7)
            color = (20, 20, 20)
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)
        
        # Multiple gouges
        for _ in range(12):
            x, y = np.random.randint(0, size[1], 2)
            radius = np.random.randint(5, 20)
            color = (10, 10, 10)
            cv2.circle(img, (x, y), radius, color, -1)
        
        # Add fragmentation pattern
        for _ in range(50):
            x, y = np.random.randint(0, size[1], 2)
            cv2.circle(img, (x, y), 1, (60, 60, 60), -1)
        
        return img
    
    @staticmethod
    def _random_color() -> Tuple[int, int, int]:
        """Generate random car paint color."""
        colors = [
            (200, 200, 200),  # Silver
            (50, 50, 50),     # Black
            (0, 0, 180),      # Red
            (0, 100, 200),    # Orange
            (0, 180, 200),    # Yellow
            (200, 0, 0),      # Blue
            (0, 0, 100),      # Dark blue
            (100, 100, 100),  # Gray
        ]
        return colors[np.random.randint(0, len(colors))]
    
    @staticmethod
    def _scratch_color() -> Tuple[int, int, int]:
        """Generate scratch/paint damage color."""
        colors = [
            (150, 150, 150),  # Light gray
            (100, 100, 100),  # Gray
            (200, 200, 150),  # Primer
            (180, 180, 180),  # Metallic
        ]
        return colors[np.random.randint(0, len(colors))]
    
    @staticmethod
    def _damage_color() -> Tuple[int, int, int]:
        """Generate damage color."""
        colors = [
            (50, 50, 50),     # Dark
            (70, 70, 70),     # Very dark
            (100, 80, 80),    # Brown/rust
            (60, 60, 60),     # Gray-black
        ]
        return colors[np.random.randint(0, len(colors))]
    
    def _print_dataset_summary(self):
        """Print summary of generated dataset."""
        print("\n[DatasetGenerator] Dataset Summary:")
        for cls in self.classes:
            num_files = len(list(self.class_dirs[cls].glob("*.jpg")))
            print(f"  {cls}: {num_files} images")


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic dataset")
    parser.add_argument("--samples", type=int, default=100, help="Samples per class")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    
    args = parser.parse_args()
    
    generator = DatasetGenerator(args.output)
    generator.generate_dataset(samples_per_class=args.samples)
