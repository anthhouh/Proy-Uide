from django.shortcuts import render

def index(request):
    return render(request, 'core/index.html')

def registro(request):
    return render(request, 'core/registro.html')

def login(request):
    return render(request, 'core/login.html')

def dashboard(request):
    return render(request, 'core/dashboard.html')

def empleo(request):
    return render(request, 'core/empleo.html')

def buscar_empleos(request):
    return render(request, 'core/buscar_empleos.html')
