import os
import requests
from datetime import datetime, timedelta

# 1. 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8" # 여기에 전달받은 API 주소를 꼭 넣어주세요.

TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "donggun_email@example.com",
    "유신": "yusin_email@example.com"
}

def get_target_date_kst():
    # KST 기준 어제 날짜 구하기
    target_dt = datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)
    return target_dt.strftime("%Y-%m-%d")

def extract_text_from_block(block):
    """블록 타입에 관계없이 내부의 rich_text를 추출합니다."""
    b_type = block.get('type')
    if not b_type: return ""
    
    # 해당 블록 타입 안의 rich_text 배열을 가져옴
    content = block.get(b_type, {})
    rich_texts = content.get('rich_text', [])
    return "".join([rt.get('plain_text', '') for rt in rich_texts])

def get_page_body_content(page_id):
    """페이지 내부의 모든 내용을 구조화된 텍스트로 변환합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "본문 데이터를 가져오지 못했습니다."

    blocks = response.json().get('results', [])
    formatted_lines = []
    num_counter = 1
    
    for block in blocks:
        b_type = block.get('type')
        text = extract_text_from_block(block)
        
        if not text.strip() and b_type != 'divider':
            continue

        # 2. 각 블록 타입별 맞춤 포맷팅 (이미지 7d48ed 재현)
        if b_type.startswith('heading'):
            # 제목(What, Why 등)은 위아래 간격을 위해 줄바꿈 두 번 추가
            formatted_lines.append(f"\n**{text}**")
            num_counter = 1 # 숫자 리스트 초기화
        elif b_type == 'bulleted_list_item':
            formatted_lines.append(f"• {text}")
        elif b_type == 'numbered_list_item':
            formatted_lines.append(f"{num_counter}. {text}")
            num_counter += 1
        elif b_type == 'divider':
            formatted_lines.append("---")
        else:
            # 일반 문단 등
            formatted_lines.append(text)

    # 3. 핵심: 시스템이 줄바꿈을 인식하도록 \n\n (이중 줄바꿈) 사용
    return "\n".join(formatted_lines).strip()

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    target_date = get_target_date_kst()
    print(f"📅 작업 날짜: {target_date}")

    query = {"filter": {"property": "날짜", "date": {"equals": target_date}}}
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    if not results:
        print("해당 날짜에 데이터가 없습니다.")
        return

    for page in results:
        props = page['properties']
        member_data = props.get('팀원', {}).get('select') or props.get('팀원', {}).get('multi_select', [None])[0]
        if not member_data: continue
        
        name = member_data['name'].strip()
        if name in TEAM_INFO:
            email = TEAM_INFO[name]
            # 본문의 상세 내용(불렛 포인트 포함)을 가져옴
            page_content = get_page_body_content(page['id'])

            # 전송할 데이터 구성
            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": page_content
            }
            
            # 최종 전송
            response = requests.post(API_URL, json=payload)
            print(f"🚀 {name} 전송 결과: {response.status_code}")
            # 전송되는 실제 텍스트 확인용 (디버깅)
            print(f"전송 내용 요약: {page_content[:50]}...")

if __name__ == "__main__":
    run_automation()
