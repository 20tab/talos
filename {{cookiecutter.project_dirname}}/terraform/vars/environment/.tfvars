{% for item in cookiecutter.tfvars.environment %}{{ item }}
{% endfor %}# database_connection_pool_size=1
# database_dumps_enabled=true
# backend_service_extra_traefik_middlewares=[]
# frontend_service_extra_traefik_middlewares=[]