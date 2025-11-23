"""Test email query and send fix"""
import requests
import json
import time

url = "http://localhost:8003/chat"

print("\n" + "="*70)
print("TEST: Email Query and Send Fix")
print("="*70)

# Test 1: Query for email (should go to Excel agent, not Gmail)
print("\n1. Testing: 'whats the email of sheila carter?'")
response = requests.post(url, json={"message": "whats the email of sheila carter?"})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    result = data.get('response', '')
    agent = data.get('agent', '')
    print(f"   Agent: {agent}")
    print(f"   Response: {result[:200]}")
    
    if 'prasannathefreelancer+bear@gmail.com' in result:
        print("   ✅ CORRECT EMAIL FOUND!")
    elif '@company.com' in result or '@example.com' in result:
        print("   ❌ HALLUCINATED EMAIL!")
    else:
        print("   ⚠️  Email not found in response")

time.sleep(1)

# Test 2: Send email using pronoun (should use context)
print("\n2. Testing: 'mail her that does she need a follow up meeting'")
response = requests.post(url, json={"message": "mail her that does she need a follow up meeting"})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    result = data.get('response', '')
    agent = data.get('agent', '')
    print(f"   Agent: {agent}")
    print(f"   Response: {result}")
    
    if 'prasannathefreelancer+bear@gmail.com' in result:
        print("   ✅ CORRECT EMAIL USED!")
    elif 'client_email_from_csv' in result:
        print("   ❌ LITERAL STRING - LLM NOT FIXED!")
    elif '@company.com' in result or '@example.com' in result:
        print("   ❌ HALLUCINATED EMAIL!")
    else:
        print("   ⚠️  Email not visible in response")

time.sleep(1)

# Test 3: Direct send with name mention
print("\n3. Testing: 'send email to sheila about meeting'")
response = requests.post(url, json={"message": "send email to sheila about meeting"})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    result = data.get('response', '')
    agent = data.get('agent', '')
    print(f"   Agent: {agent}")
    print(f"   Response: {result}")
    
    if 'prasannathefreelancer+bear@gmail.com' in result:
        print("   ✅ CORRECT EMAIL USED!")
    elif 'client_email_from_csv' in result:
        print("   ❌ LITERAL STRING!")
    elif '@company.com' in result or '@example.com' in result:
        print("   ❌ HALLUCINATED EMAIL!")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
