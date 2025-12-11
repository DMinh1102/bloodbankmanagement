"""
Simple test script to verify rate limiting is working
Run this while the Django server is running
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000/"

def test_homepage_rate_limit():
    """Test homepage rate limit (20/min)"""
    print("\n" + "="*60)
    print("Testing Homepage Rate Limit (20 requests/minute)")
    print("="*60)
    
    success_count = 0
    rate_limited = False
    start_time = time.time()
    
    for i in range(25):
        try:
            req_start = time.time()
            response = requests.get(f"{BASE_URL}", timeout=10)
            req_duration = time.time() - req_start
            
            if response.status_code == 200:
                success_count += 1
                elapsed = time.time() - start_time
                print(f"✓ Request {i+1}: Success (200) - took {req_duration:.2f}s - total elapsed: {elapsed:.1f}s")
            elif response.status_code == 429:
                print(f"\n🚫 Request {i+1}: RATE LIMITED (429)")
                print(f"   Rate limit triggered after {success_count} successful requests")
                rate_limited = True
                break
            else:
                print(f"? Request {i+1}: Unexpected status {response.status_code}")
            
            # No sleep - send requests as fast as possible
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Request {i+1}: Error - {type(e).__name__}")
            break
    
    total_time = time.time() - start_time
    if rate_limited:
        print(f"\n✅ PASS: Rate limiting is working correctly!")
        print(f"   Allowed {success_count} requests before blocking")
    else:
        print(f"\n⚠️  Rate limit not triggered")
        print(f"   Total time: {total_time:.1f} seconds for {success_count} requests")
        print(f"   Average: {total_time/success_count:.2f}s per request")
        if total_time > 60:
            print(f"   ⚠️  Requests took longer than 60s - rate limit window expired!")

def test_signup_rate_limit():
    """Test signup rate limit (3/min)"""
    print("\n" + "="*60)
    print("Testing Signup Rate Limit (3 requests/minute)")
    print("="*60)
    
    success_count = 0
    rate_limited = False
    
    for i in range(6):
        try:
            response = requests.get(f"{BASE_URL}donor/donorsignup", timeout=10)
            
            if response.status_code == 200:
                success_count += 1
                print(f"✓ Request {i+1}: Success (200)")
            elif response.status_code == 429:
                print(f"\n🚫 Request {i+1}: RATE LIMITED (429)")
                print(f"   Rate limit triggered after {success_count} successful requests")
                rate_limited = True
                break
            else:
                print(f"? Request {i+1}: Unexpected status {response.status_code}")
            
            time.sleep(0.05)
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Request {i+1}: Error - {type(e).__name__}")
            break
    
    if rate_limited:
        print(f"\n✅ PASS: Signup rate limiting is working correctly!")
        print(f"   Allowed {success_count} requests before blocking")
    else:
        print(f"\n⚠️  WARNING: Rate limit not triggered after 6 requests")

def main():
    print("\n" + "="*60)
    print("🩸 BLOOD BANK RATE LIMITING TEST")
    print("="*60)
    
    # Check if server is running
    print("\nChecking if server is running...")
    try:
        response = requests.get(BASE_URL, timeout=10)  # Increased timeout
        print(f"✓ Server is running at {BASE_URL}")
        print(f"  Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Server is NOT running at {BASE_URL}")
        print(f"  Error: {type(e).__name__}: {e}")
        print("\nPlease start the server with:")
        print("  python manage.py runserver")
        print("\nTroubleshooting:")
        print("  - Make sure server is running in another terminal")
        print("  - Check if port 8000 is available")
        print("  - Try accessing http://127.0.0.1:8000/ in your browser")
        return
    
    # Run tests
    test_homepage_rate_limit()
    
    print("\n⏳ Waiting 5 seconds before next test...")
    time.sleep(5)
    
    test_signup_rate_limit()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("\nRate limits configured:")
    print("  • Homepage: 20 requests/minute")
    print("  • Signup pages: 3 requests/minute")
    print("  • Donor/Patient actions: 5 requests/minute")
    print("  • Admin actions: 30 requests/minute")
    print("  • Critical operations (approve/reject): 3 requests/minute")
    print("\nTo manually test:")
    print("  1. Open browser and rapidly refresh any page")
    print("  2. After exceeding limit, you'll see a custom error page")
    print("  3. Wait 1 minute and try again - it should work")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
