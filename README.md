# Project Hermes

The project hermes for Imagine Cup, which allows for data collection for map based data

## Setup (Before Installation)
- Follow all steps mentioned in `INSTALLATION.md`
- Edit `project_hermes/settings/conf.sample.py` to `project_hermes/settings/conf.py`

## Setting up local machine for development
- Use Python 3.5
- Install and configure virtualenvwrapper https://virtualenvwrapper.readthedocs.org/en/latest/
- In local machine use `pip install -r requirements/local.txt`
- Edit `project_hermes/settings/conf.py` to your local settings

## Setting up Production server
- Use Python 3.5
- Install and configure virtualenvwrapper https://virtualenvwrapper.readthedocs.org/en/latest/
- In local machine use `pip install -r requirements/production.txt`
- Edit `project_hermes/settings/conf.py` to add your production level settings
- Set environment variable `DJANGO_SETTINGS_MODULE` to `project_hermes.settings.production`
- Continue with Django deployment normally
