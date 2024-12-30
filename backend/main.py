import logging
import os
from typing import Optional
# In main.py
from fastapi import Form
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.db import get_database
from backend.logger import CustomFormatter
from backend.schema import FileContent, PostInfo
from backend.utils.common import (
    load_image_from_url_or_file,
    read_files_from_directory,
    serialize_object_id,
)
from backend.utils.embedding import find_top_matches, generate_text_embedding
from backend.utils.regex_ptr import extract_info
from backend.utils.steganography import (
    decode_text_from_image,
    encode_text_in_image
)
from backend.utils.text_llm import (
    create_poem,
    decompose_user_text,
    expand_user_text_using_gemini,
    expand_user_text_using_gemma,
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)

# Initialize FastAPI app
app = FastAPI(title="Steganography API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
db = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    global db
    try:
        db = get_database()
        logger.info("Successfully initialized database connection")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise



@app.post("/encode")
async def encode_text_in_image_endpoint(
    text: str = Form(...), 
    file: UploadFile = File(...),
    output_filename: str = "encoded_image.png"
):
    """
    Encode text into an uploaded image and save locally.
    Args:
        text: Text to encode (now received from form data)
        file: Uploaded image file
        output_filename: Name for the output file
    """
    try:
        image = load_image_from_url_or_file(file=file)
        encoded_image = encode_text_in_image(image, text)
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        output_path = os.path.join("output", output_filename)
        encoded_image.save(output_path, format="PNG")
        
        return StreamingResponse(
            open(output_path, "rb"),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
    except Exception as e:
        logger.error(f"Error encoding text in image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decode")
async def decode_text_from_image_endpoint(file: UploadFile = File(...)):
    """
    Decode text from an uploaded image.
    Args:
        file: Uploaded image file containing hidden text
    """
    try:
        image = load_image_from_url_or_file(file=file)
        decoded_text = decode_text_from_image(image)
        return {"decoded_text": decoded_text}
    except Exception as e:
        logger.error(f"Error decoding text from image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Text processing endpoints
@app.post("/text-generation")
async def get_post_and_expand_its_content(post_info: PostInfo):
    """Generate expanded content from post information using multiple LLMs."""
    try:
        concatenated_text = (
            f"Name: {post_info.name}\n"
            f"Phone: {post_info.phone}\n"
            f"Location: {post_info.location}\n"
            f"Duration of Abuse: {post_info.duration_of_abuse}\n"
            f"Frequency of Incidents: {post_info.frequency_of_incidents}\n"
            f"Preferred Contact Method: {post_info.preferred_contact_method}\n"
            f"Current Situation: {post_info.current_situation}\n"
            f"Culprit Description: {post_info.culprit_description}\n"
            f"Custom Text: {post_info.custom_text}\n"
        )
        gemini_response = await expand_user_text_using_gemini(concatenated_text)
        gemma_response = await expand_user_text_using_gemma(concatenated_text)
        return {"gemini_response": gemini_response, "gemma_response": gemma_response}
    except Exception as e:
        logger.error(f"Error in text generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text-decomposition")
async def decompose_text_content(data: dict):
    """Decompose and extract information from user text."""
    try:
        text = data.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Text field is required")
        decomposed_text = decompose_user_text(text)
        return {"extracted_data": extract_info(decomposed_text)}
    except Exception as e:
        logger.error(f"Error in text decomposition: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/poem-generation")
async def create_poem_endpoint(text: str):
    """Generate an inspirational poem based on input text."""
    try:
        poem = create_poem(text)
        return {"poem": poem}
    except Exception as e:
        logger.error(f"Error generating poem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Database endpoints
@app.get("/get-admin-posts")
async def get_all_posts():
    """Retrieve all posts from the database."""
    try:
        posts = [serialize_object_id(post) for post in db["admin"].find()]
        return JSONResponse(content=posts)
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/find-match")
async def find_top_matching_posts(info: str, collection: str):
    """Find top matches based on embedding similarity."""
    try:
        description_vector = generate_text_embedding(info)
        top_matches = find_top_matches(db[collection], description_vector)
        return [serialize_object_id(match) for match in top_matches]
    except Exception as e:
        logger.error(f"Error finding matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)