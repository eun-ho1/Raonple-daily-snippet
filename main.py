import os
import requests
from datetime import datetime, timedelta

# 환경 변수 설정 (기존과 동일)
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
    # KST 기준 어제 날짜 (1월 15일 실행 시 14일 데이터 전송)
    target_dt = datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)
    return target_dt.strftime("%Y-%m-%d")

def get_page_body_content(page_id):
    """노션 본문을 읽어 시스템이 무시하지 못하도록 강한 줄바꿈 형식을 생성합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    blocks = response.json().get('results', [])
    
    formatted_parts = []
    num_counter = 1
    
    for block in blocks:
        b_type = block['type']
        
        # 텍스트 추출
        if b_type in ['paragraph', 'bulleted_list_item', 'numbered_list_item', 'heading_1', 'heading_2', 'heading_3']:
            rich_texts = block[b_type].get('rich_text', [])
            text = "".join([rt.get('plain_text', '') for rt in rich_texts])
            
            if not text.strip(): # 빈 줄인 경우
                formatted_parts.append("\n")
                continue

            # 1. 제목 처리 (가독성을 위해 위아래로 빈 줄 추가)
            if b_type.startswith('heading_'):
                formatted_parts.append(f"\n\n**{text}**\n")
                num_counter = 1
            
            # 2. 동그라미 불렛 처리 (패턴 인식 개선을 위해 * 사용)
            elif b_type == 'bulleted_list_item':
                formatted_parts.append(f"• {text}\n")
            
            # 3. 숫자 리스트 처리 (정상 작동하는 패턴 유지)
            elif b_type == 'numbered_list_item':
                formatted_parts.append(f"{num_counter}. {text}\n")
                num_counter += 1
            
            # 4. 일반 문단
            else:
                formatted_parts.append(f"{text}\n")
                num_counter = 1
        
        elif b_type == 'divider':
            formatted_parts.append("\n---\n")
            num_counter = 1

    # 모든 파트를 합친 후, 다시 한 번 줄바꿈이 뭉치지 않도록 조정
    content = "".join(formatted_parts).strip()
    
    # 만약 여전히 뭉쳐 보인다면, 아래의 replace 구문을 활성화하세요.
    # content = content.replace("\n", "\n\n") 
    
    return content

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    target_date = get_target_date_kst()
    print(f"조회 날짜: {target_date}")

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
            page_content = get_page_body_content(page['id'])

            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": page_content
            }
            
            response = requests.post(API_URL, json=payload)
            print(f"✅ {name} 전송 완료: {response.status_code}")

if __name__ == "__main__":
    run_automation()
