jQuery File Upload + Django 1.4 + Crocodoc
==========================================

A prototype which shows uploading files using jQuery File Upload and then posts the files to Crocodoc for embedded
viewing. The jQuery File Upload work was modified from:

- jQuery File Upload - [https://github.com/blueimp/jQuery-File-Upload](https://github.com/blueimp/jQuery-File-Upload)
- Django jQuery File Upload - [https://github.com/sigurdga/django-jquery-file-upload](https://github.com/sigurdga/django-jquery-file-upload)

Setup
-----
1. Set up a [Virtualenv](http://pypi.python.org/pypi/virtualenv)

        $ virtualenv venv --distribute

2. Install the required packages

        $ pip install -r requirements.txt

3. Create a new file called `local_settings.py` in the same directory as `settings.py`. Add the following setting:

        CROCODOC_API_KEY = '<your API key here>'

4. Create the DB tables

        $ python manage.py syncdb

5. Run the app

        $ python manage.py runserver

6. Test the UI [http://localhost:8000/upload/new](http://localhost:8000/upload/new)

License
-------
Released under the [MIT License](http://www.opensource.org/licenses/MIT), as the original project.