# Generated by Django 3.0.2 on 2020-04-23 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon_web', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='rate_score',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='avg_score',
            field=models.FloatField(default=5),
        ),
        migrations.AddField(
            model_name='product',
            name='rate_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='product',
            name='total_score',
            field=models.IntegerField(default=0),
        ),
    ]