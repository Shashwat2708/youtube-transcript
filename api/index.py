import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler
from requests import Session
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    RequestBlocked,
    IpBlocked,
)


def create_youtube_api():
    """
    Create YouTubeTranscriptApi instance with proxy support if configured.
    Supports proxy via environment variables:
    - PROXY_URL: Full proxy URL (e.g., http://proxy.example.com:8080)
    - PROXY_HTTP: HTTP proxy URL
    - PROXY_HTTPS: HTTPS proxy URL
    """
    # Check for proxy configuration
    proxy_url = os.environ.get('PROXY_URL')
    proxy_http = os.environ.get('PROXY_HTTP')
    proxy_https = os.environ.get('PROXY_HTTPS')
    
    if proxy_url or proxy_http or proxy_https:
        # Create a session with proxy configuration
        session = Session()
        if proxy_url:
            # Use same proxy for both HTTP and HTTPS
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url,
            }
        else:
            # Use separate proxies
            proxies = {}
            if proxy_http:
                proxies['http'] = proxy_http
            if proxy_https:
                proxies['https'] = proxy_https
            if proxies:
                session.proxies = proxies
        
        # Create API instance with custom session
        return YouTubeTranscriptApi(http_client=session)
    else:
        # No proxy configured, use default
        return YouTubeTranscriptApi()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse path and query
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path.strip('/')
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Extract query parameters (take first value if list)
            lang = query_params.get('lang', ['en'])[0] if query_params.get('lang') else 'en'
            
            # Normalize path
            path_parts = [p for p in path.split('/') if p]
            
            # Set CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            }
            
            # Health check endpoint
            if not path_parts or (len(path_parts) == 1 and path_parts[0] == 'health'):
                self.send_response(200)
                self._send_json_headers(cors_headers)
                response = {
                    'status': 'ok',
                    'message': 'YouTube Transcript API is running'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Validate path structure: /transcript/{videoId} or /transcript/{videoId}/list
            if len(path_parts) < 2 or path_parts[0] != 'transcript':
                self.send_response(404)
                self._send_json_headers(cors_headers)
                response = {
                    'success': False,
                    'error': 'Not Found. Use /transcript/{videoId} or /transcript/{videoId}/list'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            video_id = path_parts[1]
            is_list_endpoint = len(path_parts) > 2 and path_parts[2] == 'list'
            
            # Validate video ID
            if not video_id or len(video_id) < 10:
                self.send_response(400)
                self._send_json_headers(cors_headers)
                response = {
                    'success': False,
                    'error': 'Invalid video ID. YouTube video IDs are typically 11 characters.',
                    'videoId': video_id
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Handle list transcripts endpoint
            if is_list_endpoint:
                try:
                    api = create_youtube_api()
                    transcript_list = api.list(video_id)
                    available_langs = []
                    
                    # transcript_list is iterable (TranscriptList object)
                    for transcript in transcript_list:
                        available_langs.append({
                            'language': transcript.language,
                            'languageCode': transcript.language_code,
                            'isGenerated': transcript.is_generated,
                            'isTranslatable': transcript.is_translatable
                        })
                    
                    self.send_response(200)
                    self._send_json_headers(cors_headers)
                    response = {
                        'success': True,
                        'videoId': video_id,
                        'availableLanguages': available_langs
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                    
                except VideoUnavailable:
                    self.send_response(404)
                    self._send_json_headers(cors_headers)
                    response = {
                        'success': False,
                        'error': 'Video is unavailable or does not exist',
                        'videoId': video_id
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                except Exception as e:
                    self.send_response(500)
                    self._send_json_headers(cors_headers)
                    response = {
                        'success': False,
                        'error': str(e),
                        'videoId': video_id
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
            
            # Handle fetch transcript endpoint
            try:
                # Try to fetch transcript in requested language (using fetch method as in original server.py)
                api = create_youtube_api()
                transcript_result = api.fetch(video_id, languages=[lang])
                
                # Convert to list (fetch returns an iterable)
                transcript_list = list(transcript_result)
                
                # Extract text (items have .text attribute)
                transcript_text = ' '.join([item.text for item in transcript_list])
                
                self.send_response(200)
                self._send_json_headers(cors_headers)
                response = {
                    'success': True,
                    'videoId': video_id,
                    'transcript': transcript_text,
                    'length': len(transcript_text),
                    'snippets': len(transcript_list),
                    'language': lang
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
            except (RequestBlocked, IpBlocked) as block_error:
                # Handle IP blocking with helpful error message
                self.send_response(503)
                self._send_json_headers(cors_headers)
                response = {
                    'success': False,
                    'error': 'YouTube is blocking requests from this IP address.',
                    'videoId': video_id,
                    'details': 'Configure a proxy using PROXY_URL environment variable in Vercel to work around this limitation.',
                    'solution': 'Set PROXY_URL=http://your-proxy:port in Vercel project settings > Environment Variables'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
            except NoTranscriptFound:
                # Try to fetch any available transcript
                try:
                    api = create_youtube_api()
                    transcript_result = api.fetch(video_id)
                    transcript_list = list(transcript_result)
                    
                    # Extract text (items have .text attribute)
                    transcript_text = ' '.join([item.text for item in transcript_list])
                    
                    self.send_response(200)
                    self._send_json_headers(cors_headers)
                    response = {
                        'success': True,
                        'videoId': video_id,
                        'transcript': transcript_text,
                        'length': len(transcript_text),
                        'snippets': len(transcript_list),
                        'language': 'auto'
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                except Exception as e2:
                    self.send_response(404)
                    self._send_json_headers(cors_headers)
                    response = {
                        'success': False,
                        'error': 'No transcript found for this video',
                        'videoId': video_id,
                        'details': 'This video may not have captions enabled.'
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                    
            except TranscriptsDisabled:
                self.send_response(403)
                self._send_json_headers(cors_headers)
                response = {
                    'success': False,
                    'error': 'Transcripts are disabled for this video',
                    'videoId': video_id
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
            except VideoUnavailable:
                self.send_response(404)
                self._send_json_headers(cors_headers)
                response = {
                    'success': False,
                    'error': 'Video is unavailable or does not exist',
                    'videoId': video_id
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
        except Exception as e:
            # Catch any unexpected errors to prevent function crashes
            self.send_response(500)
            self._send_json_headers({
                'Access-Control-Allow-Origin': '*',
            })
            response = {
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if str(e) else 'Unknown error'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _send_json_headers(self, extra_headers=None):
        """Send JSON content type and additional headers"""
        self.send_header('Content-Type', 'application/json')
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging to prevent errors in serverless environment"""
        pass
