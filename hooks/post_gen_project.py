# cat post_gen_project.py
import os
import shutil


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


copy_secrets()
