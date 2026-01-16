import os
import requests
from datetime import datetime, timedelta

# 1. 환경 변수 및 매핑 (기존 설정 유지)
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY', '8195198d-500e-4082-aefd-bab59bfda0bf')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8"

TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "2donggeon@gachon.ac.kr",
    "유신": "wooxx3377@gachon.ac.kr",
    "형균": "gudrbs14@gachon.ac.kr"
}

def get_page_body_content(page_id):
    """줄바꿈과 리스트 번호를 보존하여 본문을 추출합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    blocks = response.json().get('results', [])
    
    lines = []
    num_counter = 1  # 숫자 리스트 번호 추적용
    
    for block in blocks:
        b_type = block['type']
        
        # 텍스트 추출 가능 블록 확인
        if b_type in ['paragraph', 'bulleted_list_item', 'numbered_list_item', 'heading_1', 'heading_2', 'heading_3']:
            rich_texts = block[b_type].get('rich_text', [])
            text = "".join([rt.get('plain_text', '') for rt in rich_texts])
            
            # 1. 동그라미 불렛 처리 (이미지의 What, Why, Highlight 등)
            if b_type == 'bulleted_list_item':
                text = f"• {text}"
                num_counter = 1 # 숫자 리스트 초기화
            
            # 2. 숫자 리스트 처리 (이미지의 Tomorrow 섹션 대응)
            elif b_type == 'numbered_list_item':
                text = f"{num_counter}. {text}"
                num_counter += 1
            
            # 3. 제목 처리 (가독성을 위해 앞뒤 줄바꿈 추가)
            elif b_type.startswith('heading_'):
                text = f"\n### {text}" # 볼드 처리나 여백 추가
                num_counter = 1
            
            else:
                num_counter = 1
                
            lines.append(text)
        else:
            # 텍스트가 없는 빈 줄이나 구분선 등 처리
            num_counter = 1
            if b_type == 'divider':
                lines.append("---")
            else:
                lines.append("")

    # 모든 라인을 줄바꿈으로 합침
    content = "\n".join(lines).strip()
    
    # ⭐️ 핵심 해결책: 만약 여전히 한 줄로 나온다면 아래 줄바꿈 변환을 활성화하세요.
    # Daily Snippet이 웹 화면이라면 \n 대신 <br>을 인식할 확률이 높습니다.
    # content = content.replace("\n", "<br>") 
    
    return content

# 나머지 run_automation 및 실행 로직은 이전과 동일하게 유지합니다.
