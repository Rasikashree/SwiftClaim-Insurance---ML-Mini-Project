"""
SwiftClaim Severity Estimator — v2
------------------------------------
Uses the same damage mask pipeline as DamageDetector so that severity
is scored ONLY on the actual damaged pixels within each part — not the
entire part region (which includes undamaged areas and inflates scores).

Severity thresholds:
  Minor    < 0.35  — surface scratches / paint damage
  Moderate 0.35–0.65 — visible deformation, likely needs replacement
  Severe   ≥ 0.65  — structural damage, immediate replacement
"""

import cv2
import numpy as np
from enum import Enum
from model_manager import get_model_manager


class Severity(str, Enum):
    MINOR    = "Minor"
    MODERATE = "Moderate"
    SEVERE   = "Severe"


SEVERITY_DESCRIPTIONS = {
    Severity.MINOR:    "Surface scratches or paint damage. Repair likely sufficient.",
    Severity.MODERATE: "Visible deformation with mechanical impact. Partial/full replacement needed.",
    Severity.SEVERE:   "Major structural damage. Immediate full replacement required.",
}

SEVERITY_MULTIPLIERS = {
    Severity.MINOR:    1.0,
    Severity.MODERATE: 2.2,
    Severity.SEVERE:   3.8,
}


def _build_damage_mask(img: np.ndarray) -> np.ndarray:
    """
    Re-computes the same 3-signal mask used by DamageDetector.
    Returns a binary H×W uint8 mask (255 = damage pixel).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    blur  = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 40, 120)
    k9    = np.ones((9, 9), np.uint8)
    edges = cv2.dilate(edges, k9, iterations=2)

    sat      = hsv[:, :, 1].astype(np.float32)
    sat_mask = np.uint8((np.abs(sat - sat.mean()) > 35) * 255)
    sat_mask = cv2.dilate(sat_mask, k9, iterations=1)

    val      = hsv[:, :, 2].astype(np.float32)
    val_mask = np.uint8((np.abs(val - val.mean()) > 45) * 255)
    val_mask = cv2.dilate(val_mask, k9, iterations=1)

    vote = (edges.astype(np.int32) // 255 +
            sat_mask.astype(np.int32) // 255 +
            val_mask.astype(np.int32) // 255)
    combined = np.uint8((vote >= 2) * 255)

    # Keep only largest connected component
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(combined)
    if num_labels <= 1:
        return combined
    best = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    largest = np.uint8((labels == best) * 255)
    if stats[best, cv2.CC_STAT_AREA] < 400:
        return combined
    return largest


class SeverityEstimator:
    def __init__(self):
        self.model_manager = None
        try:
            self.model_manager = get_model_manager()
            if self.model_manager.is_model_available():
                print("[SeverityEstimator] ML model available for inference")
            else:
                print("[SeverityEstimator] ML model not available, falling back to CV")
        except Exception as e:
            print(f"[SeverityEstimator] Could not load ML model: {e}, using CV fallback")

    def _crop_masked_region(self, img: np.ndarray, mask: np.ndarray, region: tuple):
        """
        Returns (crop_img, crop_mask) clipped to the part's bbox.
        """
        H, W = img.shape[:2]
        x1 = max(int(region[0] * W), 0)
        y1 = max(int(region[1] * H), 0)
        x2 = min(int(region[2] * W), W)
        y2 = min(int(region[3] * H), H)
        return img[y1:y2, x1:x2], mask[y1:y2, x1:x2]

    def _severity_score_from_mask(
        self,
        crop: np.ndarray,
        crop_mask: np.ndarray,
        confidence: float,
    ) -> float:
        """
        Compute severity score [0,1] using only the hotspot pixels inside
        the part region. Falls back to full-crop analysis if mask is empty.
        """
        if crop.size == 0:
            return confidence * 0.4

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        masked_px = int(np.count_nonzero(crop_mask))
        total_px = max(crop_mask.size, 1)
        mask_density = masked_px / total_px  # how much of the part is damaged

        if masked_px > 30:
            # ── Analyse only the hotspot pixels ──
            roi_gray = gray.copy()
            roi_gray[crop_mask == 0] = 0  # zero-out undamaged pixels

            # Laplacian roughness (dent depth proxy)
            lap = cv2.Laplacian(roi_gray.astype(np.float32), cv2.CV_32F)
            lap_var = float(np.var(lap[crop_mask > 0]))
            lap_s = min(lap_var / 1200.0, 1.0)

            # Edge density within masked area
            edges = cv2.Canny(gray, 60, 140)
            edge_s = float(edges[crop_mask > 0].mean()) / 255.0

            # Structural discontinuity: std of pixel values inside hotspot
            pix_std = float(gray[crop_mask > 0].std()) / 80.0
            pix_s = min(pix_std, 1.0)

            raw = 0.40 * lap_s + 0.35 * edge_s + 0.25 * pix_s
        else:
            # Fallback: whole-crop analysis at lower weight
            lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            lap_s = min(lap_var / 1200.0, 1.0)
            edges = cv2.Canny(gray, 60, 140)
            edge_s = float(edges.mean()) / 255.0
            raw = 0.5 * lap_s + 0.5 * edge_s
            mask_density = 0.15  # treat as small damage

        # Blend: signal from texture + fraction of part that is damaged + model confidence
        score = (
            0.45 * raw
            + 0.30 * min(mask_density * 3, 1.0)
            + 0.25 * confidence
        )
        score = float(score)
        # Sanitize NaN
        if score != score or score < 0 or score > 1:  # NaN check or bounds
            score = 0.5  # fallback to moderate
        return round(min(score, 1.0), 4)

    def _score_to_severity(self, score: float) -> Severity:
        if score < 0.35:
            return Severity.MINOR
        elif score < 0.65:
            return Severity.MODERATE
        else:
            return Severity.SEVERE

    def _get_ml_prediction(self, crop: np.ndarray) -> dict:
        """
        Get severity prediction from the trained ML model.
        Returns None if prediction fails.
        """
        try:
            if crop.size == 0:
                return None

            # Model expects BGR, so convert if needed
            if len(crop.shape) != 3 or crop.shape[2] != 3:
                return None

            # Use model manager to predict
            result = self.model_manager.predict(crop, confidence_threshold=0.3)

            # Return None if there's an error or no severity prediction
            if result.get("error") is not None or result.get("severity") is None:
                return None

            return {
                "severity": result.get("severity"),
                "confidence": result.get("confidence", 0),
                "all_scores": result.get("all_scores", {})
            }
        except Exception as e:
            print(f"[SeverityEstimator] ML prediction error: {e}")
            return None

    def _ml_confidence_to_score(self, ml_result: dict) -> float:
        """
        Convert ML model confidence to severity score [0,1].
        Severe=1.0, Moderate=0.5, Minor=0.2
        """
        try:
            severity = ml_result.get("severity", "Minor")
            confidence = float(ml_result.get("confidence", 0.5))

            if severity == "Severe":
                score = 0.8 + (confidence * 0.2)  # 0.8-1.0
            elif severity == "Moderate":
                score = 0.45 + (confidence * 0.2)  # 0.45-0.65
            else:  # Minor
                score = 0.15 + (confidence * 0.2)  # 0.15-0.35

            # Sanitize
            score = float(score)
            if score != score or score < 0 or score > 1:
                score = 0.5

            return round(min(score, 1.0), 4)
        except Exception as e:
            print(f"[SeverityEstimator] Error converting ML confidence: {e}")
            return 0.5

    def estimate(self, image_path: str, detected_parts: list) -> list:
        """
        Enriches each detected part with severity classification.
        Uses ML model if available, otherwise falls back to CV.
        """
        img = cv2.imread(image_path)
        if img is None:
            return [
                {**p,
                 "severity": Severity.MINOR.value,
                 "severity_score": 0.2,
                 "severity_description": SEVERITY_DESCRIPTIONS[Severity.MINOR],
                 "severity_multiplier": SEVERITY_MULTIPLIERS[Severity.MINOR],
                 "prediction_source": "fallback"}
                for p in detected_parts
            ]

        img  = cv2.resize(img, (640, 480))
        mask = _build_damage_mask(img)

        results = []
        for part in detected_parts:
            region    = part["bbox_region"]
            crop, crop_mask = self._crop_masked_region(img, mask, region)

            # Try ML model first
            ml_result = None
            if self.model_manager and self.model_manager.is_model_available():
                ml_result = self._get_ml_prediction(crop)

            # Use ML prediction if available and reliable, otherwise use CV
            if ml_result and ml_result.get("confidence", 0) > 0.4:
                severity = Severity(ml_result["severity"])
                score = self._ml_confidence_to_score(ml_result)
                prediction_source = "ml_model"
            else:
                # Fallback to CV-based estimation
                score = self._severity_score_from_mask(crop, crop_mask, part["confidence"])
                severity = self._score_to_severity(score)
                prediction_source = "computer_vision"

            results.append({
                **part,
                "severity":             severity.value,
                "severity_score":       score,
                "severity_description": SEVERITY_DESCRIPTIONS[severity],
                "severity_multiplier":  SEVERITY_MULTIPLIERS[severity],
                "prediction_source":    prediction_source,
            })

        return results
