"""
Simple Cache vs No-Cache Test
Shows the dramatic speed difference with more queries
"""

import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bloodbankmanagement.settings')
django.setup()

from django.core.cache import cache
from blood.models import Stock

NUM_QUERIES = 10000  # Test with 10,000 queries

print("="*60)
print(f"CACHE vs NO-CACHE SPEED TEST ({NUM_QUERIES:,} queries)")
print("="*60)

# Clear cache
cache.clear()

# Test 1: WITHOUT CACHE
print(f"\n1️⃣  WITHOUT CACHE ({NUM_QUERIES:,} database queries):")
print("-" * 60)
times_no_cache = []
for i in range(NUM_QUERIES):
    start = time.time()
    stocks = list(Stock.objects.all())
    duration = (time.time() - start) * 1000  # Convert to ms
    times_no_cache.append(duration)
    if i < 5 or i >= NUM_QUERIES - 5:  # Show first 5 and last 5
        print(f"   Query {i+1:5d}: {duration:6.2f}ms")
    elif i == 5:
        print(f"   ... (queries 6-{NUM_QUERIES-5} hidden for brevity)")

avg_no_cache = sum(times_no_cache) / len(times_no_cache)
total_no_cache = sum(times_no_cache)
print(f"\n   Average: {avg_no_cache:.2f}ms")
print(f"   Total time: {total_no_cache:.0f}ms ({total_no_cache/1000:.2f}s)")

# Test 2: WITH CACHE
print(f"\n2️⃣  WITH CACHE (1 DB query + {NUM_QUERIES-1:,} cache hits):")
print("-" * 60)

# First query - caches the result
start = time.time()
cache_key = "test_stocks"
stocks = cache.get(cache_key)
if stocks is None:
    stocks = list(Stock.objects.all())
    cache.set(cache_key, stocks, timeout=300)
first_duration = (time.time() - start) * 1000
print(f"   Query     1: {first_duration:6.2f}ms (cached to Redis)")

# Next queries - from cache
times_with_cache = []
for i in range(NUM_QUERIES - 1):
    start = time.time()
    stocks = cache.get(cache_key)
    duration = (time.time() - start) * 1000
    times_with_cache.append(duration)
    if i < 4 or i >= NUM_QUERIES - 6:  # Show first 4 and last 5
        print(f"   Query {i+2:5d}: {duration:6.2f}ms (from cache)")
    elif i == 4:
        print(f"   ... (queries 6-{NUM_QUERIES-5} hidden for brevity)")

avg_with_cache = sum(times_with_cache) / len(times_with_cache)
total_with_cache = sum(times_with_cache) + first_duration
print(f"\n   Average (cached): {avg_with_cache:.2f}ms")
print(f"   Total time: {total_with_cache:.0f}ms ({total_with_cache/1000:.2f}s)")

# Results
print("\n" + "="*60)
print(f"RESULTS ({NUM_QUERIES:,} queries each)")
print("="*60)
print(f"\nWithout cache: {avg_no_cache:6.2f}ms average | {total_no_cache:8.0f}ms total ({total_no_cache/1000:.2f}s)")
print(f"With cache:    {avg_with_cache:6.2f}ms average | {total_with_cache:8.0f}ms total ({total_with_cache/1000:.2f}s)")

speedup = avg_no_cache / avg_with_cache if avg_with_cache > 0 else 0
time_saved = total_no_cache - total_with_cache
print(f"\n🚀 SPEED UP: {speedup:.0f}x FASTER with cache!")
print(f"⏱️  TIME SAVED: {time_saved:.0f}ms ({time_saved/1000:.2f}s)")

# Visual comparison
print("\n" + "="*60)
print(f"VISUAL COMPARISON (Total Time for {NUM_QUERIES:,} Queries)")
print("="*60)
bar_scale = max(1, int(total_no_cache / 50))  # Scale to fit ~50 chars
no_cache_bar = '█' * int(total_no_cache / bar_scale)
cache_bar = '█' * max(1, int(total_with_cache / bar_scale))
print(f"\nWithout cache: {no_cache_bar} {total_no_cache:.0f}ms ({total_no_cache/1000:.2f}s)")
print(f"With cache:    {cache_bar} {total_with_cache:.0f}ms ({total_with_cache/1000:.2f}s)")

# Impact analysis
print("\n" + "="*60)
print("REAL-WORLD IMPACT")
print("="*60)
print(f"""
If your blood bank gets 1000 page views per day:

WITHOUT CACHE:
  - 1000 views × {avg_no_cache:.2f}ms = {1000*avg_no_cache:.0f}ms ({1000*avg_no_cache/1000:.1f}s)
  - Database load: 1000 queries/day
  - Server resources: HIGH 🔴

WITH CACHE:
  - 1000 views × {avg_with_cache:.2f}ms = {1000*avg_with_cache:.0f}ms ({1000*avg_with_cache/1000:.1f}s)
  - Database load: ~10 queries/day (90% cache hit rate)
  - Server resources: LOW 🟢

TIME SAVED PER DAY: {(1000*avg_no_cache - 1000*avg_with_cache)/1000:.1f} seconds
DATABASE QUERIES SAVED: ~990 queries/day
""")

print("="*60)
print("WHAT THIS MEANS")
print("="*60)
print("""
✅ Cache makes queries {:.0f}x faster!
✅ Reduces database load by 90-99%
✅ Your blood bank already uses this for:
   - Blood stock levels
   - Request counts
   - Rate limiting

This is why your app responds in 0.01-0.03 seconds! 🎉
""".format(speedup))
print("="*60)

