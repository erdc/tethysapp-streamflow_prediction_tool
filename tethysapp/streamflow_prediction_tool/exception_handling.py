# -*- coding: utf-8 -*-
"""exception_handling.py

    Author: Alan D. Snow, 2017
    License: BSD 3-Clause
"""
from contextlib import contextmanager
from functools import wraps
import logging
import os

from django.http import HttpResponseBadRequest, HttpResponseServerError


from .app import StreamflowPredictionTool as app

# setup logging
LOG_FILE = os.path.join(app.get_app_workspace().path, 'spt_error.log')
LOGGER = logging.getLogger('streamflow_prediction_tool')
FILE_HANDLER = logging.handlers.RotatingFileHandler(LOG_FILE,
                                                    maxBytes=5*1024*1024,
                                                    backupCount=1)
FILE_HANDLER.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s:"
                                            "%(name)s:%(message)s"))
LOGGER.addHandler(FILE_HANDLER)
LOGGER.propagate = False


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
            LOGGER.exception("Internal Server Error.")
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
        LOGGER.exception("Internal Server Error.")
        raise InvalidData("Invalid {file_type} file ..."
                          .format(file_type=file_type))
