import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

def test_upload():
    load_dotenv()
    url = os.getenv("CLOUDINARY_URL")
    if not url:
        print("FAIL: CLOUDINARY_URL not found in .env")
        return

    try:
        # Manual Configuration to ensure reliability (same logic as cloudinary_uploader.py)
        clean_url = url.replace("cloudinary://", "")
        creds, cloud_name = clean_url.split("@")
        api_key, api_secret = creds.split(":")
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        print(f"Configured Cloudinary: {cloud_name}")
        
        # Test upload with a small public image URL
        test_image = "https://res.cloudinary.com/demo/image/upload/sample.jpg"
        print(f"Attempting to upload: {test_image}")
        
        res = cloudinary.uploader.upload(
            test_image,
            public_id="test_connection_check",
            overwrite=True,
            resource_type="image"
        )
        
        secure_url = res.get('secure_url')
        if secure_url:
            print(f"SUCCESS: Uploaded to {secure_url}")
        else:
            print(f"FAIL: No secure_url in response: {res}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_upload()
