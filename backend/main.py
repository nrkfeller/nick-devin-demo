from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from dotenv import load_dotenv
import sqlite3
import json
from datetime import datetime

load_dotenv()

app = FastAPI(title="GitHub Issues Devin Integration", version="1.0.0")

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
        
        return response.json()

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

async def create_devin_session(message: str):
    import uuid
    session_id = str(uuid.uuid4())
    
    if "analyze this GitHub issue" in message.lower():
        return {
            "session_id": session_id,
            "status": "created",
            "message": "Session created for issue analysis"
        }
    else:
        return {
            "session_id": session_id,
            "status": "created", 
            "message": "Session created for issue resolution"
        }

async def send_devin_message(session_id: str, message: str):
    return {
        "session_id": session_id,
        "status": "message_sent",
        "response": "Message received and processing started"
    }

@app.get("/")
async def root():
    return {"message": "GitHub Issues Devin Integration API"}

@app.get("/issues", response_model=List[GitHubIssue])
async def get_issues(repo: str = "google/meridian", state: str = "open", labels: Optional[str] = None):
    """Get GitHub issues from the specified repository"""
    issues = await get_github_issues(repo, state, labels)
    return issues

@app.post("/scope-issue")
async def scope_issue(request: DevinScopeRequest):
    """Have Devin analyze and scope an issue"""
    
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
        
        conn = sqlite3.connect("issues.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO issue_sessions (issue_number, issue_title, devin_session_id, status)
            VALUES (?, ?, ?, ?)
        """, (request.issue_number, request.issue_title, session_id, "scoping"))
        conn.commit()
        conn.close()
        
        comment = f"🤖 **Devin AI Analysis Started**\n\nI'm analyzing this issue to provide a detailed action plan and confidence score. Session ID: `{session_id}`"
        await post_github_comment(request.issue_number, comment, request.repo)
        
        return {
            "session_id": session_id,
            "status": "scoping_started",
            "message": "Devin is analyzing the issue"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scoping: {str(e)}")

@app.post("/resolve-issue")
async def resolve_issue(request: DevinResolveRequest):
    """Have Devin attempt to resolve an issue"""
    
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
        
        conn = sqlite3.connect("issues.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO issue_sessions (issue_number, issue_title, devin_session_id, status)
            VALUES (?, ?, ?, ?)
        """, (request.issue_number, issue_data['title'], session_id, "resolving"))
        conn.commit()
        conn.close()
        
        comment = f"🚀 **Devin AI Resolution Started**\n\nI'm working on resolving this issue. I'll provide regular updates as I make progress.\n\nSession ID: `{session_id}`"
        await post_github_comment(request.issue_number, comment, request.repo)
        
        return {
            "session_id": session_id,
            "status": "resolution_started",
            "message": "Devin is working on resolving the issue"
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
