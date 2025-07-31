from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from dotenv import load_dotenv
import sqlite3
import json
from datetime import datetime
import asyncio
import logging
from devin_client import DevinClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up - checking for existing incomplete sessions to monitor")
    
    conn = sqlite3.connect("issues.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT devin_session_id, issue_number, issue_title, status 
        FROM issue_sessions 
        WHERE status IN ('scoping', 'resolving', 'blocked')
    """)
    incomplete_sessions = cursor.fetchall()
    conn.close()
    
    for session_id, issue_number, issue_title, status in incomplete_sessions:
        logger.info(f"Starting monitoring for existing session {session_id} (status: {status})")
        repo = "GoogleCloudPlatform/marketing-analytics-jumpstart"
        session_type = "scoping" if status in ['scoping', 'blocked'] else "resolving"
        
        asyncio.create_task(monitor_devin_session(session_id, issue_number, repo, session_type))
    
    yield
    logger.info("Shutting down")

app = FastAPI(title="GitHub Issues Devin Integration", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPO", "google/meridian")

devin_client = None
if DEVIN_API_KEY:
    devin_client = DevinClient(DEVIN_API_KEY)
else:
    logging.warning("DEVIN_API_KEY not provided - Devin integration features will be disabled")

def init_db():
    conn = sqlite3.connect("issues.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issue_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_number INTEGER,
            issue_title TEXT,
            devin_session_id TEXT,
            action_plan TEXT,
            confidence_score INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()


class GitHubIssue(BaseModel):
    number: int
    title: str
    body: Optional[str]
    state: str
    labels: List[dict]
    assignees: List[dict]
    html_url: str

class DevinScopeRequest(BaseModel):
    issue_number: int
    issue_title: str
    issue_body: Optional[str]
    repo: Optional[str] = "google/meridian"

class DevinResolveRequest(BaseModel):
    issue_number: int
    repo: Optional[str] = "google/meridian"

async def get_github_issues(repo: str, state: str = "open", labels: Optional[str] = None):
    if not GITHUB_TOKEN:
        logging.warning("GITHUB_TOKEN not provided - attempting to fetch public issues without authentication (rate limited)")
        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHub-Issues-Devin-Integration"
            }
            
            params = {"state": state}
            if labels:
                params["labels"] = labels
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/repos/{repo}/issues",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    issues_data = response.json()
                    filtered_issues = [issue for issue in issues_data if 'pull_request' not in issue]
                    logging.info(f"Successfully fetched {len(filtered_issues)} public issues from {repo}")
                    return filtered_issues
                else:
                    logging.warning(f"Failed to fetch public issues (status {response.status_code}), falling back to mock data")
        except Exception as e:
            logging.warning(f"Error fetching public issues: {e}, falling back to mock data")
        
        return [
            {
                "number": 1,
                "title": "Sample Issue: Add user authentication",
                "body": "This is a sample issue for local development. In production, this would fetch real GitHub issues.",
                "state": "open",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "html_url": "https://github.com/example/repo/issues/1",
                "labels": [],
                "assignees": []
            },
            {
                "number": 2,
                "title": "Sample Issue: Fix responsive design",
                "body": "Another sample issue to demonstrate the interface. Real issues would be fetched from GitHub API.",
                "state": "open",
                "created_at": "2024-01-02T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "html_url": "https://github.com/example/repo/issues/2",
                "labels": [],
                "assignees": []
            }
        ]
    
    if "/" not in repo or len(repo.split("/")) != 2:
        raise HTTPException(
            status_code=400,
            detail="Repository must be in format 'owner/repo'"
        )
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    params = {"state": state}
    if labels:
        params["labels"] = labels
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{repo}/issues",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch GitHub issues")
        
        issues_data = response.json()
        filtered_issues = [issue for issue in issues_data if 'pull_request' not in issue]
        
        return filtered_issues

async def post_github_comment(issue_number: int, comment: str, repo: str = "google/meridian"):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
            headers=headers,
            json={"body": comment}
        )
        
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail="Failed to post comment")
        
        return response.json()

async def create_devin_session(prompt: str):
    """Create a new Devin session with the given prompt."""
    try:
        response = await devin_client.create_session(prompt)
        return {
            "session_id": response.get("session_id"),
            "status": "created",
            "message": "Session created successfully",
            "url": response.get("url")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Devin session: {str(e)}")

async def send_devin_message(session_id: str, message: str):
    """Send a message to an existing Devin session."""
    try:
        response = await devin_client.send_message(session_id, message)
        return {
            "session_id": session_id,
            "status": "message_sent",
            "response": "Message sent successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message to Devin session: {str(e)}")

async def get_devin_session_status(session_id: str):
    """Get the current status and details of a Devin session."""
    try:
        return await devin_client.get_session_details(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Devin session status: {str(e)}")

async def monitor_devin_session(session_id: str, issue_number: int, repo: str, session_type: str = "scoping"):
    """
    Background task to monitor a Devin session and post results when complete.
    
    Args:
        session_id: The Devin session ID to monitor
        issue_number: The GitHub issue number
        repo: The repository name
        session_type: Either "scoping" or "resolving"
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting to monitor Devin session {session_id} for issue #{issue_number}")
    
    max_wait_time = 1800  # 30 minutes
    poll_interval = 30    # 30 seconds
    start_time = datetime.now()
    
    try:
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait_time:
                logger.warning(f"Session {session_id} monitoring timed out after {max_wait_time} seconds")
                
                conn = sqlite3.connect("issues.db")
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE issue_sessions 
                    SET status = 'timeout', updated_at = CURRENT_TIMESTAMP
                    WHERE devin_session_id = ?
                """, (session_id,))
                conn.commit()
                conn.close()
                
                timeout_comment = f"⏰ **Devin Session Timeout**\n\nThe Devin analysis session `{session_id}` has timed out after 30 minutes. Please try again or contact support if this issue persists."
                await post_github_comment(issue_number, timeout_comment, repo)
                break
            
            try:
                session_details = await devin_client.get_session_details(session_id)
                status_enum = session_details.get("status_enum")
                status = status_enum.lower() if status_enum else "unknown"
                
                logger.info(f"Session {session_id} status: {status}")
                
                if status in ["finished", "expired"]:
                    logger.info(f"Session {session_id} completed with status: {status}")
                    
                    if session_type == "scoping":
                        action_plan, confidence_score = devin_client.extract_action_plan_and_confidence(session_details)
                        
                        conn = sqlite3.connect("issues.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE issue_sessions 
                            SET action_plan = ?, confidence_score = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP
                            WHERE devin_session_id = ?
                        """, (action_plan, confidence_score, session_id))
                        conn.commit()
                        conn.close()
                        
                        if action_plan and confidence_score:
                            results_comment = f"""## 🤖 Devin Analysis Results

{action_plan}


---
*Session ID: `{session_id}`*
*Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
                        else:
                            results_comment = f"""## 🤖 Devin Analysis Complete

The analysis session has completed, but I was unable to extract a structured action plan and confidence score from the results.

**Session Details:**
- Session ID: `{session_id}`
- Status: {status}
- Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please check the [Devin session]({session_details.get('url', '#')}) for detailed results."""
                        
                        await post_github_comment(issue_number, results_comment, repo)
                        
                    else:  # resolving session
                        # Update database status for resolution sessions
                        conn = sqlite3.connect("issues.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE issue_sessions 
                            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                            WHERE devin_session_id = ?
                        """, (session_id,))
                        conn.commit()
                        conn.close()
                        
                        completion_comment = f"""## 🚀 Devin Resolution Complete

The issue resolution session has completed successfully!

**Session Details:**
- Session ID: `{session_id}`
- Status: {status}
- Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please check the [Devin session]({session_details.get('url', '#')}) for detailed results and any pull requests that may have been created."""
                        
                        await post_github_comment(issue_number, completion_comment, repo)
                    
                    break
                    
                elif status == "blocked":
                    logger.warning(f"Session {session_id} is blocked - checking for completion indicators in messages")
                    
                    if session_type == "scoping":
                        logger.info(f"Checking session {session_id} for completion indicators in messages")
                        action_plan, confidence_score = devin_client.extract_action_plan_and_confidence(session_details)
                        logger.info(f"Extraction results - Action plan: {'Found' if action_plan else 'None'}, Confidence: {confidence_score}")
                        
                        if action_plan and confidence_score:
                            logger.info(f"Session {session_id} completed analysis while blocked - processing results")
                            
                            conn = sqlite3.connect("issues.db")
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE issue_sessions 
                                SET action_plan = ?, confidence_score = ?, status = 'completed', updated_at = CURRENT_TIMESTAMP
                                WHERE devin_session_id = ?
                            """, (action_plan, confidence_score, session_id))
                            conn.commit()
                            conn.close()
                            
                            results_comment = f"""## 🤖 Devin Analysis Results

{action_plan}

**Confidence Score: {confidence_score}%**

---
*Session ID: `{session_id}`*
*Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
                            
                            await post_github_comment(issue_number, results_comment, repo)
                            break
                    
                    conn = sqlite3.connect("issues.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE issue_sessions 
                        SET status = 'blocked', updated_at = CURRENT_TIMESTAMP
                        WHERE devin_session_id = ?
                    """, (session_id,))
                    conn.commit()
                    
                    cursor.execute("SELECT COUNT(*) FROM issue_sessions WHERE devin_session_id = ? AND status = 'blocked'", (session_id,))
                    blocked_count = cursor.fetchone()[0]
                    conn.close()
                    
                    if blocked_count == 1:
                        blocked_comment = f"""## ⚠️ Devin Session Status Update

The Devin session `{session_id}` is currently blocked and may require user input. I'll continue monitoring for completion.

Please check the [Devin session]({session_details.get('url', '#')}) to see what input is needed."""
                        
                        await post_github_comment(issue_number, blocked_comment, repo)
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error checking session {session_id} status: {str(e)}")
                await asyncio.sleep(poll_interval)
                continue
                
    except Exception as e:
        logger.error(f"Error monitoring Devin session {session_id}: {str(e)}")
        
        error_comment = f"""## ❌ Devin Session Error

An error occurred while monitoring the Devin session `{session_id}`:

```
{str(e)}
```

Please try again or contact support if this issue persists."""
        
        try:
            await post_github_comment(issue_number, error_comment, repo)
        except Exception as comment_error:
            logger.error(f"Failed to post error comment: {str(comment_error)}")

@app.get("/")
async def root():
    return {"message": "GitHub Issues Devin Integration API"}

@app.get("/issues", response_model=List[GitHubIssue])
async def get_issues(repo: str = "google/meridian", state: str = "open", labels: Optional[str] = None):
    """Get GitHub issues from the specified repository"""
    issues = await get_github_issues(repo, state, labels)
    return issues

@app.post("/scope-issue")
async def scope_issue(request: DevinScopeRequest, background_tasks: BackgroundTasks):
    """Have Devin analyze and scope an issue"""
    
    if not devin_client:
        raise HTTPException(
            status_code=503, 
            detail="Devin integration is not configured. Please set the DEVIN_API_KEY environment variable to enable issue scoping."
        )
    
    scope_message = f"""
Please analyze this GitHub issue and provide:
1. A detailed action plan (step-by-step approach)
2. A confidence score (1-100%) indicating your ability to resolve this issue

Issue Title: {request.issue_title}
Issue Description: {request.issue_body or "No description provided"}

Please format your response as:
ACTION PLAN:
[Your detailed step-by-step plan]

CONFIDENCE SCORE: [Your confidence percentage]%
"""
    
    try:
        session_response = await create_devin_session(scope_message)
        session_id = session_response.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=500, detail="No session ID returned from Devin API")
        
        conn = sqlite3.connect("issues.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO issue_sessions (issue_number, issue_title, devin_session_id, status)
            VALUES (?, ?, ?, ?)
        """, (request.issue_number, request.issue_title, session_id, "scoping"))
        conn.commit()
        conn.close()
        
        session_url = session_response.get("url", "#")
        comment = f"""🤖 **Devin AI Analysis Started**

I'm analyzing this issue to provide a detailed action plan and confidence score. 

**Session Details:**
- Session ID: `{session_id}`
- Session URL: [View Progress]({session_url})

I'll post the results here once the analysis is complete (typically within 10-30 minutes)."""
        
        await post_github_comment(request.issue_number, comment, request.repo)
        
        background_tasks.add_task(
            monitor_devin_session, 
            session_id, 
            request.issue_number, 
            request.repo, 
            "scoping"
        )
        
        return {
            "session_id": session_id,
            "status": "scoping_started",
            "message": "Devin is analyzing the issue",
            "url": session_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scoping: {str(e)}")

@app.post("/resolve-issue")
async def resolve_issue(request: DevinResolveRequest, background_tasks: BackgroundTasks):
    """Have Devin attempt to resolve an issue"""
    
    if not devin_client:
        raise HTTPException(
            status_code=503, 
            detail="Devin integration is not configured. Please set the DEVIN_API_KEY environment variable to enable issue resolution."
        )
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{request.repo}/issues/{request.issue_number}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        issue_data = response.json()
    
    resolve_message = f"""
Please resolve this GitHub issue by implementing the necessary changes:

Repository: {request.repo}
Issue #{request.issue_number}: {issue_data['title']}
Description: {issue_data['body'] or "No description provided"}

Please:
1. Analyze the issue thoroughly
2. Implement the necessary code changes
3. Create a pull request with your solution
4. Provide regular updates on your progress

Post updates as comments on the GitHub issue as you work.
"""
    
    try:
        session_response = await create_devin_session(resolve_message)
        session_id = session_response.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=500, detail="No session ID returned from Devin API")
        
        conn = sqlite3.connect("issues.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO issue_sessions (issue_number, issue_title, devin_session_id, status)
            VALUES (?, ?, ?, ?)
        """, (request.issue_number, issue_data['title'], session_id, "resolving"))
        conn.commit()
        conn.close()
        
        session_url = session_response.get("url", "#")
        comment = f"""🚀 **Devin AI Resolution Started**

I'm working on resolving this issue. I'll provide regular updates as I make progress.

**Session Details:**
- Session ID: `{session_id}`
- Session URL: [View Progress]({session_url})

I'll post updates here as I work through the resolution process."""
        
        await post_github_comment(request.issue_number, comment, request.repo)
        
        background_tasks.add_task(
            monitor_devin_session, 
            session_id, 
            request.issue_number, 
            request.repo, 
            "resolving"
        )
        
        return {
            "session_id": session_id,
            "status": "resolution_started",
            "message": "Devin is working on resolving the issue",
            "url": session_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start resolution: {str(e)}")

@app.get("/sessions")
async def get_sessions():
    """Get all Devin sessions"""
    conn = sqlite3.connect("issues.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM issue_sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": session[0],
            "issue_number": session[1],
            "issue_title": session[2],
            "devin_session_id": session[3],
            "action_plan": session[4],
            "confidence_score": session[5],
            "status": session[6],
            "created_at": session[7],
            "updated_at": session[8]
        }
        for session in sessions
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
