from django.core.management.base import BaseCommand
import os
from clients.models import Client
from visa.models import Visa, VisaAccount
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.conf import settings
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def germany(client, visa, account):

    browser_options = Options()

    driver = webdriver.Chrome(
        executable_path=os.path.join(getattr(settings, 'BASE_DIR', ),
                                     'raillogistic/management/commands/chromedriver'), options=browser_options)
    driver.get(account.link)
    print("aaaaaaaaaaa")
    element = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, "email"))
    )
    print("xsqkmldkqsmdlk")
    driver.find_element_by_id("email").send_keys(account.email)
    driver.find_element_by_id("pwd").send_keys(account.password)
    time.sleep(30)


class Command(BaseCommand):
    help = 'Displays current time'

    def add_arguments(self, parser):
        parser.add_argument('--client', type=str,
                            help='client')
        parser.add_argument('--visa', type=str,
                            help='visa')

        parser.add_argument('--account', type=str,
                            help='Account')

    def handle(self, *args, **kwargs):
        client_id = kwargs['client']
        visa_id = kwargs['visa']
        account_id = kwargs['account']
        print(client_id, visa_id, account_id)
        if client_id:

            client = Client.objects.get(id=client_id)
            visa = Visa.objects.get(id=visa_id)
            account = VisaAccount.objects.get(id=account_id)
            germany(client, visa, account)
