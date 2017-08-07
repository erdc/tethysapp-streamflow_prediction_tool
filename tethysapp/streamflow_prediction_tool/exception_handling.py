# -*- coding: utf-8 -*-
"""exception_handling.py

    Author: Alan D. Snow, 2017
    License: BSD 3-Clause
"""
from functools import wraps

from django.http import HttpResponseBadRequest, HttpResponseServerError


class DatabaseError(Exception):
    """This is an exception for database errors."""
    pass


class GeoServerError(Exception):
    """This is an exception for GeoServer errors."""
    pass


class InvalidData(Exception):
    """This is an exception for request input validation errors."""
    pass


class NotFoundError(Exception):
    """This is an exception for items not found."""
    pass


class SettingsError(Exception):
    """This is an exception for app settings errors."""
    pass


class UploadError(Exception):
    """This is an exception for uploading errors."""
    pass


def exceptions_to_http_status(view_func):
    """
    This decorator is defined in the view module, and it knows to convert
    InvalidData exceptions to http status 400. Add whatever other exception types
    and http return values you need. We end with a 'catch-all' conversion of
    Exception into http 500.

    Based on: https://stackoverflow.com/questions/25422176/
        django-raise-badrequest-as-exception
    """
    @wraps(view_func)
    def inner(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except DatabaseError as ex:
            return HttpResponseBadRequest("Database error: {}".format(ex))
        except GeoServerError as ex:
            return HttpResponseBadRequest("GeoServer error: {}".format(ex))
        except InvalidData as ex:
            return HttpResponseBadRequest("Invalid data: {}".format(ex))
        except NotFoundError as ex:
            return HttpResponseBadRequest("Not found: {}".format(ex))
        except SettingsError as ex:
            return HttpResponseBadRequest("Settings error: {}".format(ex))
        except UploadError as ex:
            return HttpResponseBadRequest("Upload error: {}".format(ex))
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return HttpResponseServerError(str(ex))
    return inner