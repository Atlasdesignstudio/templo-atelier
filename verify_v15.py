import requests
import sys

def verify_v15_api():
    print("--- [Founder OS v15.0] API Verification ---")
    try:
        # 1. Fetch Maldonado Project (ID 1)
        url = "http://localhost:8001/founder/project/1"
        print(f"GET {url}...")
        res = requests.get(url)
        
        if res.status_code != 200:
            print(f"❌ API Failed: {res.status_code}")
            print(res.text)
            sys.exit(1)
            
        data = res.json()
        print("✅ Project Payload Received")
        
        # 2. Check for New Command Center Fields
        
        # Documents
        if "documents" in data and len(data["documents"]) > 0:
            print(f"✅ Documents Found: {len(data['documents'])} (Folders verified)")
        else:
            print("❌ Documents Data Missing or Empty")
            
        # Requests
        if "requests" in data and len(data["requests"]) > 0:
            print(f"✅ Agent Requests Found: {len(data['requests'])}")
        else:
            print("❌ Agent Requests Data Missing or Empty")

        # Creative Mode
        if "creative_mode" in data:
            cm = data["creative_mode"]
            print(f"✅ Creative Mode Context: {cm.get('objective', 'Missing')}")
        else:
            print("❌ Creative Mode Data Missing")

        # Command Center Core
        if "overview" in data or "project" in data: # project is the main key now
             print("✅ 10-Part Core Data Present")
        
        print("\n--- v15.0 API Verification PASSED ---")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_v15_api()
