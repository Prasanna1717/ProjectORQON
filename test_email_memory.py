"""
Test email extraction with conversation memory
"""
import requests
import json

BASE_URL = "http://localhost:8003"

def test_email_with_memory():
    """Test that Sheila's email is correctly extracted from CSV"""
    
    print("\n" + "="*70)
    print("TEST: Email Extraction with Conversation Memory")
    print("="*70)
    
    # Test 1: Query for Sheila's data (this should save to context)
    print("\n1. Querying for Sheila's trade data...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "show trades for Sheila Carter"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Response received")
    
    # Test 2: Ask for Sheila's email directly (should use memory)
    print("\n2. Asking 'what's her mail in this?'...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "whats her mail in this?"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        result = data.get('response', '')
        print(f"   Response: {result[:300]}")
        if 'prasannathefreelancer+bear@gmail.com' in result:
            print("   ✓ CORRECT EMAIL FOUND!")
        else:
            print("   ✗ Wrong email or not found")
    
    # Test 3: Send email to Sheila (should auto-detect email)
    print("\n3. Sending email to Sheila about follow-up...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "lets mail her regarding follow up date remainder"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        result = data.get('response', '')
        print(f"   Response: {result[:300]}")
        
        # Check if correct email was used
        if 'prasannathefreelancer+bear@gmail.com' in result:
            print("   ✓ CORRECT EMAIL USED!")
        elif 'heremail@example.com' in result or 'sheila@example.com' in result:
            print("   ✗ WRONG EMAIL - Using placeholder instead of CSV data")
        else:
            print("   ? Email not visible in response")
    
    # Test 4: Direct mention of Sheila in email command
    print("\n4. Direct email command with Sheila's name...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "send email to sheila about stock meeting"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        result = data.get('response', '')
        print(f"   Response: {result[:300]}")
        
        if 'prasannathefreelancer+bear@gmail.com' in result:
            print("   ✓ CORRECT EMAIL EXTRACTED FROM CSV!")
        else:
            print("   ✗ Failed to extract email from CSV")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_email_with_memory()
