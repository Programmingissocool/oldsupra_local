# Generated manually for the admin-only pretend customer proxy.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestCustomer',
            fields=[],
            options={
                'verbose_name': 'Pretend Customer',
                'verbose_name_plural': 'Pretend Customer',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.account',),
        ),
    ]