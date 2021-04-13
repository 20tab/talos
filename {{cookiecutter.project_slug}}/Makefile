.DEFAULT_GOAL := help

c = {{cookiecutter.project_slug}}_backend
p = shell
.PHONY: django
django_shell:  ## Exec django command 
	docker exec -it $(c) python manage.py $(p)

.PHONY: pull
pull:  ## Pull develop on orchestrator, frontend and backend 
	git checkout develop && git pull && \
	cd backend && git checkout develop && git pull && \{% if cookiecutter.which_frontend in ["React"] %}
	cd ../frontend && git checkout develop && git pull && \{% endif %}
	cd ..

s =
.PHONY: rebuild
rebuild:  ## Rebuild container
	docker-compose stop $(s) && docker-compose rm -f $(s) && docker-compose up -d --build $(s)

help:
	@echo "[Help] Makefile list commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
