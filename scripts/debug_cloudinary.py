import os
import cloudinary
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("CLOUDINARY_URL")
print(f"DEBUG: Found URL length: {len(url) if url else 0}")
if url:
    # Print masked to verify structure
    # cloudinary://<key>:<secret>@<cloud_name>
    try:
        parts = url.split("@")
        creds = parts[0].split("://")[1]
        key = creds.split(":")[0]
        print(f"DEBUG: Key starts with: {key[:4]}...")
        print(f"DEBUG: Cloud name: {parts[1]}")
        
        # Manually configure to verify library behavior
        cloudinary.config(
            cloud_name=parts[1],
            api_key=key,
            api_secret=creds.split(":")[1]
        )
        print("DEBUG: Manually configured cloudinary object.")
        print(f"DEBUG: Config check: {cloudinary.config().cloud_name}")
        
    except Exception as e:
        print(f"DEBUG: Parse error: {e}")
else:
    print("DEBUG: No CLOUDINARY_URL in env.")
