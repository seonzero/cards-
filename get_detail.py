from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


def get_card_detail(detail_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 5)

    driver.get(detail_url)
    time.sleep(2)

    # 연회비 / 전월실적
    try:
        condition = driver.find_element(By.CSS_SELECTOR, 'div.bnf2')
        fee = condition.find_element(By.CSS_SELECTOR, 'dd.in_out').text
        before_month = condition.find_element(By.CSS_SELECTOR, 'dl:nth-child(2)').text
    except:
        fee, before_month = "정보없음", "정보없음"

    benefit_list = []
    benefit_elements = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
    total = len(benefit_elements)

    for idx in range(total - 1):  # 마지막은 광고 제외
        # 매 루프마다 dl 목록 새로 가져오기 (클릭 후 DOM 변경 대응)
        benefit_elements = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
        benefit = benefit_elements[idx]

        try:
            main_title = benefit.find_element(By.CSS_SELECTOR, "dt p").text.strip()
            sub_title = benefit.find_element(By.CSS_SELECTOR, "dt i").text.strip()
        except:
            main_title, sub_title = "", ""

        # 클릭해서 dd 생성 대기
        try:
            benefit.click()
            # dd > div.in_box 가 실제로 DOM에 생길 때까지 대기
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"div.bene_area dl.on dd div.in_box")
            ))
        except:
            pass

        # 클릭 후 다시 해당 dl 가져오기
        try:
            benefit_elements = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
            benefit = benefit_elements[idx]
            detail_els = benefit.find_elements(By.CSS_SELECTOR, "dd div.in_box p")
            detail_content = "\n".join([e.text.strip() for e in detail_els if e.text.strip()])
        except:
            detail_content = ""

        benefit_list.append({
            "column": main_title,
            "sub_column": sub_title,
            "description": detail_content
        })

        # 닫기 (다음 항목을 위해)
        try:
            benefit_elements = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
            benefit_elements[idx].click()
            time.sleep(0.2)
        except:
            pass

    driver.quit()

    return {
        "fee_info": fee,
        "performance": before_month,
        "benefits": benefit_list
    }