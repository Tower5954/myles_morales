from flask import Flask, request, jsonify, send_from_directory, send_file, Response, stream_with_context
from flask_cors import CORS
import os
import sys
import json
import queue
import threading
import time
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description="Contact Finder API")
parser.add_argument("--config", default="../config.json", help="Path to config file")
args = parser.parse_args()

# Use config path from arguments
config_path = args.config
print(f"Loading configuration from: {config_path}")

# Import existing modules
from contact_finder import ContactFinder
from bulk_contact_finder import BulkContactFinder
from contact_evaluator import ContactEvaluator

from config_manager import ConfigManager
temp_config = ConfigManager(config_path)

# Get the model provider and force evaluator provider to match
model_provider = temp_config.get("model_provider", "ollama")
temp_config.set("evaluator_provider", model_provider)
print(f"Setting evaluator provider to match model provider: {model_provider}")


app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
# Enable CORS for cross-origin requests during development
CORS(app)  

# Initialise with config path just like in main.py
contact_finder = ContactFinder(config_path)
bulk_finder = BulkContactFinder(config_path, "../contact_search_results")
evaluator = ContactEvaluator(config_path)

# Create a dictionary to store progress queues for SSE
progress_queues = {}

@app.route('/api/find', methods=['POST'])
def api_find_contact():
    data = request.json
    query = data.get('query', '')
    url = data.get('url', None)
    
    try:
        if url:
            # If URL is provided, do deep scrape
            result = contact_finder.deep_scrape_url(url, query)
            urls = [url]
        else:
            # Otherwise do initial search
            result, urls = contact_finder.initial_search(query)
        
        response_data = {
            'text': result,
            'urls': urls
        }
        
        # AUTOMATIC EVALUATION - Always evaluate results
        try:
            # Get evaluation from prowler_ai
            evaluation = evaluator._evaluate_contact_info(result, query, urls)
            
            # Format simplified response
            simplified = evaluator._format_simplified_results(result, evaluation)
            
            # Add evaluation data to response
            response_data['evaluation'] = evaluation
            response_data['simplified'] = simplified
        except Exception as eval_err:
            print(f"Evaluation error: {str(eval_err)}")
            # Don't fail the whole request if evaluation fails
            response_data['evaluation_error'] = str(eval_err)
        
        return jsonify({'success': True, 'results': response_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# New endpoint for SSE progress updates
@app.route('/api/progress-stream/<request_id>', methods=['GET'])
def progress_stream(request_id):
    """Endpoint for SSE progress updates"""
    def generate():
        if request_id not in progress_queues:
            yield f"data: {json.dumps({'error': 'Invalid request ID'})}\n\n"
            return
            
        q = progress_queues[request_id]
        
        # Send an initial event
        yield f"data: {json.dumps({'status': 'connected'})}\n\n"
        
        while True:
            try:
                # Get progress update from the queue with a short timeout
                progress_data = q.get(timeout=0.5)
                
                # If we received a "DONE" signal, end the stream
                if progress_data == "DONE":
                    yield f"data: {json.dumps({'status': 'complete'})}\n\n"
                    break
                
                # Otherwise, send the progress update
                yield f"data: {json.dumps(progress_data)}\n\n"
                
            except queue.Empty:
                # Send an empty keep-alive message
                yield f": keepalive\n\n"
            except Exception as e:
                print(f"Error in SSE: {str(e)}")
                break
        
        # Clean up when done
        if request_id in progress_queues:
            del progress_queues[request_id]
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # Disable buffering in Nginx
        }
    )

@app.route('/api/bulk', methods=['POST'])
def api_bulk_search():
    data = request.json
    names = data.get('names', [])
    query = data.get('query', 'contact details')
    
    # Generate a unique request ID
    request_id = str(int(time.time()))
    
    # Create a queue for this request's progress updates
    progress_queues[request_id] = queue.Queue()
    
    # Create a simple dictionary to track progress
    progress_tracker = {name: False for name in names}
    
    try:
        # Define a progress callback that updates our tracker
        def progress_callback(company_name):
            progress_tracker[company_name] = True
            print(f"Updated progress for {company_name}: {progress_tracker}")
            
            # Send update through the SSE queue
            progress_queues[request_id].put({
                'companyName': company_name,
                'progress': progress_tracker
            })
        
        # Start the bulk search in a separate thread
        def run_bulk_search():
            try:
                # Pass the callback to bulk_finder
                filename = bulk_finder.bulk_search(
                    names, 
                    query, 
                    prowler=evaluator,
                    progress_callback=progress_callback
                )
                
                # Signal that search is complete
                progress_queues[request_id].put("DONE")
                
                print(f"Bulk search completed with automatic evaluation, file saved at: {filename}")
            except Exception as e:
                print(f"Error in bulk search thread: {str(e)}")
                if request_id in progress_queues:
                    progress_queues[request_id].put({
                        'error': str(e)
                    })
                    progress_queues[request_id].put("DONE")
        
        # Start the thread
        thread = threading.Thread(target=run_bulk_search)
        thread.daemon = True
        thread.start()
        
        # Immediately return the request ID so client can connect to progress stream
        return jsonify({
            'success': True, 
            'message': f"Bulk search started. Connect to progress stream for updates.",
            'requestId': request_id,
            'progress': progress_tracker  # Return the initial progress state
        })
    except Exception as e:
        print(f"Error setting up bulk search: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/evaluate', methods=['POST'])
def api_evaluate_result():
    data = request.json
    result_text = data.get('text', '')
    business_name = data.get('business_name', '')
    urls = data.get('urls', [])
    
    try:
        # Evaluate the result
        evaluation = evaluator._evaluate_contact_info(result_text, business_name, urls)
        
        # Format simplified response
        simplified = evaluator._format_simplified_results(result_text, evaluation)
        
        return jsonify({
            'success': True,
            'evaluation': evaluation,
            'simplified': simplified
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/saved-searches', methods=['GET'])
def get_saved_searches():
    try:
        search_dir = '../contact_search_results'
        if not os.path.exists(search_dir):
            return jsonify({'success': True, 'searches': []})
            
        files = [f for f in os.listdir(search_dir) if f.endswith('.csv')]
        return jsonify({'success': True, 'searches': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
        
    try:
        filepath = os.path.join('../uploads', file.filename)
        os.makedirs('../uploads', exist_ok=True)
        file.save(filepath)
        
        # Process the file if it's a list of companies
        if file.filename.endswith('.txt'):
            with open(filepath, 'r') as f:
                companies = [line.strip() for line in f if line.strip()]
            
            return jsonify({
                'success': True, 
                'message': f'File uploaded with {len(companies)} companies',
                'companies': companies
            })
        
        return jsonify({'success': True, 'message': 'File uploaded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Serve React frontend in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
    

@app.route('/api/direct-download/<path:filename>', methods=['GET'])
def direct_download(filename):
    try:
        # Get the absolute path of the file
        # For simplicity, just look for the filename in the contact_search_results directory
        files = []
        search_dir = os.path.abspath('../contact_search_results')
        
        if os.path.exists(search_dir):
            files = os.listdir(search_dir)
            
            # Find files that end with the requested filename
            matching_files = [f for f in files if f.endswith(filename)]
            
            if matching_files:
                # Use the first match
                full_path = os.path.join(search_dir, matching_files[0])
                return send_file(
                    full_path, 
                    as_attachment=True,
                    download_name=matching_files[0],
                    mimetype='text/csv'
                )
        
        # If we get here, file wasn't found
        return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        print(f"Error in direct_download: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/setup-models', methods=['POST'])
def setup_models():
    try:
        # Set up both models
        success = evaluator.setup()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully set up miles_ai and prowler_ai models'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to set up one or both models'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)