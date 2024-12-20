import os
import gitlab
from github import Github, GithubException
from git import Repo, GitCommandError
from dotenv import load_dotenv
import gc
import time
import tempfile
import string
import logging
from colorlog import ColoredFormatter
import re

# Konfiguracja colorlog
formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s:%(levelname)s:%(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
)

# Konfiguracja loggera
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Handler dla pliku logów
file_handler = logging.FileHandler('sync_repos.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
logger.addHandler(file_handler)

# Handler dla konsoli z kolorami
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Ładowanie zmiennych środowiskowych z pliku .env
load_dotenv()

GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # GitHub token jest potrzebny do tworzenia repozytoriów
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')

def sanitize_description(description):
    """
    Funkcja do usuwania znaków kontrolnych i nowych linii z opisu repozytorium.
    """
    if description:
        sanitized = ''.join(char for char in description if char in string.printable and char not in ['\n', '\r'])
        # Usunięcie dodatkowych znaków specjalnych, jeśli to konieczne
        sanitized = re.sub(r'[^\x20-\x7E]', '', sanitized)
        return sanitized
    return ""

def sanitize_repo_name(name):
    """
    Przekształca nazwę repozytorium na zgodną z GitHub.
    - Zastępuje spacje myślnikami.
    - Usuwa niedozwolone znaki.
    """
    # Zastąpienie spacji myślnikami
    name = name.replace(' ', '-')
    # Usunięcie wszystkich znaków poza alfanumerycznymi, myślnikami i podkreśleniami
    name = re.sub(r'[^\w\-]', '', name)
    return name

def get_latest_commit_gitlab(project):
    """
    Pobiera najnowszy commit na domyślnej gałęzi z GitLab.
    """
    try:
        default_branch = project.default_branch or 'main'
        commits = project.commits.list(ref_name=default_branch, per_page=1, get_all=False)
        if commits:
            return commits[0].id
        return None
    except Exception as e:
        logger.error(f"Błąd podczas pobierania najnowszego commita z GitLab dla {project.name}: {e}")
        return None

def get_latest_commit_github(gh_repo, branch_name):
    """
    Pobiera najnowszy commit na określonej gałęzi z GitHub.
    """
    try:
        branch = gh_repo.get_branch(branch_name)
        return branch.commit.sha
    except GithubException as e:
        if e.status == 404:
            return None
        else:
            logger.error(f"Błąd podczas pobierania najnowszego commita z GitHub dla {gh_repo.name}: {e}")
            return None

# Inicjalizacja klienta GitLab
gl = gitlab.Gitlab('https://gitlab.com', private_token=GITLAB_TOKEN)
try:
    gl.auth()
    logger.info("Pomyślnie uwierzytelniono się w GitLab.")
except gitlab.exceptions.GitlabAuthenticationError as e:
    logger.error(f"Uwierzytelnianie w GitLab nie powiodło się: {e}")
    exit(1)

# Inicjalizacja klienta GitHub
gh = Github(GITHUB_TOKEN)
try:
    gh_user = gh.get_user()
    logger.info("Pomyślnie uwierzytelniono się w GitHub.")
except GithubException as e:
    logger.error(f"Uwierzytelnianie w GitHub nie powiodło się: {e}")
    exit(1)

# Pobranie wszystkich repozytoriów własnych z GitLab
try:
    projects = gl.projects.list(owned=True, per_page=100, iterator=True)
    projects_list = list(projects)
    logger.info(f"Pobrano {len(projects_list)} repozytoriów z GitLab.")
except gitlab.exceptions.GitlabListError as e:
    logger.error(f"Błąd podczas pobierania repozytoriów z GitLab: {e}")
    exit(1)

def sync_repo(gitlab_project):
    """
    Funkcja do synchronizacji pojedynczego repozytorium z GitLab do GitHub.
    """
    original_repo_name = gitlab_project.name
    github_repo_name = sanitize_repo_name(original_repo_name)

    # Konstrukcja URL HTTPS dla Gitlab i GitHub z tokenem
    #gitlab_repo_url = gitlab_project.http_url_to_repo
    #github_repo_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{github_repo_name}.git"

    # Konstrukcja URL SSH dla Gitlab i GitHub
    gitlab_repo_url = gitlab_project.ssh_url_to_repo
    github_repo_url = f"git@github.com:{GITHUB_USERNAME}/{github_repo_name}.git"

    logger.info(f"Synchronizowanie repozytorium: {original_repo_name}")

    # Sprawdzenie, czy repozytorium istnieje na GitHub
    repo_exists = False
    try:
        gh_repo = gh_user.get_repo(github_repo_name)
        repo_exists = True
        logger.info(f"Repozytorium {github_repo_name} istnieje na GitHub. Sprawdzanie aktualności...")
    except GithubException as e:
        if e.status == 404:
            # Repozytorium nie istnieje, tworzenie
            try:
                gh_repo = gh_user.create_repo(
                    name=github_repo_name,
                    private=gitlab_project.visibility == 'private',
                    description=sanitize_description(gitlab_project.description)
                )
                logger.info(f"Repozytorium {github_repo_name} zostało utworzone na GitHub.")
            except GithubException as e:
                if e.status == 422 and any(error['message'] == 'name already exists on this account' for error in e.data.get('errors', [])):
                    logger.warning(f"Repozytorium {github_repo_name} już istnieje na GitHub.")
                else:
                    logger.error(f"Błąd podczas tworzenia repozytorium {github_repo_name} na GitHub: {e.data}")
                return
        else:
            logger.error(f"Błąd podczas pobierania repozytorium {github_repo_name} na GitHub: {e.data}")
            return

    if repo_exists:
        # Pobranie najnowszego commita z GitLab
        latest_commit_gitlab = get_latest_commit_gitlab(gitlab_project)
        if not latest_commit_gitlab:
            logger.warning(f"Nie udało się pobrać najnowszego commita z GitLab dla {original_repo_name}.")
            return

        # Pobranie domyślnej gałęzi z GitLab
        default_branch = gitlab_project.default_branch or 'main'

        # Pobranie najnowszego commita z GitHub
        latest_commit_github = get_latest_commit_github(gh_repo, default_branch)

        if latest_commit_github == latest_commit_gitlab:
            logger.info(f"Repozytorium {github_repo_name} jest już aktualne na GitHub.")
            return
        else:
            logger.info(f"Repozytorium {github_repo_name} różni się od GitHub. Aktualizacja...")

    # Użycie tymczasowego katalogu do klonowania
    try:
        with tempfile.TemporaryDirectory(prefix=f"{github_repo_name}_") as temp_dir:
            try:
                repo = Repo.clone_from(gitlab_repo_url, temp_dir)
                logger.info(f"Repozytorium {original_repo_name} zostało sklonowane do {temp_dir}.")
            except GitCommandError as e:
                logger.error(f"Błąd podczas klonowania repozytorium {original_repo_name} z GitLab: {e.stderr}")
                return

            # Konfiguracja zdalnego repozytorium GitHub
            try:
                origin = repo.create_remote('github', github_repo_url)
                logger.info(f"Zdalne repozytorium GitHub zostało skonfigurowane.")
            except GitCommandError as e:
                if 'already exists' in str(e):
                    origin = repo.remotes.github
                    origin.set_url(github_repo_url)
                    logger.warning(f"Zdalne repozytorium GitHub już istnieje. URL zostało zaktualizowane.")
                else:
                    logger.error(f"Błąd podczas konfigurowania zdalnego repozytorium GitHub dla {github_repo_name}: {e.stderr}")
                    return

            # Pushowanie do GitHub z wymuszeniem
            try:
                origin.push(refspec='refs/heads/*:refs/heads/*', force=True)
                origin.push(refspec='refs/tags/*:refs/tags/*', force=True)
                logger.info(f"Repozytorium {github_repo_name} zostało pomyślnie zsynchronizowane na GitHub.")
            except GitCommandError as e:
                logger.error(f"Błąd podczas pushowania repozytorium {github_repo_name} na GitHub: {e.stderr}")
                return

            # Czyszczenie referencji
            del origin
            del repo
            gc.collect()
            time.sleep(1)  # Upewnienie się, że wszystkie uchwyty plików są zwolnione

    except Exception as e:
        logger.error(f"Błąd podczas obsługi katalogu tymczasowego dla repozytorium {github_repo_name}: {e}", exc_info=True)

# Iteracja po wszystkich projektach i synchronizacja
for project in projects_list:
    sync_repo(project)

logger.info("Synchronizacja zakończona.")
