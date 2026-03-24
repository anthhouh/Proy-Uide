from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from .forms import UserEditForm, ProfileEditForm

def index(request):
    return render(request, 'core/index.html')

def registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'postulante')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'El correo ya está registrado.')
        else:
            user = User.objects.create_user(username=email, email=email, password=password)
            Profile.objects.create(user=user, role=role, nombre_visualizacion=nombre)
            user = authenticate(username=email, password=password)
            if user:
                auth_login(request, user)
                return redirect('dashboard')
    
    return render(request, 'core/registro.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Credenciales incorrectas')
            
    return render(request, 'core/login.html')

def user_logout(request):
    auth_logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')

def empleo(request):
    return render(request, 'core/empleo.html')

def buscar_empleos(request):
    return render(request, 'core/buscar_empleos.html')

@login_required
def perfil(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'core/perfil.html', {'profile': profile})

@login_required
def editar_perfil(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('perfil')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)
        
    return render(request, 'core/editar_perfil.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })
