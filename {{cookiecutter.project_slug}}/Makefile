c = {{cookiecutter.project_slug}}
createsuperuser:
	docker exec -it backend python manage.py createsuperuser

touchbackend:
	docker exec -it backend touch uwsgiconf/docker.ini

p = shell
django:
	docker exec -it backend python manage.py $(p)

s =
rebuild:
	docker-compose stop $(s) && docker-compose rm -f $(s) && docker-compose up -d --build $(s)
