# Generated by Django 5.1.4 on 2025-03-08 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ndio_app", "0019_fibreproduct_networkprovider_tickets_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="userdetail",
            name="last_updated",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="communication",
            name="message_type",
            field=models.CharField(
                choices=[("email", "Email"), ("sms", "SMS"), ("whatsapp", "Whatsapp")],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="networkprovider",
            name="guid_network_provider_id",
            field=models.UUIDField(primary_key=True, serialize=False),
        ),
    ]
