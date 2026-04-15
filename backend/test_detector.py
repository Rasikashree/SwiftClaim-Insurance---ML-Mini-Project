"""
Damage Detector tests — pytest-compatible.
Run manually: python test_detector.py
Run via pytest: pytest test_detector.py -v
"""
import sys
import os
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from damage_detector import DamageDetector

def make_synthetic_damage(zone="bottom_left"):
    """Create a synthetic damaged-car image for testing."""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 170  # silver body colour
    # --- car body ---
    cv2.rectangle(img, (60, 80), (580, 420), (160, 160, 168), -1)
    # --- windshield ---
    cv2.rectangle(img, (100, 90), (540, 230), (100, 120, 140), -1)
    # --- headlights ---
    cv2.ellipse(img, (130, 310), (40, 25), 0, 0, 360, (220, 230, 240), -1)
    cv2.ellipse(img, (510, 310), (40, 25), 0, 0, 360, (220, 230, 240), -1)

    # --- simulate damage zone ---
    if zone == "bottom_left":        # front bumper left
        cx, cy = 150, 430
    elif zone == "bottom_right":     # front bumper right
        cx, cy = 490, 430
    elif zone == "top_right":        # right fender / hood
        cx, cy = 530, 200
    elif zone == "headlight_right":  # right headlight
        cx, cy = 510, 310
    else:
        cx, cy = 320, 420           # centre bumper

    # paint dent/crumple
    cv2.ellipse(img, (cx, cy), (75, 45), 0, 0, 360, (60, 55, 65), -1)
    cv2.ellipse(img, (cx, cy), (75, 45), 0, 0, 360, (30, 28, 35), 4)
    # add scratches (lines radiating out)
    for angle in range(0, 360, 30):
        rad = angle * 3.14159 / 180
        ex  = int(cx + 90 * np.cos(rad))
        ey  = int(cy + 55 * np.sin(rad))
        cv2.line(img, (cx, cy), (ex, ey), (80, 78, 90), 2)

    return img


def run_test(zone, label):
    img  = make_synthetic_damage(zone)
    path = f"_test_{zone}.jpg"
    cv2.imwrite(path, img)

    d   = DamageDetector()
    res = d.detect(path)

    print(f"\n{'─'*55}")
    print(f"  Test: {label:35s}  → {len(res)} part(s)")
    print(f"{'─'*55}")
    if not res:
        print("  ⚠  No parts detected (fallback not triggered?)")
    for r in res:
        print(f"  ✓ {r['part_name']:25s}  conf={r['confidence']:.3f}  overlap={r['overlap_ratio']:.3f}")

    os.remove(path)
    return res


# ─── pytest-compatible test functions ───────────────────────────────────────

def test_synthetic_image_shape():
    """make_synthetic_damage() must return a valid 480x640 BGR image."""
    img = make_synthetic_damage("bottom_left")
    assert img is not None
    assert img.shape == (480, 640, 3)
    assert img.dtype == np.uint8


def test_synthetic_all_zones():
    """All named damage zones must produce a valid image."""
    zones = ["bottom_left", "bottom_right", "top_right", "headlight_right", "centre"]
    for zone in zones:
        img = make_synthetic_damage(zone)
        assert img.shape[2] == 3, f"zone '{zone}' returned wrong shape"


def test_detector_returns_list():
    """DamageDetector.detect() must return a list for a synthetic image."""
    result = run_test("bottom_left", "pytest: front bumper bottom-left")
    assert isinstance(result, list)


def test_detector_result_keys():
    """Each detected part must have the required keys."""
    result = run_test("centre", "pytest: centre bumper")
    required_keys = {"part_id", "part_name", "confidence", "overlap_ratio"}
    for item in result:
        assert required_keys.issubset(item.keys()), (
            f"Missing keys in result: {required_keys - item.keys()}"
        )


def test_detector_confidence_range():
    """Confidence scores must be in [0, 1]."""
    result = run_test("top_right", "pytest: top-right fender")
    for item in result:
        assert 0.0 <= item["confidence"] <= 1.0, (
            f"Confidence out of range: {item['confidence']}"
        )


# ─── Manual runner ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("bottom_left",     "Front bumper (bottom-left dent)"),
        ("bottom_right",    "Front bumper (bottom-right dent)"),
        ("top_right",       "Right fender / hood dent"),
        ("headlight_right", "Right headlight damage"),
        ("centre",          "Centre bumper damage"),
    ]

    for zone, label in tests:
        run_test(zone, label)

    print("\n✅ All tests completed.\n")
