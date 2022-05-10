{% if "cluster" in cookiecutter.tfvars %}{% for item in cookiecutter.tfvars.cluster|sort %}{{ item }}
{% endfor %}{% endif %}# grafana_user="admin"
# grafana_version="8.4.2"
