import math
from flask import Flask, render_template, request
from duckduckgo_search import DDGS # Works completely free on Render

app = Flask(__name__)
RESULTS_PER_PAGE = 25

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
        try:
            # Executes real-time live internet scraping effortlessly
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=100))
                total_items = len(raw_results)
                
                start_index = (page - 1) * per_page
                end_index = start_index + per_page
                results = raw_results[start_index:end_index]
                
                total_pages = math.ceil(total_items / per_page)
                current_start = start_index + 1
                current_end = min(end_index, total_items)
        except Exception as e:
            results = [{'title': 'Live Error', 'href': '#', 'body': f'Scraping failed: {str(e)}'}]

    return render_template('search.html', query=query, results=results, page=page, 
                           per_page=per_page, total_pages=total_pages, total_items=total_items,
                           current_start=current_start, current_end=current_end)

if __name__ == '__main__':
    app.run(debug=False)
