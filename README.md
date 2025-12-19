# YouTube Transcript API (Python)

A simple Python Flask API server for fetching YouTube video transcripts.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

Or if you prefer using a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the server:
```bash
python3 server.py
```

The server will run on `http://localhost:3000`

## Endpoints

### Health Check
```
GET /health
```

### Fetch Transcript
```
GET /transcript/:videoId
GET /transcript/:videoId?lang=en
```

Example:
```
GET http://localhost:3000/transcript/dQw4w9WgXcQ
GET http://localhost:3000/transcript/dQw4w9WgXcQ?lang=en
```

### List Available Transcripts
```
GET /transcript/:videoId/list
```

## Response Format

Success:
```json
{
  "success": true,
  "videoId": "dQw4w9WgXcQ",
  "transcript": "Full transcript text...",
  "length": 1234,
  "snippets": 56
}
```

Error:
```json
{
  "success": false,
  "error": "Error message",
  "videoId": "dQw4w9WgXcQ"
}
```

## For Vercel Deployment via GitHub

**Quick Start**: See `GITHUB_SETUP.md` for step-by-step instructions.

**Detailed Guide**: See `DEPLOY.md` for complete deployment documentation.

### Quick Overview:
1. Push code to GitHub
2. Import repository in Vercel dashboard
3. Deploy automatically
4. Update Flutter app with your Vercel URL

The API is already configured for Vercel with:
- `vercel.json` - Vercel configuration
- `api/index.py` - Serverless function handler
- `requirements.txt` - Python dependencies

### Automatic Deployments:
Once connected to GitHub, Vercel automatically deploys:
- ✅ Every push to `main` branch → Production
- ✅ Every pull request → Preview deployment
# youtube-transcript
