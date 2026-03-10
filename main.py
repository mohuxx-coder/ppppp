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
        snippet = item['snippet']
        c_id = snippet['channelId']
        
        v_stats = youtube.videos().list(id=v_id, part='statistics').execute()
        c_stats = youtube.channels().list(id=c_id, part='statistics').execute()
        
        views = int(v_stats['items'][0]['statistics'].get('viewCount', 0))
        subs = int(c_stats['items'][0]['statistics'].get('subscriberCount', 1))
        
        # --- 条件フィルタリング ---
        # 1. 再生数2,000回以上
        # 2. 登録者10万人以下
        # 3. 再生数 ≧ 登録者数
        if views >= 2000 and subs <= 100000 and views >= subs:
            data_list.append({
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'subs': subs,
                'views': views,
                'ratio': round((views / subs), 2),
                'url': f"https://www.youtube.com/shorts/{v_id}",
                'thumbnail': snippet['thumbnails']['high']['url'], # サムネイルURL取得
                'date': snippet['publishedAt'][:10]
            })
            
    # 全ての項目を再生数が多い順にソート
    return sorted(data_list, key=lambda x: x['views'], reverse=True)

# データの取得
weekly_data = fetch_data(7)   # 直近1週間
yearly_data = fetch_data(365) # 直近1年間

# HTMLテンプレート（デザインも強化）
html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>龍が如く極3 戦略レポート</title>
    <style>
        body { font-family: 'Hiragino Kaku Gothic ProN', sans-serif; background: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: auto; }
        h1 { color: #ff3e3e; text-align: center; border-bottom: 2px solid #ff3e3e; padding-bottom: 10px; }
        h2 { background: #333; padding: 10px; border-left: 8px solid #ff3e3e; margin-top: 40px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #2a2a2a; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .thumb-container { position: relative; width: 100%; padding-top: 177%; /* 9:16 ratio */ overflow: hidden; }
        .thumb-container img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
        .content { padding: 15px; }
        .title { font-weight: bold; font-size: 1em; height: 3em; overflow: hidden; margin-bottom: 10px; color: #fff; text-decoration: none; display: block; }
        .stats-box { background: #3d3d3d; padding: 10px; border-radius: 8px; font-size: 0.9em; }
        .views { color: #00ffcc; font-size: 1.2em; font-weight: bold; }
        .ratio { color: #ffeb3b; font-weight: bold; }
        .badge { background: #ff3e3e; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; margin-bottom: 5px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>龍が如く極3 マーケティングダッシュボード</h1>
        <p style="text-align:center;">更新日: {{ now }} (再生数 2,000回以上に限定)</p>

        <h2>🔥 直近1週間の伸びた動画 (再生数順)</h2>
        <div class="grid">
        {% for row in weekly %}
            <div class="card">
                <div class="thumb-container">
                    <a href="{{ row.url }}" target="_blank"><img src="{{ row.thumbnail }}" alt="thumbnail"></a>
                </div>
                <div class="content">
                    <span class="badge">WEEKLY HIGH</span>
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    <div class="stats-box">
                        再生数: <span class="views">{{ "{:,}".format(row.views) }}回</span><br>
                        拡散率: <span class="ratio">{{ row.ratio }}倍</span> (登録者: {{ row.subs }})
                    </div>
                </div>
            </div>
        {% endfor %}
        </div>

        <h2>📊 直近1年間のバズ動画 (再生数順)</h2>
        <div class="grid">
        {% for row in yearly %}
            <div class="card">
                <div class="thumb-container">
                    <a href="{{ row.url }}" target="_blank"><img src="{{ row.thumbnail }}" alt="thumbnail"></a>
                </div>
                <div class="content">
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    <div class="stats-box">
                        再生数: <span class="views">{{ "{:,}".format(row.views) }}回</span><br>
                        拡散率: <span class="ratio">{{ row.ratio }}倍</span> (登録者: {{ row.subs }})
                    </div>
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
    now=datetime.now().strftime('%Y-%m-%d %H:%M')
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(report_html)
