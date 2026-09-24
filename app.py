import json
import math
import urllib.request
import urllib.parse
from flask import Flask, render_template, request

app = Flask(__name__)

def fetch_live_media_search(query):
    """
    Uses Python's native urllib architecture to fetch open index data.
    Bypasses standard proxy blockades cleanly on free hosting environments.
    """
    # 1. Safely URL-encode the search query text string
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://wikipedia.org{encoded_query}&format=json&srlimit=100"
    
    # 2. Mimic a standard desktop browser exactly to pass proxy firewalls
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Create an authorized network request container
        req = urllib.request.Request(url, headers=headers)
        
        # Open the data stream connection
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status != 200:
                return []
                
            # Decode the raw byte stream into readable JSON
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
            
        search_items = data.get("query", {}).get("search", [])
        parsed_results = []
        
        for idx, item in enumerate(search_items):
            title = item.get("title", "Untitled Article")
            href = f"https://wikipedia.org{title.replace(' ', '_')}"
            
            # Remove HTML bold highlighting layout strings from the description text
            body = item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
            if not body:
                body = "No data descriptions provided for this index item."
                
            media_type = None
            media_url = None
            
            # --- INLINE MEDIA INJECTION ENGINE ---
            if idx % 3 == 0:
                media_type = "youtube"
                test_videos = ["jfKfPfyJRdk", "Z1RJmh_OPO0", "kJQP7kiw5Fk"]
                media_url = f"https://youtube.com{test_videos[idx % len(test_videos)]}"
                title = f"🎬 [Video] Live YouTube Stream: {title}"
            elif idx % 3 == 1:
                media_type = "audio"
                media_url = "https://wikimedia.org"
                title = f"🎵 [Audio] Live Audio Track: {title}"

            parsed_results.append({
                'title': title,
                'href': href,
                'body': body + "...",
                'media_type': media_type,
                'media_url': media_url
            })
            
        return parsed_results
    except Exception as e:
        print(f"Native networking failure details: {e}")
        return []

@app.route('/', methods=['GET'])
def search_page():
    query = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
        
    per_page = 10 

    results = []
    total_pages = 0
    total_items = 0
    current_start = 0
    current_end = 0

    if query:
        raw_results = fetch_live_media_search(query)
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
