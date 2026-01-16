import os
import requests
from datetime import datetime, timedelta

# 환경 변수 및 매핑 (기존 설정 유지)
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY', '8195198d-500e-4082-aefd-bab59bfda0bf')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8"

TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "donggun_email@example.com",
    "유신": "yusin_email@example.com"
}

def get_target_date_kst():
    # 현재 테스트를 위해 오늘 날짜 기준 (어제 데이터를 보내려면 - timedelta(days=1) 추가)
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")

def get_page_body_content(page_id):
    """노션 본문을 읽어 HTML 줄바꿈 형식으로 변환합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    blocks = response.json().get('results', [])
    
    lines = []
    num_counter = 1
    
    for block in blocks:
        b_type = block['type']
        
        # 텍스트 추출 가능 블록 처리
        if b_type in ['paragraph', 'bulleted_list_item', 'numbered_list_item', 'heading_1', 'heading_2', 'heading_3']:
            rich_texts = block[b_type].get('rich_text', [])
            text = "".join([rt.get('plain_text', '') for rt in rich_texts])
            
            # 1. 제목 블록인 경우 앞뒤로 빈 줄을 넣어 가독성 확보
            if b_type.startswith('heading_'):
                lines.append("") # 제목 위 빈 줄
                lines.append(f"<b>{text}</b>") # 제목은 굵게 처리 (지원될 경우)
                num_counter = 1
            
            # 2. 리스트 아이템 처리
            elif b_type == 'bulleted_list_item':
                lines.append(f"• {text}")
            elif b_type == 'numbered_list_item':
                lines.append(f"{num_counter}. {text}")
                num_counter += 1
            
            # 3. 일반 문단 처리
            else:
                if text.strip(): # 내용이 있을 때만 추가
                    lines.append(text)
                else: # 빈 줄인 경우
                    lines.append("")
                num_counter = 1
        
        elif b_type == 'divider':
            lines.append("<hr>") # 구분선
            num_counter = 1

    # ⭐️ 핵심 해결책: 모든 줄바꿈 문자를 <br> 태그로 변환
    content_with_newlines = "\n".join(lines).strip()
    html_content = content_with_newlines.replace("\n", "<br>")
    
    return html_content

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    target_date = get_target_date_kst()
    query = {"filter": {"property": "날짜", "date": {"equals": target_date}}}
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    for page in results:
        props = page['properties']
        member_data = props.get('팀원', {}).get('select') or props.get('팀원', {}).get('multi_select', [None])[0]
        if not member_data: continue
        
        name = member_data['name'].strip()
        if name in TEAM_INFO:
            email = TEAM_INFO[name]
            # HTML 줄바꿈이 적용된 본문 가져오기
            page_content = get_page_body_content(page['id'])

            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": page_content
            }
            
            response = requests.post(API_URL, json=payload)
            print(f"✅ {name} 전송 결과: {response.status_code}")

if __name__ == "__main__":
    run_automation()
