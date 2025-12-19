from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # Parse URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Health check
        if path == '/health' or path.endswith('/health'):
            response = {
                'status': 'ok',
                'message': 'YouTube Transcript API is running'
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Extract video ID from path
        # Path format: /transcript/{videoId} or /transcript/{videoId}/list
        path_parts = [p for p in path.split('/') if p]
        
        if len(path_parts) < 2 or path_parts[0] != 'transcript':
            self.send_error(404, 'Not Found')
            return
        
        video_id = path_parts[1]
        is_list_endpoint = len(path_parts) > 2 and path_parts[2] == 'list'
        
        # List transcripts endpoint
        if is_list_endpoint:
            try:
                api = YouTubeTranscriptApi()
                transcript_list = api.list(video_id)
                available_langs = []
                
                for transcript in transcript_list:
                    available_langs.append({
                        'language': transcript.language,
                        'languageCode': transcript.language_code,
                        'isGenerated': transcript.is_generated,
                        'isTranslatable': transcript.is_translatable
                    })
                
                response = {
                    'success': True,
                    'videoId': video_id,
                    'availableLanguages': available_langs
                }
                self.wfile.write(json.dumps(response).encode())
                return
            except Exception as e:
                response = {
                    'success': False,
                    'error': str(e),
                    'videoId': video_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
        
        # Fetch transcript endpoint
        lang = query_params.get('lang', ['en'])[0]
        
        print(f'📹 [API] Fetching transcript for video: {video_id}')
        print(f'📹 [API] Requested language: {lang}')
        
        # Validate video ID
        if not video_id or len(video_id) < 10:
            response = {
                'success': False,
                'error': 'Invalid video ID. YouTube video IDs are typically 11 characters.',
                'videoId': video_id
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        try:
            # Fetch transcript - try requested language first
            print(f'📡 [API] Calling YouTubeTranscriptApi.fetch...')
            api = YouTubeTranscriptApi()
            transcript_result = api.fetch(video_id, languages=[lang])
            
            transcript_list = list(transcript_result)
            transcript_text = ' '.join([item.text for item in transcript_list])
            
            print(f'✅ [API] Successfully fetched transcript: {len(transcript_text)} characters')
            
            response = {
                'success': True,
                'videoId': video_id,
                'transcript': transcript_text,
                'length': len(transcript_text),
                'snippets': len(transcript_list)
            }
            self.wfile.write(json.dumps(response).encode())
            
        except NoTranscriptFound as e:
            print(f'⚠️ [API] No transcript found in {lang}, trying any available language...')
            try:
                api = YouTubeTranscriptApi()
                transcript_result = api.fetch(video_id)
                transcript_list = list(transcript_result)
                transcript_text = ' '.join([item.text for item in transcript_list])
                
                response = {
                    'success': True,
                    'videoId': video_id,
                    'transcript': transcript_text,
                    'length': len(transcript_text),
                    'snippets': len(transcript_list),
                    'language': 'auto'
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e2:
                response = {
                    'success': False,
                    'error': f'No transcript found. Original error: {str(e)}',
                    'videoId': video_id,
                    'details': 'This video may not have captions enabled.'
                }
                self.wfile.write(json.dumps(response).encode())
                
        except TranscriptsDisabled:
            response = {
                'success': False,
                'error': 'Transcripts are disabled for this video',
                'videoId': video_id
            }
            self.wfile.write(json.dumps(response).encode())
            
        except VideoUnavailable:
            response = {
                'success': False,
                'error': 'Video is unavailable or does not exist',
                'videoId': video_id
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f'❌ [API] Unexpected error: {str(e)}')
            response = {
                'success': False,
                'error': str(e),
                'videoId': video_id,
                'details': 'Make sure the video has captions enabled and is publicly accessible.'
            }
            self.wfile.write(json.dumps(response).encode())

