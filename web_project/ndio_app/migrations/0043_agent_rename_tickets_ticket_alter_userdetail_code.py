# Generated by Django 5.1.4 on 2025-05-23 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ndio_app", "0042_rename_price_fibreproduct_product_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="Agent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("agent_id", models.CharField(max_length=6, unique=True)),
                ("agent_name", models.CharField(max_length=100)),
                ("agent_surname", models.CharField(max_length=100)),
            ],
        ),
        migrations.RenameModel(
            old_name="Tickets",
            new_name="Ticket",
        ),
        migrations.AlterField(
            model_name="userdetail",
            name="code",
            field=models.CharField(editable=False, max_length=12, unique=True),
        ),
    ]
