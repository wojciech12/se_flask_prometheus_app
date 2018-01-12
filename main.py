from flask import Flask, Response
from flask import request
from prometheus_client import (Summary, generate_latest, Histogram)


class MetricCollector:

    def observe_myself(self, path, status_code, duration):
        self._me.labels(path=path, status_code=status_code).observe(duration)


    def observe_db(self, status_code, duration):
        self._db.labels(status_code=status_code).observe(duration)


    def observe_external(self, status_code, duration):
        self._external.labels(status_code=status_code).observe(duration)


    def get_latest(self):
        return generate_latest()

    @staticmethod
    def newCollector(service_name):
        prefix = service_name.replace("-", "_")
        STATUS_CODE = 'status_code'
        PATH = "path"

        about_me = Summary(prefix + "_duration_seconds", service_name + " latency request distribution", [PATH, STATUS_CODE])
        about_db = Summary(prefix + "_database_duration_seconds", "database latency request distribution", [STATUS_CODE])
        about_her = Summary(prefix + "_audit_duration_seconds", "audit srv latency request distribution", [STATUS_CODE])

        mc = MetricCollector()
        mc._me = about_me
        mc._ab = about_db
        mc._external = about_her
        return mc



def get_collector(name):
    return MetricCollector.newCollector(name)


def get_app():
    app = Flask(__name__)
    return app


def add_routes(app,  collector): 
    @app.route('/hello')
    def hello_route():
        return 'hello'

    @app.route('/world')
    def world_route():
        return 'world'



def instrument_requests(app, collector):
    import time
    
    def before():
        print(request)
        request.start_time = time.time()
    
    def after(response):
        request_latency = time.time() - request.start_time
        collector.observe_myself(request.path, response.status_code, request_latency)
        return response

    app.before_request(before)
    app.after_request(after)


def add_metrics_route(app, collector):
    @app.route('/metrics', strict_slashes=False, methods=['GET'])
    def metrics_rotue():
        txt = generate_latest()
        return Response(txt, mimetype='text/plain')


if __name__ == "__main__":
    app = get_app()
    c = get_collector('hello-world')
    add_routes(app, c)
    add_metrics_route(app, c)
    instrument_requests(app, c)
    app.run()
