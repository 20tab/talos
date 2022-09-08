{% if "cluster" in cookiecutter.tfvars %}{% for item in cookiecutter.tfvars.cluster|sort %}{{ item }}
{% endfor %}{% endif %}
