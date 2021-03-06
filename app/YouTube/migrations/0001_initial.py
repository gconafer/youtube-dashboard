# Generated by Django 3.0.9 on 2020-08-11 02:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_name', models.CharField(max_length=50, unique=True)),
                ('email', models.CharField(max_length=50, null=True)),
                ('payment_method', models.CharField(max_length=25, null=True)),
                ('channel_split', models.DecimalField(decimal_places=2, max_digits=3)),
                ('sr_split', models.DecimalField(decimal_places=2, max_digits=3)),
                ('at_split', models.DecimalField(decimal_places=2, max_digits=3)),
                ('mc_split', models.DecimalField(decimal_places=2, max_digits=3)),
                ('office', models.CharField(choices=[('KR', 'Korea'), ('JP', 'Japan'), ('ID', 'Indonesia'), ('PH', 'Philippines')], max_length=2, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=50, unique=True, verbose_name='email')),
                ('username', models.CharField(max_length=50, unique=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Manager',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('channel_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('channel_name', models.CharField(max_length=100, unique=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='YouTube.Client')),
            ],
        ),
        migrations.CreateModel(
            name='AssetGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_name', models.CharField(max_length=150, unique=True)),
                ('asset_type', models.CharField(choices=[('sr', 'Sound Recording'), ('at', 'Art Track'), ('ch', 'Channel'), ('etc', 'Others')], max_length=3, null=True)),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='YouTube.Client')),
            ],
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('asset_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('asset_title', models.CharField(max_length=200, null=True)),
                ('asset_labels', models.CharField(max_length=200, null=True)),
                ('asset_channel_id', models.CharField(max_length=50, null=True)),
                ('asset_type', models.CharField(choices=[('Sound Recording', 'Sound Recording'), ('Art Track', 'Art Track'), ('Web', 'Web'), ('Music Video', 'Music Video'), ('Television Episode', 'Television Episode'), ('Movie', 'Movie')], max_length=50)),
                ('custom_id', models.CharField(max_length=100, null=True)),
                ('isrc', models.CharField(max_length=50, null=True)),
                ('upc', models.CharField(max_length=50, null=True)),
                ('grid', models.CharField(max_length=50, null=True)),
                ('artist', models.CharField(max_length=300, null=True)),
                ('album', models.CharField(max_length=200, null=True)),
                ('label', models.CharField(max_length=100, null=True)),
                ('office', models.CharField(choices=[('KR', 'Korea'), ('JP', 'Japan'), ('ID', 'Indonesia'), ('PH', 'Philippines'), ('CN', 'China'), ('UN', 'Unknown'), ('UD', 'Undesignated')], max_length=2, null=True)),
                ('asset_group', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='YouTube.AssetGroup')),
            ],
        ),
        migrations.CreateModel(
            name='PromotionVideo',
            fields=[
                ('video_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='YouTube.Asset')),
                ('included_asset', models.ManyToManyField(related_name='promotion_asset', to='YouTube.Asset')),
            ],
            options={
                'unique_together': {('video_id', 'asset_id')},
            },
        ),
        migrations.CreateModel(
            name='ManualClaimWhiteList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_id', models.CharField(max_length=50, unique=True)),
                ('note', models.TextField()),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='YouTube.Asset')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='YouTube.Client')),
            ],
            options={
                'unique_together': {('video_id', 'client', 'asset')},
            },
        ),
        migrations.AddField(
            model_name='client',
            name='manager',
            field=models.ManyToManyField(related_name='client_manager', to='YouTube.Manager'),
        ),
        migrations.CreateModel(
            name='AssetRevenueView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year_month', models.CharField(max_length=7)),
                ('revenue_type', models.CharField(choices=[('ads', 'Advertisement'), ('red', 'Preminum'), ('adt', 'Audio Tier'), ('etc', 'Other')], max_length=3)),
                ('adjusted', models.BooleanField()),
                ('cms', models.CharField(choices=[('Music', 'Music'), ('M', 'Managed'), ('A', 'Affiliated')], max_length=5)),
                ('manual_claimed', models.BooleanField()),
                ('promotion', models.BooleanField()),
                ('partner_revenue', models.FloatField(default=0)),
                ('owned_views', models.FloatField(default=0)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='YouTube.Asset')),
            ],
            options={
                'unique_together': {('year_month', 'asset', 'revenue_type', 'adjusted', 'cms', 'manual_claimed', 'promotion')},
            },
        ),
    ]
