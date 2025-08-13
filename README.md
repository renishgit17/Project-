# Rexon Mold & Designing Co — Django E‑commerce Starter

A minimal, production-ready starter for an e‑commerce site built with **Python + Django**.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # create admin login

# Load demo data (optional)
python manage.py loaddata sample_data.json

python manage.py runserver
```

Open http://127.0.0.1:8000/ — you should see the storefront.
Admin lives at http://127.0.0.1:8000/admin/

## Features
- Product catalog with categories, search, and stock tracking
- Session-based cart (+ update/remove)
- Checkout flow that creates Orders & OrderItems
- Auth: signup/login, admin management
- Bootstrap UI out of the box
- India-friendly defaults (₹ currency display, Asia/Kolkata timezone)

## Next steps
- Integrate a real payment gateway (Razorpay, Stripe, PayU)
- Add product images via Media storage (S3, Cloudinary)
- Add shipping rates, coupons, invoices, etc.

## After update: Reviews + COD
Run migrations to add `Review` and the `payment_method` field on `Order`:

```
python manage.py makemigrations
python manage.py migrate
```
