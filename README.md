django-static-files-monitor
===========================

Simple script that runs './manage collectstatic --noinput' whenever a
static file is changed. Static files are all files inside the
settings.STATICFILES_DIRS directories.

Usage
-----
1. Add monitor.py to PATH  
2. cd the/project/directory/that/contains/the/manage.py/file
3. $ monitor.py  
  
For any questions or improvement advice, please contact me at  
yordan [at] 4web [dot] bg

Disclaimer
----------
This script is intended for usage in development environment only.  It
is *NOT* suitable for production use.

The script is made free in the hope it'll benefit you, but without
warranty of any sort.
