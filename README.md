# CampusBite - Smart Campus Food Court Ordering System

A full-stack, modular, and responsive **College Food Court Ordering Web Application** built with clean separation into **Frontend**, **Backend**, **C-Core Algorithms**, and **Documentation**.

---

## 🗂️ Clean Modular Project Architecture

```
d:/smart-food-court/
│
├── frontend/                     # FRONTEND USER INTERFACE & ASSETS
│   ├── templates/                # HTML5 responsive UI views
│   │   ├── base.html             # Base layout, dynamic navbar & notifications
│   │   ├── index.html            # Landing page with one-click demo logins
│   │   ├── login.html            # User login (Students, Teachers, Parents, Visitors)
│   │   ├── signup.html           # Universal registration (No student ID needed)
│   │   ├── biller_login.html     # Food court cashier & kitchen staff sign-in
│   │   ├── student_dashboard.html# 26-item food catalog, category chips & diet filters
│   │   ├── cart.html             # Tray management & Google Pay UPI (with 4-digit PIN)
│   │   ├── orders.html           # Real-time visual preparation stepper & live tracking
│   │   └── biller_dashboard.html # Counter token verification, cash collection & inventory
│   └── static/                   # Styling & client-side interaction
│       ├── css/
│       │   └── styles.css        # Warm cream, forest green & terracotta color system
│       └── js/
│           └── app.js            # Shopping tray manager, notifications poller, toasts
│
├── backend/                      # BACKEND APPLICATION & SERVICES
│   ├── main.py                   # Flask server, route controllers & REST API endpoints
│   ├── database.py               # SQLite schema, transactions & 26 demo dishes seeding
│   └── c_bridge.py               # Integration layer connecting Python to C data structures
│
├── c_core/                       # C DATA STRUCTURES & ALGORITHMS MODULE
│   ├── food_court_ds.h           # Header declarations (Queue, Linked List, Sort, Search)
│   ├── food_court_ds.c           # C implementations (FIFO Queue, Merge Sort, Binary Search)
│   ├── main.c                    # C CLI runner & test suite
│   └── Makefile                  # Compilation build script for GCC / MinGW
│
├── food_court.db                 # Persistent SQLite database file
├── run.py                        # Single root application entrypoint
├── requirements.txt              # Python runtime dependencies
└── README.md                     # Comprehensive project guide
```

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your web browser.

---

## 🔑 Demo Access Accounts

| Role | Login Link | Demo Email | Password |
| :--- | :--- | :--- | :--- |
| **User (Student, Teacher, Parent, Visitor)** | [`/login`](http://127.0.0.1:5000/login) | `user@campus.edu` | `campus123` |
| **Biller / Cashier** | [`/biller/login`](http://127.0.0.1:5000/biller/login) | `biller@campus.edu` | `biller123` |

*(On checkout with Google Pay, use the 4-digit PIN: **`1234`**)*

### Menu Image Sources

The following menu photos are hosted on Wikimedia Commons; their file pages include the author and license details:

- [Masala dosa](https://commons.wikimedia.org/wiki/File:Masala_Dosa_in_Banana_Leaf_with_Chutney.jpg)
- [Idli vada](https://commons.wikimedia.org/wiki/File:Ondu_Plate_Idli_Vada.jpg)
- [Onion uttapam](https://commons.wikimedia.org/wiki/File:Onion_Uthappam.jpg)
- [Chole bhature](https://commons.wikimedia.org/wiki/File:Chole_Bhature_3.jpg)
- [Vegetable biryani](https://commons.wikimedia.org/wiki/File:Veg_Biryani_-_Mohali_2016-08-07_9120.JPG)
- [Chicken biryani](https://commons.wikimedia.org/wiki/File:Biryani_Home.jpg)
- [Pav bhaji](https://commons.wikimedia.org/wiki/File:Pav_Bhaji.jpg)
- [Gulab jamun](https://commons.wikimedia.org/wiki/File:Gulab_jamun_(Gibraltar,_November_2020).jpg)
- [Ras malai](https://commons.wikimedia.org/wiki/File:Ras_Malai.JPG)
