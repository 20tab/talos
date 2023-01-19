.DEFAULT_GOAL := help

c = {{ cookiecutter.project_slug }}_backend
p = shell
.PHONY: django
django_shell:  ## Exec django command
	docker exec -it $(c) python manage.py $(p)

.PHONY: pull
pull:  ## Pull develop on all services
	git checkout main && git pull && \{% if cookiecutter.backend_type != 'none' %}
	cd {{ cookiecutter.backend_service_slug }} && git checkout develop && git pull && \{% endif %}{% if cookiecutter.frontend_type != 'none' %}
	cd ../{{ cookiecutter.frontend_service_slug }} && git checkout develop && git pull && \{% endif %}
	cd ..

s =
.PHONY: rebuild
rebuild:  ## Rebuild container
	docker-compose stop $(s) && docker-compose rm -f $(s) && docker-compose up -d --build $(s)

trivy_target = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`
.PHONY: trivy
trivy:  ## Run image vulnerabilities scan with 'trivy'
	docker run --rm \
	--entrypoint="" \
	--env CUSTOM_GID=`id --group` \
	--env CUSTOM_UID=`id --user` \
	--env REPORT_NAME=$(call trivy_target) \
	--env TARGET_IMAGE={{ cookiecutter.project_slug }}_$(call trivy_target):latest \
	--env TRIVY_CACHE_DIR=.trivycache/ \
	--env TRIVY_NO_PROGRESS=true \
	--name trivy-{{ cookiecutter.project_slug }}-$(call trivy_target) \
	--volume /var/run/docker.sock:/var/run/docker.sock \
	--volume ${PWD}/.trivy:/app/.trivy \
	--volume ${PWD}/scripts/trivy.sh:/app/trivy.sh \
	aquasec/trivy /app/trivy.sh

help:
	@echo "[Help] Makefile list commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
