# Quick GitHub Setup Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `youtube-transcript-api`)
3. **Don't** initialize with README, .gitignore, or license (we already have these)

## Step 2: Initialize Git and Push

```bash
cd youtube-api

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: YouTube Transcript API for Vercel"

# Add remote (replace with your GitHub username and repo name)
git remote add origin https://github.com/YOUR_USERNAME/youtube-transcript-api.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Vercel

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Select your repository
5. Configure:
   - **Root Directory**: `.` (or `youtube-api` if this is a subdirectory)
   - **Framework Preset**: **Other**
6. Click **"Deploy"**

## Step 4: Get Your URL

After deployment, Vercel will show you a URL like:
```
https://youtube-transcript-api.vercel.app
```

## Step 5: Update Flutter App

In `lib/services/youtube_transcript_service.dart`, add your Vercel URL:

```dart
static const List<String> _apiBaseUrls = [
  'https://youtube-transcript-api.vercel.app',  // Your URL here
  'http://localhost:3000',
  'http://127.0.0.1:3000',
  'http://10.0.2.2:3000',
];
```

## Files Included in Repository

Make sure these files are committed:
- ✅ `api/index.py` - Serverless function
- ✅ `vercel.json` - Vercel configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `.gitignore` - Git ignore rules
- ✅ `README.md` - Documentation

## Automatic Deployments

Once connected:
- Every push to `main` branch = Production deployment
- Every pull request = Preview deployment
- No manual deployment needed!

