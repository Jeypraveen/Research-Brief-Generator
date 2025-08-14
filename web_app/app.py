import json
import time
import uuid
from flask import Flask, render_template, request, jsonify, session
from werkzeug.exceptions import BadRequest

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.workflow import workflow
from src.config import config

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'research-brief-generator-secret-key-change-in-production')

@app.route('/')
def index():
    """Main page with the research brief form."""
    return render_template('index.html')

@app.route('/brief/<brief_id>')
def view_brief(brief_id):
    """View a specific brief by ID."""
    # In a real application, you'd fetch the brief from a database
    # For now, we'll redirect to the main page
    return render_template('brief.html', brief_id=brief_id)

@app.route('/generate', methods=['POST'])
def generate_brief():
    """Generate a research brief via AJAX."""
    try:
        # Get form data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        topic = data.get('topic', '').strip()
        depth = int(data.get('depth', 3))
        follow_up = data.get('follow_up', False)
        user_id = session.get('user_id', 'anonymous')
        
        # Validate input
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
            
        if not (1 <= depth <= 5):
            return jsonify({'error': 'Depth must be between 1 and 5'}), 400
        
        # Generate thread ID for this session
        thread_id = str(uuid.uuid4())
        session['current_thread_id'] = thread_id
        
        start_time = time.time()
        
        # Execute workflow
        result = workflow.run(
            topic=topic,
            depth=depth,
            follow_up=follow_up,
            user_id=user_id,
            thread_id=thread_id
        )
        
        processing_time = time.time() - start_time
        
        # Check if workflow completed successfully
        if not result.get('success', False):
            error_message = result.get('error', 'Unknown workflow error')
            return jsonify({
                'success': False,
                'error': error_message,
                'processing_time': processing_time
            }), 500
        
        # Extract the final brief
        final_brief = result.get('final_brief')
        if not final_brief:
            return jsonify({
                'success': False,
                'error': 'No brief generated',
                'processing_time': processing_time
            }), 500
        
        # Convert Pydantic model to dict for JSON response
        if hasattr(final_brief, 'dict'):
            brief_dict = final_brief.dict()
        else:
            brief_dict = final_brief
        
        return jsonify({
            'success': True,
            'brief': brief_dict,
            'processing_time': processing_time,
            'thread_id': thread_id
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'success': False
        }), 500

@app.route('/stream/<thread_id>')
def stream_generation(thread_id):
    """Stream the generation process (Server-Sent Events)."""
    def generate_events():
        try:
            # Get parameters from session or request args
            topic = request.args.get('topic', '')
            depth = int(request.args.get('depth', 3))
            follow_up = request.args.get('follow_up', 'false').lower() == 'true'
            user_id = session.get('user_id', 'anonymous')
            
            if not topic:
                yield f"data: {json.dumps({'error': 'No topic provided'})}\\n\\n"
                return
            
            # Stream the workflow execution
            for step in workflow.stream_run(
                topic=topic,
                depth=depth,
                follow_up=follow_up,
                user_id=user_id,
                thread_id=thread_id
            ):
                # Send step update to client
                step_data = {
                    'step': step,
                    'timestamp': time.time()
                }
                yield f"data: {json.dumps(step_data, default=str)}\\n\\n"
                
        except Exception as e:
            error_data = {
                'error': str(e),
                'timestamp': time.time()
            }
            yield f"data: {json.dumps(error_data)}\\n\\n"
    
    return app.response_class(
        generate_events(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache'}
    )

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        is_configured = config.validate_config()
        
        return jsonify({
            'status': 'healthy' if is_configured else 'configuration_error',
            'timestamp': time.time(),
            'configuration': {
                'gemini_api_configured': bool(config.GEMINI_API_KEY or config.GOOGLE_API_KEY),
                'model': config.GEMINI_MODEL
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/config')
def get_config():
    """Get client-safe configuration."""
    return jsonify({
        'model': config.GEMINI_MODEL,
        'max_search_results': config.MAX_SEARCH_RESULTS,
        'max_retries': config.MAX_CONTEXT_SUMMARIZATION_ATTEMPTS,
        'api_configured': config.validate_config()
    })

@app.before_request
def before_request():
    """Set up session for each request."""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'success': False
    }), 500

if __name__ == '__main__':
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )