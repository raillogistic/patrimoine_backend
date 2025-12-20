from django.core.management.base import BaseCommand
import os
import logging
import threading
import time
from clients.models import Client
from visa.models import Visa, VisaAccount
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command

logger = logging.getLogger('multirunner')


class CommandRunner(threading.Thread):
    def __init__(self, command, args):
        threading.Thread.__init__(self)
        self.command = command
        self.args = args
        self.stop_command = threading.Event()

    def run(self):

        # while not self.stop_command.is_set():
        #     print("qsmdlkqsmldksqmdlksqmlk")
        try:
            call_command(self.command, *self.args)
        except Exception as e:
            logging.error(e)
        time.sleep(1)

    def stop(self):
        self.stop_command.set()


class MultiTask:
    def __init__(self, tasks):
        self.threads = []
        for task, args in tasks:
            print("task", task)
            self.threads.append(CommandRunner(task, args))

    def start(self):
        for t in self.threads:
            t.start()

    def stop(self):
        for t in self.threads:
            t.stop()


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
        tasks = [('visa_germany', ['--client', client_id,
                                   '--visa', visa_id, '--account', account_id]), ]
        mt = MultiTask(tasks)
        mt.start()

        # client_id = kwargs['client']
        # visa_id = kwargs['visa']
        # account_id = kwargs['account']
        # if client_id:
        #     client = Client.objects.get(id=client_id)
        #     visa = Visa.objects.get(id=visa_id)
        #     account = VisaAccount.objects.get(id=account_id)
        # germany(client, visa, account)
