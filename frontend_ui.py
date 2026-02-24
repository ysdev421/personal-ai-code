"""
Streamlit フロントエンド
WebSocket + プッシュ通知対応
"""

import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ページ設定
st.set_page_config(
    page_title="Personal AI Partner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS スタイル
st.markdown("""
<style>
/* アバターコンテナ */
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
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.status-badge {
    background: rgba(255,255,255,0.3);
    padding: 10px 20px;
    border-radius: 25px;
    margin: 8px 0;
    font-size: 14px;
    font-weight: bold;
    text-align: center;
}

.progress-bar {
    width: 100%;
    height: 6px;
    background: rgba(255,255,255,0.2);
    border-radius: 3px;
    margin-top: 15px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    width: 60%;
    animation: progress 2s ease-in-out infinite;
}

@keyframes progress {
    0% { width: 0%; }
    50% { width: 100%; }
    100% { width: 100%; }
}

/* メッセージスタイル */
.trigger-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.chat-message {
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    animation: slideIn 0.3s ease;
}

.chat-message.user {
    background: #e3f2fd;
    text-align: right;
}

.chat-message.ai {
    background: #f5f5f5;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* インプット */
.input-form {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}

input {
    flex: 1;
    padding: 12px;
    border: 2px solid #667eea;
    border-radius: 8px;
    font-size: 14px;
}

button {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
}

button:hover {
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────
# セッション状態初期化
# ────────────────────────────────────────

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'triggered_message' not in st.session_state:
    st.session_state['triggered_message'] = None

if 'ai_status' not in st.session_state:
    st.session_state['ai_status'] = 'idle'

if 'processing_steps' not in st.session_state:
    st.session_state['processing_steps'] = {
        'テキスト解析': False,
        'データ検索': False,
        'LLM推論': False
    }

if 'ws_connected' not in st.session_state:
    st.session_state['ws_connected'] = False

# ────────────────────────────────────────
# WebSocket 接続管理
# ────────────────────────────────────────

class WebSocketManager:
    def __init__(self):
        self.ws = None
        self.loop = None
    
    async def connect(self):
        """WebSocket に接続"""
        try:
            uri = "ws://localhost:8000/ws"
            self.ws = await websockets.connect(uri)
            st.session_state['ws_connected'] = True
            logger.info("WebSocket 接続成功")
            await self.listen()
        except Exception as e:
            logger.error(f"WebSocket 接続失敗: {e}")
            st.error(f"サーバーに接続できません: {e}")
    
    async def listen(self):
        """WebSocket からのメッセージを受信"""
        try:
            async for message_str in self.ws:
                message = json.loads(message_str)
                logger.info(f"受信: {message['type']}")
                
                # メッセージ種別ごとに処理
                if message['type'] == 'trigger':
                    # トリガーメッセージ
                    st.session_state['triggered_message'] = message
                    st.rerun()
                
                elif message['type'] == 'thinking':
                    # AI が思考中
                    step_map = {
                        'analyzing': 'テキスト解析',
                        'searching': 'データ検索',
                        'generating': 'LLM推論'
                    }
                    step = step_map.get(message.get('step'), 'unknown')
                    st.session_state['ai_status'] = 'thinking'
                    st.rerun()
                
                elif message['type'] == 'response':
                    # AI からの返答
                    st.session_state['messages'].append({
                        'role': 'ai',
                        'content': message['content'],
                        'timestamp': message.get('timestamp')
                    })
                    st.session_state['ai_status'] = 'idle'
                    st.rerun()
        
        except Exception as e:
            logger.error(f"リッスンエラー: {e}")
            st.session_state['ws_connected'] = False
    
    async def send_message(self, message: dict):
        """メッセージを送信"""
        try:
            if self.ws:
                await self.ws.send(json.dumps(message))
                logger.info(f"送信: {message['type']}")
        except Exception as e:
            logger.error(f"送信エラー: {e}")
    
    async def disconnect(self):
        """接続を切断"""
        if self.ws:
            await self.ws.close()
            st.session_state['ws_connected'] = False

ws_manager = WebSocketManager()

# ────────────────────────────────────────
# WebSocket 接続（バックグラウンド）
# ────────────────────────────────────────

@st.cache_resource
def get_event_loop():
    """イベントループを取得"""
    try:
        loop = asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

# WebSocket 接続を開始
if not st.session_state['ws_connected']:
    loop = get_event_loop()
    try:
        loop.run_until_complete(ws_manager.connect())
    except:
        pass

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
    
    # アバター表示（ステータスに応じて）
    if st.session_state['ai_status'] == 'idle':
        st.markdown('<div class="avatar-icon">🤖</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge">Ready</div>', unsafe_allow_html=True)
    
    elif st.session_state['ai_status'] == 'thinking':
        st.markdown('<div class="avatar-icon">🤔</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge">💭 思考中</div>', unsafe_allow_html=True)
        st.markdown('<div class="progress-bar"><div class="progress-fill"></div></div>', 
                   unsafe_allow_html=True)
    
    elif st.session_state['ai_status'] == 'triggered':
        st.markdown('<div class="avatar-icon">✨</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge">💬 メッセージあり</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ステータス詳細
    st.markdown("### 📊 Status")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state['ws_connected']:
            st.success("✅ 接続中")
        else:
            st.error("❌ 切断")
    
    with col2:
        st.info(f"メッセージ数: {len(st.session_state['messages'])}")

# ────────────────────────────────────────
# 【右側】チャット
# ────────────────────────────────────────

with col_chat:
    st.markdown("### 💬 Chat")
    
    # トリガーメッセージ表示
    if st.session_state['triggered_message']:
        msg = st.session_state['triggered_message']
        st.markdown('<div class="trigger-message">', unsafe_allow_html=True)
        st.markdown(f"**✨ AI からのメッセージ**")
        st.markdown(f"> {msg['content']}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("返答する"):
                st.session_state['replying_to'] = msg
                st.rerun()
        with col2:
            if st.button("あとで"):
                st.session_state['triggered_message'] = None
                st.rerun()
        with col3:
            if st.button("削除"):
                st.session_state['triggered_message'] = None
                st.rerun()
        
        st.divider()
    
    # チャット履歴表示
    chat_container = st.container()
    
    with chat_container:
        for i, msg in enumerate(st.session_state['messages']):
            if msg['role'] == 'user':
                st.markdown(f'<div class="chat-message user">'
                           f'<b>あなた:</b> {msg["content"]}</div>',
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message ai">'
                           f'<b>AI:</b> {msg["content"]}</div>',
                           unsafe_allow_html=True)
    
    # 入力フォーム
    st.divider()
    
    col_input, col_button = st.columns([5, 1])
    
    with col_input:
        user_input = st.text_input(
            "質問を入力してください：",
            placeholder="例：椅子を買いたい",
            label_visibility="collapsed",
            key="user_input"
        )
    
    with col_button:
        send_button = st.button("送信", use_container_width=True)
    
    # メッセージ送信処理
    if send_button and user_input:
        # ユーザーメッセージを表示
        st.session_state['messages'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # トリガーメッセージをクリア
        st.session_state['triggered_message'] = None
        
        # サーバーに送信
        loop = get_event_loop()
        try:
            loop.run_until_complete(ws_manager.send_message({
                'type': 'message',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            st.error(f"送信エラー: {e}")
        
        # UI 更新
        st.rerun()

# ────────────────────────────────────────
# サイドバー：設定
# ────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # 接続情報
    st.markdown("**接続状態**")
    if st.session_state['ws_connected']:
        st.success("✅ WebSocket 接続中")
    else:
        st.error("❌ 接続待機中...")
    
    # データ表示
    st.markdown("### 📊 Your Data")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("相談回数", len(st.session_state['messages']), "+1")
    with col2:
        st.metric("トリガー受信", "5回", "今月")
    
    # その他の設定
    st.divider()
    st.markdown("**通知設定**")
    
    col1, col2 = st.columns(2)
    with col1:
        push_enabled = st.checkbox("プッシュ通知", value=True)
    with col2:
        sound_enabled = st.checkbox("音声通知", value=False)
    
    # リセットボタン
    st.divider()
    if st.button("チャット履歴をリセット"):
        st.session_state['messages'] = []
        st.rerun()

# ────────────────────────────────────────
# プッシュ通知（JavaScript）
# ────────────────────────────────────────

if st.session_state['triggered_message']:
    st.markdown("""
    <script>
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Personal AI Partner', {
            body: '新しいメッセージがあります！',
            icon: '🤖'
        });
    }
    </script>
    """, unsafe_allow_html=True)
