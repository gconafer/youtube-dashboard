from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms import LoginForm
from .models import Client, Manager, Asset, PromotionVideo


def signin(request):
  if request.method == "POST":
    form = LoginForm(request.POST)
    email = request.POST['email']
    password = request.POST['password']
    user = authenticate(email=email, password=password)
    if user is not None:
      login(request, user)
      return redirect('home')
    else:
      return HttpResponse('로그인 실패. 다시 시도 해보세요.')
  else:
    form = LoginForm()
    return render(request, 'login.html', {'form': form})


def signout(request):  # logout 기능
  logout(request)  # logout을 수행한다.
  return redirect('login')


@login_required
def clients(request):
  if request.user.is_superuser:
    client = Client.objects.all()
  else:
    office = request.user.manager.office
    client = Client.objects.filter(office=office)
  context = {"clients": client}
  return render(request, "client.html", context)


@login_required
def promotions(request):
  promotions = PromotionVideo.objects.all()
  context = {"promotions": promotions}
  return render(request, "promotion.html", context)


@login_required
def assets(request):
  context = {"assets": 'client'}
  return render(request, "asset/assets.html", context)


@csrf_exempt
def success(request):
  thing = request.POST.getlist('asset_id')
  for asset_id in thing:
    asset = Asset.objects.get(asset_id=asset_id)
    asset.office = request.POST['office']
    asset.save()
  context = {'context': 'b'}
  return redirect('office_asset', office='UD')


@login_required
def managers(request):
  manager = Manager.objects.all()
  context = {"managers": manager}
  return render(request, "manager.html", context)
