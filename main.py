import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from jinja2 import Template

# GitHub Actionsの入力フォームから値を受け取る
SEARCH_QUERY = os.getenv('INPUT_QUERY', '龍が如く3 OR 龍が如く極3')
VIDEO_DURATION = os.getenv('INPUT_DURATION', 'short')
ADD_TAG = '#Shorts' if VIDEO_DURATION == 'short' else ''
API_KEY = os.getenv('YOUTUBE_API_KEY')

def fetch_data(days_ago):
    if not API_KEY: return []
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    time_threshold = (datetime.now() - timedelta(days=days_ago)).isoformat() + 'Z'
    
    try:
        search_res = youtube.search().list(
            q=f"{SEARCH_QUERY} {ADD_TAG}", 
            part='snippet', maxResults=50, type='video', 
            videoDuration=VIDEO_DURATION, publishedAfter=time_threshold, relevanceLanguage='ja'
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
                    'title': snippet['title'], 'channel': snippet['channelTitle'],
                    'subs': subs, 'views': views, 'ratio': round((views / subs), 1),
                    'url': f"https://www.youtube.com/watch?v={v_id}",
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'date': snippet['publishedAt'][:10]
                })
        return sorted(data_list, key=lambda x: x['views'], reverse=True)
    except: return []

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
        .header { text-align: center; padding: 20px; background: linear-gradient(to right, #ff0000, #900); border-radius: 10px; margin-bottom: 20px; }
        h2 { border-left: 5px solid #ff0000; padding-left: 10px; margin-top: 30px; }
        .grid { display: grid; grid-gap: 20px; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
        .card { background: #1e1e1e; border-radius: 10px; overflow: hidden; border: 1px solid #333; transition: 0.3s; }
        .card:hover { border-color: #ff0000; transform: translateY(-5px); }
        .thumb { position: relative; width: 100%; {% if is_short %}padding-top: 177%;{% else %}padding-top: 56.25%;{% endif %} }
        .thumb img { position: absolute; top:0; left:0; width:100%; height:100%; object-fit: cover; }
        .p-10 { padding: 15px; }
        .title { font-weight: bold; font-size: 0.9em; text-decoration: none; color: #fff; display: block; height: 2.8em; overflow: hidden; }
        .views { color: #00ffcc; font-weight: bold; font-size: 1.1em; }
        .ratio { color: #ffeb3b; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>分析: {{ query }}</h1>
            <p>モード: {{ duration }} | 更新: {{ now }}</p>
        </div>
        <h2>🔥 週間ランキング (再生順)</h2>
        <div class="grid">
        {% for row in weekly %}
            <div class="card">
                <a href="{{ row.url }}" target="_blank" class="thumb"><img src="{{ row.thumbnail }}"></a>
                <div class="p-10">
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    再生: <span class="views">{{ "{:,}".format(row.views) }}</span><br>
                    拡散: <span class="ratio">{{ row.ratio }}倍</span>
                </div>
            </div>
        {% endfor %}
        </div>
        <h2>📊 年間ランキング (再生順)</h2>
        <div class="grid">
        {% for row in yearly %}
            <div class="card">
                <a href="{{ row.url }}" target="_blank" class="thumb"><img src="{{ row.thumbnail }}"></a>
                <div class="p-10">
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    再生: <span class="views">{{ "{:,}".format(row.views) }}</span><br>
                    拡散: <span class="ratio">{{ row.ratio }}倍</span>
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
    weekly=weekly_data, yearly=yearly_data, 
    query=SEARCH_QUERY, duration=VIDEO_DURATION,
    is_short=(VIDEO_DURATION == 'short'),
    now=datetime.now().strftime('%Y-%m-%d %H:%M')
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(report_html)
