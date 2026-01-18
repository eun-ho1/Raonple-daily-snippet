import os
import requests
from datetime import datetime, timedelta

# 1. 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8" # 실제 URL로 교체 필수

# 2. 팀원 매핑
TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "donggun_email@example.com",
    "유신": "yusin_email@example.com"
}

def get_target_date_kst():
    """실행 시점 기준 어제 날짜를 가져옵니다."""
    # 현재 시간(UTC) + 9시간(KST) - 1일(어제)
    target_dt = datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)
    return target_dt.strftime("%Y-%m-%d")

def get_page_body_content(page_id):
    """노션 본문의 모든 텍스트(제목, 불렛, 번호)를 유실 없이 가져옵니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "본문 데이터를 가져오지 못했습니다."

    blocks = response.json().get('results', [])
    lines = []
    num_counter = 1
    
    for block in blocks:
        b_type = block.get('type')
        if not b_type: continue
        
        # 블록 안의 텍스트 데이터 추출
        content_data = block.get(b_type, {})
        rich_texts = content_data.get('rich_text', [])
        
        if not rich_texts:
            # 내용이 없는 빈 줄일 경우
            if b_type == 'paragraph':
                lines.append("") 
            continue
            
        text = "".join([rt.get('plain_text', '') for rt in rich_texts])
        
        # 3. 형식별 가공 (이미지 7d48ed의 구조 재현)
        if b_type.startswith('heading'):
            # 제목(What, Why 등)은 위아래 간격과 굵게 처리
            lines.append(f"<br><b>{text}</b>")
            num_counter = 1
        elif b_type == 'bulleted_list_item':
            # 불렛 포인트 유실 방지
            lines.append(f"• {text}")
        elif b_type == 'numbered_list_item':
            # 숫자 리스트
            lines.append(f"{num_counter}. {text}")
            num_counter += 1
        else:
            # 일반 문단 등
            lines.append(text)
            num_counter = 1

    # 모든 문장 사이에 <br>을 넣어 강제 줄바꿈 (뭉침 방지 핵심)
    return "<br>".join(lines).strip()

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 어제 날짜 데이터 조회
    target_date = get_target_date_kst()
    print(f"📅 조회 날짜: {target_date}")

    query = {
        "filter": {
            "property": "날짜",
            "date": { "equals": target_date }
        }
    }
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])
    print(f"📊 검색 결과: {len(results)}건 발견")

    for page in results:
        props = page['properties']
        
        # 팀원 이름 확인
        member_select = props.get('팀원', {}).get('select') or props.get('팀원', {}).get('multi_select', [None])[0]
        if not member_select: continue
        
        name = member_select['name'].strip()
        if name in TEAM_INFO:
            email = TEAM_INFO[name]
            # 본문 내용 추출
            page_content = get_page_body_content(page['id'])
            
            # 페이지의 실제 제목 가져오기
            title_data = props.get('제목', {}).get('title', [])
            page_title = title_data[0]['plain_text'] if title_data else "Daily Snippet"

            # 전송 데이터 구성
            full_html_content = f"<b>{page_title}</b><br>{page_content}"

            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": full_html_content
            }
            
            response = requests.post(API_URL, json=payload)
            print(f"🚀 {name}({email}) 전송 결과: {response.status_code}")

if __name__ == "__main__":
    run_automation()
