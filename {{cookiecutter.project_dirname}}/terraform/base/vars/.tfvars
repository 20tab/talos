{% if "base" in cookiecutter.tfvars %}{% for item in cookiecutter.tfvars.base|sort %}{{ item }}
{% endfor %}{% endif %}# database_cluster_engine="pg"
# database_cluster_node_count=1
# database_cluster_version="14"
# k8s_cluster_node_count=1
# k8s_cluster_node_size=""
# k8s_cluster_version=""
# redis_cluster_node_count=1
# redis_cluster_version="7"
