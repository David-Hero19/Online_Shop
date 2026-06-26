import os
import json
import hmac
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-prod")

STRIPE_SECRET_KEY      = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_test_YOUR_KEY_HERE")
STRIPE_WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

STRIPE_API = "https://api.stripe.com/v1"

# ──────────────────────────────────────────────
# Stripe helpers (stdlib only — no stripe pkg)
# ──────────────────────────────────────────────

def stripe_post(path, params):
    """POST to Stripe API using basic auth (secret key)."""
    data = urllib.parse.urlencode(params, doseq=True).encode()
    req = urllib.request.Request(
        STRIPE_API + path,
        data=data,
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {STRIPE_SECRET_KEY}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        return None, body.get("error", {}).get("message", "Stripe error")

# ──────────────────────────────────────────────
# Sample product catalog
# ──────────────────────────────────────────────

PRODUCTS = [
    {"id": "1",  "name": "Wireless Headphones",   "price": 7900,  "category": "Electronics", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80", "badge": "Best Seller", "description": "Premium sound with 30-hour battery and active noise cancellation."},
    {"id": "2",  "name": "Leather Crossbody Bag", "price": 5400,  "category": "Fashion",     "image": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400&q=80", "badge": "New",         "description": "Genuine leather with adjustable strap and gold-tone hardware."},
    {"id": "3",  "name": "Running Shoes",          "price": 8900,  "category": "Sports",      "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80", "badge": "",            "description": "Lightweight mesh upper with responsive foam sole."},
    {"id": "4",  "name": "Smart Watch",            "price": 19900, "category": "Electronics", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80", "badge": "Hot",        "description": "Fitness tracking, heart rate monitor, and 7-day battery."},
    {"id": "5", "name": "Powerbank 20000mAh", "price": 3500, "category": "Electronics", "image": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=400&q=80", "badge": "New", "description": "20000mAh capacity, dual USB-A and USB-C output, LED battery indicator."},    {"id": "6",  "name": "Yoga Mat",               "price": 3900,  "category": "Sports",      "image": "https://images.unsplash.com/photo-1575052814086-f385e2e2ad1b?w=400&q=80", "badge": "Sale",       "description": "Non-slip 6mm mat with alignment lines and carry strap."},
    {"id": "7",  "name": "Desk Lamp",              "price": 4500,  "category": "Home",        "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&q=80", "badge": "",            "description": "LED with 3 colour temperatures and USB charging port."},
    {"id": "8",  "name": "Sunglasses",             "price": 3200,  "category": "Fashion",     "image": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&q=80", "badge": "New",        "description": "Polarised UV400 lenses, lightweight titanium frame."},
    {"id": "9", "name": "Mechanical Keyboard", "price": 12900, "category": "Electronics", "image": "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=400&q=80", "badge": "", "description": "TKL layout, tactile switches, per-key RGB backlight."},
    {"id": "10", 'name': 'Ceramic Pour-Over Set',  'price': 4800,  'category': 'Home',        'image': 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&q=80', 'badge': 'New',        'description': 'Hand-thrown ceramic dripper, server, and two mugs.'},
    {"id": "11", "name": "Resistance Bands Set",   "price": 2200,  "category": "Sports",      "image": "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=400&q=80", "badge": "",            "description": "5 resistance levels, latex-free, includes carry bag."},
    {"id": "12", "name": "Minimalist Wallet",      "price": 2800,  "category": "Fashion",     "image": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=400&q=80", "badge": "",            "description": "Full-grain leather, holds 8 cards, RFID blocking."},
]

def get_cart():
    return session.get("cart", {})

def cart_total(cart):
    total = 0
    for pid, qty in cart.items():
        p = next((p for p in PRODUCTS if p["id"] == pid), None)
        if p:
            total += p["price"] * qty
    return total

def cart_count(cart):
    return sum(cart.values())

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    category = request.args.get("category", "All")
    search   = request.args.get("q", "").lower()
    products = PRODUCTS
    if category and category != "All":
        products = [p for p in products if p["category"] == category]
    if search:
        products = [p for p in products if search in p["name"].lower() or search in p["description"].lower()]
    categories = ["All"] + sorted(set(p["category"] for p in PRODUCTS))
    cart = get_cart()
    return render_template("index.html",
                           products=products,
                           categories=categories,
                           active_category=category,
                           search=search,
                           cart_count=cart_count(cart),
                           stripe_key=STRIPE_PUBLISHABLE_KEY)

@app.route("/cart")
def cart_page():
    cart = get_cart()
    items = []
    for pid, qty in cart.items():
        p = next((p for p in PRODUCTS if p["id"] == pid), None)
        if p:
            items.append({**p, "qty": qty, "subtotal": p["price"] * qty})
    return render_template("cart.html",
                           items=items,
                           total=cart_total(cart),
                           cart_count=cart_count(cart),
                           stripe_key=STRIPE_PUBLISHABLE_KEY)

@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    pid  = str(data.get("product_id"))
    qty  = int(data.get("quantity", 1))
    cart = get_cart()
    cart[pid] = cart.get(pid, 0) + qty
    session["cart"] = cart
    return jsonify({"success": True, "cart_count": cart_count(cart)})

@app.route("/api/cart/update", methods=["POST"])
def update_cart():
    data = request.get_json()
    pid  = str(data.get("product_id"))
    qty  = int(data.get("quantity", 0))
    cart = get_cart()
    if qty <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = qty
    session["cart"] = cart
    items = []
    for p_id, p_qty in cart.items():
        p = next((p for p in PRODUCTS if p["id"] == p_id), None)
        if p:
            items.append({"id": p_id, "subtotal": p["price"] * p_qty})
    return jsonify({"success": True, "cart_count": cart_count(cart), "total": cart_total(cart), "items": items})

@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    data = request.get_json()
    pid  = str(data.get("product_id"))
    cart = get_cart()
    cart.pop(pid, None)
    session["cart"] = cart
    return jsonify({"success": True, "cart_count": cart_count(cart), "total": cart_total(cart)})

# ──────────────────────────────────────────────
# Stripe Checkout Session
# ──────────────────────────────────────────────

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    cart = get_cart()
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400
    if not STRIPE_SECRET_KEY:
        return jsonify({"error": "STRIPE_SECRET_KEY is not set. See README for setup."}), 400

    # Build flat params for Stripe's form-encoded API
    params = {
        "payment_method_types[0]": "card",
        "mode": "payment",
        "success_url": request.host_url + "success?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": request.host_url + "cart",
    }
    idx = 0
    for pid, qty in cart.items():
        p = next((p for p in PRODUCTS if p["id"] == pid), None)
        if p:
            params[f"line_items[{idx}][price_data][currency]"] = "usd"
            params[f"line_items[{idx}][price_data][product_data][name]"] = p["name"]
            params[f"line_items[{idx}][price_data][product_data][images][0]"] = p["image"]
            params[f"line_items[{idx}][price_data][unit_amount]"] = str(p["price"])
            params[f"line_items[{idx}][quantity]"] = str(qty)
            idx += 1

    data, err = stripe_post("/checkout/sessions", params)
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"id": data["id"]})

@app.route("/success")
def success():
    session_id = request.args.get("session_id", "")
    session["cart"] = {}
    return render_template("success.html", session_id=session_id)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload    = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    if STRIPE_WEBHOOK_SECRET:
        # Verify signature
        try:
            parts = {k: v for part in sig_header.split(",") for k, v in [part.split("=", 1)]}
            ts    = parts.get("t", "")
            sig   = parts.get("v1", "")
            mac   = hmac.new(STRIPE_WEBHOOK_SECRET.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(mac, sig):
                return jsonify({"error": "Invalid signature"}), 400
        except Exception:
            return jsonify({"error": "Webhook verification failed"}), 400
    event = json.loads(payload)
    if event.get("type") == "checkout.session.completed":
        print(f"[webhook] Payment confirmed: {event['data']['object'].get('id')}")
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
