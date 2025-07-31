import httpx
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DevinClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEVIN_API_KEY")
        self.base_url = "https://api.devin.ai/v1"
        
        if not self.api_key:
            raise ValueError("Devin API key is required")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get the authentication headers for Devin API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_session(self, prompt: str) -> Dict[str, Any]:
        """Create a new Devin session with the initial prompt."""
        headers = self._get_auth_headers()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/sessions",
                    headers=headers,
                    json={"prompt": prompt}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to create Devin session: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to create Devin session: HTTP {response.status_code}")
                    
                return response.json()
            except httpx.TimeoutException:
                logger.error("Timeout creating Devin session")
                raise Exception("Timeout creating Devin session")
            except Exception as e:
                logger.error(f"Error creating Devin session: {str(e)}")
                raise
    
    async def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send a message to an existing Devin session."""
        headers = self._get_auth_headers()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/session/{session_id}/message",
                    headers=headers,
                    json={"message": message}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to send message to Devin session: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to send message to Devin session: HTTP {response.status_code}")
                    
                return response.json()
            except httpx.TimeoutException:
                logger.error("Timeout sending message to Devin session")
                raise Exception("Timeout sending message to Devin session")
            except Exception as e:
                logger.error(f"Error sending message to Devin session: {str(e)}")
                raise
    
    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get the current status and details of a Devin session."""
        headers = self._get_auth_headers()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/session/{session_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get Devin session details: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to get Devin session details: HTTP {response.status_code}")
                    
                return response.json()
            except httpx.TimeoutException:
                logger.error("Timeout getting Devin session details")
                raise Exception("Timeout getting Devin session details")
            except Exception as e:
                logger.error(f"Error getting Devin session details: {str(e)}")
                raise
    
    async def wait_for_completion(self, session_id: str, max_wait_time: int = 1800, poll_interval: int = 30) -> Dict[str, Any]:
        """
        Wait for a Devin session to complete and return the final results.
        
        Args:
            session_id: The session ID to monitor
            max_wait_time: Maximum time to wait in seconds (default 30 minutes)
            poll_interval: How often to check status in seconds (default 30 seconds)
        
        Returns:
            Final session details when completed
        """
        start_time = datetime.now()
        
        while True:
            try:
                session_details = await self.get_session_details(session_id)
                status_enum = session_details.get("status_enum")
                status = status_enum.lower() if status_enum else "unknown"
                
                if status in ["finished", "expired"]:
                    logger.info(f"Devin session {session_id} completed with status: {status}")
                    return session_details
                elif status == "blocked":
                    logger.warning(f"Devin session {session_id} is blocked - may need user input")
                    return session_details
                
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > max_wait_time:
                    logger.warning(f"Devin session {session_id} timed out after {max_wait_time} seconds")
                    return session_details
                
                logger.info(f"Devin session {session_id} status: {status}, waiting {poll_interval}s...")
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring Devin session {session_id}: {str(e)}")
                raise
    
    def extract_action_plan_and_confidence(self, session_details: Dict[str, Any]) -> tuple[Optional[str], Optional[int]]:
        """
        Extract action plan and confidence score from Devin session messages.
        
        Args:
            session_details: The session details from get_session_details()
            
        Returns:
            Tuple of (action_plan, confidence_score)
        """
        messages = session_details.get("messages", [])
        action_plan = None
        confidence_score = None
        
        for message in messages:
            if message.get("type") == "devin_message":
                content = message.get("message", "")
                
                if "ACTION PLAN:" in content.upper():
                    lines = content.split('\n')
                    plan_started = False
                    plan_lines = []
                    
                    for line in lines:
                        if "ACTION PLAN:" in line.upper():
                            plan_started = True
                            continue
                        elif "CONFIDENCE SCORE:" in line.upper() or "CONFIDENCE:" in line.upper():
                            plan_started = False
                            confidence_text = line.split(":")[-1].strip()
                            try:
                                import re
                                match = re.search(r'(\d+)', confidence_text)
                                if match:
                                    confidence_score = int(match.group(1))
                                    logger.info(f"Successfully extracted confidence score: {confidence_score}")
                            except (ValueError, AttributeError):
                                logger.warning(f"Could not parse confidence score from: {confidence_text}")
                        elif plan_started and line.strip():
                            plan_lines.append(line.strip())
                    
                    if plan_lines:
                        action_plan = '\n'.join(plan_lines)
        
        return action_plan, confidence_score
    
    async def analyze_github_issue(self, issue_title: str, issue_body: str = None, repo: str = None) -> Dict[str, Any]:
        """
        Analyze a GitHub issue and return action plan with confidence score.
        
        Args:
            issue_title: The GitHub issue title
            issue_body: The GitHub issue description
            repo: The repository name (optional)
            
        Returns:
            Dictionary containing session_id, action_plan, confidence_score, and status
        """
        prompt = f"""
Please analyze this GitHub issue and provide:
1. A detailed action plan (step-by-step approach)
2. A confidence score (1-100%) indicating your ability to resolve this issue

Issue Title: {issue_title}
Issue Description: {issue_body or "No description provided"}
{f"Repository: {repo}" if repo else ""}

Please format your response as:
ACTION PLAN:
[Your detailed step-by-step plan]

CONFIDENCE SCORE: [Your confidence percentage]%
"""
        
        try:
            session_response = await self.create_session(prompt)
            session_id = session_response.get("session_id")
            
            if not session_id:
                raise Exception("No session ID returned from Devin API")
            
            final_details = await self.wait_for_completion(session_id)
            action_plan, confidence_score = self.extract_action_plan_and_confidence(final_details)
            
            return {
                "session_id": session_id,
                "action_plan": action_plan,
                "confidence_score": confidence_score,
                "status": final_details.get("status_enum", "unknown"),
                "session_details": final_details
            }
            
        except Exception as e:
            logger.error(f"Error analyzing GitHub issue: {str(e)}")
            raise
    
    async def resolve_github_issue(self, issue_number: int, issue_title: str, issue_body: str = None, repo: str = None) -> Dict[str, Any]:
        """
        Have Devin attempt to resolve a GitHub issue.
        
        Args:
            issue_number: The GitHub issue number
            issue_title: The GitHub issue title
            issue_body: The GitHub issue description
            repo: The repository name
            
        Returns:
            Dictionary containing session_id and initial status
        """
        prompt = f"""
Please resolve this GitHub issue by implementing the necessary changes:

Repository: {repo or "Not specified"}
Issue #{issue_number}: {issue_title}
Description: {issue_body or "No description provided"}

Please:
1. Analyze the issue thoroughly
2. Implement the necessary code changes
3. Create a pull request with your solution
4. Provide regular updates on your progress

Post updates as comments on the GitHub issue as you work.
"""
        
        try:
            session_response = await self.create_session(prompt)
            session_id = session_response.get("session_id")
            
            if not session_id:
                raise Exception("No session ID returned from Devin API")
            
            return {
                "session_id": session_id,
                "status": "started",
                "url": session_response.get("url")
            }
            
        except Exception as e:
            logger.error(f"Error starting GitHub issue resolution: {str(e)}")
            raise
