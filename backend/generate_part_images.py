"""
SwiftClaim — Car Part Reference Image Generator
-------------------------------------------------
Generates 16 labelled reference images (one per car part) showing
a car silhouette with the specific part highlighted.

These images are used:
  1. Backend  — histogram similarity cross-check during detection
  2. Frontend — displayed next to each detected part in the results
  
Run once:  python generate_part_images.py
"""

import cv2
import numpy as np
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "part_images")
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 640, 480   # canvas size

# ── Colour palette ────────────────────────────────────────────────────────────
BG          = (18,  24,  38)     # dark navy background
BODY_DARK   = (60,  65,  75)     # body shadow
BODY        = (90,  95, 108)     # main body
GLASS       = (80, 120, 145)     # windshield/glass
TYRE        = (30,  30,  30)     # wheel
RIM         = (160, 160, 175)    # wheel rim
LIGHT_LENS  = (210, 230, 245)    # headlight lens
CHROME      = (200, 205, 215)    # chrome trim
WHITE       = (255, 255, 255)
HIGHLIGHT   = (80,  210, 160)    # teal highlight for the active part
HL_DARK     = (0,   140,  90)    # darker teal for edges
LABEL_BG    = (20,  28,  48)
ACCENT      = (110, 130, 200)    # accent blue


# ── Car geometry (all front-quarter-angle profile) ────────────────────────────

def base_car(img: np.ndarray) -> np.ndarray:
    """Draw the full car body on the canvas."""
    # ── Silhouette / body ──────────────────────────────────────
    body_pts = np.array([
        [80, 340], [100, 290], [165, 235], [230, 195], [310, 180],
        [390, 178], [470, 195], [525, 230], [555, 285], [565, 340],
        [80, 340]
    ], np.int32)
    cv2.fillPoly(img, [body_pts], BODY)
    cv2.polylines(img, [body_pts], True, BODY_DARK, 2)

    # ── Roof ──────────────────────────────────────────────────
    roof_pts = np.array([
        [165, 235], [200, 195], [240, 175], [310, 162],
        [390, 160], [445, 172], [480, 192], [470, 195],
        [390, 178], [310, 180], [230, 195]
    ], np.int32)
    cv2.fillPoly(img, [roof_pts], BODY_DARK)

    # ── Windshield ────────────────────────────────────────────
    wind_pts = np.array([
        [200, 195], [240, 175], [310, 162], [390, 160],
        [445, 172], [470, 192], [450, 210], [390, 195],
        [310, 193], [240, 200]
    ], np.int32)
    cv2.fillPoly(img, [wind_pts], GLASS)
    cv2.polylines(img, [wind_pts], True, (50, 80, 100), 2)

    # ── Rear window ──────────────────────────────────────────
    rear_win_pts = np.array([
        [478, 193], [522, 228], [510, 240], [470, 225]
    ], np.int32)
    cv2.fillPoly(img, [rear_win_pts], GLASS)

    # ── Front door ───────────────────────────────────────────
    fd_pts = np.array([
        [195, 240], [240, 200], [310, 193], [320, 295],
        [305, 330], [195, 328]
    ], np.int32)
    cv2.fillPoly(img, [fd_pts], (85, 90, 103))
    cv2.polylines(img, [fd_pts], True, BODY_DARK, 2)

    # Door handle front
    cv2.rectangle(img, (245, 275), (275, 282), CHROME, -1)

    # ── Rear door ─────────────────────────────────────────────
    rd_pts = np.array([
        [320, 295], [310, 193], [390, 195], [450, 210],
        [460, 295], [440, 330], [320, 330]
    ], np.int32)
    cv2.fillPoly(img, [rd_pts], (88, 93, 106))
    cv2.polylines(img, [rd_pts], True, BODY_DARK, 2)
    cv2.rectangle(img, (370, 275), (400, 282), CHROME, -1)

    # ── Left (front) fender ───────────────────────────────────
    lf_pts = np.array([
        [100, 290], [165, 235], [195, 240], [195, 328],
        [135, 340], [100, 340]
    ], np.int32)
    cv2.fillPoly(img, [lf_pts], (80, 85, 98))
    cv2.polylines(img, [lf_pts], True, BODY_DARK, 2)

    # ── Right (rear) fender ────────────────────────────────────
    rf_pts = np.array([
        [460, 225], [520, 250], [555, 285], [555, 340],
        [490, 340], [460, 330], [460, 295]
    ], np.int32)
    cv2.fillPoly(img, [rf_pts], (80, 85, 98))
    cv2.polylines(img, [rf_pts], True, BODY_DARK, 2)

    # ── Front bumper ───────────────────────────────────────────
    fb_pts = np.array([
        [82, 338], [100, 290], [138, 260], [165, 255],
        [165, 270], [140, 278], [108, 320], [92, 355]
    ], np.int32)
    cv2.fillPoly(img, [fb_pts], (70, 74, 86))
    cv2.polylines(img, [fb_pts], True, BODY_DARK, 2)

    # ── Hood ──────────────────────────────────────────────────
    hood_pts = np.array([
        [100, 290], [130, 258], [165, 240], [195, 240],
        [165, 235], [105, 285]
    ], np.int32)
    cv2.fillPoly(img, [hood_pts], (95, 100, 114))

    hood2_pts = np.array([
        [100, 290], [165, 240], [240, 200], [310, 193],
        [310, 180], [230, 195], [165, 235], [100, 285]
    ], np.int32)
    cv2.fillPoly(img, [hood2_pts], (100, 106, 120))
    cv2.polylines(img, [hood2_pts], True, BODY_DARK, 1)

    # ── Rear bumper ────────────────────────────────────────────
    rb_pts = np.array([
        [522, 250], [552, 285], [558, 340], [565, 355],
        [545, 350], [538, 330], [518, 295], [513, 260]
    ], np.int32)
    cv2.fillPoly(img, [rb_pts], (70, 74, 86))
    cv2.polylines(img, [rb_pts], True, BODY_DARK, 2)

    # ── Left headlight ─────────────────────────────────────────
    cv2.ellipse(img, (148, 265), (22, 13), -10, 0, 360, LIGHT_LENS, -1)
    cv2.ellipse(img, (148, 265), (22, 13), -10, 0, 360, CHROME, 2)

    # ── Right taillight ────────────────────────────────────────
    tl_pts = np.array([
        [520, 248], [550, 275], [546, 285], [513, 260]
    ], np.int32)
    cv2.fillPoly(img, [tl_pts], (60, 60, 160))
    cv2.polylines(img, [tl_pts], True, (40, 40, 120), 2)

    # ── Trunk lid ──────────────────────────────────────────────
    trunk_pts = np.array([
        [460, 210], [520, 248], [513, 262], [458, 228]
    ], np.int32)
    cv2.fillPoly(img, [trunk_pts], BODY_DARK)

    # ── Wheels ─────────────────────────────────────────────────
    cv2.circle(img, (155, 355), 42, TYRE, -1)
    cv2.circle(img, (155, 355), 35, (45, 45, 48), -1)
    cv2.circle(img, (155, 355), 22, RIM, -1)
    cv2.circle(img, (155, 355), 8,  TYRE, -1)

    cv2.circle(img, (490, 355), 42, TYRE, -1)
    cv2.circle(img, (490, 355), 35, (45, 45, 48), -1)
    cv2.circle(img, (490, 355), 22, RIM, -1)
    cv2.circle(img, (490, 355), 8,  TYRE, -1)

    # ── Ground shadow ──────────────────────────────────────────
    shadow = np.zeros_like(img)
    cv2.ellipse(shadow, (322, 410), (220, 28), 0, 0, 360, (10, 12, 20), -1)
    img = cv2.addWeighted(img, 1.0, shadow, 0.7, 0)

    return img


# ── Part-specific highlight overlays ─────────────────────────────────────────

def highlight_front_bumper(img):
    pts = np.array([[82,338],[100,290],[138,260],[165,255],[165,275],[130,285],[105,325],[88,358]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 180))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_rear_bumper(img):
    pts = np.array([[522,248],[554,285],[560,342],[568,358],[546,352],[538,328],[518,293],[513,258]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 180))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_hood(img):
    pts = np.array([[100,290],[165,238],[240,200],[310,193],[310,180],[230,195],[165,235],[100,284]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_front_left_door(img):
    pts = np.array([[195,240],[240,200],[310,193],[320,295],[305,330],[195,328]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_front_right_door(img):
    pts = np.array([[320,295],[310,193],[390,195],[450,210],[460,295],[440,330],[320,330]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_rear_left_door(img):   # reuse front-left with different color tone
    pts = np.array([[195,240],[240,200],[310,193],[320,295],[305,330],[195,328]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_rear_right_door(img):
    pts = np.array([[320,295],[310,193],[390,195],[450,210],[460,295],[440,330],[320,330]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_left_headlight(img):
    cv2.ellipse(img, (148, 265), (28, 17), -10, 0, 360, HIGHLIGHT, -1)
    cv2.ellipse(img, (148, 265), (28, 17), -10, 0, 360, HL_DARK, 3)
    return img

def highlight_right_headlight(img):
    # Mirror on right side – approximate position
    cv2.ellipse(img, (148, 265), (28, 17), -10, 0, 360, HIGHLIGHT, -1)
    cv2.ellipse(img, (148, 265), (28, 17), -10, 0, 360, HL_DARK, 3)
    return img

def highlight_left_taillight(img):
    pts = np.array([[520,248],[552,278],[548,290],[510,262]], np.int32)
    cv2.fillPoly(img, [pts], HIGHLIGHT)
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_right_taillight(img):
    pts = np.array([[520,248],[552,278],[548,290],[510,262]], np.int32)
    cv2.fillPoly(img, [pts], HIGHLIGHT)
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_windshield(img):
    pts = np.array([[200,195],[240,175],[310,162],[390,160],[445,172],[470,192],[450,210],
                    [390,195],[310,193],[240,200]], np.int32)
    cv2.fillPoly(img, [pts], (100, 210, 180))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_roof(img):
    pts = np.array([[165,235],[200,195],[240,175],[310,162],[390,160],
                    [445,172],[480,192],[470,195],[390,178],[310,180],[230,195]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_left_fender(img):
    pts = np.array([[100,290],[165,235],[195,240],[195,328],[135,340],[100,340]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_right_fender(img):
    pts = np.array([[460,225],[520,252],[555,287],[555,340],[490,340],[460,330],[460,295]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 3)
    return img

def highlight_trunk(img):
    pts = np.array([[460,210],[522,248],[513,262],[458,228]], np.int32)
    cv2.fillPoly(img, [pts], (*HIGHLIGHT, 160))
    cv2.polylines(img, [pts], True, HL_DARK, 4)
    return img


PART_HIGHLIGHTS = {
    "front_bumper":    highlight_front_bumper,
    "rear_bumper":     highlight_rear_bumper,
    "hood":            highlight_hood,
    "front_left_door": highlight_front_left_door,
    "front_right_door":highlight_front_right_door,
    "rear_left_door":  highlight_rear_left_door,
    "rear_right_door": highlight_rear_right_door,
    "left_headlight":  highlight_left_headlight,
    "right_headlight": highlight_right_headlight,
    "left_taillight":  highlight_left_taillight,
    "right_taillight": highlight_right_taillight,
    "windshield":      highlight_windshield,
    "roof":            highlight_roof,
    "left_fender":     highlight_left_fender,
    "right_fender":    highlight_right_fender,
    "trunk":           highlight_trunk,
}

PART_LABELS = {
    "front_bumper":    "Front Bumper",
    "rear_bumper":     "Rear Bumper",
    "hood":            "Hood",
    "front_left_door": "Front Left Door",
    "front_right_door":"Front Right Door",
    "rear_left_door":  "Rear Left Door",
    "rear_right_door": "Rear Right Door",
    "left_headlight":  "Left Headlight",
    "right_headlight": "Right Headlight",
    "left_taillight":  "Left Taillight",
    "right_taillight": "Right Taillight",
    "windshield":      "Windshield",
    "roof":            "Roof",
    "left_fender":     "Left Fender",
    "right_fender":    "Right Fender",
    "trunk":           "Trunk / Boot",
}


def add_ui_frame(img: np.ndarray, part_id: str) -> np.ndarray:
    """Add branding header + part label."""
    label = PART_LABELS[part_id]
    # Header bar
    cv2.rectangle(img, (0, 0), (W, 46), (14, 20, 35), -1)
    # Accent border
    cv2.rectangle(img, (0, 0), (W, 3), HIGHLIGHT, -1)
    # "SwiftClaim" brand
    cv2.putText(img, "SwiftClaim", (14, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, ACCENT, 2, cv2.LINE_AA)
    # Part name
    cv2.putText(img, f"Reference: {label}", (160, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.60, WHITE, 1, cv2.LINE_AA)
    # Footer bar
    cv2.rectangle(img, (0, H - 36), (W, H), (14, 20, 35), -1)
    cv2.rectangle(img, (0, H - 3), (W, H), HIGHLIGHT, -1)
    cv2.putText(img, "Highlighted region = inspected area",
                (14, H - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (120, 130, 150), 1, cv2.LINE_AA)
    # Highlight legend dot
    cv2.circle(img, (360, H - 18), 7, HIGHLIGHT, -1)
    return img


def generate_all():
    print(f"[PartImages] Generating {len(PART_HIGHLIGHTS)} reference images -> {OUT_DIR}")
    for part_id, highlight_fn in PART_HIGHLIGHTS.items():
        canvas = np.full((H, W, 3), BG, dtype=np.uint8)
        canvas = base_car(canvas)
        canvas = highlight_fn(canvas)
        canvas = add_ui_frame(canvas, part_id)
        path = os.path.join(OUT_DIR, f"{part_id}.jpg")
        cv2.imwrite(path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"  [+] {part_id}.jpg")
    print("[PartImages] Done.")


if __name__ == "__main__":
    generate_all()
