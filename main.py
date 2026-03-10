import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from jinja2 import Template

# --- GitHub Actionsの入力フォームから値を受け取る設定 ---
# 入力がない場合のデフォルトは「龍が如く3」の「ショート」にしています
SEARCH_QUERY = os.getenv('INPUT_QUERY', '龍が如く3 OR 龍が如く極3')
VIDEO_DURATION = os.getenv('INPUT_DURATION', 'short')

# ショート動画の場合のみ、検索精度を上げるために #Shorts を付与
ADD_TAG = '#Shorts' if VIDEO_DURATION == 'short' else ''

API_KEY = os.getenv('YOUTUBE_API_KEY')

def fetch_data(days_ago):
    if not API_KEY:
        print("API Key is missing!")
        return []

    youtube = build('youtube', 'v3', developerKey=API_KEY)
    time_threshold = (datetime.now() - timedelta(days=days_ago)).isoformat() + 'Z'
    
    # 検索キーワードの組み立て
    full_query = f"{SEARCH_QUERY} {ADD_TAG}"
    
    # 1. 動画検索を実行
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
        
        # 2. 各動画の詳細統計（再生数）とチャンネル統計（登録者数）を取得
        try:
            v_stats = youtube.videos().list(id=v_id, part='statistics').execute()
            c_stats = youtube.channels().list(id=snippet['channelId'], part='statistics').execute()
            
            views = int(v_stats['items'][0]['statistics'].get('viewCount', 0))
            subs = int(c_stats['items'][0]['statistics'].get('subscriberCount', 1))
            
            # --- 優秀なマーケターのフィルタリング条件 ---
            # ・再生数2,000回以上
            # ・登録者10万人以下の「これから伸びる」チャンネル
            # ・再生数 ≧ 登録者数（＝拡散されている証拠）
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
        except Exception as e:
            print(f"Error fetching details for {v_id}: {e}")
            continue
            
    # 全ての項目を「再生数が多い順」に並び替え
    return sorted(data_list, key=lambda x: x['views'], reverse=True)

# データの取得（1週間分と1年分）
weekly_data = fetch_data(7)
yearly_data = fetch_data(365)

# --- HTMLレポートの生成 ---
html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pippi's Marketing Report</title>
    <style>
        body { font-family: 'Hiragino Kaku Gothic ProN', sans-serif; background: #0f0f0f; color: #ffffff; margin: 0; padding: 20px; }
        .container { max-width: 1100px; margin: auto; }
        .header { text-align: center; padding: 30px; background: linear-gradient(135deg, #ff0000 0%, #a00000 100%); border-radius: 15px; margin-bottom: 30px; }
        h1 { margin: 0; font-size: 2em; }
        .config-info { font-size: 0.9em; opacity: 0.8; margin-top: 10px; }
        h2 { border-left: 6px solid #ff0000; padding-left: 15px; margin-top: 40px; color: #ff4444; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; }
        .card { background: #1e1e1e; border-radius: 12px; overflow: hidden; transition: 0.3s; border: 1px solid #333; }
        .card:hover { transform: translateY(-5px); border-color: #ff0000; }
        .thumb-link { position: relative; display: block; width: 100%; padding-top: 56.25%; } /* 16:9 default */
        .card.is-short .thumb-link { padding-top: 177%; } /* 9:16 for shorts */
        .thumb-link img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
        .content { padding: 15px; }
        .title { font-weight: bold; font-size: 0.95em; height: 2.8em; overflow: hidden; margin-bottom: 10px; color: #fff; text-decoration: none; display: block; line-height: 1.4; }
        .stats-box { background: #2d2d2d; padding: 10px; border-radius: 8px; font-size: 0.85em; }
        .views-num { color: #00ffcc; font-size: 1.1em; font-weight: bold; }
        .ratio-num { color: #ffeb3b; font-weight: bold; }
        .date { font-size: 0.8em; color: #aaa; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>分析キーワード: {{ query }}</h1>
            <div class="config-info">
                モード: {{ duration }} | 最終更新: {{ now }}
            </div>
        </div>

        <h2>🔥 直近1週間の伸びた動画</h2>
        <div class="grid">
        {% for row in weekly %}
            <div class="card {% if duration == 'short' %}is-short{% endif %}">
                <a href="{{ row.url }}" target="_blank" class="thumb-link">
                    <img src="{{ row.thumbnail }}" alt="thumbnail">
                </a>
                <div class="content">
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    <div class="stats-box">
                        再生数: <span class="views-num">{{ "{:,}".format(row.views) }}回</span><br>
                        拡散率: <span class="ratio-num">{{ row.ratio }}倍</span> (登録者: {{ row.subs }})
                    </div>
                    <div class="date">投稿日: {{ row.date }} | {{ row.channel }}</div>
                </div>
            </div>
        {% endfor %}
        </div>

        <h2>📊 直近1年間のバズ動画</h2>
        <div class="grid">
        {% for row in yearly %}
            <div class="card {% if duration == 'short' %}is-short{% endif %}">
                <a href="{{ row.url }}" target="_blank" class="thumb-link">
                    <img src="{{ row.thumbnail }}" alt="thumbnail">
                </a>
                <div class="content">
                    <a href="{{ row.url }}" target="_blank" class="title">{{ row.title }}</a>
                    <div class="stats-box">
                        再生数: <span class="views-num">{{ "{:,}".format(row.views) }}回</span><br>
                        拡散率: <span class="ratio-num">{{ row.ratio }}倍</span> (登録者: {{ row.subs }})
                    </div>
                    <div class="date">投稿日: {{ row.date }} | {{ row.channel }}</div>
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
