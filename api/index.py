from flask import Flask, jsonify, request
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

# Vercel serverless function handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

