"""Flask web app providing a REST API to notmuch."""


import email
import email.policy
import logging
import os

import notmuch
from flask import Flask, current_app, g
from flask_cors import CORS
from flask_restful import Api, Resource


def get_db():
    """Get a new `Database` instance. Called before every request. Cached on first call."""
    if "db" not in g:
        g.db = notmuch.Database(current_app.config["NOTMUCH_PATH"], create=False)
    return g.db


def close_db(e=None):
    """Close the Database. Called after every request."""
    pass


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["NOTMUCH_PATH"] = os.getenv("NOTMUCH_PATH")
    app.logger.setLevel(logging.INFO)

    CORS(app)

    api = Api(app)

    @app.before_request
    def before_request():
        get_db()

    app.teardown_appcontext(close_db)

    class Query(Resource):
        def get(self, query_string):
            threads = notmuch.Query(get_db(), query_string).search_threads()
            return threads_to_json(threads)

    class Thread(Resource):
        def get(self, thread_id):
            threads = notmuch.Query(
                get_db(), "thread:{}".format(thread_id)
            ).search_threads()
            thread = next(threads)
            messages = thread.get_messages()
            return messages_to_json(messages)

    api.add_resource(Query, "/api/query/<string:query_string>")
    api.add_resource(Thread, "/api/thread/<string:thread_id>")

    return app


def threads_to_json(threads):
    """Converts a list of `notmuch.threads.Threads` instances to a JSON object."""
    return [thread_to_json(t) for t in threads]


def thread_to_json(thread):
    """Converts a `notmuch.threads.Thread` instance to a JSON object."""
    return {
        "authors": thread.get_authors(),
        "matched_messages": thread.get_matched_messages(),
        "newest_date": thread.get_newest_date(),
        "oldest_date": thread.get_oldest_date(),
        "subject": thread.get_subject(),
        "tags": list(thread.get_tags()),
        "thread_id": thread.get_thread_id(),
        "total_messages": thread.get_total_messages(),
    }


def messages_to_json(messages):
    """Converts a list of `notmuch.message.Message` instances to a JSON object."""
    return [message_to_json(m) for m in messages]


def message_to_json(message):
    """Converts a `notmuch.message.Message` instance to a JSON object."""
    with open(message.get_filename(), "rb") as f:
        email_msg = email.message_from_binary_file(f, policy=email.policy.default)
    attachments = []
    for part in email_msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_disposition() == "attachment":
            attachments.append(
                {
                    "filename": part.get_filename(),
                    "content_type": part.get_content_type(),
                }
            )
    return {
        "from": email_msg["From"],
        "to": email_msg["To"],
        "cc": email_msg["CC"],
        "bcc": email_msg["BCC"],
        "date": email_msg["Date"],
        "subject": email_msg["Subject"],
        "content": email_msg.get_body().get_content(),
        "content_type": email_msg.get_body().get_content_type(),
        "attachments": attachments,
    }
