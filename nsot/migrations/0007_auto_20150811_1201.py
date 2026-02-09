# -*- coding: utf-8 -*-

from django.db import models, migrations

class Migration(migrations.Migration):

    dependencies = [
        ("nsot", "0006_auto_20150810_1947"),
    ]

    operations = [
        migrations.RenameField(
            model_name="interface",
            old_name="mac",
            new_name="mac_address",
        ),
    ]
