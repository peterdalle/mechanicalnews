# -*- coding: utf-8 -*-
"""
Module that handles everything related to the Mechanical News API that expose
the news articles to a client library.
"""
import datetime
import os
import sys
import time
from functools import wraps
from flask import Flask, jsonify, request, make_response, redirect
from flask import send_from_directory
from flask_restful import Resource, Api
from settings import AppConfig
from core import UserManager, SourceManager, ArticleManager
from core import ArticleFilter, MySqlDatabase
from stats import SummaryStats


API_VERSION = "1.0"
app = Flask(__name__)
app.debug = True
app.config["JSON_SORT_KEYS"] = False
app.config["FLASK_ENV"] = "development"
app.config["FLASK_DEBUG"] = 1
app.config["FLASK_RUN_PORT"] = 5000
api = Api(app, prefix="/api/v1")


def require_api_key(f):
    """Decorator function for API key authentication.

    Wraps around all functions that require API key. If API key is not
    authorized, a JSON error message is returned to the client that contain
    `{status: "error"}` and human-readable `message`.

    If Flask is running in debug mode, no API key is required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("api_key")
        if not MySqlDatabase.is_installed():
            return _general_api_error((
                "Database '{}' not found. Check that" +
                " database is installed correctly. See documentation for" +
                " instructions.").format(AppConfig.MYSQL_DB))
        user = UserManager()
        if user.is_valid_api_key(api_key) or app.debug:
            # Good API key. Return function.
            if api_key:
                user.incremenet_api_key_count(api_key=api_key)
            return f(*args, **kwargs)
        else:
            # Bad API key. Return error message.
            return bad_api_key()
    return decorated_function


def add_response_headers(status_code=200):
    """Decorator function that adds HTTP headers to response."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            headers = {
                "Access-Control-Allow-Origin": "*",
                "x-api-version": API_VERSION,
            }
            response = make_response(f(*args, **kwargs), status_code)
            h = response.headers
            for header, value in headers.items():
                h[header] = value
            return response
        return decorated_function
    return decorator


def append_article_resources(data):
    """Append JSON data with JSON resource URLs for an article."""
    article_id = data["id"]
    urls = {
        "article_url": "{}/articles/{}".format(
            AppConfig.API_URL, article_id),
        "versions_url": "{}/articles/{}/versions".format(
            AppConfig.API_URL, article_id),
        "metadata_url": "{}/articles/{}/metadata".format(
            AppConfig.API_URL, article_id),
        "metadataraw_url": "{}/articles/{}/metadataraw".format(
            AppConfig.API_URL, article_id),
        "images_url": "{}/articles/{}/images".format(
            AppConfig.API_URL, article_id),
        "links_url": "{}/articles/{}/links".format(
            AppConfig.API_URL, article_id),
        "logs_url": "{}/articles/{}/log".format(
            AppConfig.API_URL, article_id),
        "headers_url": "{}/articles/{}/headers".format(
            AppConfig.API_URL, article_id),
    }
    return {**data, **urls}


@add_response_headers(400)
def bad_request(message="400 Bad Request"):
    """Return error message (400 Bad Request) for invalid inputs."""
    return _general_api_error(message)


@add_response_headers(401)
def bad_api_key(message="401 Unauthorized. API key is invalid," +
                " please provide valid key."):
    """Return error message (401 Unauthorized) for invalid API key."""
    return _general_api_error(message)


@app.errorhandler(404)
def not_found(message="Not found"):
    """Return a general 404 Not Found message."""
    return _general_api_error(message)


@app.errorhandler(500)
@add_response_headers(500)
def server_error(message="Server Error"):
    """Return a general 500 Server Error message."""
    return _general_api_error(message)


def _general_api_error(message):
    """Return general API JSON error."""
    data = {
        "status": "error",
        "status_message": str(message),
    }
    return jsonify(data)


class Index(Resource):
    @add_response_headers()
    def get(self):
        """List all available resources."""
        response = {
            "status": "ok",
            "message": "List of all resources (requires API key)",
            "sources_url": "{}/sources".format(AppConfig.API_URL),
            "status_url": "{}/status".format(AppConfig.API_URL),
            "statistics_url": "{}/statistics".format(AppConfig.API_URL),
            "articles_url": "{}/articles".format(AppConfig.API_URL),
            "count_url": "{}/count".format(AppConfig.API_URL),
        }
        return jsonify(response)


class Status(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get system status: crawler statistics, database table size."""
        start_time = time.time()
        database_size = SummaryStats.get_database_size()
        stop_time = time.time()
        response = {
            "status": "ok",
            "api_version": API_VERSION,
            "elapsed_time_seconds": stop_time - start_time,
            "python_version": "{}.{}.{}".format(sys.version_info[0],
                                                sys.version_info[1],
                                                sys.version_info[2]),
            "server_datetime":
                datetime.datetime.now().replace(microsecond=0).isoformat(),
            }
        response = {**response, **database_size}
        return jsonify(response)


class Statistics(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get statistics."""
        stats = request.args.get("stats")
        if not stats:
            # URLs to all statistics resources.
            response = {
                "status": "ok",
                "message": "List of all statistics resources.",
                "summary_url":
                    "{}/statistics?stats=summary".format(
                        AppConfig.API_URL),
                "crawled_articles_url":
                    "{}/statistics?stats=crawled_articles".format(
                        AppConfig.API_URL),
                "published_articles_url":
                    "{}/statistics?stats=published_articles".format(
                        AppConfig.API_URL),
            }
        elif stats == "summary":
            response = {
                "status": "ok",
            }
            response = {**response, **SummaryStats.get_summary()}
        elif stats == "published_articles":
            response = {
                "status": "ok",
                "data": SummaryStats.get_published_articles_per_day(),
            }
        elif stats == "crawled_articles":
            response = {
                "status": "ok",
                "data": SummaryStats.get_crawled_articles_per_day()
            }
        else:
            return bad_request("Unknown stats parameter. Parameter should " +
                               " be 'summary', 'crawled_articles' or " +
                               " 'published_articles'.")
        return jsonify(response)


class Sources(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """List available sources."""
        manager = SourceManager()
        sources = []
        for source in manager.get_sources():
            sources.append(self.append_source_resources(source.get_json()))
        response = {
            "status": "ok",
            "data": sources,
        }
        return jsonify(response)

    def append_source_resources(self, data):
        """Append JSON data with JSON resource URLs for a source."""
        source_id = data["source_id"]
        urls = {
            "source_url": "{}/sources/{}".format(AppConfig.API_URL, source_id),
        }
        return {**data, **urls}


class SourceByID(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, source_id):
        """Get source by its ID."""
        manager = SourceManager()
        source = manager.get_source_by_id(source_id)
        if source:
            response = source.get_json()
            return jsonify(response)
        else:
            return not_found()


class ArticleCount(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get count of articles."""
        start_time = time.time()
        if request.args:
            filters = ArticleFilter.from_args(request.args)
        else:
            filters = None
        articles = ArticleManager()
        response = {
            "status": "ok",
            "count": articles.get_article_count(filters),
            "elapsed_time_seconds": time.time() - start_time,
        }
        return jsonify(response)


class ArticleHitsOverTime(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get article hits over time."""
        start_time = time.time()
        if request.args:
            filters = ArticleFilter.from_args(request.args)
        else:
            filters = None
        articles = ArticleManager()
        history = articles.get_article_hits_over_time(filters)
        response = {
            "status": "ok",
            "elapsed_time_seconds": time.time() - start_time,
            "data": history
        }
        return jsonify(response)


class Articles(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get latest articles."""
        # Check for invalid inputs.
        filters = ArticleFilter.from_args(request.args)
        if filters.limit > 1000:
            return bad_request("Limit must be between 0 and 1000.")
        a = ArticleManager()
        articles = []
        for article in a.get_articles(filters):
            if filters.append_resources:
                articles.append(append_article_resources(article.get_json()))
            else:
                articles.append(article.get_json())
        return jsonify(self.append_articles_paging(articles))

    def append_articles_paging(self, articles: list):
        """Append JSON paging to article list."""
        if request.args.get("limit"):
            limit = int(request.args.get("limit"))
        else:
            limit = 500
        next_url = {}
        urls = {
            "status": "ok",
            "num_results": len(articles),
            "data": articles,
        }
        if len(articles) > 0:
            next_url = {
                "next_page_url": "{}/articles?offset_id={}&limit={}".format(
                    AppConfig.API_URL, self.get_next_offset(articles), limit),
            }
        return {**next_url, **urls}

    def get_next_offset(self, articles: list) -> int:
        """Get the minimum article ID as the next offset.

        Because the results are order by descending, the minimum
        article ID will be the next page."""
        if len(articles):
            ids = []
            for article in articles:
                ids.append(article["id"])
            return min(ids)
        return 0


class ArticleByID(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get article by its ID."""
        a = ArticleManager()
        article = a.get_article_by_id(article_id)
        if article:
            response = append_article_resources(article.get_json())
            return jsonify(response)
        else:
            return not_found()


class ArticleVersions(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get article versions by its ID."""
        a = ArticleManager()
        versions = a.get_versions(article_id)
        articles = []
        for article in versions:
            articles.append(article.get_json())
        response = {
            "status": "ok",
            "num_versions": len(articles),
            "data": articles,
        }
        return jsonify(response)


class ArticleImages(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get images from article."""
        a = ArticleManager()
        images = a.get_images(article_id)
        response = {
            "status": "ok",
            "data": images,
        }
        return jsonify(response)


class ArticleLinks(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get links from article."""
        a = ArticleManager()
        links = a.get_links(article_id)
        response = {
            "status": "ok",
            "data": links,
        }
        return jsonify(response)


class ArticleMetadata(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get metadata of specific article."""
        a = ArticleManager()
        metadata = a.get_metadata(article_id)
        response = {
            "status": "ok",
            "data": metadata,
        }
        return jsonify(response)


class ArticleMetadataRaw(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get raw metadata of specific article."""
        a = ArticleManager()
        metadata = a.get_metadata_raw(article_id)
        response = {
            "status": "ok",
            "id": article_id,
            "data": metadata,
        }
        return jsonify(response)


class ArticleLog(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get log of specific article."""
        a = ArticleManager()
        log = a.get_log(article_id)
        response = {
            "status": "ok",
            "data": log,
        }
        return jsonify(response)


class ArticleHeaders(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get HTTP headers of specific article."""
        a = ArticleManager()
        headers = a.get_headers(article_id)
        response = {
            "status": "ok",
            "data": headers,
        }
        return jsonify(response)


class FrontpageByDomain(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, domain, from_date, to_date):
        """Get articles on a page a given date and time."""
        raise NotImplementedError()


class ServeImage(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, image_file):
        """Serve binary image from file system."""
        if app.debug:
            # Debug: Serve binary files dynamically via Flask (slow).
            dir_location = AppConfig.FULL_IMAGES_DIRECTORY + "/"
            full_filename = dir_location + image_file
            if os.path.isfile(full_filename):
                return send_from_directory(dir_location, image_file)
            else:
                return not_found("Image not found: '{}'".format(full_filename))
        else:
            # Production: Serve binary file statically via Apache/nginx (fast).
            location = AppConfig.FULL_IMAGES_URL + "/" + image_file
            return redirect(location, code=307)


class ServeHtml(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Serve HTML from file system."""
        filename = str(article_id) + ".html"
        if app.debug:
            # Debug: Serve binary files dynamically via Flask (slow).
            full_filename = AppConfig.HTML_FILES_DIRECTORY + "/" + filename
            if os.path.isfile(full_filename):
                return send_from_directory(AppConfig.HTML_FILES_DIRECTORY,
                                           filename)
            else:
                return not_found(
                    "HTML file not found: '{}'".format(full_filename))
        else:
            # Production: Serve binary file statically via Apache/nginx (fast).
            return NotImplementedError(
                "Serving HTML files statically is not implemented yet.")


if __name__ == "__main__":
    api.add_resource(Index, "/")
    api.add_resource(Status, "/status")
    api.add_resource(Statistics, "/statistics")
    api.add_resource(Sources, "/sources")
    api.add_resource(SourceByID, "/sources/<int:source_id>")
    api.add_resource(FrontpageByDomain, "/frontpages/<string:domain>")
    api.add_resource(ServeImage, "/images/<string:image_file>")
    api.add_resource(ServeHtml, "/html/<int:article_id>")
    api.add_resource(Articles, "/articles")
    api.add_resource(ArticleCount, "/count")
    api.add_resource(ArticleHitsOverTime, "/hits")
    api.add_resource(ArticleByID, "/articles/<int:article_id>")
    api.add_resource(ArticleImages, "/articles/<int:article_id>/images")
    api.add_resource(ArticleVersions, "/articles/<int:article_id>/versions")
    api.add_resource(ArticleLinks, "/articles/<int:article_id>/links")
    api.add_resource(ArticleLog, "/articles/<int:article_id>/log")
    api.add_resource(ArticleHeaders, "/articles/<int:article_id>/headers")
    api.add_resource(ArticleMetadata, "/articles/<int:article_id>/metadata")
    api.add_resource(ArticleMetadataRaw, "/articles/<int:article_id>/metadataraw")
    app.run()
