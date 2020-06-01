"""Flask web app providing a REST API to notmuch."""

import email
import email.policy
import io
import itertools
import logging
import os

import bleach
import notmuch
from flask import Flask, current_app, g, send_file, send_from_directory, safe_join
from flask_restful import Api, Resource

ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    "span",
    "p",
    "br",
    "div",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "style"],
    "abbr": ["title", "style"],
    "acronym": ["title", "style"],
    "p": ["style"],
    "div": ["style"],
}


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
    app = Flask(__name__, static_folder="js")
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["NOTMUCH_PATH"] = os.getenv("NOTMUCH_PATH")
    app.logger.setLevel(logging.INFO)

    api = Api(app)

    @app.route("/")
    def send_index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def send_js(path):
        if path and os.path.exists(safe_join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    @app.before_request
    def before_request():
        get_db()

    app.teardown_appcontext(close_db)

    @app.after_request
    def security_headers(response):
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    class Query(Resource):
        def get(self, query_string):
            threads = notmuch.Query(get_db(), query_string).search_threads()
            return threads_to_json(threads, number=None)

    class Thread(Resource):
        def get(self, thread_id):
            threads = notmuch.Query(
                get_db(), "thread:{}".format(thread_id)
            ).search_threads()
            thread = next(threads)  # there can be only 1
            messages = thread.get_messages()
            return messages_to_json(messages)

    api.add_resource(Query, "/api/query/<path:query_string>")
    api.add_resource(Thread, "/api/thread/<string:thread_id>")

    @app.route("/api/attachment/<string:message_id>/<int:num>")
    def download_attachment(message_id, num):
        msgs = notmuch.Query(get_db(), "mid:{}".format(message_id)).search_messages()
        msg = next(msgs)  # there can be only 1
        d = message_attachment(msg, num)
        if not d:
            return None
        if isinstance(d["content"], str):
            f = io.StringIO(d["content"])
        else:
            f = io.BytesIO(d["content"])
        return send_file(f, mimetype=d["content_type"], as_attachment=True,
            attachment_filename=d["filename"])

    @app.route("/api/message/<string:message_id>")
    def download_message(message_id):
        msgs = notmuch.Query(get_db(), "mid:{}".format(message_id)).search_messages()
        msg = next(msgs)  # there can be only 1
        return send_file(msg.get_filename(), mimetype="message/rfc822",
            as_attachment=True, attachment_filename=message_id+".eml")

    return app


def threads_to_json(threads, start=0, number=None):
    """Converts a list of `notmuch.threads.Threads` instances to a JSON object."""
    if number is None:
        stop = None
    else:
        stop = start + number
    my_threads = itertools.islice(threads, start, stop)
    return [thread_to_json(t) for t in my_threads]


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
        if part.get_content_disposition() in ["attachment", "inline"]:
            attachments.append(
                {
                    "filename": part.get_filename(),
                    "content_type": part.get_content_type(),
                }
            )
    msg_body = email_msg.get_body(preferencelist=("html", "plain"))
    content_type = msg_body.get_content_type()
    if content_type == "text/html":
        content = bleach.clean(
            msg_body.get_content(),
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True,
        )
    elif content_type == "text/plain":
        content = msg_body.get_content()
    else:
        return {}
    return {
        "from": email_msg["From"],
        "to": email_msg["To"],
        "cc": email_msg["CC"],
        "bcc": email_msg["BCC"],
        "date": email_msg["Date"],
        "subject": email_msg["Subject"],
        "content": content,
        "content_type": content_type,
        "attachments": attachments,
        "message_id": message.get_message_id(),
    }


def message_attachment(message, num):
    """Returns attachment no. `num` of a `notmuch.message.Message` instance."""
    with open(message.get_filename(), "rb") as f:
        email_msg = email.message_from_binary_file(f, policy=email.policy.default)
    attachments = []
    for part in email_msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_disposition() in ["attachment", "inline"]:
            attachments.append(part)
    if not attachments:
        return {}
    attachment = attachments[num]
    return {
        "filename": attachment.get_filename(),
        "content_type": attachment.get_content_type(),
        "content": attachment.get_content(),
    }
