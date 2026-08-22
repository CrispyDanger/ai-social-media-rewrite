include .env
export

create_user:
	docker-compose run --rm web sh -c "python manage.py createsuperuser"

migrations:
	docker-compose run --rm web sh -c "python manage.py makemigrations"

migrate:
	docker-compose run --rm web sh -c "python manage.py migrate"

test:
	docker-compose run --rm web sh -c "python manage.py test"

coverage:
	docker-compose run --rm web sh -c "coverage run manage.py test"
	docker-compose run --rm web sh -c "coverage report"
