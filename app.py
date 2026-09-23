import json
import math
import os
from flask import Flask, render_template, request

app = Flask(__name__)

# Track the absolute path to your curated media json file
JSON_PATH = os.path.join(os.path.dirname(__file__), 'media_data.json')

def fetch_live_search(query):
    """Parses local high-fidelity JSON arrays to safely simulate 500 rows with valid targets."""
    if not os.path.exists(JSON_PATH):
        return []
        
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        audio_items = data.get("audio", [])
        video_items = data.get("video", [])
        general_items = data.get("general", [])
        
        all_templates = audio_items + video_items + general_items
        parsed_results = []
        
        # Build 500 total elements using the valid templates
        for i in range(1, 501):
            # Rotate cleanly through the templates array
            template = all_templates[(i - 1) % len(all_templates)]
            
            parsed_results.append({
                'title': f"{template['title']} (Result #{i})",
                'href': template['href'], # Real working URL destination
                'body': f"[Query: {query}] {template['body']}",
                'media_type': template['media_type'],
                'media_url': template['media_url']
            })
        return parsed_results
    except Exception as e:
        print(f"File reading issue: {e}")
        return []

@app.route('/', methods=['GET'])
def search_page():
    query = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 25))
    except ValueError:
        per_page = 25

    results = []
    total_pages = 0
    total_items = 0
    current_start = 0
    current_end = 0

    if query:
        raw_results = fetch_live_search(query)
        total_items = len(raw_results)
        
        if total_items > 0:
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            results = raw_results[start_index:end_index]
            
            total_pages = math.ceil(total_items / per_page)
            current_start = start_index + 1
            current_end = min(end_index, total_items)

    return render_template('search.html', query=query, results=results, page=page, 
                           per_page=per_page, total_pages=total_pages, total_items=total_items,
                           current_start=current_start, current_end=current_end)

if __name__ == '__main__':
    app.run(debug=False)
