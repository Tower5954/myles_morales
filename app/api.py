# app/api.py
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import sys
import json

# Import existing modules
from contact_finder import ContactFinder
from bulk_contact_finder import BulkContactFinder
from contact_evaluator import ContactEvaluator

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
# Enable CORS for cross-origin requests during development
CORS(app)  

# Initialise with config path just like in main.py
config_path = "../config.json"  
contact_finder = ContactFinder(config_path)
bulk_finder = BulkContactFinder(config_path, "../contact_search_results")  # Specify the full path to match where files are saved

# Initialise prowler
evaluator = ContactEvaluator(config_path)

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

@app.route('/api/bulk', methods=['POST'])
def api_bulk_search():
    data = request.json
    names = data.get('names', [])
    query = data.get('query', 'contact details')
    
    try:
        # Always use evaluation with bulk search - pass the evaluator directly
        filename = bulk_finder.bulk_search(names, query, prowler=evaluator)
        
        # For clarity in logs
        print(f"Bulk search completed with automatic evaluation, file saved at: {filename}")
        
        # Return the full file path (we'll use this in the frontend)
        return jsonify({
            'success': True, 
            'message': f"Bulk search completed with evaluation. Results are ready to download.",
            'filepath': filename  # Return the full file path
        })
    except Exception as e:
        print(f"Error in bulk search: {str(e)}")
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
    # Setup the prowler model when the application starts
    try:
        evaluator.setup()
        print("Prowler AI model has been set up successfully.")
    except Exception as e:
        print(f"Warning: Failed to set up Prowler AI model: {e}")
        print("Evaluation functionality may not work until the model is set up.")
        
    app.run(debug=True, port=5000)