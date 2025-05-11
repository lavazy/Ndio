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
import requests


# Create your views here.
def get_session():
    """ 
        This function creates an API session, allowing
        us to interact with the API for 1 hour. And
        we can request another one after 1 hour. 
    """

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
    """
    Converts a physical address into geographical coordinates (latitude and longitude)
    using the Google Maps Geocoding API.

    Parameters:
        address (str): The physical address to geocode.

    Returns:
        tuple: A tuple containing (latitude, longitude) if successful,
               otherwise (None, None) if the API request fails.
    """
   
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
    """
    Checks for fibre availability at the specified address using the Axxess API.

    Parameters:
        address (str): The user's physical address.

    Returns:
        list: A list of available network provider IDs for the area if the request is successful,
              otherwise None.
    """

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
    """
    Retrieves a list of fibre products offered by available network providers at the given address.

    Parameters:
        address (str): The physical address to check for available fibre products.

    Returns:
        list: A list of product dictionaries from all available network providers if found,
              otherwise None.
    """

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
    """
    Handles the display and logic for the home page where users can check fibre availability.

    This view accepts a POST request with an address submitted by the user, clears any existing session,
    and checks whether fibre is available at that address by:
        - Retrieving a list of available network providers.
        - Fetching fibre products offered by those providers.
        - Storing the address in the session for use in other views.

    Parameters:
        request (HttpRequest): The HTTP request object, which may contain a POST address field.

    Returns:
        HttpResponse: Renders the 'ndio_app/home.html' template with a context dictionary containing:
            - 'products': A list of available fibre products (empty if unavailable).
            - 'fibre_is_available': A boolean indicating whether fibre is available.
            - 'address': The user's submitted address.
    """
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
    """
    Handles the referral landing page view where users can check fibre availability
    while optionally tracking referral codes passed through the URL.

    This view:
        - Checks for a referral code in the URL and verifies it against the database.
        - Stores the referrer’s ID and code in the session if valid.
        - Accepts an address via POST to check fibre availability.
        - Retrieves products from available network providers.
        - Stores the address in the session.

    Parameters:
        request (HttpRequest): The HTTP request object, possibly containing POST data.
        ref_code (str, optional): The referral code passed via the URL.

    Returns:
        HttpResponse: Renders 'home_referral.html' with context containing:
            - 'products': List of fibre products from providers (if any).
            - 'fibre_is_available': Boolean indicating availability.
            - 'address': User-submitted address.
    """
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
    Creates a new client on the Axxess API using the provided user information.

    This function sends a PUT request to the API with the required client details.
    It first obtains a session ID and then authenticates using predefined credentials.
    If the request is successful (status code 201), it returns the newly created client's unique ID.

    Parameters:
        first_name (str): The client's first name.
        last_name (str): The client's last name.
        email (str): The client's email address.
        client_password (str): The client's password.
        id_number (str): The client's ID or national identification number.
        address (str): The client's street address.
        city (str): The city where the client resides.
        postal_code (int): The postal code of the client's area.
        suburb (str): The suburb or local area name.
        province_id (int or str): The numeric ID of the province (must be castable to int).

    Returns:
        str or None: The newly created client's unique GUID if the request is successful;
                     otherwise, prints an error message and returns None.
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
    """
    Handles user registration via a custom Django form and manages session data.

    This view retrieves a fibre product ID from the query string and stores it in the session.
    When the form is submitted (POST request), it attempts to create a new user account using the
    `CustomUserCreationForm`. If successful, the user is logged in immediately and redirected to the 
    order details page. If the form is invalid, appropriate error messages are displayed.

    On GET requests, the registration form is displayed to the user.

    Session Data:
        - "fibre_product": Stores the selected product ID from the GET request.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the registration page with the form, or redirects on successful registration.
    """

    # Getting the product ID
    fibre_product = request.GET.get("product_id")
    request.session["fibre_product"] = fibre_product



    if request.method == "POST":
        # Username validation
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            messages.success(request, "Account created successfuly")
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
    """
    Authenticates and logs in a user using Django's built-in AuthenticationForm.

    On a POST request, this view processes the submitted login form. If the form is valid,
    the user is authenticated and logged in using Django's `login()` function, then redirected
    to the user account page.

    On a GET request, the view simply displays the login form to the user.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Renders the login page with the authentication form, or redirects
                      to the 'user_account' page on successful login.
    """
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
    """
    Authenticates and logs in a user using Django's built-in AuthenticationForm.

    On a POST request, this view processes the submitted login form. If the form is valid,
    the user is authenticated and logged in using Django's `login()` function, then redirected
    to the user account page.

    On a GET request, the view simply displays the login form to the user.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Renders the login page with the authentication form, or redirects
                      to the 'order_details' page on successful login.
    """
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
    """
    Logs out the currently authenticated user and clears the session.

    This view uses Django's built-in `logout()` function to terminate the user's session.
    It then explicitly flushes the session to remove any remaining session data, such as
    stored form inputs or temporary identifiers, and redirects the user to the home page.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponseRedirect: Redirects the user to the homepage after logout.
    """  
    logout(request)
    request.session.flush() # clear session
    return redirect('home')  # Redirect to the home page after logout

def lte_view(request):
    """
    Renders the LTE page of the NDIO web application.

    This view simply returns the LTE information template when the route is accessed.
    It does not require any context data and serves as a static informational or marketing page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'lte.html' template within the 'ndio_app' directory.
    """
    return render(request, 'ndio_app/lte.html', {})

def about_us(request):
    """
    Renders the 'About Us' page of the NDIO web application.

    This view displays static information about the organization, its mission, and team.
    It does not require any dynamic context data and simply loads the corresponding template.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'about_us.html' template from the 'ndio_app' directory.
    """
    return render(request, 'ndio_app/about_us.html')

def switch(request):
    """
    Renders the 'Switch' page of the NDIO web application.

    This view displays a static informational page that explains how users can switch
    their internet service provider to NDIO. It does not require any dynamic data and 
    simply serves the corresponding HTML template.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Renders the 'switch.html' template from the 'ndio_app' directory.
    """
    return render(request, 'ndio_app/switch.html')

def faqs(request):
    """
    Renders the Frequently Asked Questions (FAQs) page of the NDIO web application.

    This view queries all FAQ entries from the database and passes them to the template
    for display. It enables users to browse common questions and answers related to 
    NDIO's services.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Renders the 'faqs.html' template with a context containing all FAQ objects.
    """
    faq = FAQ.objects.all()
    context = {
        "faqs": faq
    }
    return render(request, 'ndio_app/faqs.html', context=context)

def packages(request):
    """
    Renders the Packages page of the NDIO web application.

    This view retrieves all available network providers from the database, 
    which may be used to display related fibre or LTE packages in the frontend. 
    The provider data is passed to the template for dynamic rendering.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Renders the 'packages.html' template with context containing 
                      all network provider objects.
    """
    providers = NetworkProvider.objects.all()
    context = {
        "providers": providers
    }
    return render(request, 'ndio_app/packages.html', context=context)

def home_fibre(request):
    """
    Renders the Home Fibre information page of the NDIO web application.

    This view serves a static page that provides users with information about 
    NDIO's home fibre services, including features, benefits, and how to get started.
    No dynamic data is passed to the template.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Renders the 'fibre.html' template from the 'ndio_app' directory.
    """
    return render(request, 'ndio_app/fibre.html')


def business_fibre(request):
    """
    Handles the Business Fibre service page and checks fibre availability for a given address.

    This view allows users to input a business address via POST request to check for 
    fibre availability. If available, it fetches a list of network provider products 
    for that address and displays them on the page. If fibre is not available, 
    it notifies the user accordingly.

    Parameters:
        request (HttpRequest): The incoming HTTP request. Expects POST data containing
                               an 'address' field for fibre availability lookup.

    Returns:
        HttpResponse: Renders the 'business_fibre.html' template with a context dictionary that includes:
                      - 'products': a list of available network provider products (if any),
                      - 'fibre_is_available': a boolean indicating if fibre is available,
                      - 'address': the submitted address.
    """
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
    """
    Handles the VoIP service page and processes service inquiry form submissions.

    This view supports both GET and POST requests. On a GET request, it simply renders the VoIP 
    information page. On a POST request, it captures user-submitted details from the VoIP inquiry 
    form, including personal, company, and service-related information, and stores it in the 
    `ServicesContact` database model.

    Parameters:
        request (HttpRequest): The incoming HTTP request. If POST, expects the following fields:
            - name (str): The user's first name.
            - surname (str): The user's last name.
            - email (str): The user's email address.
            - address (str): The physical address of the user or company.
            - company (str): The name of the company (if applicable).
            - requirements (str): Description of service requirements or needs.
            - service (str): The specific VoIP service being requested.

    Returns:
        HttpResponse: Renders the 'voip.html' template whether it is a GET or POST request. 
                      On POST, the user details are saved and the page is refreshed.
    """
    if request.method == "POST":
        name = request.POST.get("name")
        surname = request.POST.get("surname")
        email = request.POST.get("email")
        address = request.POST.get("address")
        company_name = request.POST.get("company")
        description = request.POST.get("requirements")
        service = request.POST.get("service")

        ServicesContact.objects.create(
            name=name,
            surname=surname,
            email=email,
            address=address,
            company_name=company_name,
            description=description,
            service=service
        )
        return render(request, 'ndio_app/voip.html')
    return render(request, 'ndio_app/voip.html')

def wireless(request):
    """
    Handles the wireless service inquiry page and processes form submissions.

    This view manages both GET and POST HTTP methods. On a GET request, it simply renders the 
    wireless service page. On a POST request, it collects customer-provided information from 
    the form—such as personal details, service requirements, and company information—and stores 
    it in the `ServicesContact` model for follow-up or processing.

    Parameters:
        request (HttpRequest): The HTTP request object. If it's a POST request, it should include:
            - name (str): The user's first name.
            - surname (str): The user's last name.
            - address (str): Installation or contact address.
            - email (str): The user's email address.
            - company (str): The company name, if applicable.
            - requirements (str): Description of the user's wireless service needs.
            - service (str): Type of service selected (e.g., wireless broadband, etc.).

    Returns:
        HttpResponse: Renders the 'wireless.html' template whether on GET or POST. 
                      On successful POST, the data is saved and the same page is returned.
    """
    if request.method == "POST":
        name = request.POST.get("name")
        surname = request.POST.get("surname")
        address = request.POST.get("address")
        email = request.POST.get("email")
        company_name = request.POST.get("company")
        description = request.POST.get("requirements")
        service = request.POST.get("service")

        ServicesContact.objects.create(
            name=name,
            surname=surname,
            address=address,
            email=email,
            company_name=company_name,
            description=description,
            service=service
        )
        return render(request, 'ndio_app/wireless.html')
    
    return render(request, 'ndio_app/wireless.html')


def network_cabling(request):
    """
    Handles the network cabling service inquiry page and processes form submissions.

    This view manages both GET and POST HTTP methods. On a GET request, it simply renders the 
    network cabling service page. On a POST request, it collects customer-provided information from 
    the form—such as personal details, service requirements, and company information—and stores 
    it in the `ServicesContact` model for follow-up or processing.

    Parameters:
        request (HttpRequest): The HTTP request object. If it's a POST request, it should include:
            - name (str): The user's first name.
            - surname (str): The user's last name.
            - address (str): Installation or contact address.
            - email (str): The user's email address.
            - company (str): The company name, if applicable.
            - requirements (str): Description of the user's wireless service needs.
            - service (str): Type of service selected (e.g., wireless broadband, etc.).

    Returns:
        HttpResponse: Renders the 'network_cabling.html' template whether on GET or POST. 
                      On successful POST, the data is saved and the same page is returned.
    """
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
    """
    Handles the managed services inquiry page.
    This view manages, on a GET request, to simply render the 
    managed services page.

    Parameters:
        request (HttpRequest): The HTTP request object. If it's a POST request, it should include:

    Returns:
        HttpResponse: Renders the 'managed.html' template whether on GET. 
    """
    return render(request, 'ndio_app/managed.html')

def privacy_policy(request):
    return render(request, 'ndio_app/privacy_policy.html')

def order_details(request):
    """Handles the order details page and process form submission."""
    referrer_id = request.session.get('referrer')
    fibre_product_id = request.session.get('fibre_product')
    referrer = User.objects.get(id=referrer_id) if referrer_id else None

    if request.method == "POST":
        form = forms.UserDetailForm(request.POST)
        form_order = forms.OrderForm(request.POST)

        if form.is_valid() and form_order.is_valid():
            # Check if user already has a UserDetail
            try:
                existing_detail = request.user.user_details
                form = forms.UserDetailForm(request.POST, instance=existing_detail)
                client = form.save(commit=False)
            except UserDetail.DoesNotExist:
                client = form.save(commit=False)
                client.user = request.user
                client.referred_by = referrer

            # Set static values
            client_email = "client@ndio.co.za"
            client_password = request.session.get("password")
            client_id_number = client.id_number

            client.save()

            # Create order
            order = form_order.save(commit=False)
            order.client = request.user
            order.save()

            # Prepare data for Axxess
            client_first_name = client.first_name
            client_last_name = client.last_name
            client_cell_number = client.phone_number
            client_address = order.address
            client_city = order.city
            postal_code = order.postal_code
            suburb = order.suburb
            province = order.province
            client_address_type = order.address_type

            # Map province to ID
            province_codes = {
                "Eastern Cape": 1, "Free State": 2, "Gauteng": 3,
                "Kwazulu-Natal": 4, "Mpumalanga": 5, "Northern Cape": 6,
                "Limpopo": 7, "North West Province": 8, "Western Cape": 9, "Other": 0,
            }
            province_id = province_codes.get(province, 0)

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

            # Product and network details
            product = FibreProduct.objects.filter(product_id=fibre_product_id).first()
            network_provider = product.network_provider
            network = NetworkProvider.objects.filter(name=network_provider).first()
            network_provider_id = network.guid_network_provider_id

            # Address parsing
            address_parts = client_address.split(" ")
            house_number = address_parts[0] if address_parts else "0"
            block_name = address_parts[1] if len(address_parts) > 1 else ""
            floor_number = 0
            apartment_number = 0

            create_fibre_service(
                session_id=get_session(),
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
                coordinates=get_coordinates(client_address),
                unit_number=apartment_number,
                floor_number=floor_number,
                block_name=block_name
            )

            return redirect("payment_view")

        else:
            print("User Detail Form Errors:", form.errors)
            print("Order Form Errors:", form_order.errors)

    else:
        # Prefill for GET
        address = request.session.get('address', '')
        address_split = address.split(', ') if address else [""] * 4
        city = address_split[2] if len(address_split) > 2 else ""

        order_initial_data = {'address': address, 'city': city}

        try:
            existing_detail = request.user.user_details
            form = forms.UserDetailForm(instance=existing_detail)
        except UserDetail.DoesNotExist:
            user_detail_initial_data = {'referred_by': referrer}
            form = forms.UserDetailForm(initial=user_detail_initial_data)

        form_order = forms.OrderForm(initial=order_initial_data)

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
                'Authorization': f'Bearer {settings.YOCO_LIVE_SK}',
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
                return redirect('unsuccessful_payment')

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
    public_key = settings.YOCO_LIVE_PK

    # Create an unbound form with initial data (DO NOT call is_valid() or save())
    form = PaymentForm(initial={'amount': total_price})

    context = {
        'yoco_public_key': public_key,
        'currency': 'ZAR',
        'product_name': product.product_name,
        'product_price': product_price,
        'form': form,
        'amount': total_price
    }

    return render(request, 'ndio_app/payments.html', context)
