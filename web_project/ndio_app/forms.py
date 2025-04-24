from django import forms
import uuid
from django.contrib.auth.models import User # User model
from django.contrib.auth.forms import UserCreationForm # Forms for user
from ndio_app.models import Order, UserDetail 

# ============== Forms for the users ===============
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    # Connects the fields of the model to the form
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserDetailForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    # Change the phine number back to normal inputs 
    phone_number = forms.CharField(max_length=10)
    id_number = forms.CharField(max_length=15)

    class Meta:
        model = UserDetail
        fields = ["first_name", "last_name", "phone_number", "id_number"]

class OrderForm(forms.ModelForm):
    ADDRESS_CHOICES = [
        ("House", "Free Standing House"),
        ("Apartment", "Apartment/Complex"),
        ("Estate", "Estate"),
    ]

    PROVINCE_CHOICES = [
        ("Eastern Cape", "Eastern Cape"),
        ("Free State", "Free State"),
        ("Gauteng", "Gauteng"),
        ("Kwazulu-Natal", "Kwazulu-Natal"),
        ("Mpumalanga", "Mpumalanga"),
        ("Northern Cape", "Northern Cape"),
        ("Limpopo", "Limpopo"),
        ("North West Province", "North West Province"),
        ("Western Cape", "Western Cape"),
        ("Other", "Other")
    ]

    address_type = forms.ChoiceField(choices=ADDRESS_CHOICES, widget=forms.Select(attrs={'id': 'id_address_type'}))
    province = forms.ChoiceField(choices=PROVINCE_CHOICES, widget=forms.Select())
    suburb = forms.CharField(max_length=50)
    apartment_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'apartment-field'}))
    apartment_floor = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'apartment-field'}))
    apartment_unit = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'apartment-field'}))
    estate_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'estate-field'}))
    estate_address = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'estate-field'}))
    address = forms.CharField(max_length=150)
    city = forms.CharField(max_length=20)
    postal_code = forms.CharField(max_length=10)

    class Meta:
        model = Order
        fields = [
            'address_type', 'province', 'suburb','address', 'apartment_name', 'apartment_floor', 
            'apartment_unit', 'estate_name', 'estate_address', 'city', 'postal_code'
        ]

class PaymentForm(forms.Form):
    # amount is read only
    amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'readonly': 'readonly'}))
    token = forms.CharField(widget=forms.HiddenInput())
    currency = forms.CharField(max_length=5, initial='ZAR', widget=forms.HiddenInput())
    name = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['token'].initial = str(uuid.uuid4())
