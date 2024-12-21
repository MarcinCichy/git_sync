# Git Sync

Git Sync is a Python-based tool designed to automate the synchronization of your repositories from GitLab to GitHub. It streamlines the process of cloning repositories from GitLab and pushing them to GitHub, ensuring your repositories are consistently up-to-date across both platforms. The tool supports both SSH and HTTPS connections, providing flexibility based on your preferred authentication method.

## Table of Contents

- [Git Sync](#git-sync)
  - [Features](#features)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
  - [Choosing Connection Type](#choosing-connection-type)
    - [SSH Setup](#ssh-setup)
    - [HTTPS Setup](#https-setup)
  - [Project Structure](#project-structure)
  - [Troubleshooting](#troubleshooting)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- **Automated Synchronization**: Syncs all your owned repositories from GitLab to GitHub.
- **SSH and HTTPS Support**: Choose between SSH and HTTPS for connecting to GitHub.
- **Sanitization**: Automatically sanitizes repository names and descriptions to comply with GitHub’s requirements.
- **Logging**: Detailed logging with color-coded console output and log files for easy monitoring.
- **Modular Structure**: Organized codebase divided into logical modules for better maintainability and scalability.
- **Secure**: Uses environment variables to manage sensitive information like tokens.

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

2. **Create a Virtual Environment (Optional but Recommended)**

    ```bash
    python -m venv .venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
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
    # Access Tokens
    GITLAB_TOKEN=your_gitlab_token
    GITHUB_TOKEN=your_github_token
    GITHUB_USERNAME=your_github_username

    # GitHub Connection Type (ssh or https)
    GITHUB_CONNECTION=https
    ```

    **Notes:**
    - Ensure that the `.env` file is added to `.gitignore` to prevent accidental publication.

    - **GITLAB_TOKEN**: Your GitLab personal access token with appropriate permissions.
    - **GITHUB_TOKEN**: Your GitHub personal access token with repo scope if using HTTPS.
    - **GITHUB_USERNAME**: Your GitHub username.
    - **GITHUB_CONNECTION**: Choose ssh or https based on your preferred connection type.

    
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
    python main.py
    ```

    **Description:**
    - The script will fetch all your personal repositories from GitLab and synchronize them to GitHub. If a repository does not exist on GitHub, it will be created. All branches and tags will be pushed to GitHub.

## Choosing Connection Type

You can choose between SSH and HTTPS for connecting to GitHub by setting the GITHUB_CONNECTION variable in your .env file.

## SSH Setup
If you prefer using SSH for authentication, follow these steps:

1. **Set Connection Type to SSH**

    ```bash
    env
    
    GITHUB_CONNECTION=ssh
    ```

2. **Generate SSH Key (If Not Already Done)**

    ```bash
    
    ssh-keygen -t ed25519 -C "your_email@example.com"
    ```
    Follow the prompts to generate the key pair. By default, keys are stored in ~/.ssh/id_ed25519 and ~/.ssh/id_ed25519.pub.


3. **Add SSH Key to ssh-agent**

    ```bash
    
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519
    ```
4. **Add SSH Key to GitHub**

   - Copy the contents of your public key to the clipboard:

    ```bash
    cat ~/.ssh/id_ed25519.pub
    ```
    - Go to GitHub Settings > SSH and GPG keys > New SSH key.

    - Paste the key and save.

5. **Test SSH Connection**

    ```bash
    
    ssh -T git@github.com
    ```
    You should see a message like:

    ```vbnet
    Hi YourUsername! You've successfully authenticated, but GitHub does not provide shell access.
    ```
## HTTPS Setup
If you prefer using HTTPS for authentication, follow these steps:

1. **Set Connection Type to HTTPS**

    ```bash
    env
   GITHUB_CONNECTION=https
    ```
2. **Create a GitHub Personal Access Token (PAT)**


- Go to GitHub Settings.
- Click on Generate new token.
- Select the repo scope for full access to your repositories.
- Generate and copy the token.
3. **Add PAT to .env**

    Ensure your .env file includes your PAT as GITHUB_TOKEN:
    ```bash
    env
    GITHUB_TOKEN=your_github_token
    ```
4. **Test HTTPS Connection**

    The script will automatically use the PAT to authenticate when pushing via HTTPS.


## Security

- **Storing Tokens:**
  - Ensure that the `.env` file is added to `.gitignore` to prevent it from being published to the repository.
  - Consider using more secure authentication methods, such as SSH or a `.netrc` file.

- **Limiting Token Permissions:**
  - Create tokens with the minimum required permissions to reduce the risk in case they are exposed.

## Project Structure
```bash
git_sync/
│
├── main.py
├── config.py
├── logger.py
├── gitlab_client.py
├── github_client.py
├── repo_sync.py
├── utils.py
├── requirements.txt
└── .env
```
### Description of Files
- **main.py**: The entry point of the application. It initializes clients, retrieves repositories, and triggers synchronization.
- **config.py**: Handles configuration and environment variables.
- **logger.py**: Sets up logging with color-coded output and file logging.
- **gitlab_client.py**: Manages interactions with the GitLab API.
- **github_client.py**: Manages interactions with the GitHub API.
- **repo_sync.py**: Contains the logic to synchronize individual repositories.
- **utils.py**: Utility functions for sanitizing repository names and descriptions.
- **requirements.txt**: Lists Python dependencies.
- **.env**: Stores configuration variables and secrets (not tracked by version control).



## Contributing

We welcome contributions to this project! If you have suggestions, bug fixes, or want to add new features, please create a pull request or open an issue.

## License

This project is licensed under the [MIT License](LICENSE).

---

**Disclaimer:** Ensure you understand the security implications of storing access tokens and using `push --force` operations, which can overwrite data on GitHub. Always back up important data before running automated synchronization scripts.
