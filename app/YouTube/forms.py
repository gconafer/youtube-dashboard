from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.forms import ModelForm
from django_select2 import forms as s2forms

from .models import Account, Manager, AssetGroup, Client, Channel, Asset, PromotionVideo, AssetRevenueView


class ClientAddForm(ModelForm):
  class Meta:
    model = Client
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(ClientAddForm, self).__init__(*args, **kwargs)
    self.form_name = 'Add Client'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Add', 'add', css_class='btn-primary'))
    self.helper.layout = Layout(
      Row(
        Column('client_name'),
        Column('email'),
        Column('payment_method'),
        Column('office'),
        css_class='form-row',
      ),
      Row(
        Column('manager'),
        css_class='form-row'
      ),
      Row(
        Column('channel_split'),
        Column('sr_split'),
        Column('at_split'),
        Column('mc_split'),
        css_class='form-row'
      ),
    )


class ChannelAddForm(ModelForm):
  class Meta:
    model = Channel
    fields = '__all__'
    widgets = {
      'channel_name': forms.TextInput(attrs={'placeholder': 'Channel Name'}),
      'channel_id': forms.TextInput(attrs={'placeholder': 'UC.....'}),
    }

  def __init__(self, *args, **kwargs):
    super(ChannelAddForm, self).__init__(*args, **kwargs)
    self.form_name = 'Add Channel'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Add', 'add', css_class='btn-primary'))
    self.helper.layout = Layout(
      Row(
        Column('channel_name'),
        Column('channel_id'),
        css_class='form-row',
      ),
      Row(
        Column('client'),
        css_class='form-row'
      )
    )


class AssetWidget(s2forms.ModelSelect2Widget):
  search_fields = [
    "asset_id__icontains",
  ]


class MultipleAssetWidget(s2forms.ModelSelect2MultipleWidget):
  search_fields = [
    "asset_id__icontains",
  ]


class PromotionAddForm(ModelForm):
  class Meta:
    model = PromotionVideo

    fields = '__all__'
    widgets = {
      'asset': AssetWidget,
      'included_asset': MultipleAssetWidget,
    }

  def __init__(self, *args, **kwargs):
    asset_choice = Asset.objects.filter(asset_id__in=AssetRevenueView.objects.filter(promotion=True).values_list('asset_id', flat=True))
    asset_choice = asset_choice.filter(~Q(asset_id__in=PromotionVideo.objects.all().values_list('asset_id', flat=True)))
    super(PromotionAddForm, self).__init__(*args, **kwargs)
    # self.fields['video_id'].widget.attrs['rows'] = 6
    self.fields['asset'].queryset = asset_choice
    self.fields['included_asset'].queryset = Asset.objects.filter(asset_type='Sound Recording')
    self.form_name = 'Add Promotion Video'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Add', 'add', css_class='btn-primary'))


class PromotionUpdateForm(ModelForm):
  class Meta:
    model = PromotionVideo

    fields = ('video_id', 'included_asset')
    widgets = {
      'included_asset': MultipleAssetWidget,
    }

  def __init__(self, *args, **kwargs):
    super(PromotionUpdateForm, self).__init__(*args, **kwargs)
    self.fields['included_asset'].queryset = Asset.objects.filter(asset_type='Sound Recording')
    self.form_name = 'Update Promotion Video'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Update', 'Update', css_class='btn-primary'))


class AssetGroupAddForm(ModelForm):
  class Meta:
    model = AssetGroup
    fields = '__all__'
    widgets = {
      'group_name': forms.TextInput(attrs={'placeholder': 'Custom Name for Asset Group'}),
    }

  def __init__(self, *args, **kwargs):
    super(AssetGroupAddForm, self).__init__(*args, **kwargs)
    self.form_name = 'Add Asset Group'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Add', 'add', css_class='btn-primary'))
    self.helper.layout = Layout(
      Row(
        Column('group_name'),
        css_class='form-row',
      ),
      Row(
        Column('asset_type'),
        css_class='form-row'
      ),
      Row(
        Column('client'),
        css_class='form-row'
      )
    )


class LoginForm(ModelForm):  # 로그인을 제공하는 class이다.
  class Meta:
    model = Account
    widgets = {'password': forms.PasswordInput}
    fields = ['email', 'password', ]

  def __init__(self, *args, **kwargs):
    super(LoginForm, self).__init__(*args, **kwargs)
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Login', 'login', css_class='btn-primary'))


class ManagerSignUpForm(UserCreationForm):
  email = forms.EmailField(max_length=50)
  password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
  password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
  CHOICES = (('KR', 'Korea'),('JP', 'Japan'),)
  office = forms.ChoiceField(choices=CHOICES)

  class Meta:
    model = Account
    fields = ('email', 'username')

  def __init__(self, *args, **kwargs):
    super(ManagerSignUpForm, self).__init__(*args, **kwargs)
    self.form_name = 'Add Manager'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Add', 'add', css_class='btn-primary'))

  def clean_password2(self):
    password1 = self.cleaned_data.get("password1")
    password2 = self.cleaned_data.get("password2")
    if password1 and password2 and password1 != password2:
      raise forms.ValidationError("Passwords don't match")
    return password2

  def save(self, commit=True):
    user = super().save(commit=False)
    user.set_password(self.cleaned_data["password1"])
    if commit:
      user.save()
    manager = Manager.objects.create(user=user, office=self.cleaned_data.get('office'))
    return user


class AssetGroupForm(forms.ModelForm):
  class Meta:
    model = AssetGroup
    fields = '__all__'


class CrispyAssetGroupForm(AssetGroupForm):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.helper = FormHelper()
    self.helper.field_class = "selectpicker"
    self.helper.layout = Layout(
      Row(
        Column('group_name', css_class='form-group col-md-6 mb-0'),
        Column('client'),
        css_class='form-row'
      ),
      Submit('submit', 'Sign in')
    )


class AssetForm(forms.ModelForm):
  class Meta:
    model = Asset
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(AssetForm, self).__init__(*args, **kwargs)
    for key in self.fields:
      self.fields[key].required = False
    self.fields['asset_id'].required = True
    self.fields['asset_type'].required = True
    self.form_name = 'Asset'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Update', 'Update', css_class='btn-primary'))
    self.helper.layout = Layout(
      Row(Column('asset_id'), Column('asset_title'), Column('asset_labels'), Column('asset_channel_id'), css_class='form-row'),
      Row(Column('asset_type'), Column('custom_id'), Column('isrc'), Column('upc'), Column('grid'), css_class='form-row'),
      Row(Column('artist'), Column('album'), Column('label'), Column('office'), Column('asset_group'), css_class='form-row')
    )


class AddAssetForm(forms.ModelForm):
  class Meta:
    model = Asset
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(AddAssetForm, self).__init__(*args, **kwargs)
    for key in self.fields:
      self.fields[key].required = False
    self.fields['asset_id'].required = True
    self.fields['asset_type'].required = True
    self.form_name = 'Add Asset'
    self.helper = FormHelper()
    self.helper.form_method = 'POST'
    self.helper.add_input(Submit('Add', 'Add', css_class='btn-primary'))
    self.helper.layout = Layout(
      Row(Column('asset_id'), Column('asset_title'), Column('asset_labels'), Column('asset_channel_id'), css_class='form-row'),
      Row(Column('asset_type'), Column('custom_id'), Column('isrc'), Column('upc'), Column('grid'), css_class='form-row'),
      Row(Column('artist'), Column('album'), Column('label'), Column('office'), Column('asset_group'), css_class='form-row')
    )
