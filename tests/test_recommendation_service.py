import json

from Foodiefy import recommendation_service as recommender


def test_find_recommendations_returns_geojson_payload():
    result = recommender.find_recommendations(39.951732, -75.142140, "pizza pasta")

    assert isinstance(result, str)
    assert "FeatureCollection" in result
    feature_collection = json.loads(result)
    assert feature_collection["type"] == "FeatureCollection"
    assert isinstance(feature_collection["features"], list)


def test_recommendation_service_exposes_compatibility_aliases():
    assert hasattr(recommender, "find_recommendations")
    assert hasattr(recommender, "findRecommendations")
    assert hasattr(recommender, "recommend_restaurants")
