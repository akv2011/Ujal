import os
from dotenv import load_dotenv
from pymongo import MongoClient
from backend.db import insert_data_into_db, find_similar_culprits

load_dotenv()

# Test data
test_data = {
    "name": "Test User",
    "location": "Test City",
    "contact_info": "test@email.com",
    "severity": "Medium",
    "culprit": "A person wearing a black jacket and blue jeans",
    "relationship_to_culprit": "Stranger",
    "other_info": "Test incident report"
}

def main():
    # Connect to database
    client = MongoClient(os.getenv("MONGO_ENDPOINT"))
    db = client["SheBuilds"]
    collection = db["complains2"]
    
    try:
        # Insert test data
        print("Inserting test data...")
        result_id = insert_data_into_db(
            test_data["name"],
            test_data["location"],
            test_data["contact_info"],
            test_data["severity"],
            test_data["culprit"],
            test_data["relationship_to_culprit"],
            test_data["other_info"]
        )
        
        if result_id:
            print(f"Successfully inserted document with ID: {result_id}")
            
            # Test similarity search
            print("\nTesting similarity search...")
            test_query = "Person in black jacket"
            similar_culprits = find_similar_culprits(test_query)
            print("\nSimilar culprits found:")
            for doc in similar_culprits:
                print(f"Culprit: {doc['culprit']}")
                print(f"Similarity: {doc['similarity_score']:.2f}")
                print("---")
            
            # Clean up - remove test data
            print("\nCleaning up - removing test data...")
            delete_result = collection.delete_one({"_id": result_id})
            if delete_result.deleted_count == 1:
                print("Test data successfully removed")
            else:
                print("Error: Could not remove test data")
                
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()
        print("\nTest completed and database connection closed")

if __name__ == "__main__":
    main()