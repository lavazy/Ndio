from decimal import Decimal
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from ndio_app.models import Payment, UserDetail, User, FibreProduct, NetworkProvider, FAQ, ServicesContact
from .forms import CustomUserCreationForm, PaymentForm, UserDetailForm, OrderForm
from . import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import requests


# Create your views here.
def get_session():
    """ This function creates an API session, allowing
        us to interact with the API for 1 hour. And
        we can request another one after 1 hour. """

    url = "https://apitest.axxess.co.za/calls/rsapi/getSession.json?strUserName=KAB149&strPassword=cW3j*-NUmKG~$5!"
    username = "ResellerAdmin"
    password = "jFbd5lg7Djfbn48idmlf4Kd"
    # Authenticating before we can access the sessionID
    response = requests.get(url, auth=(username, password))

    # Getting the session ID
    if response.status_code == 200:
        session_id = response.json().get("strSessionId")
        return session_id
    else:
        print("Something went wrong. Try again")
        return None

def get_coordinates(address):
    
    """Converts a user's address into latitude and longitude using the Google Maps API."""
    
    # Dont forget to hide this
    google_maps_api_key = "AIzaSyDvsvOuUIWak9axNX97yBDoa0oKm_f1suY"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_maps_api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        location = response.json()["results"][0]["geometry"]["location"]
        return (location["lat"], location["lng"])
    else:
        print("Failed to get coordinates.")
        return None, None

# Check if fibre is available in that area
def check_fibre_availability(address):
    """This function checks if fibre is available in the user's address.
        It accepts 1 parameters: 
        - address of the user (str)

        And it returns a list of available network providers for that area"""

    providers_list = []    # Initialize list of prviders
    session_id = get_session()
    latitude_coordinate, longitude_coordinate = get_coordinates(address=address)
    url = f"https://apitest.axxess.co.za/calls/rsapi/checkFibreAvailability.json?"

    params = {
        "strSessionId": session_id,
        "strLatitude": str(latitude_coordinate),
        "strLongitude": str(longitude_coordinate),
        "strAddress": address
    }

    # Authentication for api
    username = "ResellerAdmin"
    password = "jFbd5lg7Djfbn48idmlf4Kd"
    response = requests.get(url, auth=(username, password), params=params)

    # Check if the request was successful
    if response.status_code == 200:
        network_providers = response.json()#["arrAvailableProvidersGuids"]
        
        # Loop through list of 
        for providers in network_providers["arrAvailableProvidersGuids"]:
            provider_id = (f"{providers['guidNetworkProviderId']}")
            providers_list.append(provider_id)
        return providers_list
    else:
        return None

# Get the network provider products
def get_network_provider_products(address):
    network_providers_list = check_fibre_availability(address=address)
    products_list = []  # Initialize empty list of responses
 
    # Authentication
    username = "ResellerAdmin"
    password = "jFbd5lg7Djfbn48idmlf4Kd"

    # Loop through list if network provider IDs
    # Get the products of each network provider
    if network_providers_list is not None:
        for items in network_providers_list:
            session_id = get_session()
            response = requests.get(f"https://apitest.axxess.co.za/calls/rsapi/getNetworkProviderProducts.json?strSessionId={session_id}&guidNetworkProviderId={items}", auth=(username, password))
            response = response.json()
            for products in response["arrNetworkProviderProducts"]:
                print(products)
                products_list.append(products)       
        return products_list
    else:
        return None
    
def home(request):
    request.session.flush()
    context={}
    network_provider_products_list = []
    if request.method == "POST":
        fibre_is_available = False
        address = request.POST.get("address")
        network_providers_list = check_fibre_availability(address=address)

        # Create request session for address
        request.session["address"] = address
        print(address)

        # Check if network providers list is appended
        if network_providers_list is not None:
            fibre_is_available = True
            network_provider_products_list = get_network_provider_products(address=address)
        else:
            fibre_is_available = False
            network_providers_list = []
            
        context = {
            "products" : network_provider_products_list,
            "fibre_is_available": fibre_is_available,
            "address": address
        }
    return render(request, "ndio_app/home.html", context=context)
        
def referral_home(request, ref_code=None):
    """Home view with referral tracking."""
    # Use ref_code from URL if provided
    print(request.session.items())
    request.session.flush()
    if ref_code:
        try:
            # Check if the referral code exists in the database
            referrer = UserDetail.objects.get(code=ref_code)
            request.session['referral_code'] = ref_code  # Store ref_code in session
            referrer_id = referrer.user.id  
            request.session['referrer'] = referrer_id # Store referrer in session    
            request.session.modify = True
            request.session.save()    
            print(f"Referrer code: {referrer_id} stored in session")
            print(f"Referrer: {referrer_id}")
            print(f"Session items After: {request.session.items()}")
        except UserDetail.DoesNotExist:
            print(f"Invalid referral code: {ref_code}")

    request.session.flush()
    context={}
    network_provider_products_list = []
    if request.method == "POST":
        fibre_is_available = False
        address = request.POST.get("address")
        network_providers_list = check_fibre_availability(address=address)

        # Create request session for address
        request.session["address"] = address

        # Check if network providers list is appended
        if network_providers_list is not None:
            fibre_is_available = True
            network_provider_products_list = get_network_provider_products(address=address)
        else:
            fibre_is_available = False
            network_providers_list = []
            
        context = {
            "products" : network_provider_products_list,
            "fibre_is_available": fibre_is_available,
            "address": address
        }
    return render(request, "ndio_app/home_referral.html", context=context)

def create_client(first_name, last_name, email, client_password, id_number, address, city, postal_code, suburb, province_id):
    """ 
    This function creates a user on the api end
    using the information retrieved from a form. 
    It accepts the following parameters:
        - SessionId 
        - strName
        - strLastName
        - strEmail
        - strPassword
        - strIdNumber
        - strAddress
        - strSuburb
        - strCity
        - intPostalCode 
        """
    
    # Get session ID before interacting with API 
    session_id = get_session()

    url = f"https://apitest.axxess.co.za/calls/rsapi/createClient.json?strUserName=KAB149&strPassword=cW3j*-NUmKG~$5!"
    params = {"strSessionId": session_id,
              "strName": first_name,
              "strLastName": last_name,
              "strEmail": email,
              "strPassword": client_password,
              "strIdNumber": id_number,
              "strAddress": address,
              "strSuburb" : suburb,
              "intProvinceId" : int(province_id),
              "strCity": city,
              "intPostalCode": postal_code
              }
    username = "ResellerAdmin"
    password = "jFbd5lg7Djfbn48idmlf4Kd"

    # Building the API query
    response = requests.put(url, params=params, auth=(username, password))

    # Check if the user was created or not
    if response.status_code == 201:
        return response.json().get("guidClientId")
    else:
        print("User not created")

import os
import requests

def create_fibre_service(
    session_id, client_id, product_id, network_provider_id, owner, cellphone_number, address, 
    address_type, suburb, city, postal_code, coordinates, building_number, floor_number, 
    unit_number, block_name
):
    """
    Creates a fibre service order using the Axxess Reseller API.

    Parameters:
        session_id (str): Active session ID from getSession().
        client_id (str): Unique client identifier.
        product_id (str): Selected product's unique identifier.
        network_provider_id (str): Network provider's unique identifier.
        owner (str): Name of the fibre line owner.
        cellphone_number (str): Contact number of the owner.
        address (str): Full installation address.
        address_type (str): Type of address (House, Apartment, etc.).
        suburb (str): Suburb name.
        city (str): City name.
        postal_code (str): Postal code of the address.
        coordinates (tuple | str): Latitude and Longitude as (lat, long) or a formatted string.
        building_number (str): Building number (if applicable).
        floor_number (str): Floor number (if applicable).
        unit_number (str): Unit number (if applicable).
        block_name (str): Block name (if applicable).

    Returns:
        dict: Response containing service ID and balance or an error message.
    """

    url = "https://apitest.axxess.co.za/calls/rsapi/createFibreComboService.json"

    # Use environment variables for security
    username = "ResellerAdmin"
    password = "jFbd5lg7Djfbn48idmlf4Kd"

    # Ensure coordinates are in "lat,long" format
    if isinstance(coordinates, (list, tuple)):
        coordinates = f"{coordinates[0]},{coordinates[1]}"

    params = {
        "strSessionId": session_id,  # Do NOT reassign session_id
        "guidClientId": client_id,
        "guidProductId": product_id,
        "guidNetworkProviderId": network_provider_id,
        "strOwner": owner,
        "strCell": cellphone_number,
        "strAddress": address,
        "strSuburb": suburb,
        "strCity": city,
        "strCode": postal_code,
        "strLatLong": coordinates,
        "strAddressType": address_type,
        "strBuildingId": building_number,
        "strFloorId": floor_number,
        "strUnitNumber": unit_number,
        "strBlockName": block_name
    }

    
    response = requests.get(url, params=params, auth=(username, password))

    if response.status_code == 201:
        data = response.json()
        print("Success")
        return {
            "service_id": data.get("guidServiceId"),
            "balance": data.get("decBalance"),
            "message": "Fibre service created successfully."
        }
    else:
        print(response.json())
        return {
            "error": f"Failed to create service. Status Code: {response.status_code}",
            "details": response.json()
        }


def register_view(request):
    # Getting the product ID
    fibre_product = request.GET.get("product_id")
    request.session["fibre_product"] = fibre_product



    if request.method == "POST":
        # Username validation
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            messages.success(request, "Account created successfuly")
            request.session['password'] = user.password
            user.save()
            login(request, user)  # Log in the user immediately
            return redirect('order_details')  # Redirect to the desired page
        else:
            # Add error messages for invalid form
            messages.error(request, "Form is invalid. Please try again.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('user_account')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def login_view_order(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('order_details')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login_order.html', {'form': form})

def logout_view(request):   
    logout(request)
    request.session.flush() # clear session
    return redirect('home')  # Redirect to the home page after logout

def lte_view(request):
    #items = get_products()
    return render(request, 'ndio_app/lte.html', {})

def about_us(request):
    return render(request, 'ndio_app/about_us.html')

def switch(request):
    return render(request, 'ndio_app/switch.html')

def faqs(request):
    faq = FAQ.objects.all()
    context = {
        "faqs" : faq
    } 
    return render(request, 'ndio_app/faqs.html', context=context)

def packages(request):
    """
    This function returns all the packages from the 
    database for specific netwwork providers and renders
    them to the template.
    """

    # Get the network provider
    providers = NetworkProvider.objects.all()
    context = {
        "providers": providers
    }
    return render(request, 'ndio_app/packages.html', context=context)

def home_fibre(request):
    return render(request, 'ndio_app/fibre.html')

def business_fibre(request):
    context={}
    network_provider_products_list = []
    if request.method == "POST":
        fibre_is_available = False
        address = request.POST.get("address")
        network_providers_list = check_fibre_availability(address=address)

        # Create request session for address
        request.session["address"] = address
        print(address)

        # Check if network providers list is appended
        if network_providers_list is not None:
            fibre_is_available = True
            network_provider_products_list = get_network_provider_products(address=address)
        else:
            fibre_is_available = False
            network_providers_list = []
            
        context = {
            "products" : network_provider_products_list,
            "fibre_is_available": fibre_is_available,
            "address": address
        }
    return render(request, "ndio_app/business_fibre.html", context=context)


def voip(request):
    
    if request.method == "POST":
        name  = request.POST.get("name")
        surname = request.POST.get("surname")
        email = request.POST.get("email")
        address = request.POST.get("address")
        company_name = request.POST.get("company")
        description = request.POST.get("requirements")
        service = request.POST.get("service")
        ServicesContact.objects.create(
            name = name,
            surname = surname,
            email = email,
            address = address,
            company_name = company_name,
            description = description,
            service = service
        )
        return render(request, 'ndio_app/voip.html')
    return render(request, 'ndio_app/voip.html')  

def wireless(request):
    if request.method == "POST":
        name = request.POST.get("name")
        surname = request.POST.get("surname")
        address = request.POST.get("address")
        email = request.POST.get("email")
        company_name = request.POST.get("company")
        description = request.POST.get("requirements")
        service = request.POST.get("service")
        ServicesContact.objects.create(
            name = name,
            surname = surname,
            address = address,
            email = email,
            company_name = company_name,
            description = description,
            service = service
        )
        return render(request, 'ndio_app/wireless.html')
    
    return render(request, 'ndio_app/wireless.html')  

def network_cabling(request):
    if request.method == "POST":
        name = request.POST.get("name")
        surname = request.POST.get("surname")
        address = request.POST.get("address")
        email = request.POST.get("email")
        company_name  = request.POST.get("company")
        description = request.POST.get("requirements")
        service = request.POST.get("service")
        ServicesContact.objects.create(
            name = name,
            surname = surname,
            address = address,
            email = email,
            company_name = company_name,
            description = description,
            service = service
        )
        return render(request, 'ndio_app/network_cabling.html')
    
    return render(request, 'ndio_app/network_cabling.html')

def managed(request):
    return render(request, 'ndio_app/managed.html')

def privacy_policy(request):
    return render(request, 'ndio_app/privacy_policy.html')

def order_details(request):
    """Handles order details submission."""
    referrer_id = request.session.get('referrer')
    referrer = User.objects.get(id=referrer_id) if referrer_id else None

    if request.method == "POST":
        form = forms.UserDetailForm(request.POST)
        form_order = forms.OrderForm(request.POST)

        if form.is_valid() and form_order.is_valid():

            client = form.save(commit=False)
            client.user = request.user
            client.referred_by = referrer  
            client_first_name = (client.first_name)
            client_last_name = (client.last_name)
            client_cell_number = client.phone_number
            client_email = "client@ndio.co.za"
            # Add client phone
            client_password = request.session.get("password")
            client_id_number = client.id_number
            
            client.save()  

            order = form_order.save(commit=False)
            order.client = request.user  # Assign client
            # Get data needed for createclient func
            client_address = order.address
            client_city = order.city
            postal_code = order.postal_code
            suburb = order.suburb
            province = order.province
            client_address_type = order.address_type
            client
            
            province_codes = {
                "Eastern Cape": 1,
                "Free State":2,
                "Gauteng":3,
                "Kwazulu-Natal":4,
                "Mpumalanga":5,
                "Northern Cape":6,
                "Limpopo":7,
                "North West Province":8,
                "Western Cape":9,
                "Other":0,
            }

            for provinces in province_codes:
                if province == provinces:
                    province_id = province_codes[provinces]

            client_id = create_client(
                client_first_name,
                client_last_name,
                client_email,
                client_password,
                client_id_number,
                client_address,
                client_city,
                postal_code,
                suburb, 
                province_id
                )
            print(f"From the variable(CLIENT ID ON AXXESS!!):{client_id}")
            fibre_product_id = request.session.get("fibre_product")

            if fibre_product_id:
                product = FibreProduct.objects.filter(product_id=fibre_product_id).first()
                network_provider = product.network_provider
                print(network_provider)

            network = NetworkProvider.objects.filter(name=network_provider).first()
            network_provider_id = network.guid_network_provider_id
            print(f"Network providerId: {network_provider_id}")
            print(f"Coordinates: {get_coordinates(client_address)}")

            house_number = client_address.split(" ")[0]
            floor_number =0
            apartment_number = 0
            print(f"product_ID: {fibre_product_id}")
            block_name = client_address.split(" ")[1]
            create_fibre_service(
                session_id = get_session(),
                client_id=client_id,
                product_id=fibre_product_id,
                network_provider_id=network_provider_id,
                owner=client_first_name,
                cellphone_number=client.phone_number,
                address=client_address,
                address_type=client_address_type,
                postal_code=postal_code,
                building_number=house_number,
                suburb=suburb,
                city=client_city,
                coordinates = get_coordinates(client_address),
                unit_number=apartment_number,
                floor_number=floor_number,
                block_name=block_name),
            
            order.save()

            return redirect("payment_view")

        else:
            print("User Detail Form Errors:", form.errors)
            print("Order Form Errors:", form_order.errors)

    else:
        # GET request - Prefill form
        address = request.session.get('address', '')
        address_split = address.split(', ') if address else [""] * 4
        city = address_split[2] if len(address_split) > 2 else ""

        order_initial_data = {'address': address, 'city': city}
        user_detail_intial_data = {'referred_by': referrer}

        form = forms.UserDetailForm(initial=user_detail_intial_data)
        form_order = forms.OrderForm(initial=order_initial_data)

        print(f"Preloading Forms: {form.errors}, {form_order.errors}")

    return render(request, 'ndio_app/order_details.html', {'form': form, 'form_order': form_order})
    
#@login_required
def user_account(request):
    # Get user_id
    user_id = request.user.id
    
    # Check if Yoco sent back relevant payment data
    payment_id = request.GET.get('id')  # Example: Yoco might return an ID or reference
    status = request.GET.get('status')
    print(status)
    
    # Get user referral code using id, handling case where user has no entry
    ref_code = UserDetail.objects.filter(user_id=user_id).first()
    
    if not ref_code:
        print('No referral code found for this user.')
    
    context = {
        'ref_code': ref_code
    }

    return render(request, "accounts/user_account.html")

def unsuccessful_payment(request):
    return render(request, "ndio_app/unsuccessful.html")

def process_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get('token')
            amount = form.cleaned_data.get('amount')
            currency = form.cleaned_data.get('currency')
            name = form.cleaned_data.get('name')

            try:
                amount = Decimal(amount)
            except:
                return JsonResponse({'status': 'error', 'message': 'Invalid amount'})

            url = "https://payments.yoco.com/api/checkouts"
            headers = {
                'Authorization': f'Bearer {settings.YOCO_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = json.dumps({
                'amount': float(amount),
                'currency': currency,
                'successUrl': request.build_absolute_uri('/user_account/'),  # Redirect after success
                'cancelUrl': request.build_absolute_uri('/unsuccessful_payment/')
            })

            response = requests.post(url, headers=headers, data=data)

            if response.status_code < 400:
                # Get redirect URL from Yoco
                redirect_url = response.json().get('redirectUrl')

                # Save the payment record in the database
                Payment.objects.create(
                    user = request.user,  # Store the user who made the payment
                    amount = amount,
                    status = "Pending",  # Set status to pending initially
                    payment_id = response.json().get('id'),  # Store transaction ID
                    name = name
                )

                if redirect_url:
                    return redirect(redirect_url)

                return JsonResponse({'status': 'success', 'message': 'Payment initiated but no redirect URL received'})
            else:
                return redirect('unsuccessful')

        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid form data', 'errors': form.errors})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def payment_view(request):
    fibre_product_id = request.session.get("fibre_product")

    # Check if the product ID exists in the session
    if not fibre_product_id:
        return JsonResponse({"status": "error", "message": "No product selected"})

    # Fetch the product and handle case where it does not exist
    product = FibreProduct.objects.filter(product_id=fibre_product_id).first()
    if not product:
        return JsonResponse({"status": "error", "message": "Product not found"})

    # Calculate total price
    product_price = product.price
    total_price = product_price + 300

    # Yoco Public Key
    public_key = settings.YOCO_PUBLIC_KEY

    # Create an unbound form with initial data (DO NOT call is_valid() or save())
    form = PaymentForm(initial={'amount': total_price})

    context = {
        'yoco_public_key': public_key,
        'currency': 'ZAR',
        'product_name': product.product_name,  # Use product.name instead of the whole object
        'product_price': product_price,
        'form': form,
        'amount': total_price
    }

    return render(request, 'ndio_app/payments.html', context)
