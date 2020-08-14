# -*- coding: utf-8 -*-
"""
Module that handles everything related to the Mechanical News API that expose
the news articles to a client library.
"""
import datetime
import os
import sys
import time
import string
import random
from functools import wraps
from flask import Flask, jsonify, request, make_response, redirect, send_from_directory
from flask_restful import Resource, Api
from mechanicalnews.settings import AppConfig
from mechanicalnews.articles import Articles, ArticleFilter
from mechanicalnews.sources import Sources
from mechanicalnews.storage import MySqlDatabase, StaticFiles
from mechanicalnews.stats import SummaryStats
from mechanicalnews.users import User


API_VERSION = "1.0"
app = Flask(__name__)
app.debug = True
app.config["JSON_SORT_KEYS"] = False
app.config["FLASK_ENV"] = "development"
app.config["FLASK_DEBUG"] = 1
app.config["FLASK_RUN_PORT"] = 5000
api = Api(app, prefix="/api/v1")


def require_api_key(f):
    """Decorator thar wraps around all functions that requires API key.

    If API key is valid/active, the function is returned. Otherwise, a JSON
    error message is returned. If Flask is running in debug mode, no API key
    is required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("api_key")
        if not MySqlDatabase.is_installed():
            return api_error(("Database '{}' not found. Check that database is installed" +
                              " correctly. See documentation for instructions.").format(AppConfig.MYSQL_DB))
        if app.debug:
            return f(*args, **kwargs)
        user = User(api_key)
        if user.is_active():
            user.incremenet_api_key_count()
            return f(*args, **kwargs)
        else:
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


def append_article_resources(data, all_urls=False):
    """Append JSON data with JSON resource URLs for an article."""
    root_url = "{}/articles/{}".format(AppConfig.API_URL, data["id"])
    if all_urls:
        urls = {
            "article_url": root_url,
            "versions_url": root_url + "/versions",
            "metadata_url": root_url + "/metadata",
            "images_url": root_url + "/images",
            "links_url": root_url + "/links",
            "logs_url": root_url + "/log",
            "headers_url": root_url + "/headers",
            "html_url": root_url + "/html",
        }
    else:
        urls = {
            "article_url": root_url,
        }
    return {**data, **urls}


def append_image_url(images: list):
    """Append JSON data with URLs to article images."""
    root_url = AppConfig.API_URL
    new_images = []
    for image in images:
        urls = {
            "local_url": root_url + "/images/" + image["filename"],
        }
        new_images.append({**image, **urls})
    return new_images


@add_response_headers(400)
def bad_request(message="400 Bad Request"):
    """Return error message (400 Bad Request) for invalid inputs."""
    return api_error(message)


@add_response_headers(401)
def bad_api_key(message="401 Unauthorized. API key is invalid."):
    """Return error message (401 Unauthorized) for invalid API key."""
    return api_error(message)


@app.errorhandler(404)
def not_found(message="404 Not found"):
    """Return a general 404 Not Found message."""
    return api_error(message)


@app.errorhandler(500)
@add_response_headers(500)
def server_error(message="500 Server Error"):
    """Return a general 500 Server Error message."""
    return api_error(message)


def api_error(message):
    """Return general API JSON error."""
    data = {
        "status": "error",
        "status_message": str(message),
    }
    return jsonify(data)


def api_ok(data: dict):
    """Return OK response."""
    ok = {
        "status": "ok",
    }
    return jsonify({**ok, **data})


class Index(Resource):
    @add_response_headers()
    def get(self):
        """List all available resources."""
        root_url = AppConfig.API_URL
        response = {
            "message": "List of all resources (requires API key)",
            "sources_url": root_url + "/sources",
            "status_url": root_url + "/status",
            "statistics_url": root_url + "/statistics",
            "articles_url": root_url + "/articles",
            "count_url": root_url + "/count",
        }
        return api_ok(response)


class Status(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get system status: crawler statistics, database table size."""
        start_time = time.time()
        database_size = SummaryStats.get_database_size()
        stop_time = time.time()
        response = {
            "api_version": API_VERSION,
            "elapsed_time_seconds": stop_time - start_time,
            "python_version": "{}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]),
            "server_datetime":
                datetime.datetime.now().replace(microsecond=0).isoformat(),
            }
        response = {**response, **database_size}
        return api_ok(response)


class Statistics(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get statistics."""
        stats = request.args.get("stats")
        if not stats:
            # URLs to all statistics resources.
            root_url = AppConfig.API_URL
            response = {
                "message": "List of all statistics resources.",
                "summary_url": root_url + "/statistics?stats=summary",
                "crawled_articles_url": root_url + "/statistics?stats=crawled_articles",
                "published_articles_url": root_url + "/statistics?stats=published_articles",
            }
        elif stats == "summary":
            response = SummaryStats.get_summary()
        elif stats == "published_articles":
            response = {
                "data": SummaryStats.get_published_articles_per_day(),
            }
        elif stats == "crawled_articles":
            response = {
                "data": SummaryStats.get_crawled_articles_per_day()
            }
        else:
            return bad_request("Unknown stats parameter. Parameter should be 'summary', 'crawled_articles' or " +
                               " 'published_articles'.")
        return api_ok(response)


class SourceList(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """List available sources."""
        manager = Sources()
        sources = []
        for source in manager.get_sources():
            sources.append(self.append_source_resources(source.get_json()))
        return api_ok({"data": sources})

    def append_source_resources(self, data: dict) -> dict:
        """Append JSON data with JSON resource URLs for a source."""
        source_id = data["source_id"]
        urls = {
            "source_url": AppConfig.API_URL + "/sources/{}".format(source_id),
        }
        return {**data, **urls}


class SourceByID(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, source_id):
        """Get source by its ID."""
        manager = Sources()
        source = manager.get_source_by_id(source_id)
        if source:
            response = source.get_json()
            return api_ok(response)
        else:
            return not_found()


class ArticleCount(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get count of articles."""
        start_time = time.time()
        if request.args:
            filters = ArticleFilter(request.args)
        else:
            filters = None
        articles = Articles()
        response = {
            "count": articles.get_article_count(filters),
            "elapsed_time_seconds": time.time() - start_time,
        }
        return api_ok(response)


class ArticleHitsOverTime(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get article hits over time."""
        start_time = time.time()
        if request.args:
            filters = ArticleFilter(request.args)
        else:
            filters = None
        articles = Articles()
        history = articles.get_article_hits_over_time(filters)
        response = {
            "elapsed_time_seconds": time.time() - start_time,
            "data": history
        }
        return api_ok(response)


class ArticleList(Resource):
    @require_api_key
    @add_response_headers()
    def get(self):
        """Get latest articles."""
        # Check for invalid inputs.
        filters = ArticleFilter(request.args)
        if filters.limit < 0 or filters.limit > 1000:
            return bad_request("Limit must be between 0 and 1000.")
        a = Articles()
        articles = []
        for article in a.get_articles(filters):
            if filters.include_additionals:
                article["images"] = append_image_url(article["images"])
                articles.append(append_article_resources(article.get_json()))
            else:
                articles.append(article.get_json())
        return api_ok(self.append_articles_paging(articles))

    def append_articles_paging(self, articles: list) -> dict:
        """Append JSON paging to article list."""
        if request.args.get("limit"):
            limit = int(request.args.get("limit"))
        else:
            limit = 500
        next_url = {}
        urls = {
            "num_results": len(articles),
            "data": articles,
        }
        if len(articles) > 0:
            url = "/articles?offset_id={}&limit={}".format(self.get_next_offset(articles), limit)
            next_url = {
                "next_page_url": AppConfig.API_URL + url,
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
        a = Articles()
        article = a.get_article_by_id(article_id)
        if article:
            article = a.append_additionals(article)
            article["images"] = append_image_url(article["images"])
            response = append_article_resources(article.get_json(), all_urls=True)
            return api_ok(response)
        else:
            return not_found()


class ArticleVersions(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get article versions by its ID."""
        a = Articles()
        versions = a.get_versions(article_id)
        articles = []
        for article in versions:
            article["images"] = append_image_url(article["images"])
            articles.append(article.get_json())
        response = {
            "num_versions": len(articles),
            "data": articles,
        }
        return api_ok(response)


class ArticleImages(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get images from article."""
        a = Articles()
        images = a.get_images(article_id)
        response = {
            "data": append_image_url(images),
        }
        return api_ok(response)


class ArticleLinks(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get links from article."""
        a = Articles()
        links = a.get_links(article_id)
        response = {
            "data": links,
        }
        return api_ok(response)


class ArticleMetadata(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get metadata of specific article."""
        a = Articles()
        metadata = a.get_metadata(article_id)
        response = {
            "data": metadata,
        }
        return api_ok(response)


class ArticleLog(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get log of specific article."""
        a = Articles()
        log = a.get_log(article_id)
        response = {
            "data": log,
        }
        return api_ok(response)


class ArticleHeaders(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Get HTTP headers of specific article."""
        a = Articles()
        headers = a.get_headers(article_id)
        response = {
            "data": headers,
        }
        return api_ok(response)


class FrontpageByDomain(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, domain, from_date, to_date):
        """Get articles on a page a given date and time."""
        raise NotImplementedError()  # TODO


class ServeImage(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, image):
        """Serve binary image from file system."""
        if app.debug:
            # Debug: Serve binary files dynamically via Flask (slow).
            path = AppConfig.FULL_IMAGES_DIRECTORY + "/"
            fullname = path + image
            if os.path.isfile(fullname):
                return send_from_directory(path, image)
            else:
                return not_found("Image not found: '{}'".format(fullname))
        else:
            # Production: Serve binary file statically via web server (fast).
            location = AppConfig.FULL_IMAGES_URL + "/" + image
            return redirect(location, code=307)


class ArticleHtml(Resource):
    @require_api_key
    @add_response_headers()
    def get(self, article_id):
        """Serve HTML from file system. Uses flask for convenience even if
        it's slower than web server, because it's not a common scenario."""
        fullname = StaticFiles.get_html_full_filename(article_id)
        if os.path.isfile(fullname):
            path = AppConfig.HTML_FILES_DIRECTORY + "/"
            file = StaticFiles.get_html_filename(article_id)
            return send_from_directory(path, file, mimetype="text/plain", conditional=True)
        return not_found("HTML file not found ({})".format(fullname))


if __name__ == "__main__":
    api.add_resource(Index, "/")
    api.add_resource(Status, "/status")
    api.add_resource(Statistics, "/statistics")
    api.add_resource(SourceList, "/sources")
    api.add_resource(SourceByID, "/sources/<int:source_id>")
    api.add_resource(FrontpageByDomain, "/frontpages/<string:domain>")
    api.add_resource(ServeImage, "/images/<string:image>")
    api.add_resource(ArticleList, "/articles")
    api.add_resource(ArticleCount, "/count")
    api.add_resource(ArticleHitsOverTime, "/hits")
    api.add_resource(ArticleByID, "/articles/<int:article_id>")
    api.add_resource(ArticleHtml, "/articles/<int:article_id>/html")
    api.add_resource(ArticleImages, "/articles/<int:article_id>/images")
    api.add_resource(ArticleVersions, "/articles/<int:article_id>/versions")
    api.add_resource(ArticleLinks, "/articles/<int:article_id>/links")
    api.add_resource(ArticleLog, "/articles/<int:article_id>/log")
    api.add_resource(ArticleHeaders, "/articles/<int:article_id>/headers")
    api.add_resource(ArticleMetadata, "/articles/<int:article_id>/metadata")
    app.run()
