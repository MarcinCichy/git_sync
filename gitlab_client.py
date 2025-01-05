import gitlab
from config import Config


class GitLabClient:
    def __init__(self, logger):
        self.logger = logger
        self.gl = gitlab.Gitlab('https://gitlab.com', private_token=Config.GITLAB_TOKEN)
        self.authenticate()

    def authenticate(self):
        try:
            self.gl.auth()
            self.logger.info("Pomyślnie uwierzytelniono się w GitLab.")
        except gitlab.exceptions.GitlabAuthenticationError as e:
            self.logger.error(f"Uwierzytelnianie w GitLab nie powiodło się: {e}")
            exit(1)

    def get_projects(self):
        try:
            projects = self.gl.projects.list(owned=True, per_page=100, iterator=True)
            projects_list = list(projects)
            self.logger.info(f"Pobrano {len(projects_list)} repozytoriów z GitLab.")
            return projects_list
        except gitlab.exceptions.GitlabListError as e:
            self.logger.error(f"Błąd podczas pobierania repozytoriów z GitLab: {e}")
            exit(1)

    def get_latest_commit(self, project):
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
            self.logger.error(f"Błąd podczas pobierania najnowszego commita z GitLab dla {project.name}: {e}")
            return None
