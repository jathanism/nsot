# Convert index_together to Meta.indexes for Django 5.x compatibility.
#
# Models where index_together duplicated unique_together (attribute,
# assignment, device, network, interface's device+name) don't need new
# indexes — the unique constraint already provides one.
#
# Models with standalone indexes (value, change, interface's
# device_hostname+name) get fresh named indexes via AddIndex.
# We use AddIndex instead of RenameIndex because SQLite table
# rebuilds in prior migrations (AlterField) can lose unnamed
# index_together indexes.

import nsot.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nsot", "0039_django30_compat"),
    ]

    operations = [
        # Clear ALL index_together from state.  For models that overlap
        # with unique_together, no DB change is needed.  For standalone
        # indexes, we create fresh named indexes below.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterIndexTogether(
                    name="attribute", index_together=None,
                ),
                migrations.AlterIndexTogether(
                    name="assignment", index_together=None,
                ),
                migrations.AlterIndexTogether(
                    name="change", index_together=None,
                ),
                migrations.AlterIndexTogether(
                    name="device", index_together=None,
                ),
                migrations.AlterIndexTogether(
                    name="interface", index_together=None,
                ),
                migrations.AlterIndexTogether(
                    name="network", index_together=None,
                ),
                migrations.AlterIndexTogether(
                    name="value", index_together=None,
                ),
            ],
            database_operations=[],
        ),
        # Create named indexes for standalone index_together entries.
        # Interface: device_hostname + name
        migrations.AddIndex(
            model_name="interface",
            index=models.Index(
                fields=["device_hostname", "name"],
                name="nsot_interf_device__f01451_idx",
            ),
        ),
        # Value: (name, value, resource_name) and (resource_name, resource_id)
        migrations.AddIndex(
            model_name="value",
            index=models.Index(
                fields=["name", "value", "resource_name"],
                name="nsot_value_name_0c66ac_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="value",
            index=models.Index(
                fields=["resource_name", "resource_id"],
                name="nsot_value_resourc_62e5c1_idx",
            ),
        ),
        # Change: (resource_name, resource_id) and (resource_name, event)
        migrations.AddIndex(
            model_name="change",
            index=models.Index(
                fields=["resource_name", "resource_id"],
                name="nsot_change_resourc_fa9b1d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="change",
            index=models.Index(
                fields=["resource_name", "event"],
                name="nsot_change_resourc_9023b9_idx",
            ),
        ),
        # mac_address field type change detected by makemigrations.
        migrations.AlterField(
            model_name="interface",
            name="mac_address",
            field=nsot.fields.MACAddressField(
                blank=True,
                db_index=True,
                default=0,
                help_text="If not provided, defaults to 00:00:00:00:00:00.",
                integer=True,
                null=True,
                verbose_name="MAC Address",
            ),
        ),
    ]
