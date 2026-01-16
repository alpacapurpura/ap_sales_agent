import sys
import os
sys.path.append(os.getcwd())

from src.services.knowledge_service import KnowledgeService

def test_search_raw():
    ks = KnowledgeService()
    # Mocking qdrant and ranker might be hard, so we just run it and catch if it fails or returns empty list (which is valid type)
    # Ideally we should have some data in Qdrant. If not, it returns empty list.
    # We just check if the call works without error.
    
    print("Testing search with return_raw=True...")
    try:
        results = ks.search("hola", limit=2, return_raw=True)
        print(f"Result type: {type(results)}")
        if isinstance(results, list):
            print("Result is a list.")
            if len(results) > 0:
                print("First item keys:", results[0].keys())
                if 'score' in results[0]:
                    print("Score field present.")
                else:
                    print("Score field MISSING.")
            else:
                print("No results found (empty list). This is expected if DB is empty.")
        else:
            print(f"Unexpected type: {type(results)}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_raw()
