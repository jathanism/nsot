# -*- coding: utf-8 -*-

from django.db import models, migrations
import django.db.models.deletion
import django_extensions.db.fields.json

class Migration(migrations.Migration):

    dependencies = [
        ("nsot", "0020_move_value_data"),
    ]
    atomic = False

    operations = [
        #########
        # Value #
        #########
        # Fix constraints
        migrations.AlterUniqueTogether(
            name="value",
            unique_together=set(
                [("name", "value", "resource_name", "new_resource_id")]
            ),
        ),
        # Wrapped in SeparateDatabaseAndState because Django 5.x is strict
        # about dropping index_together indexes that overlap with
        # unique_together (the old index from 0001 may not exist as a
        # separate non-unique index). We update state and only CREATE
        # the new index.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterIndexTogether(
                    name="value",
                    index_together=set([("name", "value", "resource_name")]),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="CREATE INDEX IF NOT EXISTS nsot_val_name_val_rn ON nsot_value (name, value, resource_name)",
                    reverse_sql="DROP INDEX IF EXISTS nsot_val_name_val_rn",
                ),
            ],
        ),
        # Delete the resource fk
        migrations.RemoveField(
            model_name="value",
            name="resource",
        ),
        # Rename resource_id
        migrations.RenameField(
            model_name="value",
            old_name="new_resource_id",
            new_name="resource_id",
        ),
        #############
        # Resources #
        #############
        # Delete the now-legacy Resource-based multiple inheritance models.
        migrations.DeleteModel(
            name="Assignment",
        ),
        migrations.DeleteModel(
            name="Interface",
        ),
        migrations.DeleteModel(
            name="Network",
        ),
        migrations.DeleteModel(
            name="Device",
        ),
        # Delete the Resource model altogether
        migrations.DeleteModel(
            name="Resource",
        ),
        #################
        # Rename models #
        #################
        # Start renaming the new Resource-abstract concrete models.
        # Network & Network relations
        migrations.RenameModel(
            old_name="Network_temp",
            new_name="Network",
        ),
        migrations.AlterField(
            model_name="network",
            name="parent",
            field=models.ForeignKey(
                related_name="children",
                on_delete=django.db.models.deletion.PROTECT,
                default=None,
                blank=True,
                to="nsot.Network",
                null=True,
            ),
        ),
        # Device
        migrations.RenameModel(
            old_name="Device_temp",
            new_name="Device",
        ),
        # Interface & Interface relations
        migrations.RenameModel(
            old_name="Interface_temp",
            new_name="Interface",
        ),
        ##############
        # Assignment #
        ##############
        # Because Assignments is used as m2m-through on Interface, we have to
        # create the model anew.
        migrations.CreateModel(
            name="Assignment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "address",
                    models.ForeignKey(
                        related_name="assignments",
                        to="nsot.Network",
                        on_delete=django.db.models.deletion.CASCADE
                    ),
                ),
                (
                    "interface",
                    models.ForeignKey(
                        related_name="assignments",
                        to="nsot.Interface",
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        # Interface => m2m throgh Assignment => Network
        migrations.AlterField(
            model_name="interface",
            name="addresses",
            field=models.ManyToManyField(
                related_name="addresses",
                through="nsot.Assignment",
                to="nsot.Network",
                db_index=True,
            ),
        ),
        # Ditch the intermediate temp Assignment model
        migrations.DeleteModel(
            name="Assignment_temp",
        ),
        # Interface relations
        migrations.AlterField(
            model_name="interface",
            name="device",
            field=models.ForeignKey(
                related_name="interfaces",
                verbose_name="Device",
                to="nsot.Device",
                on_delete=django.db.models.deletion.CASCADE,
                help_text="Unique ID of the connected Device.",
            ),
        ),
        migrations.AlterField(
            model_name="interface",
            name="parent",
            field=models.ForeignKey(
                related_name="children",
                on_delete=django.db.models.deletion.PROTECT,
                default=None,
                to="nsot.Interface",
                blank=True,
                help_text="Unique ID of the parent Interface.",
                null=True,
                verbose_name="Parent",
            ),
        ),
        ###############
        # Constraints #
        ###############
        migrations.AlterUniqueTogether(
            name="assignment",
            unique_together=set([("address", "interface")]),
        ),
        migrations.AlterUniqueTogether(
            name="device",
            unique_together=set([("site", "hostname")]),
        ),
        migrations.AlterUniqueTogether(
            name="network",
            unique_together=set(
                [("site", "ip_version", "network_address", "prefix_length")]
            ),
        ),
        migrations.AlterIndexTogether(
            name="assignment",
            index_together=set([("address", "interface")]),
        ),
        migrations.AlterIndexTogether(
            name="device",
            index_together=set([("site", "hostname")]),
        ),
        migrations.AlterIndexTogether(
            name="network",
            index_together=set(
                [("site", "ip_version", "network_address", "prefix_length")]
            ),
        ),
    ]
