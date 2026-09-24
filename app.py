import math
import os
from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Fetch environment values
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CX = os.environ.get("GOOGLE_CX")

def fetch_google_search(query, start_index=1):
    """
    Connects to Google JSON API and safely intercepts setup failures or proxy errors.
    """
    # Defensive programming block: Alert developer if variables are missing
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return {
            "items": [], 
            "total_results": 0, 
            "error_msg": "Missing API Key or Search Engine ID inside your Render Environment Settings tab."
        }

    url = "https://googleapis.com"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 10,
        "start": start_index
    }
    
    try:
        response = requests.get(url, params=params, timeout=8)
        
        # Capture authorization blocks or billing validation errors safely
        if response.status_code != 200:
            return {
                "items": [], 
                "total_results": 0, 
                "error_msg": f"Google Server rejected request with Status Code: {response.status_code}. Verify credentials."
            }
            
        data = response.json()
        search_items = data.get("items", [])
        total_results = int(data.get("searchInformation", {}).get("totalResults", 0))
        
        parsed_results = []
        for item in search_items:
            title = item.get("title")
            href = item.get("link")
            body = item.get("snippet", "")
            
            media_type = None
            media_url = None
            
            # Auto-extract active YouTube video parameters safely
            if "youtube.com" in href or "youtu.be" in href:
                media_type = "youtube"
                if "v=" in href:
                    video_id = href.split("v=")[1].split("&")[0]
                    media_url = f"https://youtube.com{video_id}"
                elif "youtu.be/" in href:
                    video_id = href.split("youtu.be/")[1].split("?")[0]
                    media_url = f"https://youtube.com{video_id}"
            
            parsed_results.append({
                'title': title,
                'href': href,
                'body': body,
                'media_type': media_type,
                'media_url': media_url
            })
            
        return {"items": parsed_results, "total_results": total_results, "error_msg": None}
        
    except Exception as e:
        return {"items": [], "total_results": 0, "error_msg": f"Connection exception: {str(e)}"}

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
    error_message = None

    if query:
        api_start_index = ((page - 1) * per_page) + 1
        
        search_package = fetch_google_search(query, start_index=api_start_index)

        response = requests.get(url, params=params, timeout=8)
        
        # Enhanced logging block to see Google's exact feedback
        if response.status_code != 200:
            try:
                error_details = response.json().get("error", {}).get("message", "No clear message provided.")
                print(f"--- GOOGLE REJECTION TRACE ---")
                print(f"Status Code: {response.status_code}")
                print(f"Reason: {error_details}")
                print(f"------------------------------")
                return {"items": [], "total_results": 0, "error_msg": f"Google Server error ({response.status_code}): {error_details}"}
            except Exception:
                return {"items": [], "total_results": 0, "error_msg": f"Google Server rejected request with Status Code: {response.status_code}."}
        # END Enhanced logging block

        results = search_package["items"]
        total_items = search_package["total_results"]
        error_message = search_package["error_msg"]
        
        if total_items > 100:
            total_items = 100 # Google API max standard pagination restriction capping limit
            
        if total_items > 0:
            total_pages = math.ceil(total_items / per_page)
            current_start = api_start_index
            current_end = min(api_start_index + len(results) - 1, total_items)
        elif not error_message and total_items == 0:
            error_message = "Google returned zero results. Make sure 'Search the entire web' is turned ON in your Google control panel."

    return render_template('search.html', query=query, results=results, page=page, 
                           per_page=per_page, total_pages=total_pages, total_items=total_items,
                           current_start=current_start, current_end=current_end, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=False)
