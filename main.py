import os
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from jinja2 import Template

API_KEY = os.getenv('YOUTUBE_API_KEY')
SEARCH_QUERY = '龍が如く3 OR 龍が如く極3 #Shorts'

def get_market_data():
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    one_year_ago = (datetime.now() - timedelta(days=365)).isoformat() + 'Z'
    
    search_res = youtube.search().list(
        q=SEARCH_QUERY, part='snippet', maxResults=50,
        type='video', videoDuration='short',
        publishedAfter=one_year_ago, relevanceLanguage='ja'
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
    return data_list

results = get_market_data()

html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>龍が如く極3 ショート動画調査</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; padding: 20px; }
        .card { background: white; margin-bottom: 10px; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .ratio { color: #d32f2f; font-weight: bold; font-size: 1.2em; }
        a { color: #1a73e8; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <h1>龍が如く極3 市場調査レポート ({{ date }})</h1>
    {% for row in data %}
    <div class="card">
        <div><strong>{{ row.title }}</strong></div>
        <div>ch: {{ row.channel }} (登録者: {{ row.subs }})</div>
        <div>再生数: {{ row.views }} / <span class="ratio">拡散率: {{ row.ratio }}倍</span></div>
        <a href="{{ row.url }}" target="_blank">▶ 動画を見る</a>
    </div>
    {% endfor %}
</body>
</html>
"""
template = Template(html_template)
report_html = template.render(data=results, date=datetime.now().strftime('%Y-%m-%d'))

with open("index.html", "w", encoding="utf-8") as f:
    f.write(report_html)
