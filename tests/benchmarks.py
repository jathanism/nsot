import ipaddress
import time

import pytest
from django.db import transaction

from nsot import models


@pytest.mark.django_db
def test_create_1024(site):

    address = "10.0.0.0/20"
    models.Network.objects.create(site=site, cidr=address)
    models.Attribute.objects.create(
        site=site, resource_name="Network", name="aaaa"
    )

    start = time.time()
    network = ipaddress.ip_network(address)

    with transaction.atomic():
        for ip in network.subnets(new_prefix=30):
            models.Network.objects.create(
                site=site, cidr=ip.exploded, attributes={"aaaa": "value"}
            )

    print(f"Finished in {time.time() - start} seconds.")
