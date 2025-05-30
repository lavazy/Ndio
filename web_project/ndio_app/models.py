import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# Create your models here.
class UserDetail(models.Model):
    """
    This class extends from the default django User model. It stores the user details.
    """

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=10, unique=False)
    id_number = models.CharField(max_length=15, unique=False)
    code = models.CharField(max_length=12, unique=True, editable=False)
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="details"
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user_details"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)

    def save(self, *args, **kwargs):
        """
        Generate a 12-character referral code if one doesn't exist.
        """
        if not self.code:
            self.code = str(uuid.uuid4()).replace("-", "")[
                :12
            ]  # Remove hyphens & take first 12 chars
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} - {self.code}"


class AgentProfile(models.Model):
    """
    This class represents the Agents model, which stores data about NDIO agents.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    agent_id = models.CharField(max_length=6, unique=True, editable=False)
    agent_name = models.CharField(max_length=100)
    agent_surname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Auto-generate a 6-character alphanumeric agent ID if not set
        if not self.agent_id:
            self.agent_id = uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.agent_id})"


class ManagerProfile(models.Model):
    """
    This class represents the Managers model, which stores all data about NDIO managers
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    manager_id = models.CharField(max_length=6, unique=True, editable=False)
    manager_name = models.CharField(max_length=100)
    manager_surname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        This function autogenerates a manger ID of 6 characters by using UUIDs
        """
        if not self.manager_id:
            self.manager_id = uuid.uuid4().hex[:6].upper()
        return super().save(*args, **kwargs)

    def __str__(self):
        """
        This function returns the str format of this model by giving us the manager's username
        """
        return f"{self.user.username}"


class NetworkProvider(models.Model):
    """
    This class represents the Network Provider model that stores all data about the network providers
    """

    guid_network_provider_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=60)

    def __str__(self) -> str:
        return self.name


# Only available to the admin
class FibreProduct(models.Model):
    """
    This class represents the Fibre Products model that stores all details about our fibre products
    """

    product_id = models.CharField(max_length=100, primary_key=True)
    product_name = models.CharField(max_length=150)
    product_speed = models.CharField(max_length=15, blank=True, null=True)
    product_price = models.DecimalField(blank=True, max_digits=10, decimal_places=2)
    slug = models.SlugField(unique=True, blank=True)
    network_provider = models.ForeignKey(
        NetworkProvider, on_delete=models.CASCADE, related_name="products"
    )

    # Generate slug
    def save(self, *args, **kwargs):
        """
        This method generates a slug automatically for each
        product using the product_name field if there is no
        slug.
        """
        if not self.slug:
            self.slug = slugify(self.product_name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        This function returns the name of the product
        object in a string format to enhance readability.
        """
        return self.product_name


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    ordered_product = models.ForeignKey(
        FibreProduct, on_delete=models.SET_NULL, null=True, related_name="order"
    )
    address_type = models.CharField(max_length=50)
    province = models.CharField(max_length=150)
    suburb = models.CharField(max_length=150)
    apartment_name = models.CharField(
        max_length=30, null=True, blank=True
    )  # This field can be empty
    apartment_floor = models.CharField(null=True, blank=True, max_length=10)
    apartment_unit = models.CharField(null=True, blank=True, max_length=10)
    estate_name = models.CharField(max_length=30, null=True, blank=True)
    estate_address = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=150)
    city = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=4)
    date_created = models.DateTimeField(auto_now_add=True)
    order_complete = models.BooleanField(default=False)
    date_completed = models.DateTimeField(null=True, blank=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    def __str__(self) -> str:
        return f"Order #{self.order_id} - {self.client}"


class Payment(models.Model):
    payment_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=20)
    is_paid = models.BooleanField(default=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payment", null=True
    )

    def __str__(self) -> str:
        return f"{self.user} - {self.status}"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscription"
    )
    product = models.ForeignKey(
        FibreProduct, on_delete=models.CASCADE, related_name="subscriptions"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    activation_date = models.DateTimeField(auto_now_add=True, null=True)
    payment_due_date = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question


class ServicesContact(models.Model):
    name = models.CharField(max_length=50, null=True)
    surname = models.CharField(max_length=50, null=True)
    email = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=100, null=True)
    service = models.CharField(max_length=100, null=True)
    company_name = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=150, null=True)

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"


class Communication(models.Model):
    MESSAGE_TYPES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("whatsapp", "Whatsapp"),
    ]

    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    message_subject = models.CharField(max_length=100)
    message_receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages"
    )
    date_sent = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.message_subject} - {self.message_receiver.username}"


class Ticket(models.Model):
    """
    This is the ticket model for all the tickets submitted by users
    """

    ticket_id = models.AutoField(primary_key=True)
