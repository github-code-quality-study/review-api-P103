import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from urllib.parse import parse_qs, urlparse
import json
import pandas as pd
from datetime import datetime
import uuid
import os
from typing import Callable, Any
from wsgiref.simple_server import make_server

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('stopwords', quiet=True)

adj_noun_pairs_count = {}
sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))

reviews = pd.read_csv('data/reviews.csv').to_dict('records')

class ReviewAnalyzerServer:
    def __init__(self) -> None:
        # This method is a placeholder for future initialization logic
        pass

    def analyze_sentiment(self, review_body):
        sentiment_scores = sia.polarity_scores(review_body)
        return sentiment_scores

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> bytes:
        """
        The environ parameter is a dictionary containing some useful
        HTTP request information such as: REQUEST_METHOD, CONTENT_LENGTH, QUERY_STRING,
        PATH_INFO, CONTENT_TYPE, etc.
        """

        # Handle GET requests
        if environ["REQUEST_METHOD"] == "GET":
            # Create the response body from the reviews and convert to a JSON byte string
            # response_body = json.dumps(reviews, indent=2).encode("utf-8")
            
            # Write your code here
            response_list = []

            # check if query string is populated
            if environ['QUERY_STRING']:

                # parse query string into a dicvtionary
                parsed = parse_qs(environ['QUERY_STRING'])
                try:
                    location = parsed["location"][0]
                    try:
                        # confirm that start date and end date are missing
                        if not parsed["start_date"][0] and not parsed["end_date"][0]:
                            if review["Location"] == location:                      
                                sentiment_scores = sia.polarity_scores(review["ReviewBody"])
                                review["sentiment"] = sentiment_scores 

                                # Append the review to the response list
                                response_list.append(review)
                        else:
                            try:
                                # convert start date query string into datetime object
                                start_date = datetime.strptime(parsed["start_date"][0], "%Y-%m-%d")
                            except KeyError:
                                for review in reviews:
                                    if review["Location"] == location:
                                        # convert review Timestamp into a datetime object
                                        time_stamp = datetime.strptime(review["Timestamp"].split()[0], "%Y-%m-%d")
                                        
                                        # compare time stamp datetime object with end date datime object
                                        if time_stamp <= end_date:
                                            sentiment_scores = sia.polarity_scores(review["ReviewBody"])
                                            review["sentiment"] = sentiment_scores             
                                            response_list.append(review)
                            try:           
                                end_date = datetime.strptime(parsed["end_date"][0], "%Y-%m-%d")
                            except KeyError:
                                for review in reviews:
                                    if review["Location"] == location:
                                        time_stamp = datetime.strptime(review["Timestamp"].split()[0], "%Y-%m-%d")
                                        
                                        # should start date be smaller than time stamp fetch review
                                        if start_date <= time_stamp:
                                            sentiment_scores = sia.polarity_scores(review["ReviewBody"])
                                            review["sentiment"] = sentiment_scores 
                                            # Append the review to the response list
                                            response_list.append(review)

                            # If filter in reviews with dates within query limits 
                            for review in reviews:
                                if review["Location"] == location:
                                    time_stamp = datetime.strptime(review["Timestamp"].split()[0], "%Y-%m-%d")
                                    if start_date <= time_stamp <= end_date:
                                        sentiment_scores = sia.polarity_scores(review["ReviewBody"])
                                        review["sentiment"] = sentiment_scores 
                                        response_list.append(review)

                    except KeyError:

                        # fetch all revies that match location 
                        for review in reviews:
                            if review["Location"] == location:
                                sentiment_scores = sia.polarity_scores(review["ReviewBody"])
                                review["sentiment"] = sentiment_scores 
                                response_list.append(review)

                # Do nothing if location is empty                
                except KeyError:
                    pass
            else:
                # update all reviews with sentiment data
                for review in reviews:
                    sentiment_scores = sia.polarity_scores(review["ReviewBody"])
                    review["sentiment"] = sentiment_scores 
                    response_list.append(review)

            # Sort the response list based on sentiment scores in descending order   
            sorted_response_list = sorted(response_list, key=lambda x: x["sentiment"]["compound"], reverse=True)

            # Convert the sorted response list to JSON and encode it
            response_body = json.dumps(sorted_response_list, indent=2).encode("utf-8")

            # Set the appropriate response headers
            start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])
            
            # Return the response body
            return [response_body]

        # Handle POST request
        if environ["REQUEST_METHOD"] == "POST":
            # Write your code here

            # List of valid locations
            valid_locations = ['Albuquerque, New Mexico','Carlsbad, California', 'Chula Vista, California', 'Colorado Springs, Colorado', 'Denver, Colorado', 'El Cajon, California', 'El Paso, Texas', 'Escondido, California', 'Fresno, California', 'La Mesa, California', 'Las Vegas, Nevada', 'Los Angeles, California', 'Oceanside, California', 'Phoenix, Arizona', 'Sacramento, California', 'Salt Lake City, Utah', 'San Diego, California', 'Tucson, Arizona']
            
            # Get the size of the request body
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0

            # fetch POST payload
            request_body = environ['wsgi.input'].read(request_body_size)

            #parse request body
            parsed = parse_qs(request_body.decode("utf-8"))
            try:
                new_location = parsed["Location"][0]

                # Check if location is valid
                if new_location not in valid_locations:
                    start_response(
                        '400 Invalid location',
                        [("Content-Type", "Error String")]
                    )
                    return ["400 Invalid location".encode('utf-8')]
                
            except KeyError:
                start_response(
                    '400 Missing location',
                    [("Content-Type", "Error String")]
                )
                return ["400 Missing location".encode('utf-8')]
            try:
                new_review_body = parsed["ReviewBody"][0]
            except KeyError:
                start_response(
                    '400 Missing review body',
                    [("Content-Type", "Error String")]
                )
                return ["400 Missing review body".encode('utf-8')]

            # Set the appropriate response headers
            start_response("201 OK", [
            ("Content-Type", "application/json"),
             ])

            new_review = {
                "ReviewId": str(uuid.uuid4()),
                "ReviewBody": new_review_body,
                "Location": new_location,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            reviews.append(new_review)
            new_response_body = json.dumps(new_review, indent=2).encode("utf-8")

            return [new_response_body]


if __name__ == "__main__":
    app = ReviewAnalyzerServer()
    port = os.environ.get('PORT', 8000)
    with make_server("", port, app) as httpd:
        print(f"Listening on port {port}...")
        httpd.serve_forever()