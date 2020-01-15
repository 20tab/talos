# cat post_gen_project.py
import os
import shutil
from cookiecutter.main import cookiecutter


def remove(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)
    elif os.path.isdir(filepath):
        shutil.rmtree(filepath)


def copy_secrets():
    
    with open("k8s/secrets.yaml.tpl", "r") as f:
        text = f.read()
        text_development = text.replace("__ENVIRONMENT__", "development")
        text_integration = text.replace("__ENVIRONMENT__", "integration")
        text_production = text.replace("__ENVIRONMENT__", "production")

        with open("k8s/development/secrets.yaml", "w+") as fd:
            fd.write(text_development)

        with open("k8s/integration/secrets.yaml", "w+") as fd:
            fd.write(text_integration)
        
        with open("k8s/production/secrets.yaml", "w+") as fd:
            fd.write(text_production)


def create_apps():
    os.system('./bin/init.sh')
    cookiecutter(
        'https://github.com/20tab/django-continuous-delivery',
        extra_context={
            'project_name': "{{cookiecutter.project_name}}",
            'static_url': "/backendstatic/"
        },
        no_input=True
    )
    cookiecutter(
        'https://github.com/20tab/react-continuous-delivery',
        extra_context={'project_name': "{{cookiecutter.project_name}}"},
        no_input=True
    )


copy_secrets()
create_apps()
