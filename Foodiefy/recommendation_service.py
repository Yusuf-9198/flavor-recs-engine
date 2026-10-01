#!/usr/bin/env python
# coding: utf-8

import json
import string
import warnings
from pathlib import Path

import geojson
import nltk
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import WordPunctTokenizer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from Foodiefy.config import BUSINESS_DATA_PATH, GENERATED_DIR, OUTPUT_PATH, REVIEWS_DATA_PATH

warnings.filterwarnings("ignore")
nltk.download("stopwords", quiet=True)

GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _load_stop_words():
    cleaned_words = []
    for word in stopwords.words("english"):
        cleaned = "".join(char for char in word if char not in string.punctuation)
        cleaned_words.append(cleaned)
    return set(cleaned_words)


STOP_WORDS = _load_stop_words()


def clean_review_text(message):
    if pd.isna(message):
        return ""
    cleaned_text = "".join(char for char in str(message) if char not in string.punctuation)
    return " ".join(word for word in cleaned_text.split() if word.lower() not in STOP_WORDS)


try:
    RESTAURANT_DF = pd.read_csv(BUSINESS_DATA_PATH)
    RESTAURANT_DF = RESTAURANT_DF.copy()
except FileNotFoundError as exc:  # pragma: no cover - runtime guard for deployment
    raise FileNotFoundError(f"Restaurant business data not found at: {BUSINESS_DATA_PATH}") from exc


try:
    REVIEWS_DF = pd.read_csv(REVIEWS_DATA_PATH)
    REVIEWS_DF = REVIEWS_DF[["review_id", "user_id", "business_id", "text", "stars_business", "review_count"]].copy()
    REVIEWS_DF = REVIEWS_DF.dropna(subset=["text"]).copy()
    REVIEWS_DF["text"] = REVIEWS_DF["text"].fillna("")
    REVIEWS_DF.rename(
        columns={
            "review_id": "Review_ID",
            "user_id": "User_Id",
            "business_id": "Business_Id",
            "text": "Reviews",
            "stars_business": "Rating",
            "review_count": "Review_count",
        },
        inplace=True,
    )
    REVIEWS_DF["Reviews"] = REVIEWS_DF["Reviews"].str.replace(";", " ")
    REVIEWS_DF["Reviews"] = REVIEWS_DF["Reviews"].apply(clean_review_text)
except FileNotFoundError as exc:  # pragma: no cover - runtime guard for deployment
    raise FileNotFoundError(f"Restaurant reviews data not found at: {REVIEWS_DATA_PATH}") from exc


def recommend_restaurants(latitude, longitude):
    restaurant_frame = RESTAURANT_DF.copy()
    coordinates = restaurant_frame[["latitude", "longitude"]]

    cluster_model = KMeans(n_clusters=5, init="k-means++")
    cluster_model.fit(coordinates)
    restaurant_frame["cluster"] = cluster_model.predict(restaurant_frame[["latitude", "longitude"]])

    query_point = pd.DataFrame([[latitude, longitude]], columns=["latitude", "longitude"])
    cluster_id = cluster_model.predict(query_point)[0]
    filtered_restaurants = restaurant_frame[restaurant_frame["cluster"] == cluster_id]
    ranked_restaurants = filtered_restaurants.sort_values(
        by=["stars_business", "review_count"], ascending=False
    ).head(50)

    return ranked_restaurants[["name", "latitude", "longitude", "stars_business", "categories", "review_count", "ID"]].copy()


def vectorize_reviews(candidate_restaurants):
    shortlisted_reviews = REVIEWS_DF[REVIEWS_DF["Business_Id"].isin(candidate_restaurants["Business_Id"])].copy()

    user_reviews = shortlisted_reviews[["User_Id", "Reviews"]].groupby("User_Id").agg({"Reviews": " ".join})
    business_reviews = shortlisted_reviews[["Business_Id", "Reviews"]].groupby("Business_Id").agg({"Reviews": " ".join})

    user_vectorizer = TfidfVectorizer(tokenizer=WordPunctTokenizer().tokenize, token_pattern=None, max_features=5000)
    business_vectorizer = TfidfVectorizer(tokenizer=WordPunctTokenizer().tokenize, token_pattern=None, max_features=5000)

    user_vectors = user_vectorizer.fit_transform(user_reviews["Reviews"])
    business_vectors = business_vectorizer.fit_transform(business_reviews["Reviews"])

    user_rating_matrix = pd.pivot_table(
        shortlisted_reviews,
        values="Rating",
        index=["User_Id"],
        columns=["Business_Id"],
    )

    user_factor_matrix = pd.DataFrame(
        user_vectors.toarray(),
        index=user_reviews.index,
        columns=user_vectorizer.get_feature_names_out(),
    )
    business_factor_matrix = pd.DataFrame(
        business_vectors.toarray(),
        index=business_reviews.index,
        columns=business_vectorizer.get_feature_names_out(),
    )

    updated_user_factor_matrix, updated_business_factor_matrix = matrix_factorization(
        user_rating_matrix,
        user_factor_matrix,
        business_factor_matrix,
        steps=25,
        gamma=0.001,
        lamda=0.02,
    )
    return updated_user_factor_matrix, updated_business_factor_matrix, user_vectorizer


def matrix_factorization(rating_matrix, user_matrix, business_matrix, steps=25, gamma=0.001, lamda=0.02):
    for _ in range(steps):
        for user_id in rating_matrix.index:
            for business_id in rating_matrix.columns:
                if rating_matrix.loc[user_id, business_id] > 0:
                    error_term = rating_matrix.loc[user_id, business_id] - np.dot(user_matrix.loc[user_id], business_matrix.loc[business_id])
                    user_matrix.loc[user_id] = user_matrix.loc[user_id] + gamma * (error_term * business_matrix.loc[business_id] - lamda * user_matrix.loc[user_id])
                    business_matrix.loc[business_id] = business_matrix.loc[business_id] + gamma * (error_term * user_matrix.loc[user_id] - lamda * business_matrix.loc[business_id])

        error_total = 0.0
        for user_id in rating_matrix.index:
            for business_id in rating_matrix.columns:
                if rating_matrix.loc[user_id, business_id] > 0:
                    prediction = np.dot(user_matrix.loc[user_id], business_matrix.loc[business_id])
                    error_total += (rating_matrix.loc[user_id, business_id] - prediction) ** 2 + lamda * (
                        np.linalg.norm(user_matrix.loc[user_id]) ** 2 + np.linalg.norm(business_matrix.loc[business_id]) ** 2
                    )
        if error_total < 0.001:
            break

    return user_matrix, business_matrix


def find_recommendations(latitude, longitude, words):
    recommended_list = []

    restaurant_candidates = recommend_restaurants(latitude, longitude).copy()
    if restaurant_candidates.empty:
        return json.dumps({"type": "FeatureCollection", "features": []})

    restaurant_candidates.rename(columns={"ID": "Business_Id"}, inplace=True)

    query_frame = pd.DataFrame([words], columns=["Reviews"])
    query_frame["Reviews"] = query_frame["Reviews"].apply(clean_review_text)

    user_matrix, business_matrix, user_vectorizer = vectorize_reviews(restaurant_candidates)
    query_vectors = user_vectorizer.transform(query_frame["Reviews"])
    query_vector_frame = pd.DataFrame(
        query_vectors.toarray(),
        index=query_frame.index,
        columns=user_vectorizer.get_feature_names_out(),
    )

    predicted_ratings = pd.DataFrame(
        np.dot(query_vector_frame.loc[0], business_matrix.T),
        index=business_matrix.index,
        columns=["Rating"],
    )
    shortlisted_restaurants = predicted_ratings.sort_values(by=["Rating"], ascending=False).head(7)

    for business_id in shortlisted_restaurants.index:
        restaurant_row = restaurant_candidates[restaurant_candidates["Business_Id"] == business_id].iloc[0]
        case = {
            "Name": restaurant_row["name"],
            "Categories": restaurant_row["categories"],
            "Latitude": restaurant_row["latitude"],
            "Longitude": restaurant_row["longitude"],
            "Rating": str(restaurant_row["stars_business"]),
        }
        recommended_list.append(case)

    recommendation_frame = pd.DataFrame(recommended_list)
    return export_recommendations_to_geojson(recommendation_frame)


def findRecommendations(latitude, longitude, words):
    return find_recommendations(latitude, longitude, words)


def export_recommendations_to_geojson(recommendation_frame):
    features = []
    for _, row in recommendation_frame.iterrows():
        feature = geojson.Feature(
            geometry=geojson.Point((float(row["Longitude"]), float(row["Latitude"]))),
            properties={
                "name": row["Name"],
                "description": row["Categories"],
                "rating": row["Rating"],
            },
        )
        features.append(feature)

    feature_collection = geojson.FeatureCollection(features)
    OUTPUT_PATH.write_text(geojson.dumps(feature_collection, sort_keys=True, ensure_ascii=False, indent=4), encoding="utf-8")
    return geojson.dumps(feature_collection, sort_keys=True, ensure_ascii=False, indent=4)


def build_geojson(recommendation_frame):
    return export_recommendations_to_geojson(recommendation_frame)


__all__ = [
    "recommend_restaurants",
    "vectorize_reviews",
    "matrix_factorization",
    "find_recommendations",
    "findRecommendations",
    "export_recommendations_to_geojson",
    "build_geojson",
    "clean_review_text",
]
