"""
SwiftClaim Payout Calculator
------------------------------
Computes insurance payout estimation from severity analysis + parts DB.
Applies depreciation, policy deductible, and approval logic.
"""

from parts_database import PartsDatabase

DEPRECIATION_TABLE = {
    # age_years → depreciation rate
    (0, 1):   0.05,
    (1, 3):   0.12,
    (3, 5):   0.20,
    (5, 8):   0.30,
    (8, 12):  0.40,
    (12, 99): 0.55,
}

DEFAULT_DEDUCTIBLE    = 5000.0   # INR (policy standard)
DEFAULT_VEHICLE_AGE   = 3        # years (used when not provided)
GST_RATE              = 0.18
MAX_CLAIM_LIMIT       = 500000.0  # INR


def get_depreciation(vehicle_age: int) -> float:
    for (lo, hi), rate in DEPRECIATION_TABLE.items():
        if lo <= vehicle_age < hi:
            return rate
    return 0.55


class PayoutCalculator:
    def __init__(self, parts_db: PartsDatabase):
        self.parts_db = parts_db

    def calculate(self, severity_results: list, vehicle_age: int = DEFAULT_VEHICLE_AGE,
                  use_oem: bool = False, deductible: float = DEFAULT_DEDUCTIBLE,
                  claim_percentage: float = 100.0) -> dict:
        """
        severity_results: list from SeverityEstimator.estimate()
        claim_percentage: percentage of claim (0-100) - NOT used for deductible anymore
        Returns detailed payout breakdown.
        """
        depreciation_rate = get_depreciation(vehicle_age)
        # Fixed deductible (don't multiply by claim percentage - that was wrong!)
        effective_deductible = deductible
        line_items = []
        subtotal_parts   = 0.0
        subtotal_labor   = 0.0
        subtotal_gst     = 0.0

        for part in severity_results:
            db_entry = self.parts_db.get_part(part["part_id"])
            if db_entry is None:
                continue

            # Choose OEM or aftermarket
            base_price = db_entry["oem_price"] if use_oem else db_entry["aftermarket_price"]

            # Apply severity multiplier (partial or full replacement)
            sev = part["severity"]
            if sev == "Minor":
                # Only repair cost (~30% of part price)
                part_cost = base_price * 0.30
                action = "Repair"
            elif sev == "Moderate":
                # 70% replacement + repair
                part_cost = base_price * 0.70
                action = "Partial Replacement"
            else:
                # Full replacement
                part_cost = base_price
                action = "Full Replacement"

            # Apply depreciation
            depreciated_cost = part_cost * (1 - depreciation_rate)

            # Labor
            labor_cost = db_entry["labor_hours"] * db_entry["labor_rate"]
            if sev == "Minor":
                labor_cost *= 0.4
            elif sev == "Moderate":
                labor_cost *= 0.7

            # GST on labor + parts
            gst = (depreciated_cost + labor_cost) * GST_RATE

            # Sanitize values
            def sanitize_price(val):
                if val is None or val != val or val < 0:  # NaN or negative check
                    return 0.0
                return float(val)

            base_price = sanitize_price(base_price)
            depreciated_cost = sanitize_price(depreciated_cost)
            labor_cost = sanitize_price(labor_cost)
            gst = sanitize_price(gst)

            line_items.append({
                "part_id":          part["part_id"],
                "part_name":        part["part_name"],
                "severity":         sev,
                "action":           action,
                "base_price":       round(base_price, 2),
                "depreciated_cost": round(depreciated_cost, 2),
                "labor_cost":       round(labor_cost, 2),
                "gst":              round(gst, 2),
                "line_total":       round(depreciated_cost + labor_cost + gst, 2),
                "confidence":       part.get("confidence", 0),
            })

            subtotal_parts += depreciated_cost
            subtotal_labor += labor_cost
            subtotal_gst   += gst

        gross_total = subtotal_parts + subtotal_labor + subtotal_gst

        # Apply claim percentage: Final Payout = Gross Total - (Gross Total × Claim%)
        # Then add back the deductible (it comes from insurance's portion, not customer's)
        claim_multiplier = claim_percentage / 100.0
        insurance_covers = gross_total * claim_multiplier
        insurance_pays = insurance_covers - effective_deductible  # Insurance pays after deductible
        net_payout = gross_total - insurance_pays  # Customer pays the rest

        # Floor at 0, cap at limit
        net_payout = max(net_payout, 0)
        net_payout = min(net_payout, MAX_CLAIM_LIMIT)

        # Sanitize NaN values
        def safe_float(val):
            if val is None or (isinstance(val, float) and (val != val or val == float('inf') or val == float('-inf'))):
                return 0.0
            return float(val)

        gross_total = safe_float(gross_total)
        net_payout = safe_float(net_payout)
        subtotal_parts = safe_float(subtotal_parts)
        subtotal_labor = safe_float(subtotal_labor)
        subtotal_gst = safe_float(subtotal_gst)

        # Recommendation
        if gross_total < 10000:
            recommendation = "LOW_VALUE_CLAIM"
            recommendation_note = "Claim value is below threshold. Consider self-repair."
        elif gross_total < 50000:
            recommendation = "APPROVE"
            recommendation_note = "Standard claim. Auto-approved for processing."
        elif gross_total < 150000:
            recommendation = "APPROVE_WITH_INSPECTION"
            recommendation_note = "High-value claim. Physical inspection recommended."
        else:
            recommendation = "ESCALATE"
            recommendation_note = (
                "Premium claim support: Your vehicle damage assessment qualifies for "
                "white-glove service with priority handling by our expert claims team."
            )

        return {
            "line_items":        line_items,
            "subtotal_parts":    round(subtotal_parts, 2),
            "subtotal_labor":    round(subtotal_labor, 2),
            "subtotal_gst":      round(subtotal_gst, 2),
            "gross_total":       round(gross_total, 2),
            "deductible":        round(deductible, 2),
            "claim_percentage":  claim_percentage,
            "payout_percentage": claim_percentage,
            "effective_deductible": round(effective_deductible, 2),
            "net_payout":        round(net_payout, 2),
            "amount_after_claim": round(net_payout, 2),
            "depreciation_rate": f"{depreciation_rate * 100:.0f}%",
            "vehicle_age_years": vehicle_age,
            "parts_type":        "OEM" if use_oem else "Aftermarket",
            "recommendation":    recommendation,
            "recommendation_note": recommendation_note,
            "currency":          "INR",
        }
