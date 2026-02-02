"""
Example of how to use GenVR API directly
This shows the 3-step workflow: generate -> poll status -> get response
"""

import requests
import time

# Configuration
API_KEY = 'YOUR_API_KEY'
UID = 'YOUR_USER_ID'
BASE_URL = 'https://api.genvrresearch.com'

def generate_with_model():
    """
    Example: Generate image with background change
    Demonstrates the 3-step GenVR API workflow
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    
    # Step 1: Generate - Submit the task
    print("Step 1: Submitting generation task...")
    generate_response = requests.post(
        f'{BASE_URL}/v2/generate',
        json={
            'uid': UID,
            'category': 'imgedit',
            'subcategory': 'background_change',
            # Required parameters
            'image_url': "https://example.com/your-image.jpg",
            'prompt': "a beautiful sunset beach",
            # Optional parameters (uncomment to use)
            # 'output_format': "jpeg",
            # 'seed': 1,
        },
        headers=headers,
        timeout=120  # Increased timeout for slow models
    )
    
    generate_data = generate_response.json()
    if not generate_data.get('success'):
        raise Exception(f"Generate failed: {generate_data.get('message')}")
    
    task_id = generate_data['data']['id']
    print(f"Task submitted! ID: {task_id}")
    
    # Step 2: Poll for status
    print("Step 2: Polling for status...")
    poll_count = 0
    while True:
        status_response = requests.post(
            f'{BASE_URL}/v2/status',
            json={
                'id': task_id,
                'uid': UID,
                'category': 'imgedit',
                'subcategory': 'background_change'
            },
            headers=headers
        )
        
        status_data = status_response.json()
        if not status_data.get('success'):
            raise Exception(f"Status check failed: {status_data.get('message')}")
        
        status = status_data['data']['status']
        print(f"Status: {status} ({poll_count}s elapsed)")
        
        if status == 'completed':
            # Step 3: Get final response
            print("Step 3: Retrieving final result...")
            result_response = requests.post(
                f'{BASE_URL}/v2/response',
                json={
                    'id': task_id,
                    'uid': UID,
                    'category': 'imgedit',
                    'subcategory': 'background_change'
                },
                headers=headers,
                timeout=60  # Increased timeout for large responses
            )
            
            result_data = result_response.json()
            if not result_data.get('success'):
                raise Exception(f"Result fetch failed: {result_data.get('message')}")
            
            return result_data['data']['output']
        
        if status == 'failed':
            error = status_data['data'].get('error', 'Unknown error')
            raise Exception(f"Task failed: {error}")
        
        # Still processing, wait and retry
        time.sleep(1)
        poll_count += 1


# Usage example
if __name__ == "__main__":
    try:
        print("GenVR API Example - Background Change")
        print("=" * 50)
        
        output = generate_with_model()
        
        print("\nSuccess!")
        print("Result:", output)
        
    except Exception as error:
        print(f"\nError: {error}")

