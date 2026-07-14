from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CustomerForm,
    FoodForm,
    OrderForCustomerForm,
    OrderForm,
    OrderItemForm,
    RegisterForm,
)
from .models import Customer, Food, Order, OrderItem


def home(request):
    return render(request, "webkiosk/home.html")


def user_customer(request):
    customers = Customer.objects.filter(user=request.user)
    if customers:
        return customers[0]
    return None


def can_use_customer(request, customer):
    if request.user.is_staff:
        return True
    if request.user.is_authenticated and customer.user == request.user:
        return True
    return False


def can_use_order(request, order):
    return can_use_customer(request, order.customer)


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            customer = Customer.objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                user=user,
            )
            login(request, user)
            return redirect("webkiosk:customer_detail", pk=customer.id)
    else:
        form = RegisterForm()
    return render(request, "webkiosk/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            customer = user_customer(request)
            if customer:
                return redirect("webkiosk:customer_detail", pk=customer.id)
            return redirect("webkiosk:home")
    else:
        form = AuthenticationForm()
    return render(request, "webkiosk/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("webkiosk:home")


def customer_list(request):
    if not request.user.is_authenticated:
        return redirect("webkiosk:login")
    if request.user.is_staff:
        customers = Customer.objects.all()
    else:
        customers = Customer.objects.filter(user=request.user)
    return render(request, "webkiosk/customer_list.html", {"customers": customers})


def customer_detail(request, pk):
    customer = get_object_or_404(Customer, id=pk)
    if not can_use_customer(request, customer):
        return HttpResponseForbidden("You can only view your own records.")
    orders = customer.order_set.all()
    return render(
        request,
        "webkiosk/customer_detail.html",
        {"customer": customer, "orders": orders},
    )


def customer_add(request):
    if not request.user.is_authenticated:
        return redirect("webkiosk:login")
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            if not request.user.is_staff:
                customer.user = request.user
                customer.save()
            return redirect("webkiosk:customer_detail", pk=customer.id)
    else:
        form = CustomerForm()
    return render(request, "webkiosk/form.html", {"form": form, "title": "Add Customer"})


def customer_edit(request, pk):
    customer = get_object_or_404(Customer, id=pk)
    if not can_use_customer(request, customer):
        return HttpResponseForbidden("You can only edit your own records.")
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("webkiosk:customer_detail", pk=customer.id)
    else:
        form = CustomerForm(instance=customer)
    return render(request, "webkiosk/form.html", {"form": form, "title": "Edit Customer"})


def customer_delete(request, pk):
    customer = get_object_or_404(Customer, id=pk)
    if not can_use_customer(request, customer):
        return HttpResponseForbidden("You can only delete your own records.")
    if request.method == "POST":
        customer.delete()
        return redirect("webkiosk:customer_list")
    return render(
        request,
        "webkiosk/confirm_delete.html",
        {"object": customer, "title": "Delete Customer"},
    )


def food_list(request):
    foods = Food.objects.all()
    return render(request, "webkiosk/food_list.html", {"foods": foods})


def food_detail(request, pk):
    food = get_object_or_404(Food, id=pk)
    return render(request, "webkiosk/food_detail.html", {"food": food})


def food_add(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff can manage food records.")
    if request.method == "POST":
        form = FoodForm(request.POST)
        if form.is_valid():
            food = form.save()
            return redirect("webkiosk:food_detail", pk=food.id)
    else:
        form = FoodForm()
    return render(request, "webkiosk/form.html", {"form": form, "title": "Add Food"})


def food_edit(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff can manage food records.")
    food = get_object_or_404(Food, id=pk)
    if request.method == "POST":
        form = FoodForm(request.POST, instance=food)
        if form.is_valid():
            form.save()
            return redirect("webkiosk:food_detail", pk=food.id)
    else:
        form = FoodForm(instance=food)
    return render(request, "webkiosk/form.html", {"form": form, "title": "Edit Food"})


def food_delete(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff can manage food records.")
    food = get_object_or_404(Food, id=pk)
    if request.method == "POST":
        food.delete()
        return redirect("webkiosk:food_list")
    return render(
        request,
        "webkiosk/confirm_delete.html",
        {"object": food, "title": "Delete Food"},
    )


def order_list(request):
    if not request.user.is_authenticated:
        return redirect("webkiosk:login")
    if request.user.is_staff:
        orders = Order.objects.all()
    else:
        customer = user_customer(request)
        if customer:
            orders = Order.objects.filter(customer=customer)
        else:
            orders = Order.objects.none()
    return render(request, "webkiosk/order_list.html", {"orders": orders})


def order_detail(request, pk):
    order = get_object_or_404(Order, id=pk)
    if not can_use_order(request, order):
        return HttpResponseForbidden("You can only view your own orders.")
    items = order.orderitem_set.all()
    total = 0
    item_rows = []
    for item in items:
        subtotal = item.subtotal()
        total = total + subtotal
        item_rows.append({"item": item, "subtotal": subtotal})
    return render(
        request,
        "webkiosk/order_detail.html",
        {"order": order, "item_rows": item_rows, "total": total},
    )


def order_add(request):
    if not request.user.is_authenticated:
        return redirect("webkiosk:login")
    if not request.user.is_staff:
        customer = user_customer(request)
        if not customer:
            return HttpResponseForbidden("No customer record found.")
        return redirect("webkiosk:order_add_for_customer", customer_id=customer.id)
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            return redirect("webkiosk:order_detail", pk=order.id)
    else:
        form = OrderForm()
    return render(request, "webkiosk/form.html", {"form": form, "title": "Add Order"})


def order_add_for_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if not can_use_customer(request, customer):
        return HttpResponseForbidden("You can only add your own orders.")
    if request.method == "POST":
        form = OrderForCustomerForm(request.POST)
        if form.is_valid():
            order = form.save()
            return redirect("webkiosk:order_detail", pk=order.id)
    else:
        form = OrderForCustomerForm(initial={"customer": customer})
    return render(
        request,
        "webkiosk/form.html",
        {"form": form, "title": "Add Order for " + str(customer)},
    )


def order_edit(request, pk):
    order = get_object_or_404(Order, id=pk)
    if not can_use_order(request, order):
        return HttpResponseForbidden("You can only edit your own orders.")
    if request.user.is_staff:
        form_class = OrderForm
    else:
        form_class = OrderForCustomerForm
    if request.method == "POST":
        form = form_class(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect("webkiosk:order_detail", pk=order.id)
    else:
        form = form_class(instance=order)
    return render(request, "webkiosk/form.html", {"form": form, "title": "Edit Order"})


def order_delete(request, pk):
    order = get_object_or_404(Order, id=pk)
    if not can_use_order(request, order):
        return HttpResponseForbidden("You can only delete your own orders.")
    if request.method == "POST":
        order.delete()
        return redirect("webkiosk:order_list")
    return render(
        request,
        "webkiosk/confirm_delete.html",
        {"object": order, "title": "Delete Order"},
    )


def orderitem_add(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not can_use_order(request, order):
        return HttpResponseForbidden("You can only edit your own orders.")
    if request.method == "POST":
        form = OrderItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("webkiosk:order_detail", pk=order.id)
    else:
        form = OrderItemForm(initial={"order": order})
    return render(request, "webkiosk/form.html", {"form": form, "title": "Add Order Item"})


def orderitem_edit(request, pk):
    item = get_object_or_404(OrderItem, id=pk)
    if not can_use_order(request, item.order):
        return HttpResponseForbidden("You can only edit your own orders.")
    if request.method == "POST":
        form = OrderItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("webkiosk:order_detail", pk=item.order.id)
    else:
        form = OrderItemForm(instance=item)
    return render(
        request,
        "webkiosk/form.html",
        {"form": form, "title": "Edit Order Item"},
    )


def orderitem_delete(request, pk):
    item = get_object_or_404(OrderItem, id=pk)
    order_id = item.order.id
    if not can_use_order(request, item.order):
        return HttpResponseForbidden("You can only edit your own orders.")
    if request.method == "POST":
        item.delete()
        return redirect("webkiosk:order_detail", pk=order_id)
    return render(
        request,
        "webkiosk/confirm_delete.html",
        {"object": item, "title": "Delete Order Item"},
    )
