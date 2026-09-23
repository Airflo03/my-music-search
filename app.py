import math
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def fetch_live_search(query):
    url = "https://wikipedia.org"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 500
    }
    headers = {
        "User-Agent": "MyFlaskScraperApp/1.0 (contact: your-email@example.com; educational school project)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        if response.status_code != 200:
            return []
            
        data = response.json()
        search_items = data.get("query", {}).get("search", [])
        
        parsed_results = []
        for idx, item in enumerate(search_items):
            title = item.get("title")
            href = f"https://wikipedia.org{title.replace(' ', '_')}"
            body = item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
            
            # --- MEDIA DETECTION INITIALISATION ---
            media_type = None
            media_url = None
            
            # For testing: Let's automatically attach sample media links to the first few items
            # so you can instantly see and test the players without hunting for specific results!
            if idx == 0:
                media_type = "audio"
                media_url = "https://soundhelix.com" # Sample public MP3
            elif idx == 1:
                media_type = "video"
                media_url = "https://googleapis.com" # Sample public MP4
            
            # Real-world fallback: Check if the text actually mentions audio/video files
            elif any(ext in title.lower() or ext in body.lower() for ext in ['.mp3', 'audio', 'soundtrack', 'speech']):
                media_type = "audio"
                media_url = "https://soundhelix.com"
            elif any(ext in title.lower() or ext in body.lower() for ext in ['.mp4', 'video', 'documentary', 'film']):
                media_type = "video"
                media_url = "https://googleapis.com"
            # --------------------------------------

            parsed_results.append({
                'title': title,
                'href': href,
                'body': body + "...",
                'media_type': media_type,
                'media_url': media_url
            })
        return parsed_results
    except Exception as e:
        print(f"Network error tracing details: {e}")
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
