import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from jinja2 import Template

API_KEY = os.getenv('YOUTUBE_API_KEY')
SEARCH_QUERY = '龍が如く3 OR 龍が如く極3 #Shorts'

def fetch_data(days_ago):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    time_threshold = (datetime.now() - timedelta(days=days_ago)).isoformat() + 'Z'
    
    search_res = youtube.search().list(
        q=SEARCH_QUERY, part='snippet', maxResults=50,
        type='video', videoDuration='short',
        publishedAfter=time_threshold, relevanceLanguage='ja'
    ).execute()

    data_list = []
    for item in search_res.get('items', []):
        v_id = item['id']['videoId']
        c_id = item['snippet']['channelId']
        v_stats = youtube.videos().list(id=v_id, part='statistics').execute()
        c_stats = youtube.channels().list(id=c_id, part='statistics').execute()
        
        views = int(v_stats['items'][0]['statistics'].get('viewCount', 0))
        subs = int(c_stats['items'][0]['statistics'].get('subscriberCount', 1))
        
        if subs <= 100000 and views >= subs:
            data_list.append({
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'subs': subs, 'views': views,
                'ratio': round((views / subs), 2),
                'url': f"https://www.youtube.com/shorts/{v_id}",
                'date': item['snippet']['publishedAt'][:10]
            })
    return sorted(data_list, key=lambda x: x['ratio'], reverse=True)

# データを2種類取得
weekly_data = fetch_data(7)   # 直近7日間
yearly_data = fetch_data(365) # 直近1年間

# HTMLテンプレート
html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>龍が如く極3 市場調査</title>
    <style>
        body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #1c1e21; }
        .container { max-width: 900px; margin: auto; }
        h1 { color: #d32f2f; text-align: center; }
        h2 { border-left: 5px solid #d32f2f; padding-left: 10px; margin-top: 30px; background: #fff; padding-top: 10px; padding-bottom: 10px; }
        .card { background: white; margin-bottom: 15px; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); }
        .title { font-weight: bold; font-size: 1.1em; display: block; margin-bottom: 8px; color: #000; text-decoration: none; }
        .info { font-size: 0.9em; color: #65676b; margin-bottom: 10px; }
        .stats { display: flex; gap: 20px; align-items: center; }
        .ratio-badge { background: #ffeb3b; color: #000; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 1em; }
        .weekly-tag { color: #fff; background: #d32f2f; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-bottom: 5px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>龍が如く極3 市場調査ダッシュボード</h1>
        <p style="text-align:center;">最終更新: {{ now }}</p>

        <h2>🔥 直近1週間の急上昇 (Weekly)</h2>
        {% for row in weekly %}
        <div class="card">
            <span class="weekly-tag">NEW / WEEKLY</span>
            <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
            <div class="info">{{ row.channel }} | 投稿日: {{ row.date }}</div>
            <div class="stats">
                <div>登録者: {{ row.subs }}</div>
                <div>再生数: {{ "{:,}".format(row.views) }}</div>
                <div class="ratio-badge">拡散率: {{ row.ratio }}倍</div>
            </div>
        </div>
        {% endfor %}

        <h2>📊 直近1年間のバズ動画 (Yearly)</h2>
        {% for row in yearly %}
        <div class="card">
            <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
            <div class="info">{{ row.channel }} | 投稿日: {{ row.date }}</div>
            <div class="stats">
                <div>登録者: {{ row.subs }}</div>
                <div>再生数: {{ "{:,}".format(row.views) }}</div>
                <div class="ratio-badge">拡散率: {{ row.ratio }}倍</div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

template = Template(html_template)
report_html = template.render(
    weekly=weekly_data, 
    yearly=yearly_data, 
    now=datetime.now().strftime('%Y-%m-%d %H:%M')
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(report_html)
