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

import asyncio
import time
import unittest
from unittest import mock

import miniflux
from miniflux import (
    AccessForbidden,
    AccessUnauthorized,
    BadRequest,
    ClientError,
    ResourceNotFound,
    ServerError,
)



class TestMinifluxAsyncClient(unittest.IsolatedAsyncioTestCase):
    def test_get_error_reason(self):
        response = mock.Mock()
        response.status_code = 404
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"error_message": "some error"}
        error = ResourceNotFound(response)
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.get_error_reason(), "some error")

    def test_default_session_not_shared(self):
        client_one = miniflux.AsyncClient("http://localhost", api_key="token-one")
        client_two = miniflux.AsyncClient("http://localhost", api_key="token-two")

        self.assertIsNot(client_one._client, client_two._client)
        self.assertEqual(client_one._client.headers.get("X-Auth-Token"), "token-one")
        self.assertEqual(client_two._client.headers.get("X-Auth-Token"), "token-two")

    async def test_get_error_without_reason(self):
        response = mock.Mock()
        response.status_code = 404
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {}
        error = ResourceNotFound(response)
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.get_error_reason(), "status_code=404")

    async def test_get_error_with_bad_response(self):
        response = mock.Mock()
        response.status_code = 404
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = None
        error = ResourceNotFound(response)
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.get_error_reason(), "status_code=404")

    async def test_get_error_reason_without_json_content_type(self):
        response = mock.Mock()
        response.status_code = 500
        response.headers = {"Content-Type": "text/html"}
        response.json = mock.Mock()

        error = ServerError(response)

        self.assertEqual(error.get_error_reason(), "status_code=500")
        response.json.assert_not_called()

    async def test_get_error_reason_without_content_type_header(self):
        response = mock.Mock()
        response.status_code = 403
        response.headers = {}
        response.json = mock.Mock()

        error = AccessForbidden(response)

        self.assertEqual(error.get_error_reason(), "status_code=403")
        response.json.assert_not_called()

    async def test_flush_history(self):
        response = mock.Mock()
        response.status_code = 202

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.flush_history()

        client._request.assert_called_once_with("delete", "http://localhost/v1/flush-history")
        self.assertTrue(result)

    async def test_get_version(self):
        expected_result = {
            "version": "dev",
            "commit": "HEAD",
            "build_date": "undefined",
            "go_version": "go1.21.1",
            "compiler": "gc",
            "arch": "amd64",
            "os": "darwin",
        }

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_version()

        client._request.assert_called_once_with("get", "http://localhost/v1/version")
        self.assertEqual(result, expected_result)

    async def test_get_me(self):
        expected_result = {"id": 123, "username": "foobar"}

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.me()

        client._request.assert_called_once_with("get", "http://localhost/v1/me")
        self.assertEqual(result, expected_result)

    async def test_get_me_with_server_error(self):
        response = mock.Mock()
        response.status_code = 500

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(ClientError):
            await client.me()

    async def test_discover(self):
        expected_result = [{"url": "http://example.org/feed", "title": "Example", "type": "RSS"}]

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.discover("http://example.org/")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_discover_with_credentials(self):
        expected_result = [{"url": "http://example.org/feed", "title": "Example", "type": "RSS"}]

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.discover(
            "http://example.org/",
            username="foobar",
            password="secret",
            user_agent="Bot",
        )

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_discover_with_server_error(self):
        expected_result = {"error_message": "some error"}

        response = mock.Mock()
        response.status_code = 500
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(ClientError):
            await client.discover("http://example.org/")

    async def test_export(self):
        expected_result = "OPML feed"

        response = mock.Mock()
        response.status_code = 200
        response.text = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.export()

        client._request.assert_called_once_with("get", "http://localhost/v1/export")
        self.assertEqual(result, expected_result)

    async def test_import(self):
        input_data = "my opml data"

        response = mock.Mock()
        response.status_code = 201

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        await client.import_feeds(input_data)

        client._request.assert_called_once_with("post", "http://localhost/v1/import", data=input_data)

    async def test_import_failure(self):
        input_data = "my opml data"

        response = mock.Mock()
        response.status_code = 500
        response.json.return_value = {"error_message": "random error"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(ClientError):
            await client.import_feeds(input_data)

    async def test_get_feed(self):
        expected_result = {"id": 123, "title": "Example"}

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_feed(123)

        client._request.assert_called_once_with("get", "http://localhost/v1/feeds/123")
        self.assertEqual(result, expected_result)

    async def test_get_feed_icon(self):
        expected_result = {
            "id": 11,
            "mime_type": "image/x-icon",
            "data": "image/x-icon;base64,data",
        }

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_icon_by_feed_id(123)

        client._request.assert_called_once_with("get", "http://localhost/v1/feeds/123/icon")
        self.assertEqual(result, expected_result)

    async def test_get_icon(self):
        expected_result = {
            "id": 11,
            "mime_type": "image/x-icon",
            "data": "image/x-icon;base64,data",
        }

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_icon(11)

        client._request.assert_called_once_with("get", "http://localhost/v1/icons/11")
        self.assertEqual(result, expected_result)

    async def test_create_feed(self):
        expected_result = {"feed_id": 42}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.create_feed("http://example.org/feed", 123)

        client._request.assert_called_once()
        self.assertEqual(result, expected_result["feed_id"])

    async def test_create_feed_with_no_category(self):
        expected_result = {"feed_id": 42}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.create_feed("http://example.org/feed")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result["feed_id"])

    async def test_create_feed_with_credentials(self):
        expected_result = {"feed_id": 42}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.create_feed("http://example.org/feed", 123, username="foobar", password="secret")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result["feed_id"])

    async def test_create_feed_with_crawler_enabled(self):
        expected_result = {"feed_id": 42}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.create_feed("http://example.org/feed", 123, crawler=True)

        client._request.assert_called_once()
        self.assertEqual(result, expected_result["feed_id"])

    async def test_create_feed_with_custom_user_agent_and_crawler_disabled(self):
        expected_result = {"feed_id": 42}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.create_feed("http://example.org/feed", 123, crawler=False, user_agent="GoogleBot")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result["feed_id"])

    async def test_update_feed(self):
        expected_result = {"id": 123, "crawler": True, "username": "test"}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.update_feed(123, crawler=True, username="test")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_refresh_all_feeds(self):
        expected_result = True

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.refresh_all_feeds()

        client._request.assert_called_once_with("put", "http://localhost/v1/feeds/refresh")
        assert result == expected_result

    async def test_refresh_feed(self):
        expected_result = True

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.refresh_feed(123)

        client._request.assert_called_once_with("put", "http://localhost/v1/feeds/123/refresh")
        assert result == expected_result

    async def test_refresh_category(self):
        expected_result = True

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.refresh_category(123)

        client._request.assert_called_once_with("put", "http://localhost/v1/categories/123/refresh")
        assert result == expected_result

    async def test_get_feed_entry(self):
        expected_result = {}

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_feed_entry(123, 456)

        client._request.assert_called_once_with("get", "http://localhost/v1/feeds/123/entries/456")
        assert result == expected_result

    async def test_get_feed_entries(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_feed_entries(123)

        client._request.assert_called_once()
        assert result == expected_result

    async def test_get_feed_entries_with_direction_param(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_feed_entries(123, direction="asc")

        client._request.assert_called_once()
        assert result == expected_result

    async def test_import_entry(self):
        expected_result = {"id": 1790}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.import_entry(
            123,
            url="http://example.org/article.html",
            title="Entry Title",
            starred=True,
            tags=["tag1", "tag2"],
        )

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_import_entry_with_published_at_timestamp(self):
        expected_result = {"id": 1790}
        published_at = int(time.time())

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.import_entry(
            123,
            url="http://example.org/article.html",
            published_at=published_at,
        )

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_import_entry_when_existing(self):
        expected_result = {"id": 1790}

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.import_entry(123, url="http://example.org/article.html")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_import_entry_without_url(self):
        client = miniflux.AsyncClient("http://localhost", username="username", password="password")

        with self.assertRaises(ValueError):
            await client.import_entry(123, url="")

    async def test_mark_feed_as_read(self):
        response = mock.Mock()
        response.status_code = 204

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        await client.mark_feed_entries_as_read(123)

        client._request.assert_called_once_with("put", "http://localhost/v1/feeds/123/mark-all-as-read")

    async def test_mark_category_entries_as_read(self):
        response = mock.Mock()
        response.status_code = 204

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        await client.mark_category_entries_as_read(123)

        client._request.assert_called_once_with("put", "http://localhost/v1/categories/123/mark-all-as-read")

    async def test_mark_user_entries_as_read(self):
        response = mock.Mock()
        response.status_code = 204

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        await client.mark_user_entries_as_read(123)

        client._request.assert_called_once_with("put", "http://localhost/v1/users/123/mark-all-as-read")

    async def test_get_entry(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_entry(123)

        client._request.assert_called_once_with("get", "http://localhost/v1/entries/123")
        assert result == expected_result

    async def test_fetch_entry_content(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.fetch_entry_content(123)

        client._request.assert_called_once_with("get", "http://localhost/v1/entries/123/fetch-content")
        assert result == expected_result

    async def test_get_entries(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_entries(status="unread", limit=10, offset=5)

        client._request.assert_called_once()
        assert result == expected_result

    async def test_get_entries_with_before_param(self):
        param_value = int(time.time())
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_entries(before=param_value)

        client._request.assert_called_once()
        assert result == expected_result

    async def test_get_entries_with_starred_param(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_entries(starred=True)

        client._request.assert_called_once()
        assert result == expected_result

    async def test_get_entries_with_starred_param_at_false(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_entries(starred=False, after_entry_id=123)

        client._request.assert_called_once()
        assert result == expected_result

    async def test_get_user_by_id(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_user_by_id(123)

        client._request.assert_called_once_with("get", "http://localhost/v1/users/123")
        assert result == expected_result

    async def test_get_inexisting_user(self):
        response = mock.Mock()
        response.status_code = 404
        response.json.return_value = {"error_message": "some error"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(ResourceNotFound):
            await client.get_user_by_id(123)

    async def test_get_user_by_username(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_user_by_username("foobar")

        client._request.assert_called_once_with("get", "http://localhost/v1/users/foobar")
        assert result == expected_result

    async def test_update_user(self):
        expected_result = {"id": 123, "theme": "Black", "language": "fr_FR"}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.update_user(123, theme="black", language="fr_FR")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_api_key_auth(self):
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {}

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        await client.export()

        client._request.assert_called_once_with("get", "http://localhost/v1/export")
        self.assertEqual(client._client.headers.get("X-Auth-Token"), "secret")

    async def test_save_entry(self):
        expected_result = True

        response = mock.Mock()
        response.status_code = 202

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.save_entry(123)

        client._request.assert_called_once_with("post", "http://localhost/v1/entries/123/save")
        self.assertEqual(result, expected_result)

    async def test_get_category_entry(self):
        expected_result = {}

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_category_entry(123, 456)

        client._request.assert_called_once_with("get", "http://localhost/v1/categories/123/entries/456")
        assert result == expected_result

    async def test_get_category_entries(self):
        expected_result = []

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_category_entries(123)

        client._request.assert_called_once()
        assert result == expected_result

    async def test_update_entry_title(self):
        expected_result = {"id": 123, "title": "New title"}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.update_entry(entry_id=123, title="New title")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_update_entry_content(self):
        expected_result = {"id": 123, "content": "New content"}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.update_entry(entry_id=123, content="New content")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_update_entries_status(self):
        response = mock.Mock()
        response.status_code = 204

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.update_entries(entry_ids=[123, 456], status="read")

        client._request.assert_called_once()
        self.assertTrue(result)

    async def test_get_enclosure(self):
        expected_result = {"id": 123, "mime_type": "audio/mpeg"}

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_enclosure(123)

        client._request.assert_called_once_with("get", "http://localhost/v1/enclosures/123")
        self.assertEqual(result, expected_result)

    async def test_update_enclosure(self):
        response = mock.Mock()
        response.status_code = 204

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.update_enclosure(123, media_progression=42)

        client._request.assert_called_once()
        self.assertTrue(result)

    async def test_get_integrations_status(self):
        expected_result = {"has_integrations": True}

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_integrations_status()

        client._request.assert_called_once_with("get", "http://localhost/v1/integrations/status")
        self.assertTrue(result)

    async def test_get_api_keys(self):
        expected_result = [{"id": 1, "description": "Test API Key"}]

        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.get_api_keys()

        client._request.assert_called_once_with("get", "http://localhost/v1/api-keys")
        self.assertEqual(result, expected_result)

    async def test_create_api_key(self):
        expected_result = {"id": 2, "description": "New API Key", "token": "some-token"}

        response = mock.Mock()
        response.status_code = 201
        response.json.return_value = expected_result

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        result = await client.create_api_key("New API Key")

        client._request.assert_called_once()
        self.assertEqual(result, expected_result)

    async def test_delete_api_key(self):
        response = mock.Mock()
        response.status_code = 204

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        await client.delete_api_key(1)

        client._request.assert_called_once_with("delete", "http://localhost/v1/api-keys/1")

    async def test_not_found_response(self):
        response = mock.Mock()
        response.status_code = 404
        response.json.return_value = {"error_message": "Not found"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(ResourceNotFound):
            await client.get_version()

    async def test_unauthorized_response(self):
        response = mock.Mock()
        response.status_code = 401
        response.json.return_value = {"error_message": "Unauthorized"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(AccessUnauthorized):
            await client.get_version()

    async def test_forbidden_response(self):
        response = mock.Mock()
        response.status_code = 403
        response.json.return_value = {"error_message": "Forbidden"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(AccessForbidden):
            await client.get_version()

    async def test_bad_request_response(self):
        response = mock.Mock()
        response.status_code = 400
        response.json.return_value = {"error_message": "Bad request"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(BadRequest):
            await client.get_version()

    async def test_server_error_response(self):
        response = mock.Mock()
        response.status_code = 500
        response.json.return_value = {"error_message": "Server error"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)

        with self.assertRaises(ServerError):
            await client.get_version()

    async def test_context_manager_exit_on_error(self):
        response = mock.Mock()
        response.status_code = 500
        response.json.return_value = {"error_message": "Server error"}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password")
        client._request = mock.AsyncMock(return_value=response)
        client.close = mock.AsyncMock()

        with self.assertRaises(ServerError):
            async with client:
                await client.get_version()

        client.close.assert_called_once()

    async def test_async_client_close(self):
        mock_httpx_client = mock.Mock()
        mock_httpx_client.aclose = mock.AsyncMock()
        mock_httpx_client.headers = {}

        client = miniflux.AsyncClient("http://localhost", username="username", password="password", http_client=mock_httpx_client)

        await client.close()

        mock_httpx_client.aclose.assert_called_once()

    async def test_concurrent_requests(self):
        """Test that multiple concurrent requests work correctly."""
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {"id": 123}

        client = miniflux.AsyncClient("http://localhost", api_key="secret")
        client._request = mock.AsyncMock(return_value=response)

        # Execute multiple requests concurrently
        results = await asyncio.gather(
            client.get_feed(1),
            client.get_feed(2),
            client.get_feed(3),
        )

        # Verify all requests completed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result, {"id": 123})

        # Verify _request was called 3 times
        self.assertEqual(client._request.call_count, 3)
