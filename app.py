import math
import os
from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv

# Load local environment keys from your .env file
load_dotenv()

app = Flask(__name__)

# Securely grab your API configurations
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_ACTUAL_API_KEY")
GOOGLE_CX = os.environ.get("GOOGLE_CX", "YOUR_SEARCH_ENGINE_ID")

def fetch_google_search(query, start_index=1, per_page=25):
    """
    Queries the official Google Custom Search API.
    Returns live web results, descriptions, and media types.
    """
    url = "https://googleapis.com"
    
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": min(per_page, 10),  # Google API allows a maximum of 10 items per single API call
        "start": start_index       # Controls pagination offset (e.g., item #11 starts Page 2)
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"Google API Error: {response.status_code} - {response.text}")
            return {"items": [], "total_results": 0}
            
        data = response.json()
        search_items = data.get("items", [])
        
        # Extract total results safely from Google's response metadata
        total_results = int(data.get("searchInformation", {}).get("totalResults", 0))
        
        parsed_results = []
        for item in search_items:
            title = item.get("title")
            href = item.get("link")
            body = item.get("snippet", "")
            
            media_type = None
            media_url = None
            
            # --- LIVE YOUTUBE EMBED PARSING ---
            # If Google returns a YouTube link, extract the ID to automatically render the iframe!
            if "youtube.com" in href or "youtu.be" in href:
                media_type = "youtube"
                if "v=" in href:
                    video_id = href.split("v=")[1].split("&")[0]
                    media_url = f"https://youtube.com{video_id}"
                elif "youtu.be/" in href:
                    video_id = href.split("youtu.be/")[1].split("?")[0]
                    media_url = f"https://youtube.com{video_id}"
            
            # General file extensions handling
            elif href.lower().endswith(('.mp3', '.ogg', '.wav')):
                media_type = "audio"
                media_url = href
            elif href.lower().endswith(('.mp4', '.webm')):
                media_type = "video_file"
                media_url = href

            parsed_results.append({
                'title': title,
                'href': href,
                'body': body,
                'media_type': media_type,
                'media_url': media_url
            })
            
        return {"items": parsed_results, "total_results": total_results}
        
    except Exception as e:
        print(f"Network processing exception: {e}")
        return {"items": [], "total_results": 0}

@app.route('/', methods=['GET'])
def search_page():
    query = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
        
    # Standardise rows per page to match Google's optimal performance layout
    per_page = 10 

    results = []
    total_pages = 0
    total_items = 0
    current_start = 0
    current_end = 0

    if query:
        # Calculate Google's specific item offset (Page 1 = 1, Page 2 = 11, Page 3 = 21)
        api_start_index = ((page - 1) * per_page) + 1
        
        # Request live elements from Google
        search_package = fetch_google_search(query, start_index=api_start_index, per_page=per_page)
        
        results = search_package["items"]
        total_items = search_package["total_results"]
        
        # Google limits custom web queries to the first 100 results maximum (10 pages)
        if total_items > 100:
            total_items = 100
            
        if total_items > 0:
            total_pages = math.ceil(total_items / per_page)
            current_start = api_start_index
            current_end = min(api_start_index + len(results) - 1, total_items)

    return render_template('search.html', query=query, results=results, page=page, 
                           per_page=per_page, total_pages=total_pages, total_items=total_items,
                           current_start=current_start, current_end=current_end)

if __name__ == '__main__':
    app.run(debug=False)
