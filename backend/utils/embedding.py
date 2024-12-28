import os
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def generate_text_embedding(text):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    response = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document",
        title="Embedding of culprit info",
    )
    return response["embedding"]

def compute_similarity(embedding1, embedding2):
    """
    Compute similarity between two embeddings using Euclidean distance
    """
    distance = sum((q - r) ** 2 for q, r in zip(embedding1, embedding2)) ** 0.5
    max_distance = len(embedding1) ** 0.5
    similarity = 1 - (distance / max_distance)
    return similarity

def calculate_similarity_percentage(query_vector, result_vector):
    # Calculate Euclidean distance manually
    distance = sum((q - r) ** 2 for q, r in zip(query_vector, result_vector)) ** 0.5

    # Estimate a maximum possible distance for normalization
    max_distance = len(query_vector) ** 0.5

    # Convert distance to a similarity percentage
    similarity_percentage = max(0, (1 - distance / max_distance) * 100)
    return round(similarity_percentage, 2)

def find_top_matches(
    collection, description_embedding, num_results=1, num_candidates=100
):
    # Perform a vector search to get the top matches
    results_cursor = collection.aggregate(
        [
            {
                "$vectorSearch": {
                    "path": "culprit_embedding",
                    "index": "culpritIndex2",
                    "queryVector": description_embedding,
                    "numResults": num_results,
                    "numCandidates": num_candidates,
                    "numDimensions": 768,
                    "similarity": "euclidean",
                    "type": "knn",
                    "limit": num_results,
                },
            },
            {
                "$project": {
                    "culprit": 1,
                    "culprit_embedding": 1,
                    "_id": 1,
                }
            },
        ]
    )

    # Convert the cursor to a list to access the results
    results = list(results_cursor)
    return results