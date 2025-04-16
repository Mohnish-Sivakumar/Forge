import json
from index import test

def handler(event, context):
    """
    This is the direct entry point for Vercel serverless functions.
    It maps the event from Vercel's format to a standard AWS Lambda format.
    """
    return test(event, context) 