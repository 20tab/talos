# 20tab standard project

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![Build Status](https://travis-ci.com/20tab/20tab-standard-project.svg?branch=master)](https://travis-ci.com/20tab/20tab-standard-project?branch=master)

> A [20tab](https://www.20tab.com/) standard project cookiecutter template.

## 📝 Conventions

In the following instructions:

-   `projects` is your actual projects directory
-   `My Project Name` is your chosen project name

## 🧩 Requirements

### 🍪 Cookiecutter

[Cookiecutter](https://cookiecutter.readthedocs.io) must be installed in order to create and initialize the project structure.

```console
$ python3 -m pip install cookiecutter
```

### 🔀 Git

Install the `git` command-line, if the GitLab integration is needed.

-   🍏 macOS

    ```console
    $ brew install git
    ```

-   🐧 GNU/Linux

    ```console
    $ sudo apt install git
    ```

### 🦝 GitLab

#### 📦 Install

Install the `python-gitlab` package, if the GitLab integration is needed.

```console
$ python3 -m pip install python-gitlab
```

#### ✅ Token

A GitLab user account is required by the setup procedure to create the repositories, and by Kubernetes to pull the images from the Docker registry.

Make sure you have a local SSH key and have it associated with your GitLab account in the "SSH Keys" section in the settings.

Put the GitLab Access Token of the chosen user in an environment variable (e.g. export it in the command line or add it to the bash config).

```console
$ export GITLAB_PRIVATE_TOKEN={{ gitlab_private_token }}
```

**Note:** the access token can be generated from the GitLab settings "Access Tokens"
section. Make sure to give it full permission. Beware that GitLab only shows the token right after creation, and hides it thereafter.

## 🚀️ Quickstart

Change directory and create a new project as in this example:

# TODO: update example

```console

```

## 🚚 Setup

To configure the Kubernetes cluster now, read the [SETUP]({{ cookiecutter.project_slug }}/SETUP.md) documentation.
