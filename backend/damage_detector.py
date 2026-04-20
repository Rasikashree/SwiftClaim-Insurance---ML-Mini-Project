"""
SwiftClaim Damage Detector — v2
---------------------------------
Spatially-aware CV pipeline: finds the actual damage zone first,
then ONLY flags parts that substantially overlap with it.

Key improvements over v1:
- Finds the concentrated damage hotspot, not just any edge-rich region
- A part must have ≥ OVERLAP_THRESH fraction overlap with the hotspot to be considered
- Texture/edge scoring is LOCAL to the hotspot pixel mask, not the whole part
- Returns at most MAX_PARTS results, not 5
- Strict SCORE_THRESH keeps weak false-positives out
"""

import cv2
import numpy as np

# ── Part Regions (normalised x1, y1, x2, y2 relative to image size) ──────────
# These are tuned for a FRONT-FACING vehicle image.
# Rear parts share the same spatial zones; context is inferred from which
# adjacent parts are flagged.
PART_REGIONS = {
    "front_bumper": (0.15, 0.62, 0.85, 0.95),
    "rear_bumper": (0.15, 0.62, 0.85, 0.95),
    "hood": (0.10, 0.18, 0.90, 0.62),
    "front_left_door": (0.00, 0.25, 0.42, 0.82),
    "front_right_door": (0.58, 0.25, 1.00, 0.82),
    "rear_left_door": (0.00, 0.30, 0.38, 0.85),
    "rear_right_door": (0.62, 0.30, 1.00, 0.85),
    "left_headlight": (0.02, 0.28, 0.28, 0.58),
    "right_headlight": (0.72, 0.28, 0.98, 0.58),
    "left_taillight": (0.02, 0.30, 0.25, 0.60),
    "right_taillight": (0.75, 0.30, 0.98, 0.60),
    "windshield": (0.10, 0.05, 0.90, 0.38),
    "roof": (0.08, 0.00, 0.92, 0.22),
    "left_fender": (0.00, 0.18, 0.22, 0.68),
    "right_fender": (0.78, 0.18, 1.00, 0.68),
    "trunk": (0.12, 0.32, 0.88, 0.72),
}

PART_DISPLAY_NAMES = {
    "front_bumper": "Front Bumper",
    "rear_bumper": "Rear Bumper",
    "hood": "Hood",
    "front_left_door": "Front Left Door",
    "front_right_door": "Front Right Door",
    "rear_left_door": "Rear Left Door",
    "rear_right_door": "Rear Right Door",
    "left_headlight": "Left Headlight",
    "right_headlight": "Right Headlight",
    "left_taillight": "Left Taillight",
    "right_taillight": "Right Taillight",
    "windshield": "Windshield",
    "roof": "Roof",
    "left_fender": "Left Fender",
    "right_fender": "Right Fender",
    "trunk": "Trunk",
}

# ── Tunable constants ─────────────────────────────────────────────────────────
OVERLAP_THRESH   = 0.10   # ≥10% of the part region must sit inside the damage hotspot
SCORE_THRESH     = 0.22   # local damage score within the overlapping pixels
MAX_PARTS        = 3      # maximum parts returned
MIN_HOTSPOT_AREA = 300    # pixel² — ignore noise; contour must be this large

# Parts that cannot physically be damaged at the same time in one image
MUTUAL_EXCLUSIONS = [
    {"front_bumper", "rear_bumper"},
    {"front_left_door", "rear_left_door"},
    {"front_right_door", "rear_right_door"},
    {"left_headlight", "left_taillight"},
    {"right_headlight", "right_taillight"},
    {"front_bumper", "trunk"},
    {"hood", "trunk"},
    {"front_left_door", "front_right_door"},  # both doors at once is rare
    {"front_right_door", "rear_left_door"},
    {"front_left_door", "rear_right_door"},
    {"rear_left_door", "rear_right_door"},
]

# Max normalised distance (0-1 scale) from damage centroid to part centroid
# Parts whose centres are farther than this are eliminated
MAX_CENTROID_DIST = 0.42   # ~42% of the image diagonal


class DamageDetector:
    def __init__(self):
        print("[DamageDetector v2] Spatially-aware CV pipeline ready.")

    # ── Centroid of the damage mask ───────────────────────────────────────────
    def _mask_centroid(self, mask: np.ndarray) -> tuple:
        """
        Returns (cx_norm, cy_norm) — centroid of white pixels in mask,
        normalised to [0,1] so it is resolution-independent.
        Falls back to image centre if mask is empty.
        """
        H, W = mask.shape[:2]
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return 0.5, 0.5
        return float(xs.mean()) / W, float(ys.mean()) / H

    def _part_centroid(self, region: tuple) -> tuple:
        """Returns (cx_norm, cy_norm) for a normalised region tuple."""
        return (region[0] + region[2]) / 2.0, (region[1] + region[3]) / 2.0

    # ── Image loading ─────────────────────────────────────────────────────────
    def _load(self, path: str) -> np.ndarray:
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Cannot open image: {path}")
        return cv2.resize(img, (640, 480))

    # ── Step 1: Build a binary damage MASK ───────────────────────────────────
    def _build_damage_mask(self, img: np.ndarray) -> np.ndarray:
        """
        Returns a binary mask (uint8, same H×W as img) where 255 = 'damage pixel'.

        Strategy: combine three independent signals, then keep only the largest
        connected blob so scattered background edges don't pollute the result.

        Signal 1 — Canny edges on the grayscale image (captures dents/cracks)
        Signal 2 — Saturation drop mask: paint/metal damage loses saturation
        Signal 3 — Value (brightness) anomaly: reflections and exposed metal
        """
        H, W = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # --- Signal 1: edge map ---
        blur   = cv2.GaussianBlur(gray, (5, 5), 0)
        edges  = cv2.Canny(blur, 40, 120)
        # Dilate to fill gaps inside a damage patch
        k7     = np.ones((9, 9), np.uint8)
        edges  = cv2.dilate(edges, k7, iterations=2)

        # --- Signal 2: saturation anomaly ---
        sat     = hsv[:, :, 1].astype(np.float32)
        sat_mu  = float(sat.mean())
        sat_mask = np.uint8((np.abs(sat - sat_mu) > 35) * 255)
        sat_mask = cv2.dilate(sat_mask, k7, iterations=1)

        # --- Signal 3: brightness anomaly ---
        val      = hsv[:, :, 2].astype(np.float32)
        val_mu   = float(val.mean())
        val_mask = np.uint8((np.abs(val - val_mu) > 45) * 255)
        val_mask = cv2.dilate(val_mask, k7, iterations=1)

        # Combine: a pixel is 'damaged' if it fires in ≥2 of the three signals
        vote = (edges.astype(np.int32) // 255 +
                sat_mask.astype(np.int32) // 255 +
                val_mask.astype(np.int32) // 255)
        combined = np.uint8((vote >= 2) * 255)

        # Keep only the largest connected component (removes background scatter)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(combined)
        if num_labels <= 1:
            return combined  # nothing found — return as-is

        # stats[:,4] = area; label 0 is background
        best_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        largest_mask = np.uint8((labels == best_label) * 255)

        # If the largest blob is tiny noise, fall back to full combined mask
        if stats[best_label, cv2.CC_STAT_AREA] < MIN_HOTSPOT_AREA:
            return combined

        return largest_mask

    # ── Step 2: Score each part against the hotspot mask ─────────────────────
    def _score_part(self, img: np.ndarray, mask: np.ndarray, region: tuple) -> tuple:
        """
        Returns (overlap_ratio, local_damage_score) for one part.

        overlap_ratio  = fraction of the part's bbox that is inside the damage mask
        local_damage_score = edge+texture signal computed ONLY on the masked pixels
        """
        H, W = img.shape[:2]
        x1 = int(region[0] * W)
        y1 = int(region[1] * H)
        x2 = int(region[2] * W)
        y2 = int(region[3] * H)
        x1, x2 = max(x1, 0), min(x2, W)
        y1, y2 = max(y1, 0), min(y2, H)

        part_area = max((x2 - x1) * (y2 - y1), 1)

        # Crop mask to part bbox
        part_mask_crop = mask[y1:y2, x1:x2]
        overlap_pixels  = int(np.count_nonzero(part_mask_crop))
        overlap_ratio   = overlap_pixels / part_area

        if overlap_pixels < 50:          # essentially no overlap
            return overlap_ratio, 0.0

        # Local damage score: compute Laplacian variance + edge density
        # ONLY on pixels inside the damage mask within this part
        crop_gray  = cv2.cvtColor(img[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        roi_pixels = crop_gray[part_mask_crop > 0]

        if roi_pixels.size < 20:
            return overlap_ratio, 0.0

        # Edge density within ROI
        crop_edges   = cv2.Canny(crop_gray, 60, 140)
        in_mask_edges = crop_edges[part_mask_crop > 0]
        edge_density  = float(in_mask_edges.mean()) / 255.0

        # Laplacian roughness within ROI (captures dents)
        lap       = cv2.Laplacian(crop_gray, cv2.CV_64F)
        lap_var   = float(lap[part_mask_crop > 0].var())
        lap_score = min(lap_var / 1500.0, 1.0)

        local_score = min(0.55 * edge_density * 2.0 + 0.45 * lap_score, 1.0)
        return overlap_ratio, local_score

    # ── Main entry point ──────────────────────────────────────────────────────
    def detect(self, image_path: str) -> list:
        """
        Returns list of dicts — only parts that genuinely overlap the
        concentrated damage zone with sufficient local damage evidence.
        """
        img  = self._load(image_path)
        mask = self._build_damage_mask(img)

        # Damage centroid (normalised)
        dmg_cx, dmg_cy = self._mask_centroid(mask)

        candidates = []
        for part_id, region in PART_REGIONS.items():
            # ── Gate 0: centroid proximity ─────────────────────────────────
            pcx, pcy = self._part_centroid(region)
            dist = ((pcx - dmg_cx) ** 2 + (pcy - dmg_cy) ** 2) ** 0.5
            if dist > MAX_CENTROID_DIST:
                continue

            overlap_ratio, local_score = self._score_part(img, mask, region)

            # ── Gate 1: meaningful spatial overlap with the hotspot ────────
            if overlap_ratio < OVERLAP_THRESH:
                continue

            # ── Gate 2: real damage texture in the overlapping pixels ──────
            if local_score < SCORE_THRESH:
                continue

            # Composite confidence
            # Weight: local_score (damage signal) is primary, overlap is secondary
            prox_bonus = max(0.0, 1.0 - dist / MAX_CENTROID_DIST) * 0.05
            confidence = min(0.50 * local_score + 0.40 * overlap_ratio + prox_bonus + 0.10, 1.0)
            # Ensure minimum confidence of 0.3 for parts that pass all gates
            confidence = max(confidence, 0.3)
            candidates.append((part_id, confidence, overlap_ratio, local_score, dist))

        # Sort by confidence descending
        candidates.sort(key=lambda x: -x[1])

        # ── Mutual exclusion: keep higher-confidence part from each pair ───
        selected_ids = []
        for part_id, conf, ov, ls, dist in candidates:
            skip = False
            for excl_set in MUTUAL_EXCLUSIONS:
                if part_id in excl_set:
                    if any(s in excl_set for s in selected_ids):
                        skip = True
                        break
            if not skip:
                selected_ids.append(part_id)
            if len(selected_ids) >= MAX_PARTS:
                break

        results = []
        id_to_candidate = {c[0]: c for c in candidates}
        for part_id in selected_ids:
            _, conf, ov, ls, dist = id_to_candidate[part_id]
            # Sanitize confidence values
            conf = max(0.0, min(float(conf), 1.0)) if conf == conf else 0.5  # NaN check
            ov = max(0.0, min(float(ov), 1.0)) if ov == ov else 0.5
            results.append({
                "part_id":       part_id,
                "part_name":     PART_DISPLAY_NAMES[part_id],
                "confidence":    round(conf, 3),
                "overlap_ratio": round(ov, 3),
                "bbox_region":   PART_REGIONS[part_id],
            })

        # Absolute fallback: nothing passed gates — return highest-overlap part at low confidence
        if not results:
            scored_all = []
            for pid, region in PART_REGIONS.items():
                pcx, pcy = self._part_centroid(region)
                dist = ((pcx - dmg_cx) ** 2 + (pcy - dmg_cy) ** 2) ** 0.5
                ov, ls = self._score_part(img, mask, region)
                scored_all.append((pid, ov, ls, dist))
            # Sort by overlap first, then proximity
            scored_all.sort(key=lambda x: (-x[1], x[3]))
            pid, ov, ls, dist = scored_all[0]
            # Better fallback confidence: weight local_score more heavily
            # ov = overlap, ls = local_damage_score
            fallback_conf = max(0.20 * ov + 0.65 * ls + 0.15, 0.2)
            fallback_conf = round(max(0.0, min(float(fallback_conf), 1.0)), 3)
            if fallback_conf != fallback_conf:  # NaN check
                fallback_conf = 0.25
            ov = max(0.0, min(float(ov), 1.0)) if ov == ov else 0.1
            results.append({
                "part_id":       pid,
                "part_name":     PART_DISPLAY_NAMES[pid],
                "confidence":    fallback_conf,
                "overlap_ratio": round(ov, 3),
                "bbox_region":   PART_REGIONS[pid],
            })

        return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python damage_detector.py <image_path>")
    else:
        d = DamageDetector()
        for result in d.detect(sys.argv[1]):
            print(result)
