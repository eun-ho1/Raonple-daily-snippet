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
    "동건": "2donggeon@gachon.ac.kr",
    "유신": "wooxx3377@gachon.ac.kr",
    "형균": "gudrbs14@gachon.ac.kr"
}

def get_target_date_kst():
    """실행 시점(KST)에서 하루를 뺀 '어제' 날짜 반환"""
    # GitHub Actions는 UTC 기준이므로 9시간을 더해 KST를 만든 후, 1일을 뺍니다.
    target_dt = datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)
    return target_dt.strftime("%Y-%m-%d")

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
        if block['type'] == 'paragraph':
            rich_texts = block['paragraph'].get('rich_text', [])
            for rt in rich_texts:
                full_text.append(rt.get('plain_text', ''))
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
    
    # ⭐️ 1월 15일 새벽 3시에 실행되면 1월 14일이 타겟이 됩니다.
    target_date = get_target_date_kst()
    print(f"조회 대상 날짜(어제): {target_date}")

    query = {
        "filter": {
            "property": "날짜",
            "date": { "equals": target_date }
        }
    }
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    if not results:
        print(f"{target_date} 날짜에 해당하는 데이터를 찾지 못했습니다.")
        return

    for page in results:
        page_id = page['id']
        props = page['properties']
        
        member_data = props.get('팀원', {}).get('select') or props.get('팀원', {}).get('multi_select', [None])[0]
        if not member_data: continue
        
        name = member_data['name'].strip()
        
        if name in TEAM_INFO:
            email = TEAM_INFO[name]
            page_content = get_page_body_content(page_id)
            
            if not page_content:
                title_list = props.get('제목', {}).get('title', [])
                page_content = title_list[0]['plain_text'] if title_list else "내용 없음"

            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": page_content
            }
            
            response = requests.post(API_URL, json=payload)
            print(f"✅ {name}({target_date}분) 전송: {response.status_code}")

if __name__ == "__main__":
    run_automation()
