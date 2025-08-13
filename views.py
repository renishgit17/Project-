from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Product, Category, Order, OrderItem
from .forms import SignUpForm, CheckoutForm, ReviewForm

def _cart(request):
    return request.session.setdefault("cart", {})

def _cart_totals(cart):
    total = Decimal("0.00")
    count = 0
    for p in cart.values():
        total += Decimal(str(p["price"])) * p["qty"]
        count += p["qty"]
    return total, count

def product_list(request, slug=None):
    products = Product.objects.filter(is_active=True).select_related("category")
    categories = Category.objects.all().order_by("name")
    q = request.GET.get("q")
    if slug:
        products = products.filter(category__slug=slug)
    if q:
        products = products.filter(name__icontains=q)
    context = {
        "products": products.order_by("name"),
        "categories": categories,
        "active_slug": slug,
        "q": q or "",
    }
    return render(request, "shop/product_list.html", context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.select_related("user").all()
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "Please login to submit a review.")
            return redirect("/accounts/login/?next=" + request.path)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            try:
                review.save()
                messages.success(request, "Your review has been posted.")
            except Exception as e:
                messages.warning(request, "You have already reviewed this product.")
            return redirect("shop:product_detail", slug=slug)
    else:
        form = ReviewForm()
    return render(request, "shop/product_detail.html", {"product": product, "reviews": reviews, "form": form})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = _cart(request)
    item = cart.get(str(product.id), { "name": product.name, "price": float(product.price), "qty": 0 })
    if product.stock <= item["qty"]:
        messages.warning(request, "No more stock available for this item.")
    else:
        item["qty"] += 1
        cart[str(product.id)] = item
        request.session.modified = True
        messages.success(request, f"Added {product.name} to cart.")
    return redirect("shop:cart_view")

def update_cart(request, product_id):
    cart = _cart(request)
    qty = int(request.POST.get("qty", 1))
    key = str(product_id)
    if key in cart:
        if qty <= 0:
            cart.pop(key)
        else:
            cart[key]["qty"] = qty
        request.session.modified = True
    return redirect("shop:cart_view")

def remove_from_cart(request, product_id):
    cart = _cart(request)
    cart.pop(str(product_id), None)
    request.session.modified = True
    return redirect("shop:cart_view")

def cart_view(request):
    cart = _cart(request)
    items = []
    for pid, data in cart.items():
        try:
            product = Product.objects.get(pk=pid)
        except Product.DoesNotExist:
            continue
        items.append({
            "product": product,
            "qty": data["qty"],
            "price": Decimal(str(data["price"])),
            "line_total": Decimal(str(data["price"])) * data["qty"]
        })
    total, count = _cart_totals(cart)
    return render(request, "shop/cart.html", {"items": items, "total": total, "count": count})

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            login(request, user)
            messages.success(request, "Welcome to Rexon Mold & Designing Co!")
            return redirect("shop:product_list")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})

def checkout(request):
    cart = _cart(request)
    total, count = _cart_totals(cart)
    if count == 0:
        messages.info(request, "Your cart is empty.")
        return redirect("shop:product_list")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.create(
                user=request.user if request.user.is_authenticated else None,
                email=form.cleaned_data["email"],
                full_name=form.cleaned_data["full_name"],
                address=form.cleaned_data["address"],
                city=form.cleaned_data["city"],
                state=form.cleaned_data["state"],
                postal_code=form.cleaned_data["postal_code"],
                country=form.cleaned_data["country"],
                total=total,
                paid=False,  # COD = unpaid at checkout
                payment_reference="COD",
                payment_method="Cash on Delivery",
            )
            # create order items and reduce stock
            for pid, data in cart.items():
                try:
                    product = Product.objects.get(pk=pid)
                except Product.DoesNotExist:
                    continue
                qty = min(data["qty"], product.stock)
                OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)
                product.stock = max(0, product.stock - qty)
                product.save()
            request.session["cart"] = {}
            request.session.modified = True
            return redirect("shop:order_success", order_id=order.id)
    else:
        form = CheckoutForm(initial={
            "email": getattr(request.user, "email", ""),
            "full_name": getattr(request.user, "get_full_name", lambda: "")(),
        })
    return render(request, "shop/checkout.html", {"form": form, "total": total})

def order_success(request, order_id):
    from .models import Order
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "shop/order_success.html", {"order": order})
