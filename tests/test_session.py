# standard library
import pickle
import tempfile
from datetime import datetime, timedelta

# pypi/conda library
import flask
import pytest

# vcollective flask extension
from flask_session import Session


@pytest.mark.unittests
def test_null_session():
    app = flask.Flask(__name__)
    Session(app)

    with app.test_request_context():
        assert flask.session.get("missing_key") is None

        with pytest.raises(RuntimeError):
            flask.session["foo"] = 42

        with pytest.raises(RuntimeError):
            flask.session.pop("foo")


@pytest.mark.unittests
def test_redis_session(mocker):
    app = flask.Flask(__name__)
    app.config["SESSION_TYPE"] = "redis"
    Session(app)

    @app.route("/set", methods=["POST"])
    def set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.route("/get")
    def get():
        return flask.jsonify(value=flask.session["value"])

    @app.route("/delete", methods=["POST"])
    def delete():
        del flask.session["value"]
        return "value deleted"

    mocker.patch("redis.StrictRedis.setex").return_value = set
    mocker.patch("redis.StrictRedis.get").return_value = pickle.dumps({"value": "42"})
    mocker.patch("redis.StrictRedis.delete").return_value = delete

    c = app.test_client()
    assert c.post("/set", data={"value": "42"}).data == b"value set"
    assert c.get("/get").json["value"] == "42"
    assert c.post("/delete").data == b"value deleted"


@pytest.mark.unittests
def test_memcached_session(mocker):
    app = flask.Flask(__name__)
    app.config["SESSION_TYPE"] = "memcached"
    Session(app)

    @app.route("/set", methods=["POST"])
    def set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.route("/get")
    def get():
        return flask.session["value"]

    @app.route("/delete", methods=["POST"])
    def delete():
        del flask.session["value"]
        return "value deleted"

    mocker.patch("pylibmc.client.Client.set").return_value = set
    mocker.patch("pylibmc.client.Client.get").return_value = pickle.dumps({"value": "42"})
    mocker.patch("pylibmc.client.Client.delete").return_value = delete

    c = app.test_client()
    assert c.post("/set", data={"value": "42"}).data == b"value set"
    assert c.get("/get").data == b"42"
    assert c.post("/delete").data == b"value deleted"


@pytest.mark.unittests
def test_filesystem_session():
    app = flask.Flask(__name__)
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = tempfile.gettempdir()
    Session(app)

    @app.route("/set", methods=["POST"])
    def set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.route("/get")
    def get():
        return flask.session["value"]

    @app.route("/delete", methods=["POST"])
    def delete():
        del flask.session["value"]
        return "value deleted"

    c = app.test_client()
    assert c.post("/set", data={"value": "42"}).data == b"value set"
    assert c.get("/get").data == b"42"
    c.post("/delete")


@pytest.mark.unittests
def test_mongodb_session(mocker):
    app = flask.Flask(__name__)
    app.testing = True
    app.config["SESSION_TYPE"] = "mongodb"
    Session(app)

    @app.route("/set", methods=["POST"])
    def set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.route("/get")
    def get():
        return flask.jsonify(value=flask.session["value"])

    @app.route("/delete", methods=["POST"])
    def delete():
        del flask.session["value"]
        return "value deleted"

    mocker.patch("pymongo.collection.Collection.update_one").return_value = set
    mocker.patch("pymongo.collection.Collection.find_one").return_value = {
        "val": pickle.dumps({"value": "42"}),
        "expiration": datetime.utcnow() + timedelta(days=1),
    }
    mocker.patch("pymongo.collection.Collection.delete_one").return_value = delete

    c = app.test_client()
    assert c.post("/set", data={"value": "42"}).data == b"value set"
    assert c.get("/get").json == {"value": "42"}
    assert c.post("/delete").data == b"value deleted"


@pytest.mark.unittests
def test_flasksqlalchemy_session():

    app = flask.Flask(__name__)
    app.debug = True
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sessions.db"

    Session(app)

    # create the database and the db-table
    app.session_interface.db.create_all()

    @app.route("/set", methods=["POST"])
    def set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.route("/get")
    def get():
        return flask.session["value"]

    @app.route("/delete", methods=["POST"])
    def delete():
        del flask.session["value"]
        return "value deleted"

    c = app.test_client()
    assert c.post("/set", data={"value": "42"}).data == (b"value set")
    assert c.get("/get").data == b"42"
    assert c.post("/delete").data == b"value deleted"


@pytest.mark.unittests
def test_flasksqlalchemy_session_with_signer():

    app = flask.Flask(__name__)
    app.debug = True
    app.secret_key = "test_secret_key"
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sessions.db"
    app.config["SESSION_USE_SIGNER"] = True

    Session(app)

    # create the database and the db-table
    app.session_interface.db.create_all()

    @app.route("/set", methods=["POST"])
    def set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.route("/get")
    def get():
        return flask.session["value"]

    @app.route("/delete", methods=["POST"])
    def delete():
        del flask.session["value"]
        return "value deleted"

    c = app.test_client()
    assert c.post("/set", data={"value": "42"}).data == b"value set"
    assert c.get("/get").data == b"42"
    assert c.post("/delete").data == b"value deleted"


@pytest.mark.unittests
def test_session_use_signer(mocker):
    app = flask.Flask(__name__)
    app.secret_key = "test_secret_key"
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_USE_SIGNER"] = True
    Session(app)

    @app.route("/set", methods=["POST"])
    def set():
        flask.session["value"] = flask.request.form["value"]
        return "value set"

    @app.route("/get")
    def get():
        return flask.session["value"]

    @app.route("/delete", methods=["POST"])
    def delete():
        del flask.session["value"]
        return "value deleted"

    mocker.patch("redis.StrictRedis.setex").return_value = set
    mocker.patch("redis.StrictRedis.get").return_value = pickle.dumps({"value": "42"})
    mocker.patch("redis.StrictRedis.delete").return_value = delete

    c = app.test_client()
    assert c.post("/set", data={"value": "42"}).data == b"value set"
    assert c.get("/get").data == b"42"
    assert c.post("/delete").data == b"value deleted"
