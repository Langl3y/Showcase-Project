
from app.api.common import Namespace, Resource, respond_with_code

ns = Namespace('System')


@ns.route('/health')
@respond_with_code
class HealthResource(Resource):
    @classmethod
    def get(cls):
        return {
            "status": "healthy",
            "service": "hieu-ho-python-assessment",
        }


@ns.route('/info')
@respond_with_code
class InfoResource(Resource):
    @classmethod
    def get(cls):
        return {
            "version": "1.0.0",
            "name": "Hieu Ho Python Assessment",
            "api_prefixes": ["/frontend", "/admin"],
        }
