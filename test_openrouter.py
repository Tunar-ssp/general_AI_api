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

def test_openrouter_integration():
    """Test the OpenRouter integration by checking if the API key is configured"""
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key or openrouter_api_key == "your_openrouter_api_key":
        logger.warning("OpenRouter API key not configured or using default value")
        return False
    
    logger.info("OpenRouter API key is configured")
    return True

def test_openrouter_endpoint():
    """Test that the OpenRouter endpoint is properly configured"""
    openrouter_endpoint = os.getenv("OPENROUTER_ENDPOINT")
    if not openrouter_endpoint or "openrouter.ai" not in openrouter_endpoint:
        logger.warning("OpenRouter endpoint not properly configured")
        return False
    
    logger.info(f"OpenRouter endpoint is configured: {openrouter_endpoint}")
    return True

def test_api_integration():
    """Test that the API is properly integrated with OpenRouter"""
    # First check if the OpenRouter client file exists
    import os
    openrouter_client_path = os.path.join("app", "services", "openrouter_client.py")
    if not os.path.exists(openrouter_client_path):
        logger.warning("OpenRouter client file not found")
        return False
    
    logger.info("OpenRouter client file exists")
    return True

def test_openrouter_request():
    """Test making an actual request to the API using OpenRouter as the provider"""
    # Check if the server is running first
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            logger.warning(f"API server not running or health check failed: {health_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to API server: {str(e)}")
        return False
    
    # Make a request to the generate endpoint with OpenRouter as the provider
    payload = {
        "prompt": "Write a one-sentence test response.",
        "temperature": 0.7,
        "max_tokens": 50,
        "force_provider": "openrouter"  # Force using OpenRouter
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=30)
        latency = (time.time() - start_time) * 1000  # in milliseconds
        
        logger.info(f"OpenRouter request status: {response.status_code}, latency: {latency:.2f}ms")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response from provider: {data['provider']}")
            logger.info(f"Content: {data['content'][:50]}...")
            
            # Verify that the response came from OpenRouter
            if "openrouter" in data['provider'].lower():
                logger.info("Successfully received response from OpenRouter")
                return True
            else:
                logger.warning(f"Response came from {data['provider']} instead of OpenRouter")
                return False
        elif response.status_code == 503:
            logger.warning(f"Service unavailable: {response.json().get('detail')}")
            return False
        else:
            logger.error(f"Unexpected error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception during OpenRouter request: {str(e)}")
        return False

def run_openrouter_tests():
    """Run all OpenRouter tests"""
    logger.info("Starting OpenRouter tests")
    
    tests = [
        ("OpenRouter API Key", test_openrouter_integration),
        ("OpenRouter Endpoint", test_openrouter_endpoint),
        ("OpenRouter API Integration", test_api_integration),
        ("OpenRouter Request", test_openrouter_request)
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
    run_openrouter_tests()