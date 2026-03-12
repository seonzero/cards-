"""
step1_parse.py의 파싱/검증 로직 테스트
실제 API 호출 없이 파싱 결과 시뮬레이션
"""
import json, sys
sys.path.insert(0, ".")

from step1_parse import validate_refined, VALID_CATEGORIES, VALID_BENEFIT_TYPES

from dotenv import load_dotenv
load_dotenv()

# ─── 시뮬레이션: Claude가 이런 JSON을 반환했다고 가정 ───
MOCK_RESULTS = {
    "ONE 체크카드": {
        "card_name": "ONE 체크카드",
        "company": "케이뱅크",
        "card_type": "체크",
        "image_url": "https://d1c5n4ri2guedi.cloudfront.net/card/2749/card_img/47326/2749card_1.png",
        "source_url": "https://www.card-gorilla.com/card/detail/2749",
        "fee": "해외겸용 없음",
        "required_performance": 0,
        "benefits": [
            {
                "category": "교통비",
                "benefit_type": "mileage",
                "benefit_value": 53.0,
                "benefit_unit": "%",
                "benefit_summary": "K-패스 대중교통 최대 53% 마일리지",
                "raw_description": "전국 어디서나 대중교통을 이용하고 이용금액의 20~53%를 적립받을 수 있어요"
            },
            {
                "category": "교통비",
                "benefit_type": "cashback_fixed",
                "benefit_value": 3000,
                "benefit_unit": "KRW",
                "benefit_summary": "대중교통 캐시백 3천원",
                "raw_description": "대중교통 5만원 이상 이용 시 매월 3천원 캐시백(전월실적 30만원 이상)"
            },
            {
                "category": "생활비",
                "benefit_type": "cashback_rate",
                "benefit_value": 1.1,
                "benefit_unit": "%",
                "benefit_summary": "온라인 1.1% / 오프라인 0.6% 캐시백",
                "raw_description": "오프라인 0.6% 캐시백: 국내 모든 오프라인 가맹점, 온라인 1.1% 캐시백"
            },
            {
                "category": "식비",
                "benefit_type": "cashback_rate",
                "benefit_value": 5.0,
                "benefit_unit": "%",
                "benefit_summary": "커피/편의점/배달 등 5% 캐시백",
                "raw_description": "6개 영역(커피, 편의점, OTT, 배달, 영화, 통신) 5% 캐시백, 월 25,000원 한도"
            },
            {
                "category": "기타",
                "benefit_type": "free_service",
                "benefit_value": None,
                "benefit_unit": None,
                "benefit_summary": "국내 ATM 수수료 무료 (월 30회)",
                "raw_description": "국내 모든 ATM 수수료 무료(입/출금, 이체 포함 월 30회까지)"
            }
        ]
    },
    "KB Youth Club 체크카드": {
        "card_name": "KB Youth Club 체크카드",
        "company": "KB국민카드",
        "card_type": "체크",
        "image_url": "https://d1c5n4ri2guedi.cloudfront.net/card/2929/card_img/45849/2929card_1.png",
        "source_url": "https://www.card-gorilla.com/card/detail/2929",
        "fee": "국내전용 없음 해외겸용 없음",
        "required_performance": 200000,
        "benefits": [
            {
                "category": "여가비",
                "benefit_type": "discount_rate",
                "benefit_value": 50.0,
                "benefit_unit": "%",
                "benefit_summary": "OTT/여가/교통/편의점/영화 최대 50% 할인 (A팩)",
                "raw_description": "A팩: OTT, APP, 여가, 교통, 편의점, 영화관 최대 50% 할인"
            },
            {
                "category": "쇼핑",
                "benefit_type": "discount_rate",
                "benefit_value": 50.0,
                "benefit_unit": "%",
                "benefit_summary": "쇼핑/통신/배달/편의점 최대 50% 할인 (B팩)",
                "raw_description": "B팩: 쇼핑 멤버십, 통신요금, 패션/라이프, 배달, 편의점, 데이트 최대 50% 할인"
            }
        ]
    },
    "신한카드 SOL트래블 체크": {
        "card_name": "신한카드 SOL트래블 체크",
        "company": "신한카드",
        "card_type": "체크",
        "image_url": "https://d1c5n4ri2guedi.cloudfront.net/card/2667/card_img/32473/2660card.png",
        "source_url": "https://www.card-gorilla.com/card/detail/2667",
        "fee": "국내전용 없음 해외겸용 없음",
        "required_performance": 0,
        "benefits": [
            {
                "category": "기타",
                "benefit_type": "free_service",
                "benefit_value": None,
                "benefit_unit": None,
                "benefit_summary": "해외 수수료 면제 (국제브랜드 1% + 서비스 0.2%)",
                "raw_description": "국제 브랜드 수수료(1%)/해외 서비스 수수료(0.2%) 면제, 전월실적 무관"
            },
            {
                "category": "여가비",
                "benefit_type": "free_service",
                "benefit_value": None,
                "benefit_unit": None,
                "benefit_summary": "공항라운지 무료 입장 (연 2회)",
                "raw_description": "더라운지 공항라운지 본인 무료 입장, 반기별 1회 연 2회, 전월실적 30만원 이상"
            },
            {
                "category": "생활비",
                "benefit_type": "discount_rate",
                "benefit_value": 5.0,
                "benefit_unit": "%",
                "benefit_summary": "국내 편의점 5% 할인",
                "raw_description": "GS25, CU, 세븐일레븐, 이마트24 5% 결제일 할인, 월 3천원 한도"
            },
            {
                "category": "교통비",
                "benefit_type": "discount_rate",
                "benefit_value": 1.0,
                "benefit_unit": "%",
                "benefit_summary": "국내 대중교통 1% 할인",
                "raw_description": "국내 대중교통 1% 결제일 할인, 월 3천원 한도, 전월실적 30만원 이상"
            },
            {
                "category": "여가비",
                "benefit_type": "discount_rate",
                "benefit_value": 5.0,
                "benefit_unit": "%",
                "benefit_summary": "해외(일본/베트남/미국) 편의점·마트 5% 할인",
                "raw_description": "일본 3대 편의점, 베트남 롯데마트·Grab, 미국 스타벅스 5% 할인"
            }
        ]
    }
}

def run_test():
    from pathlib import Path
    import os

    refined_dir = Path("data/refined")
    refined_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("Step 1 파싱 결과 검증 테스트 (mock)")
    print("=" * 50)

    all_pass = True
    for card_name, refined in MOCK_RESULTS.items():
        errors = validate_refined(refined)
        if errors:
            print(f"\n❌ {card_name}")
            for e in errors:
                print(f"   - {e}")
            all_pass = False
        else:
            benefit_count = len(refined["benefits"])
            categories = list({b["category"] for b in refined["benefits"]})
            print(f"\n✅ {card_name}")
            print(f"   혜택 수: {benefit_count}개")
            print(f"   카테고리: {categories}")
            for b in refined["benefits"]:
                val = f"{b['benefit_value']}{b['benefit_unit']}" if b['benefit_value'] else "무료제공"
                print(f"   [{b['category']}] {b['benefit_type']} → {val} | {b['benefit_summary']}")

            # 파일 저장
            out_path = refined_dir / f"{card_name}.json"
            out_path.write_text(json.dumps(refined, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*50}")
    if all_pass:
        print("✅ 모든 검증 통과!")
        print(f"정제 파일 저장됨: {refined_dir}/")
        print("\n다음 단계: python step2_load.py --db <DB_URL>")
    else:
        print("❌ 일부 검증 실패. 위 오류를 확인하세요.")

if __name__ == "__main__":
    run_test()
