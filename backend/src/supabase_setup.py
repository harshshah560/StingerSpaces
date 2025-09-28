#!/usr/bin/env python3
"""
Supabase Setup Helper Script
This script helps you configure and test your Supabase connection for StingerSpaces
"""

import os
import sys
from typing import Optional
import json

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import supabase
        print("✅ Supabase library is installed")
        return True
    except ImportError:
        print("❌ Supabase library not found")
        print("📦 Installing supabase...")
        os.system("pip install supabase python-dotenv")
        return True

def get_credentials_from_user():
    """Interactively get Supabase credentials from user"""
    print("\n🔑 Supabase Credentials Setup")
    print("=" * 40)
    print("You can find these in your Supabase dashboard:")
    print("Go to Settings → API")
    print()
    
    url = input("Enter your Supabase URL (https://your-project.supabase.co): ").strip()
    if not url.startswith('https://'):
        url = 'https://' + url
    
    print("\n⚠️  Use the 'service_role' key (not 'anon' key) for full database access")
    key = input("Enter your Supabase service_role key: ").strip()
    
    return url, key

def create_env_file(url: str, key: str):
    """Create or update .env file with Supabase credentials"""
    env_path = '/Users/harshshah/Documents/hackgt/.env'
    
    # Read existing .env if it exists
    env_content = ""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
    
    # Update or add Supabase credentials
    lines = env_content.split('\n')
    updated_lines = []
    supabase_url_found = False
    supabase_key_found = False
    
    for line in lines:
        if line.startswith('SUPABASE_URL='):
            updated_lines.append(f'SUPABASE_URL={url}')
            supabase_url_found = True
        elif line.startswith('SUPABASE_KEY='):
            updated_lines.append(f'SUPABASE_KEY={key}')
            supabase_key_found = True
        else:
            updated_lines.append(line)
    
    # Add new entries if not found
    if not supabase_url_found:
        updated_lines.append(f'SUPABASE_URL={url}')
    if not supabase_key_found:
        updated_lines.append(f'SUPABASE_KEY={key}')
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"✅ Updated .env file at {env_path}")

def test_connection(url: str, key: str):
    """Test the Supabase connection"""
    try:
        from supabase import create_client
        
        print("\n🧪 Testing Supabase connection...")
        client = create_client(url, key)
        
        # Try to query apartments table
        result = client.table('apartments').select('*').limit(1).execute()
        print("✅ Connection successful!")
        print(f"📊 Found {len(result.data)} records in apartments table")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your URL format: https://your-project.supabase.co")
        print("2. Make sure you're using the service_role key, not anon key")
        print("3. Verify tables are created (run SQL script in Supabase dashboard)")
        return False

def create_tables_sql():
    """Display SQL for creating tables"""
    sql = """
-- Copy and paste this into Supabase SQL Editor:

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

-- Insert initial apartment data
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
"""
    return sql

def main():
    """Main setup wizard"""
    print("🚀 StingerSpaces Supabase Setup Wizard")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check if credentials already exist
    existing_url = os.getenv('SUPABASE_URL')
    existing_key = os.getenv('SUPABASE_KEY')
    
    if existing_url and existing_key:
        print(f"\n🔍 Found existing credentials:")
        print(f"URL: {existing_url}")
        print(f"Key: {existing_key[:20]}...")
        
        use_existing = input("\nUse existing credentials? (y/n): ").lower().strip()
        if use_existing == 'y':
            url, key = existing_url, existing_key
        else:
            url, key = get_credentials_from_user()
    else:
        url, key = get_credentials_from_user()
    
    # Save credentials
    create_env_file(url, key)
    
    # Set environment variables for current session
    os.environ['SUPABASE_URL'] = url
    os.environ['SUPABASE_KEY'] = key
    
    # Test connection
    if test_connection(url, key):
        print("\n🎉 Setup complete! Your application will now use Supabase.")
        
        # Test the grid manager
        try:
            sys.path.append('/Users/harshshah/Documents/hackgt/backend/src')
            from supabase_grid_manager import SupabaseGridManager
            
            grid_manager = SupabaseGridManager()
            if not grid_manager.use_local_storage:
                print("✅ Grid manager successfully connected to Supabase")
            else:
                print("⚠️  Grid manager still using local storage - check credentials")
                
        except Exception as e:
            print(f"⚠️  Could not test grid manager: {e}")
    else:
        print("\n❌ Setup incomplete. Please check the troubleshooting tips above.")
        print("\n📋 SQL Script for Creating Tables:")
        print("=" * 40)
        print(create_tables_sql())
        print("\n1. Copy the SQL above")
        print("2. Go to your Supabase dashboard → SQL Editor")
        print("3. Paste and run the SQL")
        print("4. Run this setup script again")

if __name__ == "__main__":
    main()
