import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from jinja2 import Template

# GitHubの画面から入力された値を取得
SEARCH_QUERY = os.getenv('INPUT_QUERY', '龍が如く3 OR 龍が如く極3')
VIDEO_DURATION = os.getenv('INPUT_DURATION', 'short')

# ショート動画の場合は自動で #Shorts を付与
ADD_TAG = '#Shorts' if VIDEO_DURATION == 'short' else ''

API_KEY = os.getenv('YOUTUBE_API_KEY')

def fetch_data(days_ago):
    if not API_KEY:
        print("API Key is missing!")
        return []

    youtube = build('youtube', 'v3', developerKey=API_KEY)
    time_threshold = (datetime.now() - timedelta(days=days_ago)).isoformat() + 'Z'
    
    full_query = f"{SEARCH_QUERY} {ADD_TAG}"
    
    try:
        search_res = youtube.search().list(
            q=full_query, 
            part='snippet', 
            maxResults=50,
            type='video', 
            videoDuration=VIDEO_DURATION,
            publishedAfter=time_threshold, 
            relevanceLanguage='ja'
        ).execute()

        data_list = []
        for item in search_res.get('items', []):
            v_id = item['id']['videoId']
            snippet = item['snippet']
            
            v_stats = youtube.videos().list(id=v_id, part='statistics').execute()
            c_stats = youtube.channels().list(id=snippet['channelId'], part='statistics').execute()
            
            views = int(v_stats['items'][0]['statistics'].get('viewCount', 0))
            subs = int(c_stats['items'][0]['statistics'].get('subscriberCount', 1))
            
            if views >= 2000 and subs <= 100000 and views >= subs:
                data_list.append({
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'subs': subs,
                    'views': views,
                    'ratio': round((views / subs), 1),
                    'url': f"https://www.youtube.com/watch?v={v_id}",
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'date': snippet['publishedAt'][:10]
                })
        return sorted(data_list, key=lambda x: x['views'], reverse=True)
    except Exception as e:
        print(f"Error: {e}")
        return []

weekly_data = fetch_data(7)
yearly_data = fetch_data(365)

html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marketing Report</title>
    <style>
        body { font-family: sans-serif; background: #0f0f0f; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 1100px; margin: auto; }
        .header { text-align: center; padding: 20px; background: #ff0000; border-radius: 10px; margin-bottom: 20px; }
        h2 { border-left: 5px solid #ff0000; padding-left: 10px; }
        .grid { display: grid; grid-gap: 20px; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }
        .card { background: #1e1e1e; border-radius: 10px; overflow: hidden; border: 1px solid #333; }
        .card.short { aspect-ratio: 9/16; }
        img { width: 100%; height: auto; display: block; }
        .p-10 { padding: 10px; }
        .title { font-weight: bold; font-size: 0.9em; text-decoration: none; color: #fff; display: block; margin-bottom: 5px; }
        .views { color: #00ffcc; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>分析: {{ query }} ({{ duration }})</h1>
        </div>
        <h2>🔥 週間ランキング</h2>
        <div class="grid">
        {% for row in weekly %}
            <div class="card">
                <a href="{{ row.url }}" target="_blank"><img src="{{ row.thumbnail }}"></a>
                <div class="p-10">
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    再生数: <span class="views">{{ "{:,}".format(row.views) }}</span><br>
                    拡散率: {{ row.ratio }}倍
                </div>
            </div>
        {% endfor %}
        </div>
        <h2>📊 年間ランキング</h2>
        <div class="grid">
        {% for row in yearly %}
            <div class="card">
                <a href="{{ row.url }}" target="_blank"><img src="{{ row.thumbnail }}"></a>
                <div class="p-10">
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    再生数: <span class="views">{{ "{:,}".format(row.views) }}</span><br>
                    拡散率: {{ row.ratio }}倍
                </div>
            </div>
        {% endfor %}
        </div>
    </div>
</body>
</html>
"""

template = Template(html_template)
report_html = template.render(
    weekly=weekly_data, 
    yearly=yearly_data, 
    query=SEARCH_QUERY,
    duration=VIDEO_DURATION
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(report_html)
