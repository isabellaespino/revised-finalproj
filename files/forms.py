from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Customer, Food, Order, OrderItem


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["first_name", "last_name"]


class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = ["name", "description", "price"]


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["orderdatetime", "paymentmode", "customer"]


class OrderForCustomerForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["orderdatetime", "paymentmode", "customer"]
        widgets = {"customer": forms.HiddenInput()}


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["order", "food", "quantity"]
        widgets = {"order": forms.HiddenInput()}


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "password1", "password2"]
