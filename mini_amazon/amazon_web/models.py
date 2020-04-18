from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import uuid
# Create your models here.

class AmazonUser(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)

class Warehouse(models.Model):
    whid = models.AutoField(primary_key=True)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)

class Product(models.Model):
    item_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50,default="")
    description = models.CharField(max_length=100,default="")
    whid = models.IntegerField(default=1)
    count = models.IntegerField(default=0)

class Order(models.Model):
    pkgid = models.AutoField(primary_key=True)
    userid = models.IntegerField(default=0)
    upsid = models.CharField(null=True,blank=True,max_length=50)
    status = models.IntegerField(default=0)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.now,editable=False)
    item_description = models.CharField(max_length=100,default="")
    purchase_num = models.IntegerField(default=1)

