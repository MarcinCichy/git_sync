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
            logger.error(f"Nie udało się utworzyć repozytorium {github_repo_name} na GitHub.")
            return

    # NOWA LOGIKA: porównywanie nie tylko commitów domyślnej gałęzi, ale i gałęzi
    if repo_exists:
        # Pobierz wszystkie gałęzie z GitLaba
        try:
            gitlab_branches = [b.name for b in gitlab_project.branches.list(all=True)]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania gałęzi z GitLab dla {original_repo_name}: {e}")
            gitlab_branches = []

        # Pobierz wszystkie gałęzie z GitHuba
        try:
            github_branches = [b.name for b in gh_repo.get_branches()]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania gałęzi z GitHub dla {github_repo_name}: {e}")
            github_branches = []

        # Porównaj domyślną gałąź (jak było)
        latest_commit_gitlab = gitlab_client.get_latest_commit(gitlab_project)
        default_branch = gitlab_project.default_branch or 'main'
        latest_commit_github = github_client.get_latest_commit(gh_repo, default_branch)

        # WARUNEK: czy repozytoria są identyczne? (commit na main i ten sam zestaw branchy)
        if (latest_commit_github == latest_commit_gitlab and set(gitlab_branches) == set(github_branches)):
            logger.info(f"Repozytorium {github_repo_name} jest już aktualne na GitHub (commity i gałęzie identyczne).")
            return
        else:
            logger.warning(f"Repozytorium {github_repo_name} wymaga synchronizacji (zmiany w branchach lub commitach).")

    # --- Jeżeli wymagana synchronizacja, wykonaj klonowanie i push ---
    try:
        with tempfile.TemporaryDirectory(prefix=f"{github_repo_name}_") as temp_dir:
            try:
                repo = Repo.clone_from(gitlab_repo_url, temp_dir)
                logger.info(f"Repozytorium {original_repo_name} zostało sklonowane do {temp_dir}.")
            except GitCommandError as e:
                logger.error(f"Błąd podczas klonowania repozytorium {original_repo_name} z GitLab: {e.stderr}")
                return

            # Konfiguracja remote do GitHub
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

            # Push wszystkich branchy i tagów
            try:
                origin.push(refspec='refs/heads/*:refs/heads/*', force=True)
                origin.push(refspec='refs/tags/*:refs/tags/*', force=True)
                logger.info(f"Repozytorium {github_repo_name} zostało pomyślnie zsynchronizowane na GitHub.")
            except GitCommandError as e:
                logger.error(f"Błąd podczas pushowania repozytorium {github_repo_name} na GitHub: {e.stderr}")
                return

            del origin
            del repo
            gc.collect()
            time.sleep(1)

    except Exception as e:
        logger.error(f"Błąd podczas obsługi katalogu tymczasowego dla repozytorium {github_repo_name}: {e}", exc_info=True)
