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

    time.sleep(2)  # JS 렌더링 대기

    condition = driver.find_element(By.CSS_SELECTOR, 'div.bnf2')
    fee = condition.find_element(By.CSS_SELECTOR, 'dd.in_out').text
    before_month = condition.find_element(By.CSS_SELECTOR, 'dl:nth-child(2)').text

    benefit_array = []

    benefit_elements = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
    for idx, benefit in enumerate(benefit_elements):
        try:
            if idx == len(benefit_elements) - 1:
                break
            if idx != 0:
                # 클릭 전에 요소가 보이도록 스크롤
                driver.execute_script("arguments[0].scrollIntoView(true);", benefit)
                # 요소가 clickable할 때까지 대기
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.bene_area dl")))

            benefit.click()
            time.sleep(0.5)  # 짧은 클릭 후 렌더링 대기
            main_title = benefit.find_element(By.CSS_SELECTOR, "dt p").text
            sub_title = benefit.find_element(By.CSS_SELECTOR, "dt i").text
            in_box = benefit.find_element(By.CSS_SELECTOR, "dd div.in_box")
            detail_el = in_box.find_elements(By.CSS_SELECTOR, "p")
            detail_content = ''
            for element in detail_el:
                detail_content += element.text.strip() + '\n'
            
            benefit_array.append({
                main_title,
                sub_title,
                detail_content
            })
            benefit.click()
            time.sleep(0.5)
        except Exception as e:
            print(f"[오류] 혜택 {idx+1} 클릭 또는 추출 실패: {e}")

    driver.quit()

    return {
        "fee": fee,
        "before_month": before_month,
        "benefits": benefit_array
    }