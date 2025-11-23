"""Comprehensive test for all email command formats"""
import requests
import time

url = "http://localhost:8003/chat"

print("\n" + "="*70)
print("COMPREHENSIVE EMAIL COMMAND TEST")
print("="*70)

tests = [
    {
        "name": "Query Email (Excel Agent)",
        "command": "whats the email of sheila carter?",
        "expected_agent": "excel",
        "expected_email": "prasannathefreelancer+bear@gmail.com",
        "should_send": False
    },
    {
        "name": "Mail Her (Gmail Agent)",
        "command": "mail her about follow up",
        "expected_agent": "gmail",
        "expected_email": "prasannathefreelancer+bear@gmail.com",
        "should_send": True
    },
    {
        "name": "Gmail + Name (Gmail Agent)",
        "command": "gmail sheila about her stocks",
        "expected_agent": "gmail",
        "expected_email": "prasannathefreelancer+bear@gmail.com",
        "should_send": True
    },
    {
        "name": "Mail + Name (Gmail Agent)",
        "command": "mail sheila",
        "expected_agent": "gmail",
        "expected_email": "prasannathefreelancer+bear@gmail.com",
        "should_send": True
    },
    {
        "name": "Email Her (Gmail Agent)",
        "command": "email her about the meeting",
        "expected_agent": "gmail",
        "expected_email": "prasannathefreelancer+bear@gmail.com",
        "should_send": True
    }
]

passed = 0
failed = 0

for i, test in enumerate(tests, 1):
    print(f"\n{i}. {test['name']}")
    print(f"   Command: '{test['command']}'")
    
    try:
        response = requests.post(url, json={"message": test['command']}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('response', '')
            agent = data.get('agent', '')
            
            print(f"   Agent: {agent}")
            print(f"   Response: {result[:150]}...")
            
            # Check agent routing
            if agent != test['expected_agent']:
                print(f"   ❌ WRONG AGENT! Expected {test['expected_agent']}, got {agent}")
                failed += 1
                continue
            
            # Check email presence
            if test['should_send']:
                if test['expected_email'] in result:
                    print(f"   ✅ CORRECT EMAIL USED!")
                    passed += 1
                elif 'client_email_from_csv' in result:
                    print(f"   ❌ LITERAL STRING - NOT FIXED!")
                    failed += 1
                elif '@example.com' in result or '@company.com' in result:
                    print(f"   ❌ HALLUCINATED EMAIL!")
                    failed += 1
                else:
                    print(f"   ⚠️  Email not visible in response")
                    failed += 1
            else:
                if test['expected_email'] in result:
                    print(f"   ✅ EMAIL FOUND IN QUERY RESPONSE!")
                    passed += 1
                else:
                    print(f"   ⚠️  Email not found")
                    failed += 1
        else:
            print(f"   ❌ HTTP {response.status_code}")
            failed += 1
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        failed += 1
    
    time.sleep(1)

print("\n" + "="*70)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
print("="*70)
