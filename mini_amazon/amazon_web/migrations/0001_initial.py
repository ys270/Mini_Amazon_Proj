# Generated by Django 3.0.2 on 2020-04-17 04:41

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('pkgid', models.AutoField(primary_key=True, serialize=False)),
                ('userid', models.IntegerField(default=0)),
                ('status', models.IntegerField(default=0)),
                ('x', models.IntegerField(default=0)),
                ('y', models.IntegerField(default=0)),
                ('date', models.DateTimeField(default=datetime.datetime.now, editable=False)),
                ('item_description', models.CharField(max_length=100)),
                ('purchase_num', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('item_id', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=100)),
                ('whid', models.IntegerField(default=1)),
                ('count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('whid', models.AutoField(primary_key=True, serialize=False)),
                ('x', models.IntegerField(default=0)),
                ('y', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='AmazonUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]