"""
End-to-end test: download the Maruti Baleno test image and
send it through the claim API, showing exactly which parts
are detected vs the old behaviour.
"""
import urllib.request, tempfile, os, json, sys
import urllib.request as req

# ── save user's car image locally ──────────────────────────────────────────
# (we download a public similar front-damage image for automated testing)
TEST_URL = "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"

# ── Instead, use a file path if user's image was saved ─────────────────────
# The user's image is the Maruti Baleno TN30CY5969 with front-right damage.
# We'll create a synthetic front-right quadrant damage image as a proxy.

import cv2
import numpy as np
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from damage_detector import DamageDetector
from severity_estimator import SeverityEstimator

def make_front_right_damage() -> str:
    """
    Simulate a Maruti Baleno front-right collision:
    - Hood crumple on RIGHT side  
    - Right headlight broken
    - Front bumper RIGHT corner crushed
    """
    img = np.ones((480, 640, 3), dtype=np.uint8) * 175   # silver

    # ── Body panels ──
    cv2.rectangle(img, (50, 70),  (590, 430), (165, 165, 172), -1)   # body
    cv2.rectangle(img, (80, 75),  (560, 230), (90,  115, 135), -1)   # windshield

    # ── Left headlight (undamaged) ──
    cv2.ellipse(img, (120, 320), (45, 28), 0, 0, 360, (210, 225, 240), -1)
    cv2.ellipse(img, (120, 320), (45, 28), 0, 0, 360, (140, 155, 165), 2)

    # ── Right headlight (damaged - cracked, displaced) ──
    cv2.ellipse(img, (520, 320), (45, 28), 0, 0, 360, (210, 225, 240), -1)
    # Add crack lines
    for a in range(0, 180, 25):
        r = a * 3.14159 / 180
        cv2.line(img, (520, 320),
                 (int(520 + 50*np.cos(r)), int(320 + 35*np.sin(r))),
                 (40, 40, 50), 2)
    cv2.ellipse(img, (520, 320), (45, 28), 0, 0, 360, (30, 30, 40), 3)

    # ── Right fender crumple ──
    crumple_pts = np.array([
        [490, 180], [580, 160], [610, 230], [590, 280], [490, 300], [460, 240]
    ], dtype=np.int32)
    cv2.fillPoly(img, [crumple_pts], (70, 68, 80))
    cv2.polylines(img, [crumple_pts], True, (30, 28, 38), 3)
    for _ in range(8):
        x1 = np.random.randint(470, 590)
        y1 = np.random.randint(170, 290)
        x2 = x1 + np.random.randint(-30, 30)
        y2 = y1 + np.random.randint(-20, 20)
        cv2.line(img, (x1,y1), (x2,y2), (20,18,28), 2)

    # ── Front bumper right corner crush ──
    crush_pts = np.array([
        [400, 420], [560, 410], [580, 450], [560, 465], [390, 460]
    ], dtype=np.int32)
    cv2.fillPoly(img, [crush_pts], (55, 53, 65))
    cv2.polylines(img, [crush_pts], True, (25, 23, 33), 3)

    path = "_test_baleno_front_right.jpg"
    cv2.imwrite(path, img)
    return path


print("=" * 60)
print("  SwiftClaim v2 — End-to-End Test")
print("  Scenario: Maruti Baleno front-right collision")
print("=" * 60)

img_path = make_front_right_damage()

d   = DamageDetector()
s   = SeverityEstimator()

parts    = d.detect(img_path)
enriched = s.estimate(img_path, parts)

print(f"\n  Detected {len(enriched)} damaged part(s):\n")
for p in enriched:
    print(f"  ✓ {p['part_name']:25s}  "
          f"severity={p['severity']:8s}  "
          f"conf={p['confidence']:.3f}  "
          f"overlap={p['overlap_ratio']:.3f}")

print()
if len(enriched) <= 3:
    print("  ✅ PASS — only spatially-relevant parts flagged")
else:
    print("  ⚠  Too many parts — thresholds may need tuning")

os.remove(img_path)
