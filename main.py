import os
import requests
from datetime import datetime, timedelta

# 1. 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY', '8195198d-500e-4082-aefd-bab59bfda0bf')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8"

# 2. 팀원 매핑 (노션 이름 : 이메일)
TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "donggun_email@example.com",
    "유신": "yusin_email@example.com"
}

def get_today_kst():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")

def get_page_body_content(page_id):
    """페이지 ID를 받아 내부 본문의 텍스트 내용을 추출합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    blocks = response.json().get('results', [])
    
    full_text = []
    for block in blocks:
        # 문단(paragraph) 타입의 블록에서 텍스트 추출
        if block['type'] == 'paragraph':
            rich_texts = block['paragraph'].get('rich_text', [])
            for rt in rich_texts:
                full_text.append(rt.get('plain_text', ''))
        
        # 목록(bulleted_list_item) 타입 등 필요시 추가 가능
        elif block['type'] == 'bulleted_list_item':
            rich_texts = block['bulleted_list_item'].get('rich_text', [])
            for rt in rich_texts:
                full_text.append(f"• {rt.get('plain_text', '')}")

    return "\n".join(full_text).strip()

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    today = get_today_kst()
    query = {
        "filter": {
            "property": "날짜",
            "date": { "equals": today }
        }
    }
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    if not results:
        print(f"{today} 날짜의 데이터를 찾지 못했습니다.")
        return

    for page in results:
        page_id = page['id']
        props = page['properties']
        
        # 팀원 이름 가져오기
        member_data = props.get('팀원', {}).get('select') or props.get('팀원', {}).get('multi_select', [None])[0]
        if not member_data: continue
        
        name = member_data['name'].strip()
        
        if name in TEAM_INFO:
            email = TEAM_INFO[name]
            
            # ⭐️ 핵심: 제목 대신 페이지 본문 내용을 가져옵니다.
            page_content = get_page_body_content(page_id)
            
            # 만약 본문이 비어있으면 제목이라도 보낼 수 있게 예외 처리
            if not page_content:
                title_list = props.get('제목', {}).get('title', [])
                page_content = title_list[0]['plain_text'] if title_list else "내용 없음"

            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": today,
                "content": page_content # 추출한 본문 내용 전송
            }
            
            response = requests.post(API_URL, json=payload)
            print(f"✅ {name} 본문 전송: {response.status_code}")

if __name__ == "__main__":
    run_automation()
