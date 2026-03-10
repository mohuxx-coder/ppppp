import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# ページの設定
st.set_page_config(page_title="Pippi's Marketing App", layout="wide")

# スタイル設定（龍が如く風の赤黒デザイン）
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; background-color: #ff0000; color: white; border-radius: 5px; }
    .video-card { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-bottom: 20px; }
    .ratio-text { color: #ffeb3b; font-weight: bold; }
    .view-text { color: #00ffcc; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# サイドバー：設定項目
st.sidebar.header("🔍 調査条件")
api_key = st.sidebar.text_input("YouTube API Key", type="password", help="Google Cloudで取得したキーを入力してください")
query = st.sidebar.text_input("検索キーワード", value="龍が如く3 OR 龍が如く極3")
duration = st.sidebar.selectbox("動画の長さ", ["short", "any", "medium", "long"], index=0)
days = st.sidebar.slider("期間（何日前まで）", 1, 365, 7)

# 検索実行ボタン
if st.sidebar.button("調査開始！"):
    if not api_key:
        st.error("APIキーを入力してください。")
    else:
        with st.spinner('YouTubeのデータを分析中...'):
            try:
                youtube = build('youtube', 'v3', developerKey=api_key)
                time_threshold = (datetime.now() - timedelta(days=days)).isoformat() + 'Z'
                full_query = f"{query} #Shorts" if duration == "short" else query

                # 検索
                search_res = youtube.search().list(
                    q=full_query, part='snippet', maxResults=30,
                    type='video', videoDuration=duration,
                    publishedAfter=time_threshold, relevanceLanguage='ja'
                ).execute()

                st.title(f"📊 「{query}」の分析結果")
                
                cols = st.columns(3) # 3列表示
                
                for idx, item in enumerate(search_res.get('items', [])):
                    v_id = item['id']['videoId']
                    snippet = item['snippet']
                    
                    v_stats = youtube.videos().list(id=v_id, part='statistics').execute()
                    c_stats = youtube.channels().list(id=snippet['channelId'], part='statistics').execute()
                    
                    views = int(v_stats['items'][0]['statistics'].get('viewCount', 0))
                    subs = int(c_stats['items'][0]['statistics'].get('subscriberCount', 1))
                    
                    # フィルタリング：再生数 ≧ 登録者数 かつ 再生2000以上
                    if views >= 2000 and views >= subs:
                        with cols[idx % 3]:
                            st.markdown(f"""
                            <div class="video-card">
                                <a href="https://www.youtube.com/watch?v={v_id}" target="_blank">
                                    <img src="{snippet['thumbnails']['high']['url']}" style="width:100%; border-radius:5px;">
                                </a>
                                <p style="font-weight:bold; margin-top:10px; height:3em; overflow:hidden;">{snippet['title']}</p>
                                <p style="font-size:0.8em; color:#aaa;">{snippet['channelTitle']}</p>
                                <p>再生: <span class="view-text">{views:,}回</span> / 拡散率: <span class="ratio-text">{round(views/subs, 1)}倍</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
else:
    st.info("左側のサイドバーで条件を入力して「調査開始！」を押してください。")
