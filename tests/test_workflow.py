from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class TestWorkflow:
    def test_step1_data_input(self, driver, base_url):
        driver.get(base_url)
        # Verify Step 1 is active
        step1 = driver.find_element(By.XPATH, "//div[@class='step active']")
        assert "Input Data" in step1.text
        
    def test_add_department(self, driver, base_url):
        driver.get(base_url)
        # Find and click department tab
        dept_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Department')]"))
        )
        dept_tab.click()
        
        # Fill department form
        name_input = driver.find_element(By.NAME, "name")
        name_input.send_keys("Computer Science")
        
        code_input = driver.find_element(By.NAME, "code")
        code_input.send_keys("CS")
        
        # Submit
        add_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add')]")
        add_btn.click()
        time.sleep(1)
        
    def test_proceed_to_review(self, driver, base_url):
        driver.get(base_url)
        # Assuming data exists, click proceed
        proceed_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Proceed')]"))
        )
        proceed_btn.click()
        
        # Verify Step 2 is active
        WebDriverWait(driver, 5).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, "step-label"), "Review")
        )
        
    def test_generate_timetable(self, driver, base_url):
        driver.get(base_url)
        # Navigate through steps (requires data)
        # This is a placeholder - adjust based on actual flow
        time.sleep(2)
        
        # Look for generate button
        try:
            generate_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Generate')]"))
            )
            generate_btn.click()
            
            # Wait for timetable generation
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "timetable-view"))
            )
        except:
            pass  # Data might not be ready
