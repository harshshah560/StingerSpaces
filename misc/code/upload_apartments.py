import os
import json
import base64
import uuid
from supabase import create_client, Client

# --- CONFIGURATION ---
# Set these as environment variables for security.
# Find them in your Supabase project settings under "API".
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # IMPORTANT: Use the service_role key

# --- INITIALIZATION ---
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("You must set the SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE_NAME = 'apartments'
BUCKET_NAME = 'apartment-images'

def upload_processed_data():
    """
    Reads JSON, pre-processes Base64 images, uploads them to Supabase Storage,
    and inserts the clean record into the database table.
    """
    # 1. Load the data from the JSON file
    try:
        with open('/Users/harshshah/Documents/hackgt/misc/data/apartment_data.json', 'r') as f:
            apartments = json.load(f)
        print(f"✅ Loaded {len(apartments)} apartments from apartment_data.json.")
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return

    # 2. Loop through each apartment to process and upload
    for apartment in apartments:
        print(f"Processing '{apartment['name']}'...")
        
        # Pop the base64 string from the dictionary. It won't be inserted into the table.
        base64_string = apartment.pop('image_base64', None)

        if not base64_string:
            print("  - No image data found. Setting image_url to null.")
            apartment['image_url'] = None
        else:
            try:
                # --- THIS IS THE PRE-PROCESSING ---
                # A. Decode the Base64 string into raw image bytes.
                image_bytes = base64.b64decode(base64_string)
                
                # B. Create a unique filename to prevent overwriting files.
                file_name = f"{uuid.uuid4()}.webp"

                # C. Upload the image bytes to your Supabase Storage bucket.
                supabase.storage.from_(BUCKET_NAME).upload(
                    file_name, 
                    image_bytes, 
                    {"content-type": "image/webp"}
                )

                # D. Get the public URL for the newly uploaded image.
                public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
                apartment['image_url'] = public_url
                print(f"  - ✅ Image uploaded successfully.")

            except Exception as e:
                print(f"  - ❌ Error uploading image: {e}")
                apartment['image_url'] = None

        # 3. Insert the final, clean record into the database table
        try:
            supabase.table(TABLE_NAME).insert(apartment).execute()
        except Exception as e:
             # This will often happen if the URL is not unique (if you run the script twice)
             print(f"  - ❌ Error inserting record into database: {e}")

    print("\n🎉 Process complete! Check your Supabase table and storage bucket.")

if __name__ == "__main__":
    upload_processed_data()