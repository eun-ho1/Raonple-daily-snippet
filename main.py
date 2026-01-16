import os
import requests
from datetime import datetime, timedelta

# 1. 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY', '8195198d-500e-4082-aefd-bab59bfda0bf')
API_URL = "여기에_실제_API_엔드포인트_주소를_입력하세요"

# 2. 팀원 매핑 (노션 이름 : 이메일)
TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "donggun_email@example.com",
    "유신": "yusin_email@example.com"
}

def get_target_date_kst():
    # KST 기준 어제 날짜 계산
    target_dt = datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)
    return target_dt.strftime("%Y-%m-%d")

def get_page_body_content(page_id):
    """페이지 ID를 받아 내부 본문의 줄바꿈을 보존하여 텍스트를 추출합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    blocks = response.json().get('results', [])
    
    lines = []
    for block in blocks:
        b_type = block['type']
        block_text = ""
        
        # 텍스트가 포함될 수 있는 주요 블록 타입들 처리
        if b_type in ['paragraph', 'bulleted_list_item', 'numbered_list_item', 'heading_1', 'heading_2', 'heading_3']:
            rich_texts = block[b_type].get('rich_text', [])
            # 한 블록 내부의 텍스트 조각들을 하나로 합침 (줄바꿈 없이)
            block_text = "".join([rt.get('plain_text', '') for rt in rich_texts])
            
            # 리스트 기호 추가
            if b_type == 'bulleted_list_item':
                block_text = f"• {block_text}"
            elif b_type == 'numbered_list_item':
                block_text = f"- {block_text}"
        
        # 빈 줄이든 내용이 있든 일단 한 줄로 간주하여 추가
        lines.append(block_text)

    # 1. 일반적인 줄바꿈(\n)으로 합침
    final_content = "\n".join(lines).strip()
    
    # 2. 만약 웹 페이지에서 줄바꿈이 안 보인다면 아래 주석(#)을 해제하고 사용하세요.
    # final_content = final_content.replace("\n", "<br>")
    
    return final_content

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    target_date = get_target_date_kst()
    print(f"조회 대상 날짜: {target_date}")

    query = {
        "filter": {
            "property": "날짜",
            "date": { "equals": target_date }
        }
    }
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    if not results:
        print(f"{target_date}의 데이터를 찾지 못했습니다.")
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
            print(f"✅ {name} 전송 성공: {response.status_code}")

if __name__ == "__main__":
    run_automation()
