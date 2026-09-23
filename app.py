import math
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# A public, machine-ready meta-search index instance that accepts data centre traffic
SEARXNG_INSTANCE = "https://crit.ch"

def fetch_live_media_search(query):
    """
    Queries an open meta-search engine to find live video and audio matches
    across YouTube, SoundCloud, and other streaming websites.
    """
    params = {
        "q": query,
        "format": "json",
        "categories": "videos,music", # Limit results specifically to media streams
        "pageno": 1
    }
    
    headers = {
        "User-Agent": "MediaSearchDashboard/2.0 (contact: admin@example.com; Educational Application)"
    }
    
    try:
        # Request data from the meta-search aggregator
        response = requests.get(SEARXNG_INSTANCE, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
            
        data = response.json()
        raw_results = data.get("results", [])
        
        parsed_results = []
        for item in raw_results:
            title = item.get("title", "")
            href = item.get("url", "#")
            body = item.get("content", "No description available.")
            
            media_type = None
            media_url = None
            
            # --- DETECT MEDIA PLATFORMS & EXTRACT EMBED PARAMS ---
            # 1. YouTube Video Context Handling
            if "youtube.com" in href or "youtu.be" in href:
                media_type = "youtube"
                # Convert a standard watch URL into an embeddable format
                if "v=" in href:
                    video_id = href.split("v=")[1].split("&")[0]
                    media_url = f"https://youtube.com{video_id}"
                elif "youtu.be/" in href:
                    video_id = href.split("youtu.be/")[1].split("?")[0]
                    media_url = f"https://youtube.com{video_id}"
            
            # 2. General Audio / Podcast File Stream Handling
            elif any(ext in href.lower() or ext in body.lower() for ext in [".mp3", ".ogg", "soundcloud", "podcast"]):
                media_type = "audio"
                # If an explicit file path isn't exposed, use a stable public domain testing fallback track
                media_url = item.get("audio_link", "https://soundhelix.com")
            
            # 3. Alternative Video Handling (Vimeo, Dailymotion, etc.)
            elif any(ext in href.lower() for ext in ["vimeo.com", "dailymotion.com", ".mp4"]):
                media_type = "video_file"
                media_url = href if href.endswith(".mp4") else "https://googleapis.com"

            parsed_results.append({
                'title': title,
                'href': href,
                'body': body,
                'media_type': media_type,
                'media_url': media_url
            })
            
        return parsed_results
    except Exception as e:
        print(f"Meta-Search Engine error: {e}")
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
