"""
Streamlit フロントエンド - シンプル版
Python 3.14 対応
"""

import streamlit as st
import requests
import json
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="Personal AI Partner",
    page_icon="🤖",
    layout="wide"
)

# CSS スタイル
st.markdown("""
<style>
.avatar-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 30px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    color: white;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.avatar-icon {
    font-size: 100px;
    margin-bottom: 15px;
}

.status-badge {
    background: rgba(255,255,255,0.3);
    padding: 10px 20px;
    border-radius: 25px;
    margin: 8px 0;
    font-weight: bold;
    text-align: center;
}

.chat-message {
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}

.chat-message.user {
    background: #e3f2fd;
    text-align: right;
}

.chat-message.ai {
    background: #f5f5f5;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────
# セッション状態初期化
# ────────────────────────────────────────

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'ai_status' not in st.session_state:
    st.session_state['ai_status'] = 'idle'

if 'server_connected' not in st.session_state:
    st.session_state['server_connected'] = False

# ────────────────────────────────────────
# サーバー接続確認
# ────────────────────────────────────────

def check_server_health():
    """バックエンドサーバーが動いてるか確認"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# サーバー接続確認
server_ok = check_server_health()
st.session_state['server_connected'] = server_ok

# ────────────────────────────────────────
# メインUI
# ────────────────────────────────────────

st.title("🤖 Personal AI Partner")

# レイアウト
col_avatar, col_chat = st.columns([1, 2.5], gap="large")

# ────────────────────────────────────────
# 【左側】AI アバター + ステータス
# ────────────────────────────────────────

with col_avatar:
    st.markdown('<div class="avatar-container">', unsafe_allow_html=True)
    
    if st.session_state['ai_status'] == 'idle':
        st.markdown('<div class="avatar-icon">🤖</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge">Ready</div>', unsafe_allow_html=True)
    
    elif st.session_state['ai_status'] == 'thinking':
        st.markdown('<div class="avatar-icon">🤔</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge">💭 思考中</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ステータス詳細
    st.markdown("### 📊 Status")
    if server_ok:
        st.success("✅ サーバー接続中")
    else:
        st.error("❌ サーバーに接続できません")
    
    st.info(f"メッセージ: {len(st.session_state['messages'])} 件")

# ────────────────────────────────────────
# 【右側】チャット
# ────────────────────────────────────────

with col_chat:
    st.markdown("### 💬 Chat")
    
    # チャット履歴表示
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state['messages']:
            if msg['role'] == 'user':
                st.markdown(
                    f'<div class="chat-message user"><b>あなた:</b> {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-message ai"><b>AI:</b> {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
    
    # 入力フォーム
    st.divider()
    
    col_input, col_button = st.columns([5, 1])
    
    with col_input:
        user_input = st.text_input(
            "質問を入力してください：",
            placeholder="例：椅子を買いたい",
            label_visibility="collapsed"
        )
    
    with col_button:
        send_button = st.button("送信", use_container_width=True)
    
    # メッセージ送信処理
    if send_button and user_input:
        if not server_ok:
            st.error("❌ サーバーに接続できません。バックエンドが起動しているか確認してください。")
        else:
            # ユーザーメッセージを表示
            st.session_state['messages'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            })
            
            # ステータスを思考中に
            st.session_state['ai_status'] = 'thinking'
            st.rerun()

# ────────────────────────────────────────
# AI が思考中の場合、メッセージを送信
# ────────────────────────────────────────

if st.session_state['ai_status'] == 'thinking' and len(st.session_state['messages']) > 0:
    last_user_msg = None
    for msg in reversed(st.session_state['messages']):
        if msg['role'] == 'user':
            last_user_msg = msg
            break
    
    if last_user_msg:
        try:
            # バックエンドに送信
            response = requests.post(
                "http://localhost:8000/chat",
                json={
                    'type': 'message',
                    'content': last_user_msg['content'],
                    'timestamp': last_user_msg['timestamp']
                },
                timeout=60
            )
            
            if response.status_code == 200:
                ai_response = response.json()
                
                # AI メッセージを追加
                st.session_state['messages'].append({
                    'role': 'ai',
                    'content': ai_response.get('content', 'エラーが発生しました'),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                st.session_state['messages'].append({
                    'role': 'ai',
                    'content': f'エラー: {response.status_code}',
                    'timestamp': datetime.now().isoformat()
                })
        
        except requests.Timeout:
            st.session_state['messages'].append({
                'role': 'ai',
                'content': 'タイムアウト：AI の応答が遅すぎます',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            st.session_state['messages'].append({
                'role': 'ai',
                'content': f'エラー: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
        
        finally:
            st.session_state['ai_status'] = 'idle'
            st.rerun()

# ────────────────────────────────────────
# サイドバー
# ────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    if st.button("チャット履歴をリセット"):
        st.session_state['messages'] = []
        st.rerun()
