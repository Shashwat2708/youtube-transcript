# Proxy Setup Guide for YouTube Transcript API

YouTube blocks requests from cloud provider IPs (like Vercel), so you need to use a proxy service to fetch transcripts reliably.

## Quick Setup

### Option 1: Using a Proxy Service (Recommended)

1. **Sign up for a proxy service** (some free/paid options):
   - [ScraperAPI](https://www.scraperapi.com/) - Has a free tier
   - [Bright Data](https://brightdata.com/) - Enterprise-grade
   - [ProxyMesh](https://proxymesh.com/) - Simple proxy service
   - Or use any HTTP/HTTPS proxy service

2. **Get your proxy URL** from the service (format: `http://username:password@proxy.example.com:8080`)

3. **Add to Vercel Environment Variables**:
   - Go to your Vercel project dashboard
   - Navigate to **Settings** → **Environment Variables**
   - Add a new variable:
     - **Key**: `PROXY_URL`
     - **Value**: Your proxy URL (e.g., `http://proxy.example.com:8080`)
     - **Environment**: Select all (Production, Preview, Development)

4. **Redeploy** your Vercel function

### Option 2: Separate HTTP/HTTPS Proxies

If you need different proxies for HTTP and HTTPS:

- **PROXY_HTTP**: `http://proxy.example.com:8080`
- **PROXY_HTTPS**: `https://proxy.example.com:8080`

### Option 3: Free/Open Proxy (Not Recommended)

You can use free proxies, but they are:
- Unreliable
- Slow
- May not work consistently
- Security concerns

## Example: Using ScraperAPI

1. Sign up at https://www.scraperapi.com/
2. Get your API key
3. Set `PROXY_URL` to: `http://scraperapi:YOUR_API_KEY@proxy-server.scraperapi.com:8001`
4. Add to Vercel environment variables
5. Redeploy

## Testing

After setting up the proxy, test your endpoint:

```bash
curl https://your-app.vercel.app/health
curl https://your-app.vercel.app/transcript/dQw4w9WgXcQ
```

If you still get blocking errors, check:
- Proxy URL is correct
- Proxy credentials are valid
- Proxy service is working
- Environment variable is set for the correct environment

## Cost Considerations

- **Free tier proxies**: Usually limited requests/month
- **Paid proxies**: More reliable, higher cost
- **Self-hosted proxy**: Most cost-effective for high volume, but requires infrastructure

For production apps, consider a paid proxy service for reliability.

