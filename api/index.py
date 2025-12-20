from flask import Flask, jsonify, request
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

app = Flask(__name__)

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response

# Health check endpoint
@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'ok',
        'message': 'YouTube Transcript API is running'
    })

# Fetch transcript endpoint
@app.route('/transcript/<video_id>', methods=['GET', 'OPTIONS'])
def get_transcript(video_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    lang = request.args.get('lang', 'en')
    
    print(f'📹 [API] Fetching transcript for video: {video_id}')
    print(f'📹 [API] Requested language: {lang}')
    
    # Validate video ID
    if not video_id or len(video_id) < 10:
        print(f'❌ [API] Invalid video ID: {video_id}')
        return jsonify({
            'success': False,
            'error': 'Invalid video ID. YouTube video IDs are typically 11 characters.',
            'videoId': video_id
        }), 400
    
    try:
        # Fetch transcript - try requested language first
        print(f'📡 [API] Calling YouTubeTranscriptApi.fetch...')
        api = YouTubeTranscriptApi()
        transcript_result = api.fetch(video_id, languages=[lang])
        
        transcript_list = list(transcript_result)
        transcript_text = ' '.join([item.text for item in transcript_list])
        
        print(f'✅ [API] Successfully fetched transcript: {len(transcript_text)} characters')
        
        return jsonify({
            'success': True,
            'videoId': video_id,
            'transcript': transcript_text,
            'length': len(transcript_text),
            'snippets': len(transcript_list)
        })
        
    except NoTranscriptFound as e:
        print(f'⚠️ [API] No transcript found in {lang}, trying any available language...')
        try:
            api = YouTubeTranscriptApi()
            transcript_result = api.fetch(video_id)
            transcript_list = list(transcript_result)
            transcript_text = ' '.join([item.text for item in transcript_list])
            
            print(f'✅ [API] Fetched transcript in alternative language: {len(transcript_text)} characters')
            
            return jsonify({
                'success': True,
                'videoId': video_id,
                'transcript': transcript_text,
                'length': len(transcript_text),
                'snippets': len(transcript_list),
                'language': 'auto'
            })
        except Exception as e2:
            print(f'❌ [API] Fallback also failed: {str(e2)}')
            return jsonify({
                'success': False,
                'error': f'No transcript found. Original error: {str(e)}',
                'videoId': video_id,
                'details': 'This video may not have captions enabled.'
            }), 500
            
    except TranscriptsDisabled:
        print(f'❌ [API] Transcripts are disabled for this video')
        return jsonify({
            'success': False,
            'error': 'Transcripts are disabled for this video',
            'videoId': video_id
        }), 500
        
    except VideoUnavailable:
        print(f'❌ [API] Video is unavailable')
        return jsonify({
            'success': False,
            'error': 'Video is unavailable or does not exist',
            'videoId': video_id
        }), 500
        
    except Exception as e:
        print(f'❌ [API] Unexpected error: {str(e)}')
        import traceback
        print(f'📚 [API] Traceback: {traceback.format_exc()}')
        return jsonify({
            'success': False,
            'error': str(e),
            'videoId': video_id,
            'details': 'Make sure the video has captions enabled and is publicly accessible.'
        }), 500

# List available transcripts endpoint
@app.route('/transcript/<video_id>/list', methods=['GET', 'OPTIONS'])
def list_transcripts(video_id):
    if request.method == 'OPTIONS':
        return '', 200
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
        
        return jsonify({
            'success': True,
            'videoId': video_id,
            'availableLanguages': available_langs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'videoId': video_id
        }), 500

# Vercel Python handler - simplified version
def handler(req):
    """
    Vercel serverless function handler
    req is a dict with 'path', 'method', 'headers', 'query', 'body'
    """
    import io
    from urllib.parse import urlencode
    
    # Extract request info
    method = req.get('method', 'GET')
    path = req.get('path', '/')
    query = req.get('query', {})
    headers = req.get('headers', {})
    
    # Build query string
    query_string = urlencode(query) if query else ''
    
    # Create WSGI environ dict
    environ = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'CONTENT_TYPE': headers.get('content-type', ''),
        'CONTENT_LENGTH': headers.get('content-length', '0'),
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': io.BytesIO(),
        'wsgi.errors': io.StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add HTTP headers
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Create a response object to capture Flask's response
    response_headers = []
    response_status = [200]
    response_body = []
    
    def start_response(status, headers):
        response_status[0] = int(status.split()[0])
        response_headers.extend(headers)
    
    # Call Flask app as WSGI application
    try:
        response_iter = app(environ, start_response)
        response_body = [b''.join(response_iter).decode('utf-8')]
    except Exception as e:
        import traceback
        print(f'❌ [Handler] Error: {str(e)}')
        print(f'📚 [Handler] Traceback: {traceback.format_exc()}')
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
    
    # Convert headers to dict
    headers_dict = {}
    for header in response_headers:
        headers_dict[header[0]] = header[1]
    
    return {
        'statusCode': response_status[0],
        'headers': headers_dict,
        'body': response_body[0] if response_body else ''
    }

