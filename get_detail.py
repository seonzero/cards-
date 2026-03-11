# 혜택의 카테고리와 상세내용을 딕셔너리 구조로 변경
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

def get_card_detail(detail_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(detail_url)

    # 렌더링 대기
    time.sleep(2)

    try:
        condition = driver.find_element(By.CSS_SELECTOR, 'div.bnf2')
        fee = condition.find_element(By.CSS_SELECTOR, 'dd.in_out').text
        before_month = condition.find_element(By.CSS_SELECTOR, 'dl:nth-child(2)').text
    except:
        fee, before_month = "정보없음", "정보없음"

    benefit_list = []
    benefit_elements = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
    
    for idx, benefit in enumerate(benefit_elements):
        try:
            # 마지막 요소가 광고인 경우 제외
            if idx == len(benefit_elements) - 1: break
            
            driver.execute_script("arguments[0].scrollIntoView(true);", benefit)
            benefit.click()
            time.sleep(0.5)

            # AI가 읽기 좋게 구조화 (Column / Description 형태)
            main_title = benefit.find_element(By.CSS_SELECTOR, "dt p").text.strip()
            sub_title = benefit.find_element(By.CSS_SELECTOR, "dt i").text.strip()
            
            detail_el = benefit.find_elements(By.CSS_SELECTOR, "dd div.in_box p")
            detail_content = " ".join([e.text.strip() for e in detail_el])
            
            # 질문하신 형식에 맞춘 구조화
            benefit_list.append({
                "column": main_title,      # 혜택 종류 (예: 주유, 영화)
                "sub_column": sub_title,   # 요약 혜택 (예: 10% 할인)
                "description": detail_content # 상세 조건 설명
            })
            
            benefit.click() # 다시 닫기
        except Exception as e:
            continue

    driver.quit()

    return {
        "fee_info": fee,
        "performance": before_month,
        "benefits": benefit_list
    }