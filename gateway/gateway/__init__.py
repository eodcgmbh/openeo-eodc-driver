from os import environ
from flask import Flask, redirect, current_app
from flask_cors import CORS
from flask_nameko import FlaskPooledClusterRpcProxy
from flask_restful_swagger_2 import Api, swagger


rpc = FlaskPooledClusterRpcProxy()


def create_gateway():

    gateway = Flask(__name__)
    CORS(gateway, resources={r"/spec/*": {"origins": "*"}})

    gateway.config.from_object(environ.get('GATEWAY_SETTINGS'))
    gateway.config.update(
        dict(
            NAMEKO_AMQP_URI="pyamqp://{0}:{1}@{2}:{3}".format(
                environ.get("RABBIT_USER"),
                environ.get("RABBIT_PASSWORD"),
                environ.get("RABBIT_HOST"),
                environ.get("RABBIT_PORT")
            )
        )
    )

    rpc.init_app(gateway)
    generate_api(gateway)

    return gateway


def generate_api(gateway):
    api = Api(
        gateway,
        api_version='0.0.2',
        host=environ.get("HOST"),
        title="openEO API",
        api_spec_url= "/spec/swagger",
        base_path="/api/v0.0.2/",
        description="API implementation of openEO",
        contact={
            "name": environ.get("CONTACT_NAME"),
            "url": environ.get("CONTACT_URL"),
            "email": environ.get("CONTACT_EMAIL")
        },
        consumes=[
            "application/json"
        ],
        produces=[
            "application/json"
        ],
        schemes=[
            "https",
            "http"
        ],
        security_definitions={
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header"
            },
            "Basic": {
                "type": "basic"
            }
        }
    )

    from .index import Index, Capabilities, OutputFormats
    from .health import HealthApi
    from .auth import RegisterApi, LoginApi
    from .data import RecordsApi, ProductDetailApi
    from .processes import ProcessApi, ProcessDetailApi
    from .jobs import JobsApi, JobDetailApi,BatchJobApi, DownloadApi, DownloadFileApi

    api.add_resource(Index, "/")
    api.add_resource(Capabilities, "/capabilities")
    api.add_resource(OutputFormats, "/capabilities/output_formats")
    api.add_resource(HealthApi, "/health")
    api.add_resource(RegisterApi, "/auth/register")
    api.add_resource(LoginApi, "/auth/login")
    api.add_resource(RecordsApi, "/data")
    api.add_resource(ProductDetailApi, "/data/<string:product_id>")
    api.add_resource(ProcessApi, "/processes")
    api.add_resource(ProcessDetailApi, "/processes/<string:process_id>")
    api.add_resource(JobsApi, "/jobs")
    api.add_resource(JobDetailApi, "/jobs/<string:job_id>")
    api.add_resource(BatchJobApi, "/jobs/<string:job_id>/queue")
    api.add_resource(DownloadApi, "/jobs/<string:job_id>/download")
    api.add_resource(DownloadFileApi, "/download/<string:job_id>/<string:file_name>")
