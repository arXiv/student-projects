# An instance of the app.
from app import create_app
import os

if __name__ == '__main__':
    #create_app().run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=True)
    create_app().run(port=int(os.environ.get("PORT", 8080)), debug=True)
