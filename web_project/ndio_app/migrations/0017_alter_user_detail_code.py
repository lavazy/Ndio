# Generated by Django 5.1.4 on 2025-02-11 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ndio_app", "0016_user_detail_code_user_detail_created_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user_detail",
            name="code",
            field=models.CharField(blank=True, max_length=12, unique=True),
        ),
    ]
