# MongoDB Integration Setup Guide

## Overview
This document provides step-by-step instructions to set up MongoDB as the document database for the SwiftClaim insurance claims processing application.

## Prerequisites
- MongoDB installed locally OR MongoDB Atlas account (https://www.mongodb.com/cloud/atlas)
- Python 3.11+ with pip
- Node.js 18+ with npm

## Option 1: Local MongoDB Setup (Development)

### Step 1: Install MongoDB

#### On Windows
1. Download MongoDB Community Edition from https://www.mongodb.com/try/download/community
2. Run the installer
3. Verify installation:
   ```bash
   mongosh --version
   ```

#### On macOS
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### On Linux (Ubuntu/Debian)
```bash
wget -qO - https://www.mongodb.com/docs/manual/reference/encrypted-server-side-transport-tls/server-ca.crt | sudo tee /etc/apt/trusted.gpg.d/mongodb.asc > /dev/null
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

### Step 2: Connect to MongoDB

Open MongoDB Shell:
```bash
mongosh
```

### Step 3: Configure .env File

Create `.env` in the backend folder:
```env
# Local MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=swiftclaim

# Other configurations
FLASK_ENV=development
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

---

## Option 2: MongoDB Atlas Setup (Cloud - Recommended for Production)

### Step 1: Create MongoDB Atlas Account

1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up or log in
3. Create a new organization and project

### Step 2: Create a Cluster

1. Click "Create Deployment"
2. Choose "M0 Shared Cluster" (free tier)
3. Select your preferred cloud provider and region
4. Click "Create Cluster"

### Step 3: Get Connection String

1. Click "Connect" on the cluster
2. Choose "Drivers" → "Python"
3. Copy the connection string
4. Create a database user:
   - Username: `swiftclaim_user`
   - Password: `your-secure-password` (save this!)

### Step 4: Configure .env File

Update `.env` in the backend folder:
```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://swiftclaim_user:your-secure-password@cluster-name.mongodb.net/swiftclaim?retryWrites=true&w=majority
MONGODB_DATABASE=swiftclaim

# Other configurations
FLASK_ENV=production
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

---

## Step 4: Create Database Schema (Collections)

Open MongoDB Shell and run:

```bash
mongosh
```

Then execute:

```javascript
// Switch to swiftclaim database
use swiftclaim

// Create collections
db.createCollection("users")
db.createCollection("claims")
db.createCollection("damage_assessments")
db.createCollection("payouts")
db.createCollection("parts")

// Create indexes for better performance
db.users.createIndex({ email: 1 }, { unique: true })
db.claims.createIndex({ user_id: 1 })
db.claims.createIndex({ status: 1 })
db.claims.createIndex({ created_at: -1 })
db.damage_assessments.createIndex({ claim_id: 1 })
db.payouts.createIndex({ claim_id: 1 })
db.payouts.createIndex({ status: 1 })
db.parts.createIndex({ part_name: 1 }, { unique: true })

// Verify collections were created
show collections
```

### Collection Schemas

#### Users Collection
```javascript
{
  _id: ObjectId,
  email: String (unique),
  full_name: String,
  phone: String,
  password_hash: String,
  created_at: Date,
  updated_at: Date
}
```

#### Claims Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  status: String, // pending, approved, rejected, paid
  vehicle_make: String,
  vehicle_model: String,
  vehicle_year: Number,
  damage_description: String,
  total_damage_cost: Number,
  approved_payout: Number,
  created_at: Date,
  updated_at: Date
}
```

#### Damage Assessments Collection
```javascript
{
  _id: ObjectId,
  claim_id: ObjectId (ref: claims),
  damaged_parts: [String], // array of part IDs
  severity_score: Number,
  damage_images: [String], // array of image URLs
  assessment_notes: String,
  created_at: Date
}
```

#### Payouts Collection
```javascript
{
  _id: ObjectId,
  claim_id: ObjectId (ref: claims),
  amount: Number,
  status: String, // pending, approved, rejected, completed
  oem_vs_aftermarket: String, // oem or aftermarket
  payment_method: String,
  reference_number: String (unique),
  created_at: Date,
  updated_at: Date
}
```

#### Parts Collection
```javascript
{
  _id: ObjectId,
  part_name: String (unique),
  oem_price: Number,
  aftermarket_price: Number,
  labor_hours: Number,
  labor_rate: Number,
  created_at: Date
}
```

---

## Step 5: Insert Sample Data

```javascript
// Insert sample users
db.users.insertMany([
  {
    email: "john@example.com",
    full_name: "John Doe",
    phone: "+1234567890",
    created_at: new Date(),
    updated_at: new Date()
  }
])

// Insert sample parts
db.parts.insertMany([
  {
    part_name: "Front Bumper",
    oem_price: 12000,
    aftermarket_price: 7500,
    labor_hours: 4.0,
    labor_rate: 800,
    created_at: new Date()
  },
  {
    part_name: "Windshield",
    oem_price: 18000,
    aftermarket_price: 11000,
    labor_hours: 3.0,
    labor_rate: 800,
    created_at: new Date()
  }
])
```

---

## Step 6: Configure Backend

### Update Backend Requirements

Backend `requirements.txt` already includes:
```
pymongo>=4.6.0
python-dotenv>=1.0.0
```

Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Import and Use MongoDB Client

In your Flask app (`app.py`):

```python
from mongodb_client import MongoDB, init_mongodb

# Initialize MongoDB
init_mongodb()
db = MongoDB()

# Create a claim
claim_id = db.create_claim(
    user_id="user-uuid",
    claim_data={
        "vehicle_make": "Toyota",
        "vehicle_model": "Corolla",
        "damage_description": "Front bumper damage"
    }
)

# Get user claims
claims = db.get_user_claims("user-uuid")

# Update claim status
db.update_claim(claim_id, {"status": "approved"})
```

---

## Step 7: Configure Frontend

### Update Frontend Dependencies

```bash
cd frontend
npm install
```

This installs `axios` (already added to package.json)

### Use MongoDB Client in React

```javascript
import { MongoDB } from '@/lib/mongodbClient';

// Create a claim
const claim = await MongoDB.createClaim(userId, {
  vehicle_make: "Toyota",
  vehicle_model: "Corolla",
  damage_description: "Front damage"
});

// Get user claims
const claims = await MongoDB.getUserClaims(userId);

// Update claim
await MongoDB.updateClaim(claimId, { status: "approved" });
```

---

## Step 8: Docker Setup (Optional)

Using Docker Compose, MongoDB is automatically set up:

```bash
# Start all services (MongoDB, Backend, Frontend)
docker compose up --build

# View logs
docker compose logs -f mongodb
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down
```

MongoDB will be available at `mongodb://root:swiftclaim_password@localhost:27017`

---

## MongoDB Operations Reference

### Backend (Python)

```python
from mongodb_client import MongoDB

db = MongoDB()

# CREATE
user_id = db.create_user({"email": "user@example.com", "full_name": "John"})
claim_id = db.create_claim(user_id, {"vehicle_make": "Toyota"})

# READ
user = db.get_user(user_id)
claims = db.get_user_claims(user_id)
claim = db.get_claim(claim_id)

# UPDATE
db.update_claim(claim_id, {"status": "approved"})

# DELETE
db.delete_claim(claim_id)

# ANALYTICS
stats = db.get_claims_statistics()
payouts = db.get_total_payouts()
```

### Frontend (JavaScript)

```javascript
import { MongoDB } from '@/lib/mongodbClient';

// CREATE
const user = await MongoDB.createUser({ email: "user@example.com" });
const claim = await MongoDB.createClaim(userId, { vehicle_make: "Toyota" });

// READ
const userClaims = await MongoDB.getUserClaims(userId);
const allParts = await MongoDB.getAllParts();

// UPDATE
await MongoDB.updateClaim(claimId, { status: "approved" });

// DELETE
await MongoDB.deleteClaim(claimId);

// ANALYTICS
const stats = await MongoDB.getClaimsStatistics();
```

---

## Troubleshooting

### Error: "Failed to connect to MongoDB"
- Ensure MongoDB is running locally: `brew services start mongodb-community` (macOS) or check Windows Services
- For Atlas: Verify internet connection and whitelist your IP in cluster settings
- Check connection string in `.env` file

### Error: "MONGODB_URI not set"
- Create `.env` file in backend folder
- Verify it has the correct MONGODB_URI value
- Restart the application

### Error: "Connection timeout"
- Increase connection timeout in MongoDB URI: `?serverSelectionTimeoutMS=10000`
- Check firewall settings
- For Atlas: Add your IP to IP Whitelist

### Error: "Authentication failed"
- Verify MongoDB username and password
- For local: Check if credentials match those in docker-compose.yml
- For Atlas: Confirm user exists and password is correct

### Error: "Database 'swiftclaim' does not exist"
- Run SQL schema commands above to create collections
- Or first insert a document (MongoDB creates DB on first write)

---

## Performance Optimization

### Index Creation (Already Handled)
Indexes are created automatically for:
- User emails (unique)
- Claim user_id and status
- Payout claim_id and status
- Part names (unique)

### Query Optimization Tips
```python
# Use find() with filters instead of loading all data
claims = db.get_claims_by_status("pending")  # Better

# Use aggregation for analytics
stats = db.get_claims_statistics()  # Uses $group aggregation
```

---

## Backup and Restore

### Local MongoDB
```bash
# Backup
mongodump --uri="mongodb://localhost:27017/swiftclaim" --out=./backup

# Restore
mongorestore --uri="mongodb://localhost:27017/swiftclaim" ./backup
```

### MongoDB Atlas
1. Go to Atlas Dashboard → Your Cluster
2. Click "Backup" tab
3. Click "Restore" to restore from snapshot
4. Or download backups manually

---

## Next Steps

1. **Enable Authentication**: Secure your MongoDB with authentication
2. **Set up Replication**: For production, configure replica sets
3. **Enable Encryption**: Use TLS/SSL for data in transit
4. **Configure Backups**: Enable automated backups (Atlas)
5. **Monitor Performance**: Use MongoDB Atlas monitoring tools

---

## Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/)
- [MongoDB Query Language](https://docs.mongodb.com/manual/crud/)
- [Best Practices](https://www.mongodb.com/docs/manual/administration/best-practices/)
