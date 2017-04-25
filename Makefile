requirements:
	pip install --process-dependency-links -r requirements.txt

test:
	coverage run ./manage.py test
	coverage report
