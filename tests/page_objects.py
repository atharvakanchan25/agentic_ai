from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
class HomePage(BasePage):
    HEADER = (By.TAG_NAME, "header")
    CHATBOT_TOGGLE = (By.CLASS_NAME, "chatbot-toggle")
    PROGRESS_BAR = (By.CLASS_NAME, "progress-bar")
    
    def get_header_text(self):
        return self.wait.until(EC.presence_of_element_located(self.HEADER)).text
    
    def open_chatbot(self):
        self.wait.until(EC.element_to_be_clickable(self.CHATBOT_TOGGLE)).click()
        
class DataInputPage(BasePage):
    DEPT_TAB = (By.XPATH, "//button[contains(text(), 'Department')]")
    NAME_INPUT = (By.NAME, "name")
    CODE_INPUT = (By.NAME, "code")
    ADD_BTN = (By.XPATH, "//button[contains(text(), 'Add')]")
    PROCEED_BTN = (By.XPATH, "//button[contains(text(), 'Proceed')]")
    
    def add_department(self, name, code):
        self.wait.until(EC.element_to_be_clickable(self.DEPT_TAB)).click()
        self.driver.find_element(*self.NAME_INPUT).send_keys(name)
        self.driver.find_element(*self.CODE_INPUT).send_keys(code)
        self.driver.find_element(*self.ADD_BTN).click()
        
    def proceed_to_review(self):
        self.wait.until(EC.element_to_be_clickable(self.PROCEED_BTN)).click()

class ReviewPage(BasePage):
    GENERATE_BTN = (By.XPATH, "//button[contains(text(), 'Generate')]")
    BACK_BTN = (By.XPATH, "//button[contains(text(), 'Back')]")
    
    def generate_timetable(self):
        self.wait.until(EC.element_to_be_clickable(self.GENERATE_BTN)).click()
