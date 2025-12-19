from flask import Flask, jsonify, request
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

PORT = 3000

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'YouTube Transcript API is running'
    })

# Fetch transcript endpoint
@app.route('/transcript/<video_id>', methods=['GET'])
def get_transcript(video_id):
    lang = request.args.get('lang', 'en')
    
    print(f'📹 [API] Fetching transcript for video: {video_id}')
    print(f'📹 [API] Video ID length: {len(video_id)}')
    print(f'📹 [API] Requested language: {lang}')
    
    # Validate video ID (YouTube IDs are typically 11 characters)
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
        
        # Convert to list of snippets
        transcript_list = list(transcript_result)
        print(f'📊 [API] Received {len(transcript_list)} transcript items')
        
        # Combine all transcript snippets into a single string
        transcript_text = ' '.join([item.text for item in transcript_list])
        
        print(f'✅ [API] Successfully fetched transcript: {len(transcript_text)} characters')
        print(f'📄 [API] Transcript preview (first 200 chars): {transcript_text[:200]}')
        
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
            # Try to get any available transcript
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
        
    except Exception as rate_limit_error:
        if '429' in str(rate_limit_error) or 'too many' in str(rate_limit_error).lower():
            print(f'❌ [API] Too many requests')
            return jsonify({
                'success': False,
                'error': 'Too many requests. Please try again later.',
                'videoId': video_id
            }), 429
        raise
        
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
@app.route('/transcript/<video_id>/list', methods=['GET'])
def list_transcripts(video_id):
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

if __name__ == '__main__':
    print(f'🚀 [API] Starting YouTube Transcript API server on http://localhost:{PORT}')
    print(f'📡 [API] Endpoints:')
    print(f'   GET /health - Health check')
    print(f'   GET /transcript/<videoId> - Fetch transcript')
    print(f'   GET /transcript/<videoId>?lang=en - Fetch transcript in specific language')
    print(f'   GET /transcript/<videoId>/list - List available transcripts')
    app.run(host='0.0.0.0', port=PORT, debug=True)

