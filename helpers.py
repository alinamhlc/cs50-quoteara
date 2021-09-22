from functools import wraps
from os import environ
from os.path import dirname, join

import requests
from dotenv import load_dotenv
from flask import redirect, session
from PIL import Image
from pytesseract import pytesseract


def img_to_text(img):
    """Extracts text from img wrapped as FileStorage
    
    https://www.geeksforgeeks.org/how-to-extract-text-from-images-with-python/
    """ 

    # Open the image & store it in an image object
    image = Image.open(img)
    
    # Passing the image object to image_to_string() function tol extract the text from image
    text = pytesseract.image_to_string(image)
    
    return text[:-1]


def get_envvar(name):
    """ Gets value of a environment variable for a virtualenv"""

    # Set up access for env var
    dotenv_path = join(dirname(__file__), 'env\.env')
    load_dotenv(dotenv_path)

    return environ.get(name)


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(book_id):
    """Look up books based on id"""

    # Contact API
    try:
        url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    
    # Ensure title exists
    try:
        title = response.json()["volumeInfo"]["title"]
    except:
        title = ""

    # Ensure author exists
    try:
        authors = response.json()["volumeInfo"]["authors"]
    except:
        authors=""
        
    return {
        "title": title,
        "authors": authors
        }
