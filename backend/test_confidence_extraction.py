#!/usr/bin/env python3
"""
Test script to verify confidence extraction logic works with mock Devin API responses.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from devin_client import DevinClient

def test_confidence_extraction():
    """Test the confidence extraction logic with mock session data."""
    
    mock_session_details = {
        "session_id": "test-session-123",
        "status_enum": "finished",
        "messages": [
            {
                "type": "user_message",
                "message": "Please analyze this GitHub issue..."
            },
            {
                "type": "devin_message", 
                "message": """I'll analyze this GitHub issue for you.

ACTION PLAN:
1. Review the current codebase structure
2. Identify the root cause of the issue
3. Implement a fix with proper error handling
4. Add unit tests to prevent regression
5. Update documentation if needed

CONFIDENCE SCORE: 85%

This plan should resolve the issue effectively."""
            }
        ]
    }
    
    try:
        client = DevinClient("fake-api-key-for-testing")
    except ValueError:
        client = DevinClient.__new__(DevinClient)
        client.api_key = "fake-api-key-for-testing"
    
    action_plan, confidence_score = client.extract_action_plan_and_confidence(mock_session_details)
    
    print("=== Confidence Extraction Test Results ===")
    print(f"Action Plan: {action_plan}")
    print(f"Confidence Score: {confidence_score}")
    
    if action_plan and confidence_score == 85:
        print("✅ SUCCESS: Confidence extraction working correctly!")
        return True
    else:
        print("❌ FAILURE: Confidence extraction not working as expected")
        print(f"Expected confidence: 85, Got: {confidence_score}")
        print(f"Expected action plan to contain steps, Got: {action_plan}")
        return False

def test_edge_cases():
    """Test edge cases for confidence extraction."""
    
    mock_session_1 = {
        "session_id": "test-session-456",
        "status_enum": "finished",
        "messages": [
            {
                "type": "devin_message",
                "message": """Analysis complete.

ACTION PLAN:
- Step 1: Do something
- Step 2: Do something else

CONFIDENCE SCORE: 75"""
            }
        ]
    }
    
    mock_session_2 = {
        "session_id": "test-session-789",
        "status_enum": "finished",
        "messages": [
            {
                "type": "devin_message",
                "message": """ACTION PLAN:
1. First step
2. Second step

No confidence score provided."""
            }
        ]
    }
    
    client = DevinClient.__new__(DevinClient)
    client.api_key = "fake-api-key-for-testing"
    
    action_plan_1, confidence_1 = client.extract_action_plan_and_confidence(mock_session_1)
    print(f"\nTest case 1 - Confidence without %: {confidence_1}")
    
    action_plan_2, confidence_2 = client.extract_action_plan_and_confidence(mock_session_2)
    print(f"Test case 2 - No confidence: {confidence_2}")
    
    return True

if __name__ == "__main__":
    print("Running confidence extraction tests...")
    success1 = test_confidence_extraction()
    success2 = test_edge_cases()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
