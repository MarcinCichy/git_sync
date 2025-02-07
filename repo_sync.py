import tempfile
import gc
import time
from git import Repo, GitCommandError
from utils import sanitize_repo_name, sanitize_description


def sync_repo(gitlab_project, gitlab_client, github_client, logger, connection_type):
    """
    Synchronizuje pojedyncze repozytorium z GitLab do GitHub.

    Parameters:
        gitlab_project: Obiekt projektu z GitLab.
        gitlab_client: Instancja GitLabClient.
        github_client: Instancja GitHubClient.
        logger: Logger do logowania.
        connection_type: 'ssh' lub 'https'.
    """
    original_repo_name = gitlab_project.name
    github_repo_name = sanitize_repo_name(original_repo_name)

    # Wybór URL na podstawie typu połączenia
    if connection_type == 'ssh':
        gitlab_repo_url = gitlab_project.ssh_url_to_repo
        github_repo_url = f"git@github.com:{github_client.gh_user.login}/{github_repo_name}.git"
    else:
        # HTTPS z tokenem
        gitlab_repo_url = gitlab_project.http_url_to_repo
        github_repo_url = f"https://{github_client.token}@github.com/{github_client.gh_user.login}/{github_repo_name}.git"

    logger.info(f"Synchronizowanie repozytorium: {original_repo_name}")

    # Sprawdzenie, czy repozytorium istnieje na GitHub
    gh_repo = github_client.get_repo(github_repo_name)
    if gh_repo:
        logger.info(f"Repozytorium {github_repo_name} istnieje na GitHub. Sprawdzanie aktualności...")
        repo_exists = True
    else:
        # Tworzenie repozytorium na GitHub
        gh_repo = github_client.create_repo(
            repo_name=github_repo_name,
            private=gitlab_project.visibility == 'private',
            description=sanitize_description(gitlab_project.description)
        )
        if gh_repo:
            repo_exists = False
        else:
            # Nie udało się utworzyć repozytorium
            logger.error(f"Nie udało się utworzyć repozytorium {github_repo_name} na GitHub.")
            return

    if repo_exists:
        # Pobranie najnowszego commita z GitLab
        latest_commit_gitlab = gitlab_client.get_latest_commit(gitlab_project)
        if not latest_commit_gitlab:
            logger.warning(f"Nie udało się pobrać najnowszego commita z GitLab dla {original_repo_name}.")
            return

        # Pobranie domyślnej gałęzi z GitLab
        default_branch = gitlab_project.default_branch or 'main'

        # Pobranie najnowszego commita z GitHub
        latest_commit_github = github_client.get_latest_commit(gh_repo, default_branch)

        if latest_commit_github == latest_commit_gitlab:
            logger.info(f"Repozytorium {github_repo_name} jest już aktualne na GitHub.")
            return
        else:
            logger.warning(f"Repozytorium {github_repo_name} różni się od GitHub. Aktualizacja...")

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
                push_results = origin.push(all=True, force=True)  # Pushuje wszystkie gałęzie
                push_results_tags = origin.push(refspec='refs/tags/*:refs/tags/*', force=True)  # Pushuje wszystkie tagi

                # Sprawdzenie, czy push się powiódł
                push_failed = False
                for result in push_results + push_results_tags:
                    if result.flags & result.ERROR:
                        logger.error(f"Błąd podczas pushowania: {result.summary}")
                        push_failed = True

                if not push_failed:
                    logger.warning(f"Repozytorium {github_repo_name} zostało pomyślnie zsynchronizowane na GitHub.")
                else:
                    logger.warning(f"Repozytorium {github_repo_name} zostało zsynchronizowane, ale wystąpiły błędy podczas pushowania.")
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
