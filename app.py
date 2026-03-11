import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import re

# 1. ページ設定
st.set_page_config(page_title="Pippi's Strategic Research", layout="wide")

# 2. デザイン設定
st.markdown("""
    <style>
    .main { background-color: #0f0f0f; color: white; }
    .stButton>button { width: 100%; background-color: #ff0000; color: white; border-radius: 8px; font-weight: bold; border: none; height: 50px; }
    .video-card { background-color: #1e1e1e; padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 20px; }
    .title-text { font-weight: bold; font-size: 1em; color: #ffffff; text-decoration: none; display: block; margin-top: 10px; line-height: 1.4; }
    .view-text { color: #00ffcc; font-weight: bold; }
    .ratio-badge { background-color: #ffeb3b; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }
    .hashtag { color: #3ea6ff; font-size: 0.85em; margin-right: 5px; }
    .channel-info { font-size: 0.8em; color: #aaa; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. サイドバー：詳細な検索条件
st.sidebar.header("🎯 戦略ターゲット設定")

api_key = st.secrets.get("YOUTUBE_API_KEY") or st.sidebar.text_input("YouTube API Key", type="password")

query = st.sidebar.text_input("検索キーワード", value="龍が如く3")

# 登録者数の上限フィルタ
sub_limit = st.sidebar.selectbox(
    "登録者数の上限",
    options=[10000, 50000, 100000, 500000, 1000000],
    format_func=lambda x: f"{x//10000}万人以下",
    index=2
)

# 投稿日フィルタ
date_option = st.sidebar.selectbox(
    "投稿日",
    options=["1日前", "1週間前", "2週間前", "1か月前", "半年前", "1年前"],
    index=1
)
date_map = {"1日前": 1, "1週間前": 7, "2週間前": 14, "1か月前": 30, "半年前": 180, "1年前": 365}

# 動画の形態
v_format = st.sidebar.radio("動画の形態", ["縦動画（ショート）", "横動画（通常）"])

if st.sidebar.button("この条件で分析を開始！"):
    if not api_key:
        st.error("APIキーを設定してください。")
    else:
        with st.spinner('穴場動画を抽出中...'):
            try:
                youtube = build('youtube', 'v3', developerKey=api_key)
                days = date_map[date_option]
                time_threshold = (datetime.now() - timedelta(days=days)).isoformat() + 'Z'
                
                # 検索設定
                duration = "short" if v_format == "縦動画（ショート）" else "any"
                search_q = f"{query} #Shorts" if v_format == "縦動画（ショート）" else query

                search_res = youtube.search().list(
                    q=search_q, part='snippet', maxResults=50,
                    type='video', videoDuration=duration,
                    publishedAfter=time_threshold, relevanceLanguage='ja'
                ).execute()

                st.title(f"🚀 分析結果: {query}")
                
                cols = st.columns(3)
                valid_count = 0
                
                for item in search_res.get('items', []):
                    v_id = item['id']['videoId']
                    snippet = item['snippet']
                    
                    # 動画詳細とチャンネル詳細を取得
                    v_stats = youtube.videos().list(id=v_id, part='snippet,statistics').execute()
                    c_stats = youtube.channels().list(id=snippet['channelId'], part='statistics').execute()
                    
                    v_detail = v_stats['items'][0]
                    views = int(v_detail['statistics'].get('viewCount', 0))
                    subs = int(c_stats['items'][0]['statistics'].get('subscriberCount', 1))
                    
                    # ハッシュタグの抽出（説明文から抽出）
                    description = v_detail['snippet'].get('description', '')
                    hashtags = re.findall(r'#\w+', description)
                    
                    # 【Pippiさんの指定条件でフィルタリング】
                    # 1. 再生数2000回以上
                    # 2. 再生数 ≧ 登録者数
                    # 3. 指定した登録者数以下
                    if views >= 2000 and views >= subs and subs <= sub_limit:
                        with cols[valid_count % 3]:
                            ratio = round(views / subs, 1)
                            st.markdown(f"""
                            <div class="video-card">
                                <a href="https://www.youtube.com/watch?v={v_id}" target="_blank">
                                    <img src="{snippet['thumbnails']['high']['url']}" style="width:100%; border-radius:8px;">
                                </a>
                                <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="title-text">{snippet['title']}</a>
                                <p class="channel-info">{snippet['channelTitle']} (登録者: {subs:,}人)</p>
                                <div style="margin: 10px 0;">
                                    <span class="view-text">{views:,} 回再生</span>
                                    <span class="ratio-badge">{ratio} 倍拡散</span>
                                </div>
                                <div style="height: 3.5em; overflow: hidden; border-top: 1px solid #333; padding-top: 5px;">
                                    {' '.join([f'<span class="hashtag">{tag}</span>' for tag in hashtags[:5]])}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            valid_count += 1
                
                if valid_count == 0:
                    st.warning("条件に合う「穴場動画」が見つかりませんでした。登録者数の上限を上げるか、期間を広げてみてください。")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
else:
    st.info("サイドバーでターゲットを絞り込んで、「分析を開始！」を押してください。")
