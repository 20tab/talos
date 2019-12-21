#!/bin/bash

cp .env.tpl .env

echo "BACKEND project initialization"
echo ""
cookiecutter https://github.com/20tab/django-continuous-delivery

echo "FRONTEND project initialization"
echo ""
cookiecutter https://github.com/20tab/react-continuous-delivery