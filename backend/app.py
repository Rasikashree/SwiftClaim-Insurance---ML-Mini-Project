"""
SwiftClaim Flask API
----------------------
Main backend server for the SwiftClaim insurance claims engine.
"""

import os
import uuid
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

from damage_detector import DamageDetector
from severity_estimator import SeverityEstimator
from parts_database import PartsDatabase
from payout_calculator import PayoutCalculator
from mongodb_client import MongoDB

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
print("[SwiftClaim] Loading components...")
detector      = DamageDetector()
severity_est  = SeverityEstimator()
parts_db      = PartsDatabase()
payout_calc   = PayoutCalculator(parts_db)
mongo_db      = MongoDB()
print("[SwiftClaim] All components ready.")

# In-memory claim store (production would use SQL)
CLAIMS = {}


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status":  "ok",
        "service": "SwiftClaim Engine v1.0",
        "uptime":  time.strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/api/upload-claim", methods=["POST"])
def upload_claim():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided. Use multipart/form-data with key 'image'."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    # Customer details from form
    customer_name = request.form.get("customer_name", "")
    customer_phone = request.form.get("customer_phone", "")
    vehicle_no = request.form.get("vehicle_no", "")
    insurance_no = request.form.get("insurance_no", "")
    claim_percentage = float(request.form.get("claim_percentage", 0))

    # Optional metadata from form
    vehicle_age = int(request.form.get("vehicle_age", 3))
    use_oem     = request.form.get("use_oem", "false").lower() == "true"
    deductible  = float(request.form.get("deductible", 5000))
    policy_id   = request.form.get("policy_id", f"POL-{uuid.uuid4().hex[:6].upper()}")

    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    ext      = os.path.splitext(file.filename)[1] or ".jpg"
    filepath = os.path.join(UPLOAD_FOLDER, f"{claim_id}{ext}")
    file.save(filepath)

    start = time.time()

    try:
        # --- Pipeline ---
        detected_parts  = detector.detect(filepath)
        severity_result = severity_est.estimate(filepath, detected_parts)
        payout_result   = payout_calc.calculate(
            severity_result,
            vehicle_age=vehicle_age,
            use_oem=use_oem,
            deductible=deductible,
            claim_percentage=claim_percentage,
        )

        processing_ms = round((time.time() - start) * 1000, 1)

        claim = {
            "claim_id":          claim_id,
            "policy_id":         policy_id,
            "customer_name":     customer_name,
            "customer_phone":    customer_phone,
            "vehicle_no":        vehicle_no,
            "insurance_no":      insurance_no,
            "claim_percentage":  claim_percentage,
            "status":            "PROCESSED",
            "processing_time_ms": processing_ms,
            "detected_parts":    severity_result,
            "payout_estimation": payout_result,
            "submitted_at":      time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        CLAIMS[claim_id] = claim

        # Store in MongoDB
        try:
            mongo_claim_id = mongo_db.create_claim(
                user_id="system",
                claim_data={
                    "claim_id": claim_id,
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "vehicle_no": vehicle_no,
                    "insurance_no": insurance_no,
                    "claim_percentage": claim_percentage,
                    "status": "PROCESSED",
                    "detected_parts": severity_result,
                    "payout_estimation": payout_result,
                }
            )
            print(f"[MongoDB] Claim stored: {mongo_claim_id}")
        except Exception as mongo_err:
            print(f"[MongoDB] Error storing claim: {mongo_err}")
        CLAIMS[claim_id] = claim

        # Log to DB
        for item in payout_result.get("line_items", []):
            parts_db.log_claim(
                claim_id, item["part_id"],
                item["severity"], item["line_total"]
            )

        return jsonify(claim), 200

    except Exception as e:
        return jsonify({"error": str(e), "claim_id": claim_id}), 500
    finally:
        # Clean up uploaded file for privacy
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/claims", methods=["GET"])
def list_claims():
    return jsonify(list(CLAIMS.values()))


@app.route("/api/claim/<claim_id>", methods=["GET"])
def get_claim(claim_id):
    claim = CLAIMS.get(claim_id)
    if not claim:
        return jsonify({"error": "Claim not found"}), 404
    return jsonify(claim)


@app.route("/api/parts-prices", methods=["GET"])
def get_parts():
    return jsonify(parts_db.get_all_parts())


@app.route("/api/claims-log", methods=["GET"])
def claims_log():
    return jsonify(parts_db.get_claims_log())


@app.route("/api/stats", methods=["GET"])
def stats():
    all_claims = list(CLAIMS.values())
    total_payout = sum(c["payout_estimation"]["net_payout"] for c in all_claims)
    severity_dist = {}
    for c in all_claims:
        for part in c["detected_parts"]:
            sev = part["severity"]
            severity_dist[sev] = severity_dist.get(sev, 0) + 1
    return jsonify({
        "total_claims":    len(all_claims),
        "total_payout":    round(total_payout, 2),
        "severity_distribution": severity_dist,
        "avg_payout":      round(total_payout / max(len(all_claims), 1), 2),
    })


if __name__ == "__main__":
    print("[SwiftClaim Engine] Starting on http://localhost:5001")
    app.run(debug=True, port=5001, host="0.0.0.0")
