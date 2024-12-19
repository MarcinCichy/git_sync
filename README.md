# GitLab to GitHub Repository Sync

An automated Python script to synchronize your personal repositories from GitLab to GitHub, keeping GitLab as the primary source. Repositories on GitHub are updated or created based on the state of your repositories on GitLab.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Automation](#automation)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Repository Synchronization:** Automatically clones and pushes repositories from GitLab to GitHub.
- **GitHub Repository Creation:** If a repository does not exist on GitHub, it is automatically created.
- **Repository Updates:** GitHub repositories are overwritten with the latest changes from GitLab.
- **Branch and Tag Support:** Synchronizes all branches and tags from GitLab to GitHub.
- **Security:** Access tokens are stored in a `.env` file, which is ignored by Git.

## Requirements

- Python 3.8 or higher
- GitLab and GitHub accounts
- Personal Access Tokens (PAT) for both platforms
- Permissions to create repositories on GitHub

## Installation

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/YourUsername/gitlab-to-github-sync.git
    cd gitlab-to-github-sync
    ```

2. **Create and Activate a Virtual Environment:**

    ```bash
    python -m venv .venv
    ```

    - **On Unix/Linux/MacOS:**

      ```bash
      source .venv/bin/activate
      ```

    - **On Windows:**

      ```bash
      .\.venv\Scripts\activate
      ```

3. **Install Required Packages:**

    ```bash
    pip install -r requirements.txt
    ```

    If you don't have a `requirements.txt` file, install the packages manually:

    ```bash
    pip install python-gitlab PyGithub gitpython python-dotenv
    ```

## Configuration

1. **Generate Personal Access Tokens (PAT):**

    - **GitLab:**
      - Log in to GitLab.
      - Navigate to `User Settings` > `Access Tokens`.
      - Create a new token with `read_api` and `write_repository` permissions.
      - Copy the token.

    - **GitHub:**
      - Log in to GitHub.
      - Navigate to [Settings](https://github.com/settings/tokens) > `Developer settings` > `Personal access tokens`.
      - Create a new token with `repo` permissions.
      - Copy the token.

2. **Create a `.env` File:**

    In the project directory, create a `.env` file and add your tokens and GitHub username:

    ```env
    GITLAB_TOKEN=your_gitlab_token
    GITHUB_TOKEN=your_github_token
    GITHUB_USERNAME=your_github_username
    ```

    **Notes:**
    - Ensure that the `.env` file is added to `.gitignore` to prevent accidental publication.

3. **Add `.env` to `.gitignore`:**

    If you don't have a `.gitignore` file yet, create one and add the following:

    ```gitignore
    .env
    /temp/
    ```

## Usage

1. **Activate the Virtual Environment:**

    - **On Unix/Linux/MacOS:**

      ```bash
      source .venv/bin/activate
      ```

    - **On Windows:**

      ```bash
      .\.venv\Scripts\activate
      ```

2. **Run the Script:**

    ```bash
    python sync_repos.py
    ```

    **Description:**
    - The script will fetch all your personal repositories from GitLab and synchronize them to GitHub. If a repository does not exist on GitHub, it will be created. All branches and tags will be pushed to GitHub.

## Automation

To automatically synchronize repositories at regular intervals, you can set up a cron job (on Unix/Linux/MacOS) or use Task Scheduler (on Windows).

### Example Cron Job (Unix/Linux/MacOS)

1. **Open Crontab:**

    ```bash
    crontab -e
    ```

2. **Add a Line to Sync Daily at 2:00 AM:**

    ```cron
    0 2 * * * /path/to/git_sync/.venv/bin/python /path/to/git_sync/sync_repos.py >> /path/to/git_sync/sync.log 2>&1
    ```

### Example Task Scheduler (Windows)

1. **Open Task Scheduler:**
   - `Start` > `Administrative Tools` > `Task Scheduler`

2. **Create a New Task:**
   - Click `Create Task` and configure the appropriate settings, such as name, trigger time, and actions (running Python and the script).

## Security

- **Storing Tokens:**
  - Ensure that the `.env` file is added to `.gitignore` to prevent it from being published to the repository.
  - Consider using more secure authentication methods, such as SSH or a `.netrc` file.

- **Limiting Token Permissions:**
  - Create tokens with the minimum required permissions to reduce the risk in case they are exposed.

## Contributing

We welcome contributions to this project! If you have suggestions, bug fixes, or want to add new features, please create a pull request or open an issue.

## License

This project is licensed under the [MIT License](LICENSE).

---

**Disclaimer:** Ensure you understand the security implications of storing access tokens and using `push --force` operations, which can overwrite data on GitHub. Always back up important data before running automated synchronization scripts.
