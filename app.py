from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import re

app = Flask(__name__)

def get_terabox_direct_link(shared_url):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    }
    session = requests.Session()
    response = session.get(shared_url, headers=headers)
    
    if response.status_code != 200:
        return None, f"Failed to fetch page, status code: {response.status_code}"

    soup = BeautifulSoup(response.text, 'html.parser')
    scripts = soup.find_all('script', type='application/json')

    for script in scripts:
        try:
            data = json.loads(script.string)
            def find_video_urls(obj):
                urls = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            urls.extend(find_video_urls(value))
                        elif isinstance(value, str):
                            if re.search(r'https?:\/\/.*\.(mp4|m3u8|ogg|webm)', value, re.I):
                                urls.append(value)
                elif isinstance(obj, list):
                    for item in obj:
                        urls.extend(find_video_urls(item))
                return urls

            video_urls = find_video_urls(data)
            if video_urls:
                return video_urls[0], None
        except (json.JSONDecodeError, TypeError):
            continue

    links = re.findall(r'https?:\/\/[^\s\'"]+\.(mp4|m3u8)', response.text, re.I)
    if links:
        return links[0], None

    return None, "No direct video URL found on the page."

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/api/get_video_link', methods=['POST'])
def get_video_link():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    direct_link, error = get_terabox_direct_link(url)
    if error:
        return jsonify({'error': error}), 400

    return jsonify({'video_url': direct_link})

if __name__ == '__main__':
    app.run(debug=True)
