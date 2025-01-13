from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ref", models.CharField(max_length=24, unique=True)),
                ("amount_cents", models.BigIntegerField(default=0)),
                ("status", models.CharField(default="open", max_length=16)),
                ("note", models.CharField(blank=True, default="", max_length=80)),
            ],
        ),
    ]
