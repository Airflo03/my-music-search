import math
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def fetch_live_search(query):
    """
    Fetches real-time web articles from an open machine index.
    Includes a unique User-Agent string to satisfy Wikipedia's robot security block.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 100
    }
    
    # CRITICAL FIX: Tell Wikipedia who is making the request to avoid a 403 Block
    headers = {
        "User-Agent": "MyFlaskScraperApp/1.0 (contact: your-email@example.com; educational school project)"
    }
    
    try:
        # Pass the headers parameter explicitly
        response = requests.get(url, params=params, headers=headers, timeout=8)
        
        # This will print the actual error code inside your Render log explorer if it fails
        if response.status_code != 200:
            print(f"Server returned HTTP Error Status: {response.status_code}")
            return []
            
        data = response.json()
        search_items = data.get("query", {}).get("search", [])
        
        parsed_results = []
        for item in search_items:
            title = item.get("title")
            href = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            body = item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
            
            parsed_results.append({
                'title': title,
                'href': href,
                'body': body + "..."
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
