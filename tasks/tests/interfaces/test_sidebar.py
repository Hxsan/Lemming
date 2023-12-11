from django.test import LiveServerTestCase
from django.urls import reverse
from tasks.models import User, Task, Team

from django.core.management import call_command

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class SidebarTestCase(LiveServerTestCase):

    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(self.live_server_url)
        self.create_teams(self.user)
        login_button = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/log_in/']")
        login_button.click()
        self.login_user(self.user)

    def login_user(self, user):
        username_field = self.driver.find_element(By.ID, "id_username")
        password_field = self.driver.find_element(By.ID, "id_password")
        login_submit = self.driver.find_element(By.CSS_SELECTOR, "input[value='Log in'][type='submit']")
        username_field.send_keys(self.user.username)
        password_field.send_keys("Password123")
        login_submit.click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'stretched-link'))
        )

    def create_teams(self, user): 
        team_names = ['Test Team 1', 'Test Team 2', 'Test Team 3']
        self.teams = []
        for team_name in team_names:
            team = Team.objects.create(
                team_name=team_name,
                admin_user=user,
            )
            team.members.set([user])
            self.teams.append(team)
        user.teams.set(self.teams)

    def tearDown(self):
        self.driver.quit()

    def test_sidebar_shows_all_teams_user_is_in(self):
        tabs = self.driver.find_elements(By.CSS_SELECTOR, '[role="tab"]')
        self.assertEqual(len(tabs), 3)
    
    def test_default_team_displayed_is_first_team(self):
        tabs = self.driver.find_elements(By.CSS_SELECTOR, '[role="tab"]')
        active_tab = None
        for tab in tabs:
            classes = tab.get_attribute('class')
            if 'active' in classes:
                active_tab = tab
                break
        self.assertEqual(active_tab.text, 'Test Team 1')
    
    def test_deleting_team_removes_it_from_sidebar(self):
        view_team_button = self.driver.find_element(By.XPATH, '//a[contains(@class, "view-team-button")]/ancestor::div[@class="card-body"]')
        view_team_button.click()
        
        delete_team_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[type="submit"]'))
        )

        delete_team_button.click()

        tabs = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[role="tab"]'))
        )

        # There should now be 2 tabs visible
        self.assertEqual(len(tabs), 2)

    def test_clicking_different_team_changes_content(self):
        tabs = self.driver.find_elements(By.CSS_SELECTOR, '[role="tab"]')

        # Clicks the 2nd team
        tabs[1].click()
        title2_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.tab-pane.active'))
        )
        title2 = title2_div.find_element(By.TAG_NAME, 'h3')

        # Checks if content changes accordingly
        self.assertNotIn('Test Team 1', title2.text)
        self.assertNotIn('Test Team 3', title2.text)
        self.assertIn('Test Team 2', title2.text)
        
        # Checks if URL changes accordingly
        url2 = self.driver.current_url
        self.assertIn(f'#{self.teams[1].id}', url2)

        # Clicks the 3rd team
        tabs[2].click()
        title3_div = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.tab-pane.active'))
        )
        title3 = title3_div.find_element(By.TAG_NAME, 'h3')

        # Checks if content changes accordingly
        self.assertNotIn('Test Team 1', title3.text)
        self.assertNotIn('Test Team 2', title3.text)
        self.assertIn('Test Team 3', title3.text)

        # Checks if URL changes accordingly
        url3 = self.driver.current_url
        self.assertIn(f'#{self.teams[2].id}', url3)
    
    def test_active_team_stays_active_on_dashboard_redirect(self):
        tabs = self.driver.find_elements(By.CSS_SELECTOR, '[role="tab"]')

        # Clicks the 2nd team
        tabs[1].click()

        view_team_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "view-team-button")]/ancestor::div[@class="card-body"]'))
        )

        # Clicks the view team button
        view_team_button.click()

        brand_name = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[class="navbar-brand"]'))
        )

        # Clicks the top right title (brand name)
        brand_name.click()

        tabs = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[role="tab"]'))
        )

        # Find the active tab
        for tab in tabs:
            classes = tab.get_attribute('class')
            if 'active' in classes:
                active_tab = tab
                break

        # Active tab must be the 2nd team
        self.assertEqual(active_tab.text, 'Test Team 2')
    
    def test_adding_team_ID_to_URL_changes_active_team(self):

        # Change URL by adding the 2nd team's team ID
        self.driver.get(self.driver.current_url + f'#{self.teams[1].id}')

        tabs1 = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[role="tab"]'))
        )

        # Find the active tab
        for tab in tabs1:
            classes = tab.get_attribute('class')
            if 'active' in classes:
                active_tab1 = tab
                break
        
        # Active tab must be the 2nd team
        self.assertEqual(active_tab1.text, 'Test Team 2')