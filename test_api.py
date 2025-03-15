import requests
import json
import time
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL for API
BASE_URL = "http://localhost:8000"

# Test functions
def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    logger.info(f"Health check status: {response.status_code}")
    assert response.status_code == 200, "Health check failed"
    return True

def test_api_stats():
    """Test the API stats endpoint"""
    response = requests.get(f"{BASE_URL}/api/stats")
    logger.info(f"API stats status: {response.status_code}")
    assert response.status_code == 200, "API stats check failed"
    data = response.json()
    assert "gemini" in data, "Gemini stats not found"
    assert "deepseek" in data, "Deepseek stats not found"
    return True

def test_generate_content(provider=None):
    """Test the generate content endpoint"""
    payload = {
        "prompt": "Write a short poem about artificial intelligence.",
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    if provider:
        payload["force_provider"] = provider
        logger.info(f"Testing with forced provider: {provider}")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/generate", json=payload)
    latency = (time.time() - start_time) * 1000  # in milliseconds
    
    logger.info(f"Generate content status: {response.status_code}, latency: {latency:.2f}ms")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Response from provider: {data['provider']}")
        logger.info(f"Cached: {data['cached']}")
        logger.info(f"Content: {data['content'][:50]}...")
        return True
    elif response.status_code == 503:
        logger.warning(f"Service unavailable: {response.json().get('detail')}")
        return False
    else:
        logger.error(f"Unexpected error: {response.text}")
        return False

def test_caching():
    """Test that responses are properly cached"""
    # Send the same request twice
    payload = {
        "prompt": "What is the capital of France?",
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    # First request
    start_time = time.time()
    response1 = requests.post(f"{BASE_URL}/api/generate", json=payload)
    latency1 = (time.time() - start_time) * 1000
    
    if response1.status_code != 200:
        logger.error("First request failed, can't test caching")
        return False
    
    data1 = response1.json()
    logger.info(f"First request - provider: {data1['provider']}, cached: {data1['cached']}, latency: {latency1:.2f}ms")
    
    # Second request (should be cached)
    start_time = time.time()
    response2 = requests.post(f"{BASE_URL}/api/generate", json=payload)
    latency2 = (time.time() - start_time) * 1000
    
    if response2.status_code != 200:
        logger.error("Second request failed")
        return False
    
    data2 = response2.json()
    logger.info(f"Second request - provider: {data2['provider']}, cached: {data2['cached']}, latency: {latency2:.2f}ms")
    
    # Check if second response was cached
    assert data2['cached'] == True, "Response was not cached"
    assert latency2 < latency1, "Cached response should be faster"
    
    return True

def test_rate_limiting():
    """Test rate limiting by making multiple requests quickly"""
    # Get current stats
    stats_response = requests.get(f"{BASE_URL}/api/stats")
    stats = stats_response.json()
    
    # Choose a provider with the lowest current usage
    providers = ["gemini", "deepseek"]
    provider = min(providers, key=lambda p: stats[p]["minute"])
    
    logger.info(f"Testing rate limiting with provider: {provider}")
    limit = stats[provider]["limit_per_minute"]
    current = stats[provider]["minute"]
    
    logger.info(f"Current usage: {current}/{limit}")
    
    # Make requests until we hit the rate limit or reach 5 requests
    max_requests = min(5, limit - current)  # Don't exceed the limit
    success_count = 0
    
    for i in range(max_requests):
        logger.info(f"Making request {i+1}/{max_requests}")
        result = test_generate_content(provider)
        if result:
            success_count += 1
        time.sleep(0.5)  # Small delay between requests
    
    logger.info(f"Successful requests: {success_count}/{max_requests}")
    return success_count > 0

def run_all_tests():
    """Run all tests"""
    logger.info("Starting API tests")
    
    tests = [
        ("Health Check", test_health_check),
        ("API Stats", test_api_stats),
        ("Generate Content", test_generate_content),
        ("Caching", test_caching),
        ("Rate Limiting", test_rate_limiting)
    ]
    
    results = {}
    
    for name, test_func in tests:
        logger.info(f"Running test: {name}")
        try:
            result = test_func()
            results[name] = "PASS" if result else "FAIL"
        except Exception as e:
            logger.error(f"Test {name} raised an exception: {str(e)}")
            results[name] = "ERROR"
    
    # Print summary
    logger.info("\nTest Results:")
    for name, result in results.items():
        logger.info(f"{name}: {result}")

if __name__ == "__main__":
    run_all_tests()