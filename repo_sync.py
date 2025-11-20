import tempfile
import gc
import time
from git import Repo, GitCommandError
from utils import sanitize_repo_name, sanitize_description


def sync_repo(gitlab_project, gitlab_client, github_client, logger, connection_type):
    """
    Synchronizuje pojedyncze repozytorium z GitLab do GitHub w trybie LUSTRZANYM (mirror).
    """
    original_repo_name = gitlab_project.name
    github_repo_name = sanitize_repo_name(original_repo_name)

    # Wybór URL na podstawie typu połączenia
    if connection_type == 'ssh':
        gitlab_repo_url = gitlab_project.ssh_url_to_repo
        github_repo_url = f"git@github.com:{github_client.gh_user.login}/{github_repo_name}.git"
    else:
        gitlab_repo_url = gitlab_project.http_url_to_repo
        github_repo_url = f"https://{github_client.token}@github.com/{github_client.gh_user.login}/{github_repo_name}.git"

    logger.info(f"Analiza repozytorium: {original_repo_name} -> {github_repo_name}")

    # 1. Sprawdzenie czy repozytorium istnieje na GitHub
    gh_repo = github_client.get_repo(github_repo_name)
    repo_exists = False

    if gh_repo:
        repo_exists = True
    else:
        # Tworzenie repozytorium na GitHub
        gh_repo = github_client.create_repo(
            repo_name=github_repo_name,
            private=gitlab_project.visibility == 'private',
            description=sanitize_description(gitlab_project.description)
        )
        if not gh_repo:
            logger.error(f"Nie udało się utworzyć ani znaleźć repozytorium {github_repo_name}.")
            return

    # 2. Logika sprawdzania czy synchronizacja jest potrzebna
    needs_sync = True

    if repo_exists:
        try:
            latest_commit_gitlab = gitlab_client.get_latest_commit(gitlab_project)
            default_branch = gitlab_project.default_branch or 'main'
            latest_commit_github = github_client.get_latest_commit(gh_repo, default_branch)

            # Pobieramy nazwy gałęzi jako zbiory (set)
            gitlab_branches = {b.name for b in gitlab_project.branches.list(all=True)}
            github_branches = {b.name for b in gh_repo.get_branches()}

            if latest_commit_github == latest_commit_gitlab and gitlab_branches == github_branches:
                logger.info(f"Repozytorium {github_repo_name} jest w pełni aktualne (commity i struktura gałęzi).")
                needs_sync = False
            else:
                logger.warning(f"Wykryto różnice w {github_repo_name}. Rozpoczynam synchronizację...")

        except Exception as e:
            logger.warning(f"Nie udało się zweryfikować statusu repozytorium, wymuszam synchronizację: {e}")
            needs_sync = True

    if not needs_sync:
        return

    # 3. Synchronizacja typu MIRROR
    try:
        with tempfile.TemporaryDirectory(prefix=f"{github_repo_name}_") as temp_dir:

            # A. KLONOWANIE Z OPCJĄ --mirror
            logger.info(f"Klonowanie (mirror) z GitLab...")
            try:
                repo = Repo.clone_from(
                    gitlab_repo_url,
                    temp_dir,
                    multi_options=['--mirror']
                )
            except GitCommandError as e:
                logger.error(f"Błąd klonowania {original_repo_name}: {e.stderr}")
                return

            # B. Konfiguracja remote GitHub
            try:
                if 'origin' in repo.remotes:
                    repo.delete_remote('origin')

                gh_remote = repo.create_remote('github_target', github_repo_url)
            except Exception as e:
                logger.error(f"Błąd konfiguracji remote: {e}")
                return

            # C. PUSH Z OPCJĄ --mirror
            logger.info(f"Wypychanie (mirror) do GitHub...")
            try:
                # --- TU BYŁ BŁĄD, TERAZ JEST POPRAWKA ---
                # Używamy argumentu nazwanego mirror=True, zamiast listy ['--mirror']
                gh_remote.push(mirror=True)
                logger.info(f"Sukces: {github_repo_name} zsynchronizowane.")
            except GitCommandError as e:
                logger.error(f"Błąd podczas pushowania do GitHub: {e.stderr}")
                return

            repo.close()
            del repo
            gc.collect()
            time.sleep(0.5)

    except Exception as e:
        logger.error(f"Nieoczekiwany błąd przy repozytorium {github_repo_name}: {e}", exc_info=True)