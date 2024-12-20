import os
import gitlab
from github import Github, GithubException
from git import Repo, GitCommandError
import shutil
from dotenv import load_dotenv
import gc
import time
import tempfile
import string
import logging

# Konfiguracja logowania do pliku oraz konsoli
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler('sync_repos.log'),
        logging.StreamHandler()
    ]
)

# Ładowanie zmiennych środowiskowych z pliku .env
load_dotenv()

GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Opcjonalnie, jeśli używasz SSH
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')

def sanitize_description(description):
    """
    Funkcja do usuwania znaków kontrolnych i nowych linii z opisu repozytorium.
    """
    if description:
        # Usunięcie znaków kontrolnych i nowych linii
        return ''.join(char for char in description if char in string.printable and char not in ['\n', '\r'])
    return ""

# Inicjalizacja klienta GitLab
gl = gitlab.Gitlab('https://gitlab.com', private_token=GITLAB_TOKEN)
try:
    gl.auth()
    logging.info("Pomyślnie uwierzytelniono się w GitLab.")
except gitlab.exceptions.GitlabAuthenticationError as e:
    logging.error(f"Uwierzytelnianie w GitLab nie powiodło się: {e}")
    exit(1)

# Inicjalizacja klienta GitHub
gh = Github(GITHUB_TOKEN)  # GitHub token jest potrzebny do tworzenia repozytoriów
try:
    gh_user = gh.get_user()
    logging.info("Pomyślnie uwierzytelniono się w GitHub.")
except GithubException as e:
    logging.error(f"Uwierzytelnianie w GitHub nie powiodło się: {e}")
    exit(1)

# Pobranie wszystkich repozytoriów własnych z GitLab
try:
    projects = gl.projects.list(owned=True, per_page=100, iterator=True)
    projects_list = list(projects)
    logging.info(f"Pobrano {len(projects_list)} repozytoriów z GitLab.")
except gitlab.exceptions.GitlabListError as e:
    logging.error(f"Błąd podczas pobierania repozytoriów z GitLab: {e}")
    exit(1)

def sync_repo(gitlab_project):
    """
    Funkcja do synchronizacji pojedynczego repozytorium z GitLab do GitHub.
    """
    repo_name = gitlab_project.name
    gitlab_repo_url = gitlab_project.ssh_url_to_repo  # Używanie URL SSH dla GitLab
    github_repo_name = repo_name

    # Konstrukcja URL SSH dla GitHub
    github_repo_url = f"git@github.com:{GITHUB_USERNAME}/{github_repo_name}.git"

    logging.info(f"Synchronizowanie repozytorium: {repo_name}")

    # Sprawdzenie, czy repozytorium istnieje na GitHub
    try:
        gh_repo = gh_user.get_repo(github_repo_name)
        logging.info(f"Repozytorium {github_repo_name} istnieje na GitHub. Aktualizacja...")
    except GithubException as e:
        if e.status == 404:
            # Repozytorium nie istnieje, tworzenie
            try:
                gh_repo = gh_user.create_repo(
                    name=github_repo_name,
                    private=gitlab_project.visibility == 'private',
                    description=sanitize_description(gitlab_project.description)
                )
                logging.info(f"Repozytorium {github_repo_name} zostało utworzone na GitHub.")
            except GithubException as e:
                logging.error(f"Błąd podczas tworzenia repozytorium {github_repo_name} na GitHub: {e.data}")
                return
        else:
            logging.error(f"Błąd podczas pobierania repozytorium {github_repo_name} na GitHub: {e.data}")
            return

    # Użycie tymczasowego katalogu do klonowania
    try:
        with tempfile.TemporaryDirectory(prefix=f"{repo_name}_") as temp_dir:
            try:
                repo = Repo.clone_from(gitlab_repo_url, temp_dir)
                logging.info(f"Repozytorium {repo_name} zostało sklonowane do {temp_dir}.")
            except GitCommandError as e:
                logging.error(f"Błąd podczas klonowania repozytorium {repo_name} z GitLab: {e.stderr}")
                return

            # Konfiguracja zdalnego repozytorium GitHub
            try:
                origin = repo.create_remote('github', github_repo_url)
                logging.info(f"Zdalne repozytorium GitHub zostało skonfigurowane.")
            except GitCommandError as e:
                if 'already exists' in str(e):
                    origin = repo.remotes.github
                    origin.set_url(github_repo_url)
                    logging.info(f"Zdalne repozytorium GitHub już istnieje. URL zostało zaktualizowane.")
                else:
                    logging.error(f"Błąd podczas konfigurowania zdalnego repozytorium GitHub dla {github_repo_name}: {e.stderr}")
                    return

            # Pushowanie do GitHub z wymuszeniem
            try:
                origin.push(refspec='refs/heads/*:refs/heads/*', force=True)
                origin.push(refspec='refs/tags/*:refs/tags/*', force=True)
                logging.info(f"Repozytorium {repo_name} zostało pomyślnie zsynchronizowane na GitHub.")
            except GitCommandError as e:
                logging.error(f"Błąd podczas pushowania repozytorium {repo_name} na GitHub: {e.stderr}")
                return

            # Czyszczenie referencji
            del origin
            del repo
            gc.collect()
            time.sleep(1)  # Upewnienie się, że wszystkie uchwyty plików są zwolnione

    except Exception as e:
        logging.error(f"Błąd podczas obsługi katalogu tymczasowego dla repozytorium {repo_name}: {e}", exc_info=True)

# Iteracja po wszystkich projektach i synchronizacja
for project in projects_list:
    sync_repo(project)

logging.info("Synchronizacja zakończona.")
