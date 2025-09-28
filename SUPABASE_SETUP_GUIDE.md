# 🚀 Supabase Configuration Guide for StingerSpaces

This guide will help you set up Supabase database storage for Reddit comments and validation data instead of using local JSON files.

## 📋 Prerequisites

- Supabase account (free tier available)
- Python environment with the project dependencies

## 🛠️ Step 1: Create Supabase Project

### 1.1 Sign up for Supabase
1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project" 
3. Sign up with GitHub, Google, or email

### 1.2 Create New Project
1. Click "New Project"
2. Choose your organization (or create one)
3. Fill in project details:
   - **Name**: `stinger-spaces` (or your preferred name)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your location
4. Click "Create new project"
5. Wait 2-3 minutes for setup to complete

## 🔑 Step 2: Get Your Credentials

### 2.1 Find Your Project Settings
1. In your Supabase dashboard, go to **Settings** → **API**
2. You'll see two important values:

```
Project URL: https://your-project-id.supabase.co
anon/public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2.2 Get Service Role Key (Recommended)
1. In the same API settings page, scroll down to "Service Role"
2. Copy the **service_role** key (this has full database access)
3. This key should look like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## 🗄️ Step 3: Create Database Tables

### 3.1 Open SQL Editor
1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"

### 3.2 Create Tables
Copy and paste this SQL script:

```sql
-- Apartments table
CREATE TABLE apartments (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    aliases JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Comments validation table
CREATE TABLE comment_validations (
    id SERIAL PRIMARY KEY,
    comment_id TEXT UNIQUE NOT NULL,
    source_apartment TEXT NOT NULL,
    mentioned_apartment TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    confidence_score FLOAT NOT NULL,
    validation_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    reddit_post_id TEXT,
    reddit_comment_id TEXT,
    FOREIGN KEY (source_apartment) REFERENCES apartments(name),
    FOREIGN KEY (mentioned_apartment) REFERENCES apartments(name)
);

-- Validation grid summary table
CREATE TABLE validation_grid (
    id SERIAL PRIMARY KEY,
    source_apartment TEXT NOT NULL,
    mentioned_apartment TEXT NOT NULL,
    comment_count INTEGER DEFAULT 0,
    verified_comments INTEGER DEFAULT 0,
    confidence_sum FLOAT DEFAULT 0.0,
    average_confidence FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_apartment, mentioned_apartment),
    FOREIGN KEY (source_apartment) REFERENCES apartments(name),
    FOREIGN KEY (mentioned_apartment) REFERENCES apartments(name)
);

-- Insert initial apartment data (optional)
INSERT INTO apartments (name) VALUES 
('Catalyst Midtown'),
('One12 Courtland'),
('Square On 5th'),
('The Connector'),
('Whistler'),
('Westmar Student Lofts'),
('The Flats at Atlantic Station Student Housing'),
('The Mix Apartments'),
('Reflection'),
('100 Midtown'),
('Yugo Atlanta Summerhill'),
('Paloma West Midtown'),
('Kinetic'),
('The Rive Atlanta'),
('The Legacy at Centennial'),
('Parsons Pointe'),
('Entra West End');
```

3. Click **Run** to execute the script
4. You should see "Success. No rows returned" message

## 🔧 Step 4: Configure Environment Variables

### 4.1 Install Supabase Python Library
```bash
cd /Users/harshshah/Documents/hackgt
source .venv/bin/activate
pip install supabase
```

### 4.2 Set Environment Variables

#### Option A: Create .env file (Recommended)
1. Create a `.env` file in your project root:

```bash
# In /Users/harshshah/Documents/hackgt/
touch .env
```

2. Add your credentials to `.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...your-service-role-key...

# Reddit API (if you have them)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# University Configuration
UNIVERSITY_CONFIG=gt
```

3. Install python-dotenv to load .env files:

```bash
pip install python-dotenv
```

#### Option B: Export directly in terminal

```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...your-service-role-key..."
```

## 🧪 Step 5: Test the Configuration

### 5.1 Test Supabase Connection
Run this test script:

```bash
cd backend/src
python -c "
from supabase_grid_manager import SupabaseGridManager
import os

# Check if credentials are loaded
print('SUPABASE_URL:', os.getenv('SUPABASE_URL'))
print('SUPABASE_KEY:', os.getenv('SUPABASE_KEY', 'Not set'))

# Test connection
try:
    grid_manager = SupabaseGridManager()
    if not grid_manager.use_local_storage:
        print('✅ Supabase connection successful!')
        print(f'Connected to: {grid_manager.supabase_url}')
    else:
        print('❌ Using local storage - check credentials')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### 5.2 Run Full Test
```bash
cd backend/src
python supabase_grid_manager.py
```

Expected output:
```
✅ Supabase connection successful!
Adding test validations...
✅ Added: Catalyst Midtown -> Square On 5th
✅ Added: Square On 5th -> The Connector  
✅ Added: The Connector -> 100 Midtown
```

## 🔍 Step 6: Verify Data in Supabase

### 6.1 Check Tables
1. Go to **Table Editor** in Supabase dashboard
2. You should see 3 tables: `apartments`, `comment_validations`, `validation_grid`
3. Click on each table to see the data

### 6.2 Check Test Data
- `apartments` table should have your apartment list
- `comment_validations` should have test comments
- `validation_grid` should have summary statistics

## 🚀 Step 7: Run Your Application

Now your application will use Supabase instead of local JSON:

```bash
cd backend/src
python enhanced_reddit_ai.py --run-main
```

## 🔧 Troubleshooting

### Common Issues:

#### 1. "Supabase not installed"
```bash
pip install supabase
```

#### 2. "Authentication failed"
- Double-check your `SUPABASE_KEY` (use service_role key, not anon key)
- Verify `SUPABASE_URL` format: `https://your-id.supabase.co`

#### 3. "Foreign key constraint violation"
- Make sure apartments are inserted in the `apartments` table first
- Check apartment names match exactly (case-sensitive)

#### 4. "Permission denied"
- Ensure you're using the `service_role` key, not the `anon` key
- Check Row Level Security (RLS) settings in Supabase

### 4.1 Disable RLS (if needed)
If you get permission errors, you can disable Row Level Security:

1. Go to **Authentication** → **Policies** in Supabase
2. Find your tables and click "Disable RLS" (for development only)

## 📊 Benefits of Supabase Storage

✅ **Scalable**: Handle thousands of comments  
✅ **Concurrent**: Multiple users can access simultaneously  
✅ **Reliable**: Automatic backups and replication  
✅ **Queryable**: Use SQL for complex analytics  
✅ **Real-time**: Subscribe to changes via WebSockets  

## 🔄 Migration from JSON

Your existing JSON data in `validation_grid.json` can be migrated:

```python
# Run this script to migrate existing data
from supabase_grid_manager import SupabaseGridManager
import json

grid_manager = SupabaseGridManager()

# Load existing JSON data
with open('/Users/harshshah/Documents/hackgt/backend/output/validation_grid.json', 'r') as f:
    data = json.load(f)

# Migrate comments to Supabase
for comment_id, comment_data in data['comments'].items():
    # Migration logic here
    pass
```

## 🎉 You're All Set!

Your StingerSpaces application now uses Supabase for robust, scalable comment storage! 🚀

---

**Need help?** Check the [Supabase documentation](https://supabase.com/docs) or create an issue in your repository.
