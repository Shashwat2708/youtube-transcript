import json
import urllib.parse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

def handler(req):
    """
    Vercel Python serverless function handler
    req is a dict with 'path', 'method', 'headers', 'query', 'body'
    """
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    # Handle OPTIONS request
    method = req.get('method', 'GET')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Parse path
    path = req.get('path', '/')
    query = req.get('query', {})
    
    # Health check
    if path == '/health' or path.endswith('/health'):
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'ok',
                'message': 'YouTube Transcript API is running'
            })
        }
    
    # Extract video ID from path
    # Path format: /transcript/{videoId} or /transcript/{videoId}/list
    path_parts = [p for p in path.split('/') if p]
    
    if len(path_parts) < 2 or path_parts[0] != 'transcript':
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Not Found'
            })
        }
    
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
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'videoId': video_id,
                    'availableLanguages': available_langs
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'videoId': video_id
                })
            }
    
    # Fetch transcript endpoint
    lang = query.get('lang', 'en') if isinstance(query.get('lang'), str) else (query.get('lang', ['en'])[0] if query.get('lang') else 'en')
    
    print(f'📹 [API] Fetching transcript for video: {video_id}')
    print(f'📹 [API] Requested language: {lang}')
    
    # Validate video ID
    if not video_id or len(video_id) < 10:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Invalid video ID. YouTube video IDs are typically 11 characters.',
                'videoId': video_id
            })
        }
    
    try:
        # Fetch transcript - try requested language first
        print(f'📡 [API] Calling YouTubeTranscriptApi.fetch...')
        api = YouTubeTranscriptApi()
        transcript_result = api.fetch(video_id, languages=[lang])
        
        transcript_list = list(transcript_result)
        transcript_text = ' '.join([item.text for item in transcript_list])
        
        print(f'✅ [API] Successfully fetched transcript: {len(transcript_text)} characters')
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'videoId': video_id,
                'transcript': transcript_text,
                'length': len(transcript_text),
                'snippets': len(transcript_list)
            })
        }
        
    except NoTranscriptFound as e:
        print(f'⚠️ [API] No transcript found in {lang}, trying any available language...')
        try:
            api = YouTubeTranscriptApi()
            transcript_result = api.fetch(video_id)
            transcript_list = list(transcript_result)
            transcript_text = ' '.join([item.text for item in transcript_list])
            
            print(f'✅ [API] Fetched transcript in alternative language: {len(transcript_text)} characters')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'videoId': video_id,
                    'transcript': transcript_text,
                    'length': len(transcript_text),
                    'snippets': len(transcript_list),
                    'language': 'auto'
                })
            }
        except Exception as e2:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': f'No transcript found. Original error: {str(e)}',
                    'videoId': video_id,
                    'details': 'This video may not have captions enabled.'
                })
            }
            
    except TranscriptsDisabled:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Transcripts are disabled for this video',
                'videoId': video_id
            })
        }
        
    except VideoUnavailable:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Video is unavailable or does not exist',
                'videoId': video_id
            })
        }
        
    except Exception as e:
        print(f'❌ [API] Unexpected error: {str(e)}')
        import traceback
        print(f'📚 [API] Traceback: {traceback.format_exc()}')
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'videoId': video_id,
                'details': 'Make sure the video has captions enabled and is publicly accessible.'
            })
        }

