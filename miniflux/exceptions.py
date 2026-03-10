# The MIT License (MIT)
#
# Copyright (c) Frederic Guillot
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


class ClientError(Exception):
    """
    Exception raised when the API client receives an error response from the server.

    Attributes:
        status_code (int): The HTTP status code of the error response.
    """

    def __init__(self, response):
        self.status_code = response.status_code
        self._response = response

    def get_error_reason(self) -> str:
        """
        Returns the error message from the response body, or a default message if not available.

        Returns:
            str: The error message from the response body, or a default message if not available.
        """
        default_reason = f"status_code={self.status_code}"
        if self._response.headers.get("Content-Type") == "application/json":
            result = self._response.json()
            if isinstance(result, dict):
                return result.get("error_message", default_reason)
        return default_reason


class ResourceNotFound(ClientError):
    """
    Exception raised when the API client receives a 404 response from the server.
    """

    pass


class AccessForbidden(ClientError):
    """
    Exception raised when the API client receives a 403 response from the server.
    """

    pass


class AccessUnauthorized(ClientError):
    """
    Exception raised when the API client receives a 401 response from the server.
    """

    pass


class BadRequest(ClientError):
    """
    Exception raised when the API client receives a 400 response from the server.
    """

    pass


class ServerError(ClientError):
    """
    Exception raised when the API client receives a 500 response from the server.
    """

    pass
