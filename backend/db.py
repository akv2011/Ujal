import os
import pickle
import logging  
from bson import Binary
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

from backend.utils.embedding import generate_text_embedding, compute_similarity
from backend.logger import CustomFormatter

load_dotenv()
print("MONGO_ENDPOINT:", os.getenv("MONGO_ENDPOINT"))

# Initialize db_client as None globally to cache the connection
db_client = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)

def get_database():
    """
    Connect to the MongoDB database. Caches the connection so that it is reused
    across multiple calls, improving performance by avoiding repeated handshakes.
    """
    global db_client
    if db_client is None:
        try:
            # Create a single MongoClient instance
            db_client = MongoClient(os.getenv("MONGO_ENDPOINT"))
            logger.info("Connected to the database")    
        except Exception as e:
            print("Error connecting to the database:", e)
            return None
    return db_client["SheBuilds"]

def insert_data_into_db(
    name, location, contact_info, severity, culprit, relationship_to_culprit, other_info
):
    """
    Inserts a document into the 'posts' collection of the MongoDB database.
    Reuses the cached database connection.
    """
    db = get_database()
    if db is None:
        print("Database connection is not available.")
        return None

    collection = db["complains2"]
    document = {
        "name": name,
        "location": location,
        "contact_info": contact_info,
        "severity": severity,
        "culprit": culprit,
        "relationship_to_culprit": relationship_to_culprit,
        "other_info": other_info,
        "status": "Pending",
    }
    
    # Generate embedding for culprit description
    culprit_embedding = generate_text_embedding(culprit)
    if culprit_embedding:
        document["culprit_embedding"] = culprit_embedding
    
    try:
        # Insert the document into the collection
        result = collection.insert_one(document)
        logger.info(f"Inserted document with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error inserting data: {e}")
        return None

def find_similar_culprits(query_text, threshold=0.7):
    """
    Find similar culprit descriptions using embedding similarity
    """
    db = get_database()
    if db is None:
        return []

    collection = db["complains2"]
    query_embedding = generate_text_embedding(query_text)
    
    if not query_embedding:
        return []

    # Find documents and compute similarities
    similar_documents = []
    for doc in collection.find({"culprit_embedding": {"$exists": True}}):
        similarity = compute_similarity(query_embedding, doc["culprit_embedding"])
        if similarity >= threshold:
            doc["similarity_score"] = similarity
            similar_documents.append(doc)

    # Sort by similarity score
    similar_documents.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar_documents

def upload_embeddings_to_mongo(file_contents):
    """
    Upload document embeddings to MongoDB
    """
    db = get_database()
    collection = db["doc_embedding"]
    
    for filename, content in file_contents:
        # Generate embeddings for the document content
        embedding = generate_text_embedding(content)
        
        if embedding:
            # Prepare the document to insert into MongoDB
            doc = {
                "filename": filename,
                "embedding": Binary(pickle.dumps(embedding)),
                "content": content[:500],  # Store first 500 chars for preview
            }

            try:
                # Insert the document
                collection.insert_one(doc)
                logger.info(f"Uploaded {filename} to MongoDB")
            except Exception as e:
                logger.error(f"Error uploading {filename}: {e}")

def search_similar_documents(query_text, threshold=0.7):
    """
    Search for similar documents using embedding similarity
    """
    db = get_database()
    if db is None:
        return []

    collection = db["doc_embedding"]
    query_embedding = generate_text_embedding(query_text)
    
    if not query_embedding:
        return []

    similar_docs = []
    for doc in collection.find():
        stored_embedding = pickle.loads(doc["embedding"])
        similarity = compute_similarity(query_embedding, stored_embedding)
        if similarity >= threshold:
            doc["similarity_score"] = similarity
            similar_docs.append(doc)

    similar_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar_docs

# Example usage
if __name__ == "__main__":
    # Test similarity search
    test_query = "A tall person wearing dark clothes"
    similar_culprits = find_similar_culprits(test_query)
    for doc in similar_culprits:
        print(f"Culprit: {doc['culprit']}")
        print(f"Similarity: {doc['similarity_score']:.2f}")
        print("---")