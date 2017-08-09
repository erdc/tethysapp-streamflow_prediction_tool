# -*- coding: utf-8 -*-
"""exception_handling.py

    Author: Alan D. Snow, 2017
    License: BSD 3-Clause
"""
from contextlib import contextmanager
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
    InvalidData exceptions to http status 400. Add whatever other
    exception type and http return values you need.
    We end with a 'catch-all' conversion of Exception into http 500.

    Based on: https://stackoverflow.com/questions/25422176/
        django-raise-badrequest-as-exception
    """
    @wraps(view_func)
    def inner(*args, **kwargs):
        """
        Catch exceptions and convert them to django http response objects
        """
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
        except Exception:
            import traceback
            traceback.print_exc()
            return HttpResponseServerError("Internal Server Error. Please "
                                           "check your input parameters.")
    return inner


@contextmanager
def rivid_exception_handler(file_type, river_id):
    """
    Raises proper exceptions for rivids queries
    """
    try:
        yield
    except (IndexError, KeyError):
        raise NotFoundError('{file_type} river with ID {river_id}.'
                            .format(file_type=file_type, river_id=river_id))
    except Exception:
        import traceback
        traceback.print_exc()
        raise InvalidData("Invalid {file_type} file ..."
                          .format(file_type=file_type))
