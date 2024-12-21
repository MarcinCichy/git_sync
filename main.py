from config import Config
from logger import setup_logger
from gitlab_client import GitLabClient
from github_client import GitHubClient
from repo_sync import sync_repo

def main():
    logger = setup_logger()

    # Sprawdzenie, czy typ połączenia jest prawidłowy
    if Config.GITHUB_CONNECTION not in ['ssh', 'https']:
        logger.error("Nieprawidłowy typ połączenia. Ustaw `GITHUB_CONNECTION` na 'ssh' lub 'https' w pliku .env.")
        exit(1)

    # Inicjalizacja klientów GitLab i GitHub
    gitlab_client = GitLabClient(logger)
    github_client = GitHubClient(logger)

    # Pobranie wszystkich repozytoriów z GitLab
    projects_list = gitlab_client.get_projects()

    # Iteracja po wszystkich projektach i synchronizacja
    for project in projects_list:
        sync_repo(project, gitlab_client, github_client, logger, Config.GITHUB_CONNECTION)

    logger.info("Synchronizacja zakończona.")

if __name__ == "__main__":
    main()
