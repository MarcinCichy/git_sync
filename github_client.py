from github import Github, GithubException
from config import Config

class GitHubClient:
    def __init__(self, logger):
        self.logger = logger
        self.token = Config.GITHUB_TOKEN  # Dodanie atrybutu token
        self.gh = Github(self.token)
        self.authenticate()

    def authenticate(self):
        try:
            self.gh_user = self.gh.get_user()
            self.logger.info("Pomyślnie uwierzytelniono się w GitHub.")
        except GithubException as e:
            self.logger.error(f"Uwierzytelnianie w GitHub nie powiodło się: {e}")
            exit(1)

    def get_repo(self, repo_name):
        try:
            repo = self.gh_user.get_repo(repo_name)
            return repo
        except GithubException as e:
            if e.status == 404:
                return None
            else:
                self.logger.error(f"Błąd podczas pobierania repozytorium {repo_name} na GitHub: {e.data}")
                return None

    def create_repo(self, repo_name, private, description):
        try:
            repo = self.gh_user.create_repo(
                name=repo_name,
                private=private,
                description=description
            )
            self.logger.info(f"Repozytorium {repo_name} zostało utworzone na GitHub.")
            return repo
        except GithubException as e:
            if e.status == 422 and any(error['message'] == 'name already exists on this account' for error in e.data.get('errors', [])):
                self.logger.warning(f"Repozytorium {repo_name} już istnieje na GitHub.")
                return self.get_repo(repo_name)
            else:
                self.logger.error(f"Błąd podczas tworzenia repozytorium {repo_name} na GitHub: {e.data}")
                return None

    def get_latest_commit(self, gh_repo, branch_name):
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
                self.logger.error(f"Błąd podczas pobierania najnowszego commita z GitHub dla {gh_repo.name}: {e}")
                return None
