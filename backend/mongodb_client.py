"""
MongoDB Client Configuration
-------------------------------
Manages connection to MongoDB database and CRUD operations.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "swiftclaim")


class MongoDBClient:
    """Singleton MongoDB client for the application."""

    _instance = None
    _client = None

    @classmethod
    def get_client(cls):
        """Get or create MongoDB client instance."""
        if cls._instance is None:
            try:
                cls._client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
                # Verify connection
                cls._client.admin.command('ping')
                cls._instance = cls._client[MONGODB_DATABASE]
                print(f"[MongoDB] Connected to {MONGODB_DATABASE}")
            except ServerSelectionTimeoutError:
                raise ConnectionError(
                    f"Failed to connect to MongoDB at {MONGODB_URI}. "
                    "Make sure MongoDB is running."
                )
            except Exception as e:
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the client (useful for testing)."""
        if cls._client:
            cls._client.close()
        cls._instance = None
        cls._client = None


def init_mongodb():
    """Initialize and return MongoDB client."""
    return MongoDBClient.get_client()


# Collection names
COLLECTIONS = {
    "users": "users",
    "claims": "claims",
    "damage_assessments": "damage_assessments",
    "payouts": "payouts",
    "parts": "parts",
}


class MongoDB:
    """High-level MongoDB database operations."""

    def __init__(self):
        self.db = MongoDBClient.get_client()

    # ─────── USERS ──────────────────────────────────────────
    def create_user(self, user_data: dict) -> str:
        """Create a new user. Returns user ID."""
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        result = self.db[COLLECTIONS["users"]].insert_one(user_data)
        return str(result.inserted_id)

    def get_user(self, user_id: str) -> dict:
        """Retrieve a specific user."""
        return self.db[COLLECTIONS["users"]].find_one({"_id": ObjectId(user_id)})

    def get_user_by_email(self, email: str) -> dict:
        """Retrieve user by email."""
        return self.db[COLLECTIONS["users"]].find_one({"email": email})

    def update_user(self, user_id: str, updates: dict) -> bool:
        """Update user information."""
        updates["updated_at"] = datetime.utcnow()
        result = self.db[COLLECTIONS["users"]].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        result = self.db[COLLECTIONS["users"]].delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    # ─────── CLAIMS ──────────────────────────────────────────
    def create_claim(self, user_id: str, claim_data: dict) -> str:
        """Create a new insurance claim. Returns claim ID."""
        claim = {
            "user_id": ObjectId(user_id),
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **claim_data
        }
        result = self.db[COLLECTIONS["claims"]].insert_one(claim)
        return str(result.inserted_id)

    def get_claim(self, claim_id: str) -> dict:
        """Retrieve a specific claim."""
        return self.db[COLLECTIONS["claims"]].find_one({"_id": ObjectId(claim_id)})

    def get_user_claims(self, user_id: str) -> list:
        """Retrieve all claims for a user."""
        return list(
            self.db[COLLECTIONS["claims"]]
            .find({"user_id": ObjectId(user_id)})
            .sort("created_at", -1)
        )

    def get_claims_by_status(self, status: str) -> list:
        """Get all claims with a specific status."""
        return list(
            self.db[COLLECTIONS["claims"]]
            .find({"status": status})
            .sort("created_at", -1)
        )

    def update_claim(self, claim_id: str, updates: dict) -> bool:
        """Update a claim."""
        updates["updated_at"] = datetime.utcnow()
        result = self.db[COLLECTIONS["claims"]].update_one(
            {"_id": ObjectId(claim_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def delete_claim(self, claim_id: str) -> bool:
        """Delete a claim."""
        result = self.db[COLLECTIONS["claims"]].delete_one(
            {"_id": ObjectId(claim_id)}
        )
        return result.deleted_count > 0

    # ─────── DAMAGE ASSESSMENTS ──────────────────────────────
    def create_assessment(self, claim_id: str, assessment_data: dict) -> str:
        """Create a damage assessment. Returns assessment ID."""
        assessment = {
            "claim_id": ObjectId(claim_id),
            "created_at": datetime.utcnow(),
            **assessment_data
        }
        result = self.db[COLLECTIONS["damage_assessments"]].insert_one(assessment)
        return str(result.inserted_id)

    def get_assessment(self, assessment_id: str) -> dict:
        """Retrieve a specific assessment."""
        return self.db[COLLECTIONS["damage_assessments"]].find_one(
            {"_id": ObjectId(assessment_id)}
        )

    def get_claim_assessments(self, claim_id: str) -> list:
        """Retrieve all assessments for a claim."""
        return list(
            self.db[COLLECTIONS["damage_assessments"]].find(
                {"claim_id": ObjectId(claim_id)}
            )
        )

    def update_assessment(self, assessment_id: str, updates: dict) -> bool:
        """Update an assessment."""
        result = self.db[COLLECTIONS["damage_assessments"]].update_one(
            {"_id": ObjectId(assessment_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def delete_assessment(self, assessment_id: str) -> bool:
        """Delete an assessment."""
        result = self.db[COLLECTIONS["damage_assessments"]].delete_one(
            {"_id": ObjectId(assessment_id)}
        )
        return result.deleted_count > 0

    # ─────── PAYOUTS ────────────────────────────────────────
    def create_payout(self, claim_id: str, payout_data: dict) -> str:
        """Create a payout record. Returns payout ID."""
        payout = {
            "claim_id": ObjectId(claim_id),
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **payout_data
        }
        result = self.db[COLLECTIONS["payouts"]].insert_one(payout)
        return str(result.inserted_id)

    def get_payout(self, payout_id: str) -> dict:
        """Retrieve a specific payout."""
        return self.db[COLLECTIONS["payouts"]].find_one(
            {"_id": ObjectId(payout_id)}
        )

    def get_claim_payout(self, claim_id: str) -> dict:
        """Retrieve payout for a claim."""
        return self.db[COLLECTIONS["payouts"]].find_one(
            {"claim_id": ObjectId(claim_id)}
        )

    def update_payout(self, payout_id: str, updates: dict) -> bool:
        """Update a payout."""
        updates["updated_at"] = datetime.utcnow()
        result = self.db[COLLECTIONS["payouts"]].update_one(
            {"_id": ObjectId(payout_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def get_payouts_by_status(self, status: str) -> list:
        """Get all payouts with a specific status."""
        return list(
            self.db[COLLECTIONS["payouts"]]
            .find({"status": status})
            .sort("created_at", -1)
        )

    # ─────── PARTS ──────────────────────────────────────────
    def create_part(self, part_data: dict) -> str:
        """Create a new part. Returns part ID."""
        part_data["created_at"] = datetime.utcnow()
        result = self.db[COLLECTIONS["parts"]].insert_one(part_data)
        return str(result.inserted_id)

    def get_part(self, part_id: str) -> dict:
        """Retrieve a specific part."""
        return self.db[COLLECTIONS["parts"]].find_one({"_id": ObjectId(part_id)})

    def get_part_by_name(self, part_name: str) -> dict:
        """Retrieve part by name."""
        return self.db[COLLECTIONS["parts"]].find_one({"part_name": part_name})

    def get_all_parts(self) -> list:
        """Retrieve all parts."""
        return list(self.db[COLLECTIONS["parts"]].find({}))

    def update_part(self, part_id: str, updates: dict) -> bool:
        """Update part information."""
        result = self.db[COLLECTIONS["parts"]].update_one(
            {"_id": ObjectId(part_id)},
            {"$set": updates}
        )
        return result.modified_count > 0

    def delete_part(self, part_id: str) -> bool:
        """Delete a part."""
        result = self.db[COLLECTIONS["parts"]].delete_one(
            {"_id": ObjectId(part_id)}
        )
        return result.deleted_count > 0

    # ─────── AGGREGATIONS & ANALYTICS ───────────────────────
    def get_claims_statistics(self) -> dict:
        """Get claims statistics."""
        stats = self.db[COLLECTIONS["claims"]].aggregate([
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_damage": {"$sum": "$total_damage_cost"},
                    "avg_damage": {"$avg": "$total_damage_cost"}
                }
            }
        ])
        return list(stats)

    def get_user_claims_count(self, user_id: str) -> int:
        """Get total claims count for a user."""
        return self.db[COLLECTIONS["claims"]].count_documents(
            {"user_id": ObjectId(user_id)}
        )

    def get_total_payouts(self) -> dict:
        """Get total payouts information."""
        payouts = self.db[COLLECTIONS["payouts"]].aggregate([
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"}
                }
            }
        ])
        return list(payouts)
