import os.path
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.auth.oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import chromadb
from chromadb.config import Settings
from datetime import datetime, timedelta

# Gmail API スコープ
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Gmail API 認証"""
    creds = None
    
    # token.json が存在する場合は読み込み
    if os.path.exists('token.json'):
        creds = UserCredentials.from_authorized_user_file('token.json', SCOPES)
    
    # 認証情報がない場合は、OAuth フロー開始
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json をダウンロード必要
            # https://console.cloud.google.com/apis/credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # token.json に保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_gmail_service(creds):
    """Gmail API サービス初期化"""
    return build('gmail', 'v1', credentials=creds)

def extract_amazon_order(email_body):
    """Amazon メールから注文情報を抽出"""
    
    # HTML タグ削除
    text = re.sub('<[^<]+?>', '', email_body)
    
    # 商品名抽出
    product_match = re.search(r'商品名[：:]\s*(.+?)(?=\n|価格)', text, re.DOTALL)
    product = product_match.group(1).strip() if product_match else "不明"
    
    # 価格抽出
    price_match = re.search(r'合計金額[：:]\s*([¥0-9,]+)', text)
    price = price_match.group(1) if price_match else "不明"
    
    # 注文日抽出
    date_match = re.search(r'注文日時[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)', text)
    order_date = date_match.group(1) if date_match else datetime.now().strftime('%Y年%m月%d日')
    
    return {
        'product': product,
        'price': price,
        'date': order_date,
        'source': 'amazon_email'
    }

def fetch_amazon_emails(service, days=7):
    """過去 N 日間の Amazon メールを取得"""
    
    # 検索クエリ
    date_after = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
    query = f'from:order-update@amazon.co.jp after:{date_after}'
    
    print(f"検索中: '{query}'")
    
    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("メールが見つかりませんでした")
            return []
        
        print(f"{len(messages)} 件のメールが見つかりました")
        
        orders = []
        for msg_id_obj in messages:
            msg_id = msg_id_obj['id']
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            # メール本文取得
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            
            # 本文取得（複雑な場合あり）
            if 'parts' in msg['payload']:
                email_body = base64.urlsafe_b64decode(
                    msg['payload']['parts'][0]['data']
                ).decode('utf-8')
            else:
                email_body = base64.urlsafe_b64decode(
                    msg['payload']['body'].get('data', '')
                ).decode('utf-8')
            
            # 注文情報抽出
            order_info = extract_amazon_order(email_body)
            orders.append(order_info)
            
            print(f"✅ {order_info['date']} - {order_info['product']} ({order_info['price']})")
        
        return orders
    
    except Exception as e:
        print(f"エラー: {e}")
        return []

def save_to_chromadb(orders):
    """抽出した注文情報を Chromadb に保存"""
    
    chroma_client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chroma_data"
    ))
    
    try:
        collection = chroma_client.get_collection(name="user_knowledge")
    except:
        collection = chroma_client.create_collection(name="user_knowledge")
    
    print("\nChromadb に保存中...")
    for order in orders:
        try:
            doc_id = f"amazon_{order['date']}_{order['product'][:10]}"
            collection.add(
                ids=[doc_id],
                documents=[f"購入日: {order['date']}\n商品: {order['product']}\n価格: {order['price']}"],
                metadatas=[{
                    "type": "purchase",
                    "source": "amazon_email",
                    "date": order['date']
                }]
            )
            print(f"✅ 保存: {order['product']}")
        except Exception as e:
            print(f"❌ エラー: {e}")

def main():
    """メイン処理"""
    print("=== Amazon メール自動抽出 ===\n")
    
    # Gmail 認証
    print("Gmail 認証中...")
    creds = authenticate_gmail()
    service = get_gmail_service(creds)
    print("✅ 認証成功\n")
    
    # Amazon メール取得（過去 7 日間）
    orders = fetch_amazon_emails(service, days=7)
    
    if orders:
        # Chromadb に保存
        save_to_chromadb(orders)
        print(f"\n完了！{len(orders)} 件の注文を保存しました")
    else:
        print("\n注文が見つかりませんでした")

if __name__ == '__main__':
    main()
