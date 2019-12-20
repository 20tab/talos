apiVersion: v1
kind: Secret
metadata:
  name: __ENVIRONMENT__-{{cookiecutter.project_slug}}-secrets
type: Opaque
stringData:
  DJANGO_ADMINS: {{cookiecutter.project_slug}},errors@{{cookiecutter.project_slug}}.com
  DJANGO_ALLOWED_HOSTS: 127.0.0.1,localhost
  DJANGO_DEBUG: True
  DJANGO_SECRET_KEY: secretkey
  DJANGO_SERVER_EMAIL: info@{{cookiecutter.project_slug}}.com
  EMAIL_URL: console:///
  POSTGRES_DB: {{cookiecutter.project_slug}}
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: password
  POSTGRES_HOST: 127.0.0.1
