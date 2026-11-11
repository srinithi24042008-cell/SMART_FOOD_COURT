import os
import sys
import random
import time
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from backend.database import get_db_connection, init_db
from backend.c_bridge import (
    OrderNode, KitchenOrderQueue, OrderHistoryLinkedList,
    merge_sort_orders_by_amount, binary_search_order_by_id,
    get_c_module_status
)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app = Flask(__name__,
            template_folder=os.path.join(FRONTEND_DIR, "templates"),
            static_folder=os.path.join(FRONTEND_DIR, "static"))
app.secret_key = os.environ.get("SECRET_KEY", "smart_campus_food_court_secure_key_2026")
CORS(app)
init_db()
kitchen_queue = KitchenOrderQueue()
history_linked_list = OrderHistoryLinkedList()
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"error": "Unauthorized. Please log in."}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "student":
            if request.is_json:
                return jsonify({"error": "Forbidden. Student access only."}), 403
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function
def biller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "biller":
            if request.is_json:
                return jsonify({"error": "Forbidden. Biller access only."}), 403
            return redirect(url_for("biller_login_page"))
        return f(*args, **kwargs)
    return decorated_function
def sync_active_queue():
    """Sync active confirmed/preparing orders into C-Core Kitchen Queue"""
    global kitchen_queue, history_linked_list
    conn = get_db_connection()
    active_rows = conn.execute("""
        SELECT o.*, u.name as student_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.order_status IN ('CONFIRMED', 'PREPARING')
        ORDER BY o.id ASC
    """).fetchall()
    new_queue = KitchenOrderQueue()
    for r in active_rows:
        node = OrderNode(
            order_id=r["id"],
            bill_no=r["bill_no"],
            token_no=r["token_no"],
            student_id=r["user_id"],
            student_name=r["student_name"],
            total_amount=r["total_amount"],
            payment_method=r["payment_method"],
            payment_status=r["payment_status"],
            order_status=r["order_status"],
            created_at=int(time.time())
        )
        new_queue.enqueue(node)
    kitchen_queue = new_queue
    all_rows = conn.execute("""
        SELECT o.*, u.name as student_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.id DESC LIMIT 100
    """).fetchall()
    new_list = OrderHistoryLinkedList()
    for r in all_rows:
        node = OrderNode(
            order_id=r["id"],
            bill_no=r["bill_no"],
            token_no=r["token_no"],
            student_id=r["user_id"],
            student_name=r["student_name"],
            total_amount=r["total_amount"],
            payment_method=r["payment_method"],
            payment_status=r["payment_status"],
            order_status=r["order_status"],
            created_at=int(time.time())
        )
        new_list.append(node)
    history_linked_list = new_list
    conn.close()
sync_active_queue()
@app.route("/")
def index():
    if "user_id" in session:
        if session.get("role") == "biller":
            return redirect(url_for("biller_dashboard"))
        return redirect(url_for("student_dashboard"))
    return render_template("index.html")
@app.route("/login")
def login_page():
    return render_template("login.html")
@app.route("/signup")
def signup_page():
    return render_template("signup.html")
@app.route("/biller/login")
def biller_login_page():
    return render_template("biller_login.html")
@app.route("/student/dashboard")
@student_required
def student_dashboard():
    return render_template("student_dashboard.html")
@app.route("/cart")
@student_required
def cart_page():
    return render_template("cart.html")
@app.route("/orders")
@student_required
def orders_page():
    return render_template("orders.html")
@app.route("/biller/dashboard")
@biller_required
def biller_dashboard():
    return render_template("biller_dashboard.html")
@app.route("/c-core-info")
def c_core_info_page():
    return render_template("c_core_info.html")
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    phone = data.get("phone", "").strip()
    student_id = data.get("student_id", "").strip()
    role = data.get("role", "student")
    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email and password are required."}), 400
    if role == "biller":
        return jsonify({
            "success": False,
            "error": "Biller accounts cannot be registered here. Please sign in through the biller portal."
        }), 403
    if role not in ["student", "biller"]:
        role = "student"
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"success": False, "error": "An account with this email already exists."}), 409
    hashed_pw = generate_password_hash(password)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, phone, student_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, hashed_pw, role, phone, student_id))
    conn.commit()
    user_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO notifications (user_id, title, message, type)
        VALUES (?, ?, ?, ?)
    """, (user_id, "Welcome to Campus Food Court!", "Your account has been set up successfully. Explore delicious food and enjoy queue-less ordering!", "success"))
    conn.commit()
    conn.close()
    session["user_id"] = user_id
    session["name"] = name
    session["email"] = email
    session["role"] = role
    redirect_url = "/biller/dashboard" if role == "biller" else "/student/dashboard"
    return jsonify({"success": True, "message": "Registered successfully", "redirect": redirect_url})
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    expected_role = data.get("role", None)
    if not email or not password:
        return jsonify({"success": False, "error": "Please provide email and password."}), 400
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid email or password."}), 401
    if expected_role and user["role"] != expected_role:
        return jsonify({
            "success": False,
            "error": f"Access denied. This portal is for {expected_role} accounts. Your account is registered as '{user['role']}'."
        }), 403
    session["user_id"] = user["id"]
    session["name"] = user["name"]
    session["email"] = user["email"]
    session["role"] = user["role"]
    redirect_url = "/biller/dashboard" if user["role"] == "biller" else "/student/dashboard"
    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['name']}!",
        "role": user["role"],
        "redirect": redirect_url
    })
@app.route("/api/auth/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    if request.is_json:
        return jsonify({"success": True, "message": "Logged out successfully"})
    return redirect(url_for("login_page"))
@app.route("/api/auth/current_user", methods=["GET"])
def current_user():
    if "user_id" not in session:
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "user_id": session["user_id"],
        "name": session["name"],
        "email": session["email"],
        "role": session["role"]
    })
@app.route("/api/food/items", methods=["GET"])
def get_food_items():
    category = request.args.get("category")
    is_veg = request.args.get("is_veg")
    search = request.args.get("search", "").strip()
    featured_only = request.args.get("featured")
    query = "SELECT * FROM food_items WHERE 1=1"
    params = []
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if is_veg is not None and is_veg != "":
        query += " AND is_veg = ?"
        params.append(int(is_veg))
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")
    if featured_only:
        query += " AND is_featured = 1"
    query += " ORDER BY is_available DESC, name ASC"
    conn = get_db_connection()
    items = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY display_order ASC").fetchall()
    conn.close()
    return jsonify({
        "success": True,
        "items": [dict(row) for row in items],
        "categories": [dict(cat) for cat in categories]
    })
@app.route("/api/biller/food/add", methods=["POST"])
@biller_required
def add_food_item():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    price = float(data.get("price", 0))
    category = data.get("category", "South Indian")
    image_url = data.get("image_url", "").strip()
    is_veg = 1 if data.get("is_veg", True) else 0
    stock_quantity = int(data.get("stock_quantity", 30))
    prep_time_mins = int(data.get("prep_time_mins", 10))
    is_available = 1 if data.get("is_available", True) else 0
    is_featured = 1 if data.get("is_featured", False) else 0
    if not name or price <= 0:
        return jsonify({"success": False, "error": "Valid name and positive price are required."}), 400
    if not image_url:
        image_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO food_items (name, description, price, category, image_url, is_veg, stock_quantity, prep_time_mins, is_available, is_featured)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, description, price, category, image_url, is_veg, stock_quantity, prep_time_mins, is_available, is_featured))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"success": True, "message": f"'{name}' added to food court menu!", "id": new_id})
@app.route("/api/biller/food/update/<int:item_id>", methods=["PUT", "POST"])
@biller_required
def update_food_item(item_id):
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description")
    price = float(data.get("price", 0)) if "price" in data else None
    category = data.get("category")
    image_url = data.get("image_url")
    is_veg = 1 if data.get("is_veg") else 0 if "is_veg" in data else None
    stock_quantity = int(data.get("stock_quantity")) if "stock_quantity" in data else None
    prep_time_mins = int(data.get("prep_time_mins")) if "prep_time_mins" in data else None
    is_available = 1 if data.get("is_available") else 0 if "is_available" in data else None
    is_featured = 1 if data.get("is_featured") else 0 if "is_featured" in data else None
    conn = get_db_connection()
    cur = conn.cursor()
    item = cur.execute("SELECT * FROM food_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"success": False, "error": "Item not found"}), 404
    cur.execute("""
        UPDATE food_items
        SET name = COALESCE(?, name),
            description = COALESCE(?, description),
            price = COALESCE(?, price),
            category = COALESCE(?, category),
            image_url = COALESCE(?, image_url),
            is_veg = COALESCE(?, is_veg),
            stock_quantity = COALESCE(?, stock_quantity),
            prep_time_mins = COALESCE(?, prep_time_mins),
            is_available = COALESCE(?, is_available),
            is_featured = COALESCE(?, is_featured)
        WHERE id = ?
    """, (name, description, price, category, image_url, is_veg, stock_quantity, prep_time_mins, is_available, is_featured, item_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Food item updated successfully!"})
@app.route("/api/biller/food/toggle-stock/<int:item_id>", methods=["POST"])
@biller_required
def toggle_stock(item_id):
    conn = get_db_connection()
    cur = conn.cursor()
    item = cur.execute("SELECT is_available, name FROM food_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"success": False, "error": "Item not found"}), 404
    new_status = 0 if item["is_available"] else 1
    cur.execute("UPDATE food_items SET is_available = ? WHERE id = ?", (new_status, item_id))
    conn.commit()
    conn.close()
    status_str = "Available" if new_status else "Out of Stock"
    return jsonify({"success": True, "is_available": new_status, "message": f"'{item['name']}' is now marked as {status_str}."})
@app.route("/api/biller/food/delete/<int:item_id>", methods=["DELETE", "POST"])
@biller_required
def delete_food_item(item_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Food item removed from menu."})
def generate_bill_no():
    """Generate unique bill number, e.g. BILL-82910"""
    rand = random.randint(10000, 99999)
    return f"BILL-{rand}"
def generate_token_no():
    """Generate human-friendly pickup token, e.g. TKN-A47"""
    letter = random.choice(["A", "B", "C", "D", "K"])
    num = random.randint(10, 99)
    return f"TKN-{letter}{num}"
@app.route("/api/orders/place", methods=["POST"])
@student_required
def place_order():
    data = request.get_json() or {}
    items = data.get("items", [])  # list of {food_id, quantity}
    payment_method = data.get("payment_method", "UPI")  # 'UPI' or 'CASH'
    simulated_payment = data.get("simulated_payment", False) # True for GPay/UPI verified simulation
    upi_pin = str(data.get("upi_pin", "")).strip()
    special_instructions = data.get("special_instructions", "")
    if payment_method == "UPI" and simulated_payment:
        if len(upi_pin) != 4 or not upi_pin.isdigit():
            return jsonify({"success": False, "error": "Invalid UPI PIN. Please enter a valid 4-digit PIN (e.g. 1234)."}), 400
    if not items or len(items) == 0:
        return jsonify({"success": False, "error": "Your cart is empty. Add food items before checkout."}), 400
    if payment_method not in ["UPI", "CASH"]:
        return jsonify({"success": False, "error": "Invalid payment method. Choose UPI or Cash on Delivery."}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        total_amount = 0.0
        verified_items = []
        for item in items:
            f_id = item.get("food_id")
            qty = int(item.get("quantity", 1))
            if qty <= 0:
                continue
            food = cur.execute("SELECT * FROM food_items WHERE id = ?", (f_id,)).fetchone()
            if not food:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "error": f"Food item ID {f_id} not found."}), 404
            if not food["is_available"]:
                conn.rollback()
                conn.close()
                return jsonify({"success": False, "error": f"'{food['name']}' is currently marked Out of Stock by the biller."}), 400
            if food["stock_quantity"] < qty:
                conn.rollback()
                conn.close()
                return jsonify({
                    "success": False,
                    "error": f"Insufficient stock for '{food['name']}'. Only {food['stock_quantity']} portions remaining."
                }), 400
            subtotal = round(food["price"] * qty, 2)
            total_amount += subtotal
            verified_items.append({
                "food_id": f_id,
                "name": food["name"],
                "quantity": qty,
                "price": food["price"],
                "subtotal": subtotal
            })
        if not verified_items:
            conn.close()
            return jsonify({"success": False, "error": "No valid items to place order."}), 400
        if payment_method == "UPI":
            payment_status = "PAID" if simulated_payment else "PENDING"
        else: # CASH
            payment_status = "PENDING" # Must be collected at counter by biller
        order_status = "CONFIRMED"
        bill_no = generate_bill_no()
        token_no = generate_token_no()
        for itm in verified_items:
            cur.execute("""
                UPDATE food_items
                SET stock_quantity = stock_quantity - ?,
                    is_available = CASE WHEN (stock_quantity - ?) <= 0 THEN 0 ELSE is_available END
                WHERE id = ?
            """, (itm["quantity"], itm["quantity"], itm["food_id"]))
        user_id = session["user_id"]
        cur.execute("""
            INSERT INTO orders (bill_no, token_no, user_id, total_amount, subtotal, tax_amount, payment_method, payment_status, order_status, special_instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bill_no, token_no, user_id, round(total_amount, 2), round(total_amount, 2), 0.0, payment_method, payment_status, order_status, special_instructions))
        order_id = cur.lastrowid
        for itm in verified_items:
            cur.execute("""
                INSERT INTO order_items (order_id, food_item_id, food_name, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, itm["food_id"], itm["name"], itm["quantity"], itm["price"], itm["subtotal"]))
        pay_info = "Payment verified via UPI" if payment_status == "PAID" else "Pay at counter when collecting"
        cur.execute("""
            INSERT INTO notifications (user_id, order_id, title, message, type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            order_id,
            f"Order Confirmed: {bill_no}",
            f"Your pickup token is {token_no}. Total: ₹{total_amount:.2f} ({pay_info}). The kitchen is preparing your meal!",
            "success"
        ))
        conn.commit()
        conn.close()
        sync_active_queue()
        return jsonify({
            "success": True,
            "message": "Order placed successfully!",
            "order": {
                "id": order_id,
                "bill_no": bill_no,
                "token_no": token_no,
                "total_amount": round(total_amount, 2),
                "payment_method": payment_method,
                "payment_status": payment_status,
                "order_status": order_status,
                "items": verified_items
            }
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "error": f"Error processing order: {str(e)}"}), 500
@app.route("/api/orders/my-orders", methods=["GET"])
@student_required
def get_student_orders():
    user_id = session["user_id"]
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()
    result = []
    for o in orders:
        items = conn.execute("""
            SELECT * FROM order_items WHERE order_id = ?
        """, (o["id"],)).fetchall()
        od = dict(o)
        od["items"] = [dict(it) for it in items]
        result.append(od)
    conn.close()
    return jsonify({"success": True, "orders": result})
@app.route("/api/orders/cancel/<int:order_id>", methods=["POST"])
@student_required
def cancel_student_order():
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()
    order = cur.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id)).fetchone()
    if not order:
        conn.close()
        return jsonify({"success": False, "error": "Order not found."}), 404
    if order["order_status"] in ["PREPARING", "READY_FOR_PICKUP", "COLLECTED"]:
        conn.close()
        return jsonify({
            "success": False,
            "error": f"Cannot cancel: Food preparation is already in progress ({order['order_status']}). Please speak with the billing counter."
        }), 400
    if order["order_status"] == "CANCELLED":
        conn.close()
        return jsonify({"success": False, "error": "Order is already cancelled."}), 400
    items = cur.execute("SELECT food_item_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    for itm in items:
        cur.execute("""
            UPDATE food_items
            SET stock_quantity = stock_quantity + ?,
                is_available = 1
            WHERE id = ?
        """, (itm["quantity"], itm["food_item_id"]))
    new_pay_status = "REFUNDED" if order["payment_status"] == "PAID" else "FAILED"
    cur.execute("""
        UPDATE orders
        SET order_status = 'CANCELLED',
            payment_status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_pay_status, order_id))
    cur.execute("""
        INSERT INTO notifications (user_id, order_id, title, message, type)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        order_id,
        f"Order Cancelled: {order['bill_no']}",
        f"Order {order['bill_no']} was cancelled. Stock has been restored. If paid online, ₹{order['total_amount']} is queued for refund.",
        "warning"
    ))
    conn.commit()
    conn.close()
    sync_active_queue()
    return jsonify({"success": True, "message": "Order cancelled successfully and stock restored."})
@app.route("/api/biller/orders", methods=["GET"])
@biller_required
def get_biller_orders():
    status = request.args.get("status")
    payment_method = request.args.get("payment_method")
    token_search = request.args.get("token")
    sort_by = request.args.get("sort", "id_desc")
    conn = get_db_connection()
    query = """
        SELECT o.*, u.name as student_name, u.email as student_email, u.phone as student_phone
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE 1=1
    """
    params = []
    if status and status != "ALL":
        query += " AND o.order_status = ?"
        params.append(status)
    if payment_method and payment_method != "ALL":
        query += " AND o.payment_method = ?"
        params.append(payment_method)
    if token_search:
        query += " AND (o.token_no LIKE ? OR o.bill_no LIKE ? OR u.name LIKE ?)"
        params.append(f"%{token_search}%")
        params.append(f"%{token_search}%")
        params.append(f"%{token_search}%")
    query += " ORDER BY o.id DESC"
    orders = conn.execute(query, params).fetchall()
    orders_list = []
    for o in orders:
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()
        od = dict(o)
        od["items"] = [dict(it) for it in items]
        orders_list.append(od)
    if sort_by == "amount_asc":
        orders_list = merge_sort_orders_by_amount(orders_list, ascending=True)
    elif sort_by == "amount_desc":
        orders_list = merge_sort_orders_by_amount(orders_list, ascending=False)
    conn.close()
    return jsonify({"success": True, "orders": orders_list})
@app.route("/api/biller/orders/update-status/<int:order_id>", methods=["POST"])
@biller_required
def update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get("order_status")
    payment_status = data.get("payment_status")
    valid_statuses = ['CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP', 'COLLECTED', 'CANCELLED']
    if new_status and new_status not in valid_statuses:
        return jsonify({"success": False, "error": f"Invalid order status '{new_status}'"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    order = cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({"success": False, "error": "Order not found"}), 404
    if new_status == "CANCELLED" and order["order_status"] != "CANCELLED":
        items = cur.execute("SELECT food_item_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        for itm in items:
            cur.execute("""
                UPDATE food_items
                SET stock_quantity = stock_quantity + ?,
                    is_available = 1
                WHERE id = ?
            """, (itm["quantity"], itm["food_item_id"]))
    update_fields = []
    params = []
    if new_status:
        update_fields.append("order_status = ?")
        params.append(new_status)
    if payment_status:
        update_fields.append("payment_status = ?")
        params.append(payment_status)
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(order_id)
    cur.execute(f"UPDATE orders SET {', '.join(update_fields)} WHERE id = ?", params)
    if new_status:
        notif_msg = {
            "PREPARING": f"Your order {order['bill_no']} is being freshly prepared in the kitchen!",
            "READY_FOR_PICKUP": f"DING! 🔔 Order {order['bill_no']} is READY! Show Token {order['token_no']} at the collection counter.",
            "COLLECTED": f"Order {order['bill_no']} has been picked up. Enjoy your meal!",
            "CANCELLED": f"Order {order['bill_no']} was cancelled by food court staff. Stock has been adjusted."
        }.get(new_status, f"Order status updated to {new_status}")
        cur.execute("""
            INSERT INTO notifications (user_id, order_id, title, message, type)
            VALUES (?, ?, ?, ?, ?)
        """, (order["user_id"], order_id, f"Order Update: {new_status.replace('_', ' ')}", notif_msg, "success" if new_status == "READY_FOR_PICKUP" else "info"))
    conn.commit()
    conn.close()
    sync_active_queue()
    return jsonify({"success": True, "message": f"Order #{order_id} updated successfully."})
@app.route("/api/biller/orders/verify-token", methods=["POST"])
@biller_required
def verify_token():
    data = request.get_json() or {}
    token = data.get("token", "").strip().upper()
    if not token:
        return jsonify({"success": False, "error": "Please enter a pickup token number."}), 400
    conn = get_db_connection()
    order = conn.execute("""
        SELECT o.*, u.name as student_name, u.phone as student_phone, u.student_id as student_reg_no
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE UPPER(o.token_no) = ? OR UPPER(o.bill_no) = ?
    """, (token, token)).fetchone()
    if not order:
        conn.close()
        return jsonify({"success": False, "error": f"No order found matching token/bill '{token}'"}), 404
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
    conn.close()
    od = dict(order)
    od["items"] = [dict(it) for it in items]
    return jsonify({"success": True, "order": od})
@app.route("/api/biller/analytics", methods=["GET"])
@biller_required
def get_analytics():
    conn = get_db_connection()
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    pending_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status IN ('CONFIRMED', 'PREPARING')").fetchone()[0]
    ready_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'READY_FOR_PICKUP'").fetchone()[0]
    completed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'COLLECTED'").fetchone()[0]
    cancelled_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'CANCELLED'").fetchone()[0]
    daily_sales = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE payment_status = 'PAID'").fetchone()[0]
    cash_pending = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE payment_method = 'CASH' AND payment_status = 'PENDING'").fetchone()[0]
    low_stock = conn.execute("SELECT * FROM food_items WHERE stock_quantity <= 10 OR is_available = 0 ORDER BY stock_quantity ASC").fetchall()
    conn.close()
    return jsonify({
        "success": True,
        "analytics": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "ready_orders": ready_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "daily_sales": round(daily_sales, 2),
            "cash_pending": round(cash_pending, 2),
            "low_stock_count": len(low_stock),
            "low_stock_items": [dict(r) for r in low_stock],
            "active_kitchen_queue_size": kitchen_queue.size
        }
    })
@app.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications():
    user_id = session["user_id"]
    conn = get_db_connection()
    notifs = conn.execute("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 20
    """, (user_id,)).fetchall()
    unread_count = conn.execute("""
        SELECT COUNT(*) FROM notifications
        WHERE user_id = ? AND is_read = 0
    """, (user_id,)).fetchone()[0]
    conn.close()
    return jsonify({
        "success": True,
        "notifications": [dict(n) for n in notifs],
        "unread_count": unread_count
    })
@app.route("/api/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    user_id = session["user_id"]
    conn = get_db_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
@app.route("/api/c-core/status", methods=["GET"])
def get_c_status():
    status = get_c_module_status()
    status["queue_live_count"] = kitchen_queue.size
    status["history_linked_list_count"] = history_linked_list.count
    return jsonify({"success": True, "c_core": status})
@app.route("/api/c-core/queue", methods=["GET"])
def get_c_queue():
    sync_active_queue()
    return jsonify({
        "success": True,
        "queue_size": kitchen_queue.size,
        "queue_orders": kitchen_queue.get_all(),
        "peek_next": kitchen_queue.peek().to_dict() if kitchen_queue.peek() else None
    })
@app.route("/api/user/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json() or {}
    old_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")
    if len(new_pw) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters long."}), 400
    conn = get_db_connection()
    user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not user or not check_password_hash(user["password_hash"], old_pw):
        conn.close()
        return jsonify({"success": False, "error": "Current password incorrect."}), 400
    new_hash = generate_password_hash(new_pw)
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, session["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Password changed successfully!"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
