from django.contrib import admin
from django.contrib.auth.models import Group

from YouTube.models import Account, Client, Manager, Asset, Channel, AssetGroup, AssetRevenueView, ManualClaimWhiteList, PromotionVideo, PaidFeature


class AssetRevenueViewAdmin(admin.ModelAdmin):
  list_display = ['year_month', 'asset', 'revenue_type', 'adjusted', 'manual_claimed', 'promotion', 'partner_revenue', 'owned_views']


#
admin.site.register(Account)
admin.site.register(Client)
admin.site.register(Manager)
admin.site.register(Asset)
admin.site.register(Channel)
admin.site.register(AssetGroup)
admin.site.register(ManualClaimWhiteList)
admin.site.register(PromotionVideo)
admin.site.register(PaidFeature)
admin.site.register(AssetRevenueView, AssetRevenueViewAdmin)
#
admin.site.unregister(Group)
