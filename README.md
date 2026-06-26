# Nexus Store — Python eCommerce + Stripe

A full-featured eCommerce web app built with Flask and Stripe Checkout.

## Features

- Product catalog with category filtering & search
- Shopping cart (session-based, no database required to start)
- Stripe Checkout integration for secure payments
- Stripe Webhook support for payment confirmation
- Fully responsive design

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Stripe API keys

Get your keys from https://dashboard.stripe.com/test/apikeys

```bash
# Linux / macOS
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLISHABLE_KEY="pk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."   # optional, for webhooks
export FLASK_SECRET_KEY="your-random-secret"

# Windows (PowerShell)
$env:STRIPE_SECRET_KEY="sk_test_..."
$env:STRIPE_PUBLISHABLE_KEY="pk_test_..."
```

### 3. Run the app

```bash
python app.py
```

Visit http://localhost:5000

## Testing Payments

Use Stripe's test card: `4242 4242 4242 4242`  
Any future expiry, any 3-digit CVC.

## Project Structure

```
shop/
├── app.py                  # Flask app + routes + Stripe logic
├── requirements.txt
├── static/
│   ├── css/style.css       # All styles
│   └── js/main.js          # Cart JS
└── templates/
    ├── base.html           # Shared nav + layout
    ├── index.html          # Shop / product listing
    ├── cart.html           # Cart + Stripe checkout button
    └── success.html        # Post-payment confirmation
```

## Adding Real Products

Edit the `PRODUCTS` list in `app.py`. Each product has:
- `id`, `name`, `price` (in cents), `category`, `image` (URL)
- `badge` (optional: "New", "Hot", "Sale", "Best Seller")
- `description`

For a production app, replace this list with a database (SQLite, PostgreSQL, etc.).

## Webhook Setup (Production)

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Run: `stripe listen --forward-to localhost:5000/webhook`
3. Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET`
