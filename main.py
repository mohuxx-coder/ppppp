import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from jinja2 import Template

# --- ★ここを自由に書き換えれば調査対象が変わります★ ---
# 調査したいキーワード (例: '龍が如く3', 'ベトナム 旅行', '歌ってみた')
SEARCH_QUERY = '龍が如く3 OR 龍が如く極3' 

# 動画の長さ ('any' = すべて, 'short' = ショートのみ, 'medium' = 4〜20分, 'long' = 20分以上)
VIDEO_DURATION = 'any' 

# キーワードに自動で追加するハッシュタグ（ショート専用にしたい場合は '#Shorts' を入れる）
ADD_TAG = '#Shorts' 
# --------------------------------------------------

API_KEY = os.getenv('YOUTUBE_API_KEY')

def fetch_data(days_ago):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    time_threshold = (datetime.now() - timedelta(days=days_ago)).isoformat() + 'Z'
    
    # 検索クエリの組み立て
    full_query = f"{SEARCH_QUERY} {ADD_TAG}"
    
    search_res = youtube.search().list(
        q=full_query, part='snippet', maxResults=50,
        type='video', 
        videoDuration=VIDEO_DURATION,
        publishedAfter=time_threshold, relevanceLanguage='ja'
    ).execute()

    data_list = []
    for item in search_res.get('items', []):
        v_id = item['id']['videoId']
        snippet = item['snippet']
        v_stats = youtube.videos().list(id=v_id, part='statistics').execute()
        c_stats = youtube.channels().list(id=snippet['channelId'], part='statistics').execute()
        
        views = int(v_stats['items'][0]['statistics'].get('viewCount', 0))
        subs = int(c_stats['items'][0]['statistics'].get('subscriberCount', 1))
        
        # 条件：再生2,000回以上 ＆ 登録者10万以下 ＆ 再生数≧登録者数
        if views >= 2000 and subs <= 100000 and views >= subs:
            data_list.append({
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'subs': subs, 'views': views,
                'ratio': round((views / subs), 1),
                'url': f"https://www.youtube.com/watch?v={v_id}",
                'thumbnail': snippet['thumbnails']['high']['url'],
                'date': snippet['publishedAt'][:10]
            })
    return sorted(data_list, key=lambda x: x['views'], reverse=True)

# 実行
weekly_data = fetch_data(7)
yearly_data = fetch_data(365)

# HTML出力（デザインは前回同様）
# ※テンプレート部分は長くなるため省略しますが、前回のコードのままでOKです
