# Project Hermes

Imagine Cup Project Hermes, OpenData system

## Setup (Before Installation)
- Follow all steps mentioned in `INSTALLATION.md`
- Edit `hermes/settings/conf.sample.py` to `hermes/settings/conf.py`

## Setting up local machine for development
- Use Python 3.5
- Install and configure virtualenvwrapper https://virtualenvwrapper.readthedocs.org/en/latest/
- In local machine use `pip install -r requirements/local.txt`
- Edit `hermes/settings/conf.py` to your local settings

## Setting up Production server
- Use Python 3.5
- Install and configure virtualenvwrapper https://virtualenvwrapper.readthedocs.org/en/latest/
- In local machine use `pip install -r requirements/production.txt`
- Edit `hermes/settings/conf.py` to add your production level settings
- Set environment variable `DJANGO_SETTINGS_MODULE` to `hermes.settings.production`
- Continue with Django deployment normally
