requirements:
	pip install -r requirements.txt

test:
	coverage run ./manage.py test
	coverage report
