import os
import gitlab
from github import Github
from git import Repo
import shutil
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')

# Inicjalizacja klienta GitLab
gl = gitlab.Gitlab('https://gitlab.com', private_token=GITLAB_TOKEN)
gl.auth()

# Inicjalizacja klienta GitHub
gh = Github(GITHUB_TOKEN)
gh_user = gh.get_user()

# Pobierz listę osobistych repozytoriów z GitLab
projects = gl.projects.list(owned=True, visibility='all', per_page=100, iterator=True)

# Funkcja do synchronizacji repozytorium
def sync_repo(gitlab_project):
    repo_name = gitlab_project.name
    gitlab_repo_url = gitlab_project.http_url_to_repo
    github_repo_name = repo_name
    github_repo_url = f"https://github.com/{GITHUB_USERNAME}/{github_repo_name}.git"

    print(f"Synchronizowanie repozytorium: {repo_name}")

    # Sprawdź czy repozytorium istnieje na GitHub
    try:
        gh_repo = gh_user.get_repo(github_repo_name)
        print(f"Repozytorium {github_repo_name} istnieje na GitHub. Aktualizacja...")
    except Exception as e:
        print(f"Repozytorium {github_repo_name} nie istnieje na GitHub. Tworzenie...")
        try:
            gh_repo = gh_user.create_repo(
                name=github_repo_name,
                private=gitlab_project.visibility == 'private',
                description=gitlab_project.description or ""
            )
            print(f"Repozytorium {github_repo_name} zostało utworzone na GitHub.")
        except Exception as e:
            print(f"Błąd podczas tworzenia repozytorium na GitHub: {e}")
            return

    # Klonuj repozytorium z GitLab
    temp_dir = f"./temp/{repo_name}"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        Repo.clone_from(gitlab_repo_url, temp_dir)
    except Exception as e:
        print(f"Błąd podczas klonowania repozytorium {repo_name} z GitLab: {e}")
        shutil.rmtree(temp_dir)
        return

    # Skonfiguruj remote do GitHub
    try:
        repo = Repo(temp_dir)
        if 'github' in repo.remotes:
            origin = repo.remotes.github
            origin.set_url(github_repo_url)
        else:
            origin = repo.create_remote('github', github_repo_url)
    except Exception as e:
        print(f"Błąd podczas konfigurowania remote GitHub: {e}")
        shutil.rmtree(temp_dir)
        return

    # Push do GitHub
    try:
        origin.push(refspec='refs/heads/*:refs/heads/*', force=True)
        origin.push(refspec='refs/tags/*:refs/tags/*', force=True)
        print(f"Repozytorium {repo_name} zostało zsynchronizowane na GitHub.")
    except Exception as e:
        print(f"Błąd podczas pushowania do GitHub: {e}")
    finally:
        # Usuń tymczasowe repozytorium
        shutil.rmtree(temp_dir)

# Synchronizuj każde repozytorium
for project in projects:
    sync_repo(project)

print("Synchronizacja zakończona.")
