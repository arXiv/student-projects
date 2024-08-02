# An instance of the app.
import google.cloud.logging as gcp_logging
from app import create_app

import os



if __name__ == '__main__':
    client = gcp_logging.Client()
    client.setup_logging()
    create_app().run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=True)



