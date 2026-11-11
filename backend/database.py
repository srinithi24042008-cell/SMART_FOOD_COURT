import sqlite3
import os
import time
from werkzeug.security import generate_password_hash

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "food_court.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'biller')),
        phone TEXT,
        student_id TEXT,
        user_type TEXT DEFAULT 'student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        icon TEXT,
        display_order INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        image_url TEXT,
        is_veg INTEGER NOT NULL DEFAULT 1,
        stock_quantity INTEGER NOT NULL DEFAULT 50,
        prep_time_mins INTEGER NOT NULL DEFAULT 10,
        is_available INTEGER NOT NULL DEFAULT 1,
        is_featured INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no TEXT UNIQUE NOT NULL,
        token_no TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        subtotal REAL NOT NULL,
        tax_amount REAL DEFAULT 0,
        payment_method TEXT NOT NULL CHECK(payment_method IN ('UPI', 'CASH')),
        payment_status TEXT NOT NULL CHECK(payment_status IN ('PAID', 'PENDING', 'FAILED', 'REFUNDED')),
        order_status TEXT NOT NULL CHECK(order_status IN ('CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP', 'COLLECTED', 'CANCELLED')),
        special_instructions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        food_item_id INTEGER NOT NULL,
        food_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
        FOREIGN KEY (food_item_id) REFERENCES food_items (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_id INTEGER,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (order_id) REFERENCES orders (id)
    )
    """)

    default_categories = [
        ("South Indian", "bi-egg-fried", 1),
        ("North Indian", "bi-fire", 2),
        ("Snacks & Chaat", "bi-cup-hot", 3),
        ("Beverages & Juices", "bi-cup-straw", 4),
        ("Combos & Thali", "bi-collection", 5),
        ("Desserts", "bi-heart", 6)
    ]
    for cat in default_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name, icon, display_order) VALUES (?, ?, ?)", cat)

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_user_pw = generate_password_hash("campus123")
        demo_biller_pw = generate_password_hash("biller123")

        cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, phone, student_id, user_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Aarav Sharma", "user@campus.edu", demo_user_pw, "student", "9876543210", "CAMPUS-2024-001", "student_teacher"))

        cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, phone, student_id, user_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Chief Biller / Cashier", "biller@campus.edu", demo_biller_pw, "biller", "9876543211", "STAFF-FC-01", "biller"))

    cursor.execute("SELECT COUNT(*) FROM food_items")
    item_count = cursor.fetchone()[0]
    if item_count < 24:
        cursor.execute("DELETE FROM food_items")
        sample_foods = [
            ("Masala Dosa", "Crispy golden fermented crepe stuffed with spiced potato mash, served with coconut chutney & piping hot sambar.", 75.0, "South Indian", "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2e/Masala_Dosa_in_Banana_Leaf_with_Chutney.jpg/960px-Masala_Dosa_in_Banana_Leaf_with_Chutney.jpg", 1, 40, 8, 1, 1),
            ("Ghee Podi Dosa", "Crisp golden crepe generously smeared with aromatic spicy gun powder (podi) and pure desi ghee.", 90.0, "South Indian", "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80", 1, 35, 9, 1, 1),
            ("Idli Vada Combo", "Two steamed fluffy rice idlis and one crispy medu vada with fresh green mint and coconut chutneys.", 60.0, "South Indian", "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/51/Ondu_Plate_Idli_Vada.jpg/960px-Ondu_Plate_Idli_Vada.jpg", 1, 45, 5, 1, 1),
            ("Onion Uttapam", "Thick savory rice-lentil pancake topped with diced onions, green chillies, curry leaves & cilantro.", 70.0, "South Indian", "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d7/Onion_Uthappam.jpg/960px-Onion_Uthappam.jpg", 1, 30, 8, 1, 0),
            
            ("Paneer Butter Masala Combo", "Rich cottage cheese cubes simmered in a velvet tomato cashew gravy, served with 2 butter naans & jeera rice.", 150.0, "North Indian", "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80", 1, 30, 12, 1, 1),
            ("Chole Bhature", "Two puffed deep-fried golden bhatures served with spicy Punjabi chickpea masala, sliced onions & tangy pickle.", 95.0, "North Indian", "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f0/Chole_Bhature_3.jpg/960px-Chole_Bhature_3.jpg", 1, 35, 10, 1, 1),
            ("Butter Chicken Meal Box", "Succulent chicken chunks bathed in aromatic butter-makhani gravy, with 2 garlic naans and salad.", 175.0, "North Indian", "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80", 0, 25, 14, 1, 1),
            ("Dal Makhani with Jeera Rice", "Overnight slow-cooked black lentils with fresh cream and butter, served with fragrant cumin basmati rice.", 110.0, "North Indian", "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80", 1, 40, 7, 1, 0),

            ("Veg Dum Biryani", "Fragrant basmati rice layered with garden fresh vegetables, saffron, aromatic whole spices, served with cooling raita.", 120.0, "Combos & Thali", "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/af/Veg_Biryani_-_Mohali_2016-08-07_9120.JPG/960px-Veg_Biryani_-_Mohali_2016-08-07_9120.JPG", 1, 28, 10, 1, 1),
            ("Chicken Biryani (Campus Special)", "Tender juicy chicken slow-cooked with spiced long-grain basmati rice, hard-boiled egg, and mint raita.", 160.0, "Combos & Thali", "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/35/Biryani_Home.jpg/960px-Biryani_Home.jpg", 0, 25, 12, 1, 1),
            ("Executive Campus Mini Thali", "Complete balanced lunch box: Paneer curry, Dal fry, 2 chapatis, Jeera rice, Curd, and Sweet pickle.", 130.0, "Combos & Thali", "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?w=600&auto=format&fit=crop&q=80", 1, 30, 8, 1, 1),
            ("Egg Fried Rice & Chilli Chicken Combo", "Wok-tossed Indo-Chinese egg fried rice paired with crispy glazed chilli chicken cubes.", 155.0, "Combos & Thali", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=600&auto=format&fit=crop&q=80", 0, 22, 11, 1, 0),

            ("Grilled Veg Cheese Sandwich", "Three-tier toasted multigrain bread loaded with cucumber, tomato, capsicum, mint chutney & melted mozzarella.", 70.0, "Snacks & Chaat", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=600&auto=format&fit=crop&q=80", 1, 40, 7, 1, 0),
            ("Crispy Samosa Plate (2 pcs)", "Flaky crust stuffed with spicy seasoned potatoes and green peas, drizzled with tamarind & mint sauces.", 40.0, "Snacks & Chaat", "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80", 1, 50, 4, 1, 0),
            ("Crispy French Fries (Peri Peri)", "Golden crispy potato batons tossed in fiery peri-peri seasoning, served with creamy mayonnaise.", 60.0, "Snacks & Chaat", "https://images.unsplash.com/photo-1576107232684-1279f3908594?w=600&auto=format&fit=crop&q=80", 1, 45, 6, 1, 1),
            ("Pani Puri / Golgappa Platter (8 pcs)", "Crispy hollow puris filled with spiced potato-chickpea mix and dipped in mint-coriander spiced water.", 45.0, "Snacks & Chaat", "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=600&auto=format&fit=crop&q=80", 1, 35, 3, 1, 1),
            ("Chicken Roll / Franky", "Flaky layered paratha rolled with tandoori grilled chicken shreds, sliced onions, and garlic pepper sauce.", 85.0, "Snacks & Chaat", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=600&auto=format&fit=crop&q=80", 0, 30, 7, 1, 1),
            ("Pav Bhaji (Extra Butter)", "Spiced mashed vegetable curry garnished with butter, chopped cilantro, served with two soft butter-toasted pavs.", 80.0, "Snacks & Chaat", "https://upload.wikimedia.org/wikipedia/commons/6/63/Pav_Bhaji.jpg", 1, 30, 6, 1, 0),

            ("Filter Coffee (South Indian)", "Authentic brass tumbler frothy chicory-blended filter coffee brewed fresh to order.", 30.0, "Beverages & Juices", "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop&q=80", 1, 60, 3, 1, 1),
            ("Fresh Mango Lassi", "Thick churned creamy yogurt blended with Alphonso mango pulp and garnished with crushed pistachios.", 55.0, "Beverages & Juices", "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=600&auto=format&fit=crop&q=80", 1, 35, 4, 1, 0),
            ("Cold Coffee with Ice Cream", "Rich blended iced espresso shake crowned with a generous scoop of vanilla ice cream & chocolate drizzle.", 65.0, "Beverages & Juices", "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=600&auto=format&fit=crop&q=80", 1, 35, 5, 1, 1),
            ("Fresh Mint Lemonade / Mojito", "Chilled sparkling lemonade infused with crushed garden mint leaves, black salt, and roasted cumin.", 40.0, "Beverages & Juices", "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80", 1, 50, 3, 1, 0),
            ("Masala Chai (Kullad Special)", "Strong boiled tea steeped with crushed ginger, green cardamom, cloves, served in traditional clay kullad.", 25.0, "Beverages & Juices", "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80", 1, 70, 3, 1, 1),

            ("Gulab Jamun (2 pcs)", "Warm melt-in-mouth milk-solid dumplings soaked in rose and cardamom-infused sugar syrup.", 45.0, "Desserts", "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c4/Gulab_jamun_%28Gibraltar%2C_November_2020%29.jpg/960px-Gulab_jamun_%28Gibraltar%2C_November_2020%29.jpg", 1, 35, 2, 1, 0),
            ("Sizzling Chocolate Brownie", "Warm fudgy walnut brownie topped with a scoop of vanilla ice cream and hot molten chocolate fudge.", 85.0, "Desserts", "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop&q=80", 1, 25, 4, 1, 1),
            ("Rasmalai (2 pcs)", "Soft flattened cottage cheese dumplings soaked in chilled saffron cardamom flavored thickened milk.", 60.0, "Desserts", "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/df/Ras_Malai.JPG/960px-Ras_Malai.JPG", 1, 20, 2, 1, 1)
        ]

        cursor.executemany("""
        INSERT INTO food_items (name, description, price, category, image_url, is_veg, stock_quantity, prep_time_mins, is_available, is_featured)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_foods)

    legacy_image_updates = [
        ("Masala Dosa", "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2e/Masala_Dosa_in_Banana_Leaf_with_Chutney.jpg/960px-Masala_Dosa_in_Banana_Leaf_with_Chutney.jpg"),
        ("Idli Vada Combo", "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/51/Ondu_Plate_Idli_Vada.jpg/960px-Ondu_Plate_Idli_Vada.jpg"),
        ("Onion Uttapam", "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d7/Onion_Uthappam.jpg/960px-Onion_Uthappam.jpg"),
        ("Chole Bhature", "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f0/Chole_Bhature_3.jpg/960px-Chole_Bhature_3.jpg"),
        ("Veg Dum Biryani", "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/af/Veg_Biryani_-_Mohali_2016-08-07_9120.JPG/960px-Veg_Biryani_-_Mohali_2016-08-07_9120.JPG"),
        ("Chicken Biryani (Campus Special)", "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/35/Biryani_Home.jpg/960px-Biryani_Home.jpg"),
        ("Chicken Roll / Franky", "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=600&auto=format&fit=crop&q=80"),
        ("Pav Bhaji (Extra Butter)", "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=600&auto=format&fit=crop&q=80", "https://upload.wikimedia.org/wikipedia/commons/6/63/Pav_Bhaji.jpg"),
        ("Gulab Jamun (2 pcs)", "https://images.unsplash.com/photo-1589119908995-c6837fa14d48?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c4/Gulab_jamun_%28Gibraltar%2C_November_2020%29.jpg/960px-Gulab_jamun_%28Gibraltar%2C_November_2020%29.jpg"),
        ("Rasmalai (2 pcs)", "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80", "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/df/Ras_Malai.JPG/960px-Ras_Malai.JPG")
    ]
    cursor.executemany(
        "UPDATE food_items SET image_url = ? WHERE name = ? AND image_url = ?",
        [(new_url, name, old_url) for name, old_url, new_url in legacy_image_updates]
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
