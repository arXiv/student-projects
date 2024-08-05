# An instance of the app.
from app import create_app
from datetime import datetime
import os



if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=True)



