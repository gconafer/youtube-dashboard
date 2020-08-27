from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.db import models


class MyAccountManager(BaseUserManager):
  def create_user(self, email, username, password=None):
    if not email:
      raise ValueError('Users must have an email address')
    if not username:
      raise ValueError('Users must have an username')

    user = self.model(
      email=self.normalize_email(email),
      username=username,
    )
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_superuser(self, email, username, password=None):
    user = self.create_user(
      email=self.normalize_email(email),
      password=password,
      username=username,
    )
    user.is_admin = True
    user.is_staff = True
    user.is_superuser = True
    user.save(using=self._db)
    return user


class Account(AbstractBaseUser):
  email = models.EmailField(verbose_name="email", max_length=50, unique=True)
  username = models.CharField(max_length=50, unique=True)
  is_admin = models.BooleanField(default=False)
  is_active = models.BooleanField(default=True)
  is_staff = models.BooleanField(default=False)
  is_superuser = models.BooleanField(default=False)

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['username', ]

  objects = MyAccountManager()

  def __str__(self):
    return self.email

  def has_perm(self, perm, obj=None):
    return self.is_admin

  def has_module_perms(self, app_label):
    return True


class Manager(models.Model):
  user = models.OneToOneField(Account, on_delete=models.CASCADE, primary_key=True)
  OFFICE_CHOICES = (
    ('KR', 'Korea'),
    ('JP', 'Japan'),
    ('ID', 'Indonesia'),
    ('PH', 'Philippines'),
  )
  office = models.CharField(max_length=2, choices=OFFICE_CHOICES, null=True)

  def __str__(self):
    return self.user.email


class Client(models.Model):
  client_name = models.CharField(max_length=50, unique=True)
  email = models.CharField(max_length=50, null=True)
  manager = models.ManyToManyField(Manager, related_name='client_manager')
  payment_method = models.CharField(max_length=25, null=True)
  channel_split = models.DecimalField(max_digits=3, decimal_places=2)
  sr_split = models.DecimalField(max_digits=3, decimal_places=2)
  at_split = models.DecimalField(max_digits=3, decimal_places=2)
  mc_split = models.DecimalField(max_digits=3, decimal_places=2)
  OFFICE_CHOICES = (
    ('KR', 'Korea'),
    ('JP', 'Japan'),
    ('ID', 'Indonesia'),
    ('PH', 'Philippines'),
  )
  office = models.CharField(max_length=2, choices=OFFICE_CHOICES, null=True)

  def __str__(self):
    return self.client_name


class Channel(models.Model):
  channel_id = models.CharField(max_length=50, primary_key=True)
  channel_name = models.CharField(max_length=100, unique=True)
  client = models.ForeignKey(Client, on_delete=models.CASCADE)

  def __str__(self):
    return self.channel_name


class AssetGroup(models.Model):
  group_name = models.CharField(max_length=150, unique=True)
  TYPE_CHOICES = (
    ('sr', 'Sound Recording'),
    ('at', 'Art Track'),
    ('ch', 'Channel'),
    ('etc', 'Others'),
  )
  asset_type = models.CharField(max_length=3, choices=TYPE_CHOICES, null=True)
  client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)

  def __str__(self):
    return self.group_name


class Asset(models.Model):
  asset_id = models.CharField(max_length=50, primary_key=True)
  asset_title = models.CharField(max_length=200, null=True)
  asset_labels = models.CharField(max_length=200, null=True)
  asset_channel_id = models.CharField(max_length=50, null=True)
  TYPE_CHOICES = (
    ('Sound Recording', 'Sound Recording'),
    ('Art Track', 'Art Track'),
    ('Web', 'Web'),
    ('Music Video', 'Music Video'),
    ('Television Episode', 'Television Episode'),
    ('Movie', 'Movie'),
  )
  asset_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
  custom_id = models.CharField(max_length=100, null=True)
  isrc = models.CharField(max_length=50, null=True)
  upc = models.CharField(max_length=50, null=True)
  grid = models.CharField(max_length=50, null=True)
  artist = models.CharField(max_length=300, null=True)
  album = models.CharField(max_length=200, null=True)
  label = models.CharField(max_length=100, null=True)
  OFFICE_CHOICES = (
    ('KR', 'Korea'),
    ('JP', 'Japan'),
    ('ID', 'Indonesia'),
    ('PH', 'Philippines'),
    ('CN', 'China'),
    ('UN', 'Unknown'),
    ('UD', 'Undesignated'),
  )
  office = models.CharField(max_length=2, choices=OFFICE_CHOICES, null=True)
  asset_group = models.ForeignKey(AssetGroup, on_delete=models.CASCADE, default=None, null=True)

  def __str__(self):
    return self.asset_id

  def save(self, *args, **kwargs):
    cache.clear()
    # cache.delete('profit_labels')
    # cache.delete('profit_values')
    super().save(*args, **kwargs)

  def delete(self, *args, **kwargs):
    cache.clear()
    # cache.delete('profit_labels')
    # cache.delete('profit_values')
    super().delete(*args, **kwargs)


class AssetRevenueView(models.Model):
  year_month = models.CharField(max_length=7)
  asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
  TYPE_CHOICES = (
    ('ads', 'Advertisement'),
    ('red', 'Preminum'),
    ('adt', 'Audio Tier'),
    ('etc', 'Other')
  )
  revenue_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
  adjusted = models.BooleanField()
  CMS_CHOICES = (
    ('Music', 'Music'),
    ('Other', 'Other'),
  )
  cms = models.CharField(max_length=5, choices=CMS_CHOICES)
  manual_claimed = models.BooleanField()
  promotion = models.BooleanField()
  partner_revenue = models.FloatField(default=0)
  owned_views = models.FloatField(default=0)

  class Meta:
    unique_together = ('year_month', 'asset', 'revenue_type', 'adjusted', 'cms', 'manual_claimed', 'promotion')


class PaidFeature(models.Model):
  year_month = models.CharField(max_length=7)
  channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
  amount = models.FloatField(default=0)


class ManualClaimWhiteList(models.Model):
  video_id = models.CharField(max_length=50, unique=True)
  client = models.ForeignKey(Client, on_delete=models.CASCADE)
  asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
  note = models.TextField()

  class Meta:
    unique_together = ('video_id', 'client', 'asset')

  def __str__(self):
    return self.video_id


class PromotionVideo(models.Model):
  video_id = models.CharField(max_length=50, primary_key=True)
  asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
  included_asset = models.ManyToManyField(Asset, related_name='promotion_asset')

  class Meta:
    unique_together = ('video_id', 'asset_id')

  def __str__(self):
    return self.video_id
