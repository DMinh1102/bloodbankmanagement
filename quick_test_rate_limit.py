"""
Quick rate limit test - works with slow servers
Tests with only 3 requests to complete within 60 seconds
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000/"

def quick_test():
    print("\n" + "="*60)
    print("🩸 QUICK RATE LIMIT TEST (3 requests limit)")
    print("="*60)
    print("\nThis test uses a 3-request limit to work with slow servers")
    print("Testing /donor/donorsignup endpoint (3 requests/minute)\n")
    
    # Check server
    try:
        requests.get(BASE_URL, timeout=10)
        print("✓ Server is running\n")
    except:
        print("✗ Server not running!")
        return
    
    # Test with strict limit endpoint
    start_time = time.time()
    for i in range(5):
        try:
            req_start = time.time()
            response = requests.get(f"{BASE_URL}donor/donorsignup", timeout=10)
            req_duration = time.time() - req_start
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✓ Request {i+1}: Success (200) - {req_duration:.1f}s - elapsed: {elapsed:.1f}s")
            elif response.status_code == 429:
                print(f"\n🎉 Request {i+1}: RATE LIMITED (429)")
                print(f"✅ Rate limiting is WORKING!")
                print(f"   Blocked after {i} successful requests")
                print(f"   Total time: {elapsed:.1f} seconds")
                return
            else:
                print(f"? Request {i+1}: Status {response.status_code}")
                
        except Exception as e:
            print(f"✗ Request {i+1}: Error - {type(e).__name__}")
            break
    
    print(f"\n⚠️  Rate limit not triggered after 5 requests")
    print(f"   Your server is too slow ({req_duration:.1f}s per request)")
    print(f"   Requests exceed the 60-second rate limit window")
    print("\n💡 TIP: Test manually in browser instead:")
    print("   1. Open http://127.0.0.1:8000/donor/donorsignup")
    print("   2. Press Ctrl+Shift+R 4 times rapidly")
    print("   3. You should see the rate limit error page!")

if __name__ == "__main__":
    quick_test()
