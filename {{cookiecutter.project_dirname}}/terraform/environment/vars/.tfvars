{% if "environment" in cookiecutter.tfvars %}{% for item in cookiecutter.tfvars.environment|sort %}{{ item }}
{% endfor %}{% endif %}# database_connection_pool_size=1
# database_dumps_enabled=true
# backend_service_extra_traefik_middlewares=[]
# frontend_service_extra_traefik_middlewares=[]
