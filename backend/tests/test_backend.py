import os
import sys
import logging
from pathlib import Path
import pytest
import requests
from PIL import Image
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from backend.utils.steganography import encode_text_in_image, decode_text_from_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create test client
client = TestClient(app)

# Define a single test image path
test_image_path = Path("/home/harisudhan/Downloads/OIP.jpeg")  # You can change the extension if needed

def create_test_image(filepath):
    """Creates a simple test image."""
    img = Image.new('RGB', (100, 100), color='red')
    img.save(filepath)
    return filepath

def test_encode_endpoint():
    """Test the steganography encode endpoint."""
    # Create a test image in a temporary directory
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        img_path = Path(tmp.name)
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path)

    try:
        # Test data
        test_text = "Hello, this is a test message!"

        # Prepare the file upload with explicit form data
        with open(img_path, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            data = {"text": test_text}
            response = client.post(
                "/encode",
                files=files,
                data=data
            )

        assert response.status_code == 200, f"Failed with status {response.status_code}: {response.text}"
        
    finally:
        # Cleanup
        if img_path.exists():
            img_path.unlink()

def test_decode_endpoint():
    """Test the steganography decode endpoint."""
    # Create and encode a test image
    original_img_path = create_test_image(test_image_path)
    img = Image.open(original_img_path)
    test_text = "Secret test message"
    encoded_img = encode_text_in_image(img, test_text)

    encoded_image_path = Path("test_encoded_image.png") # Keep a separate path for the encoded image
    encoded_img.save(encoded_image_path)

    try:
        # Test decoding
        with open(encoded_image_path, "rb") as f:
            files = {"file": (encoded_image_path.name, f, f"image/{encoded_image_path.suffix[1:].lower()}")}
            response = client.post("/decode", files=files)

        assert response.status_code == 200
        assert "decoded_text" in response.json()
        assert test_text in response.json()["decoded_text"]
        logger.info("Decode endpoint test passed")

    finally:
        # Cleanup
        if encoded_image_path.exists():
            encoded_image_path.unlink()
        if original_img_path.exists():
            original_img_path.unlink() # Ensure original test image is also cleaned up

def test_text_generation():
    """Test the text generation endpoint."""
    test_data = {
        "name": "Test User",
        "phone": "1234567890",
        "location": {"lat": 40.7128, "lng": -74.0060},
        "duration_of_abuse": "2 months",
        "frequency_of_incidents": "weekly",
        "preferred_contact_method": ["phone", "email"],
        "current_situation": "Test situation",
        "culprit_description": "Test description",
        "custom_text": "Additional test information"
    }

    response = client.post("/text-generation", json=test_data)
    assert response.status_code == 200
    assert "gemini_response" in response.json()
    assert "gemma_response" in response.json()
    logger.info("Text generation endpoint test passed")

def test_poem_generation():
    """Test the poem generation endpoint."""
    test_text = "Hope and strength"
    response = client.get(f"/poem-generation?text={test_text}")
    assert response.status_code == 200
    assert "poem" in response.json()
    logger.info("Poem generation endpoint test passed")
    
if __name__ == "__main__":
    logger.info("Starting backend tests...")
    
    # Run all tests
    test_functions = [
        test_encode_endpoint,
        test_decode_endpoint,
        test_text_generation,
        test_poem_generation
    ]
    
    for test in test_functions:
        try:
            test()
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {e}")
        else:
            logger.info(f"Test {test.__name__} completed successfully")
    
    logger.info("All tests completed")