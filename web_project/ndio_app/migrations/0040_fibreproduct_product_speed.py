# Generated by Django 5.1.4 on 2025-05-16 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ndio_app", "0039_alter_payment_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="fibreproduct",
            name="product_speed",
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]
