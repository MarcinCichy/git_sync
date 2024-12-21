import os
from dotenv import load_dotenv

# Ładowanie zmiennych środowiskowych z pliku .env
load_dotenv()

class Config:
    GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
    GITHUB_CONNECTION = os.getenv('GITHUB_CONNECTION', 'https').lower()  # Domyślnie HTTPS
