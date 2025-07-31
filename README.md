# GitHub Issues Devin Integration

An intelligent GitHub Issues automation system that leverages Devin AI to provide automated issue analysis, scoping, and resolution capabilities.

## Overview

This application helps development teams manage GitHub repositories by automating issue triage and resolution through AI-powered analysis. Users can automatically generate detailed action plans with confidence scores and initiate AI-driven resolution attempts.

## Features

- **🔍 Intelligent Issue Analysis**: Automatically analyze GitHub issues to generate detailed action plans and confidence scores
- **🤖 AI-Powered Resolution**: Initiate Devin AI sessions to attempt automated issue resolution with code changes and PRs  
- **📊 Real-time Monitoring**: Track AI session progress with persistent database storage and live status updates
- **💬 GitHub Integration**: Automatic posting of analysis results and status updates directly to issue comments
- **🎯 Confidence Scoring**: Visual confidence indicators (85-98%) displayed on frontend for scoped issues
- **📱 Modern UI**: Clean Next.js frontend with real-time session monitoring and issue management

## Architecture

- **Backend**: FastAPI service with SQLite database for session persistence
- **Frontend**: Next.js application with real-time updates and responsive design
- **Integration**: GitHub API and Devin AI API for automated workflows

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- GitHub Personal Access Token
- Devin API Key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export GITHUB_TOKEN="your_github_token"
export DEVIN_API_KEY="your_devin_api_key"
export DISABLE_BLOCKED_COMMENTS="false"  # Optional: set to "true" to disable blocked session warning comments

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Usage
1. Navigate to the frontend application
2. Browse GitHub issues from your configured repository
3. Click "Scope with Devin" to analyze issues and generate action plans
4. View confidence scores and detailed analysis results
5. Optionally use "Resolve with Devin" for automated resolution attempts

## API Endpoints

- `GET /issues` - Fetch GitHub issues with filtering
- `POST /scope-issue` - Initiate Devin AI issue analysis  
- `POST /resolve-issue` - Start automated issue resolution
- `GET /sessions` - Retrieve all Devin session data

## Deployment

The application is configured for deployment on Fly.io (backend) and supports static export for frontend hosting.

## Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token for API access
- `DEVIN_API_KEY`: Devin API key for session management  
- `DISABLE_BLOCKED_COMMENTS`: Set to "true", "1", or "yes" to disable warning comments when sessions become blocked (optional, defaults to posting comments)

## Contributing

This repository demonstrates Devin AI integration patterns and automated GitHub workflow management.
