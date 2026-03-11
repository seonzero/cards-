# fix: 저장방식을 csv에서 json으로 변경
import json
import time
from get_top_100 import get_top100_cards 
from get_detail import get_card_detail 

all_cards = []
top_cards = get_top100_cards("2026-03-11")

for card in top_cards:
    print(f"구조화 수집 중: {card['name']}")
    try:
        detail = get_card_detail(card['detail_url'])
        
        # AI 입력을 위한 최종 데이터 모델링
        card_obj = {
            "card_name": card['name'],
            "company": card['corp'],
            "meta": {
                "url": card['detail_url'],
                "fee": detail['fee_info'],
                "required_performance": detail['performance']
            },
            "benefit_details": detail['benefits'] # 여기서 column/description 구조가 들어감
        }
        
        all_cards.append(card_obj)
        time.sleep(1)
    except Exception as e:
        print(f"오류 발생: {e}")

# 최종 결과를 JSON 파일로 저장
with open("card_data_for_ai.json", "w", encoding="utf-8") as f:
    json.dump(all_cards, f, ensure_ascii=False, indent=2)

print("AI용 구조화 데이터 생성 완료!")