import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.server import app

if __name__ == "__main__":
    print("Starting server on port 5000...")
    app.run(debug=True, port=5000)
