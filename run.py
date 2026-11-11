import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app

if __name__ == "__main__":
    print("=" * 60)
    print("CampusBite Smart Food Court Web Application")
    print("Frontend: ./frontend/ (templates & static assets)")
    print("Backend:  ./backend/  (Flask API & SQLite DB)")
    print("Core:     ./c_core/   (C Data Structures & Algorithms)")
    print("Server running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
