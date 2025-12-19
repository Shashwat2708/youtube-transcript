# Deploying YouTube Transcript API to Vercel via GitHub

## Prerequisites

1. Make sure you have a Vercel account (sign up at https://vercel.com)
2. Have your code pushed to a GitHub repository

## Deployment Steps (GitHub Integration)

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push your code to GitHub**:
   ```bash
   cd youtube-api
   git init  # If not already a git repo
   git add .
   git commit -m "Initial commit: YouTube Transcript API"
   git remote add origin https://github.com/your-username/your-repo-name.git
   git push -u origin main
   ```

2. **Go to Vercel Dashboard**:
   - Visit https://vercel.com/dashboard
   - Click **"Add New..."** → **"Project"**

3. **Import from GitHub**:
   - Click **"Import Git Repository"**
   - Select your GitHub repository
   - If this is your first time, authorize Vercel to access your GitHub account

4. **Configure Project**:
   - **Project Name**: `youtube-transcript-api` (or your preferred name)
   - **Root Directory**: Leave as `.` (or set to `youtube-api` if the API is in a subdirectory)
   - **Framework Preset**: Select **"Other"** or **"Python"**
   - **Build Command**: Leave empty (not needed for Python serverless functions)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty (Vercel will use `requirements.txt` automatically)

5. **Deploy**:
   - Click **"Deploy"**
   - Wait for the build to complete (usually 1-2 minutes)

### Option 2: Deploy via Vercel CLI (Alternative)

If you prefer using CLI:

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Navigate to the API directory**:
   ```bash
   cd youtube-api
   ```

3. **Login to Vercel**:
   ```bash
   vercel login
   ```

4. **Link to GitHub** (if not already linked):
   ```bash
   vercel link
   ```
   - Follow prompts to connect to your GitHub repository

5. **Deploy**:
   ```bash
   vercel --prod
   ```

## After Deployment

1. **Get your deployment URL**: 
   - After deployment, Vercel will give you a URL like:
     ```
     https://your-project-name.vercel.app
     ```
   - You can find it in the Vercel dashboard under your project's "Domains" section

2. **Update Flutter app**: 
   - Open `lib/services/youtube_transcript_service.dart`
   - Update the `_apiBaseUrls` list to include your Vercel URL:
   ```dart
   static const List<String> _apiBaseUrls = [
     'https://your-project-name.vercel.app',  // Your Vercel URL (add this)
     'http://localhost:3000',  // Keep for local development
     'http://127.0.0.1:3000',
     'http://10.0.2.2:3000',
   ];
   ```

## Testing

Test your deployed API:
```bash
curl https://your-project-name.vercel.app/health
curl https://your-project-name.vercel.app/transcript/dQw4w9WgXcQ
```

## Environment Variables

If you need to add environment variables (like API keys):

**Via Dashboard**:
1. Go to your project in Vercel dashboard
2. Click **"Settings"** → **"Environment Variables"**
3. Add your variables for Production, Preview, and Development

**Via CLI** (alternative):
```bash
vercel env add VARIABLE_NAME
```

## Automatic Deployments (GitHub Integration)

Once connected to GitHub, Vercel will automatically:
- **Deploy to Production**: When you push to `main` or `master` branch
- **Create Preview Deployments**: For every pull request
- **Redeploy**: When you push new commits

## Updating Deployment

### Via GitHub (Automatic):
1. Make your changes
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update API"
   git push
   ```
3. Vercel will automatically deploy the changes

### Via CLI (Manual):
```bash
vercel --prod
```

## Troubleshooting

- **Build errors**: Check Vercel dashboard logs
- **Timeout errors**: Vercel has a 10-second timeout for free tier, 60 seconds for Pro
- **CORS issues**: The API already includes CORS headers

