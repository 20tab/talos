c = {{cookiecutter.project_slug}}_backend
p = shell
django:
	docker exec -it $(c) python manage.py $(p)

pull:
	git checkout develop && git pull && \
	cd backend && git checkout develop && git pull && \{% if cookiecutter.which_frontend in ["React", "React (TypeScript)"] %}
	cd ../frontend && git checkout develop && git pull && \{% endif %}
	cd ..

s =
rebuild:
	docker-compose stop $(s) && docker-compose rm -f $(s) && docker-compose up -d --build $(s)

touchbackend:
	docker exec -it $(c) touch uwsgiconf/docker.ini
