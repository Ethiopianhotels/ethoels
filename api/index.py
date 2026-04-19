from flask import Flask, jsonify, request
import requests
import time

app = Flask(__name__)

APIFY_TOKEN = "apify_api_03O5zHQhiFTNd06cHBwYopWKExAZ4R4CC9dG"

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', 'Addis Ababa hotels')
    
    try:
        start_url = f"https://api.apify.com/v2/acts/apify~google-maps-scraper/runs?token={APIFY_TOKEN}"
        payload = {
            "startUrls": [{"url": f"https://www.google.com/maps/search/{query}"}],
            "maxReviews": 5,
            "scrapeReviews": True,
            "maxCrawledPlaces": 6
        }
        
        response = requests.post(start_url, json=payload)
        run_id = response.json()['data']['id']
        
        for i in range(5):
            time.sleep(2)
            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            status_res = requests.get(status_url)
            status_data = status_res.json()
            
            if status_data['data']['status'] == 'SUCCEEDED':
                dataset_id = status_data['data']['defaultDatasetId']
                break
            elif status_data['data']['status'] == 'FAILED':
                return jsonify({"error": "Apify scraping failed"}), 500
        else:
            return jsonify({"error": "Timeout - please try again"}), 408
        
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&limit=10"
        items = requests.get(dataset_url).json()
        
        hotels = []
        for item in items:
            hotel = {
                "name": item.get("title", "Unknown Hotel"),
                "address": item.get("address", "Address not available"),
                "rating": item.get("stars", 0),
                "reviewsCount": item.get("reviewsCount", 0),
                "image": item.get("image", ""),
                "reviews": []
            }
            
            for rev in item.get("reviews", [])[:5]:
                hotel["reviews"].append({
                    "author": rev.get("name", "Anonymous"),
                    "rating": rev.get("stars", 0),
                    "text": rev.get("text", "No review text"),
                    "date": rev.get("publishedAtDate", "Recent")
                })
            
            hotels.append(hotel)
        
        return jsonify(hotels)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

app = app

if __name__ == '__main__':
    app.run()
