import json

from flask import Response, jsonify, render_template, request

from Foodiefy import recommendation_service


def register_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    @app.route("/ready")
    def health_check():
        return jsonify({
            "status": "ok",
            "service": "restaurant-recommendation-service",
            "healthy": True,
        })

    @app.route("/test", methods=["POST"])
    def test():
        payload = request.get_json(silent=True)

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (TypeError, json.JSONDecodeError):
                return jsonify({"error": "Invalid JSON payload."}), 400

        if not isinstance(payload, dict):
            return jsonify({"error": "Expected a JSON object."}), 400

        try:
            latitude = float(payload.get("latitude"))
        except (TypeError, ValueError):
            return jsonify({"error": "Latitude must be a valid number."}), 400

        try:
            longitude = float(payload.get("longitude"))
        except (TypeError, ValueError):
            return jsonify({"error": "Longitude must be a valid number."}), 400

        words = payload.get("words", "")
        if words is None:
            words = ""
        if not isinstance(words, str):
            words = str(words)

        recommendation_payload = recommendation_service.find_recommendations(latitude, longitude, words)
        return Response(recommendation_payload, mimetype="application/json")

    return app
