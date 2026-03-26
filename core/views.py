from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Profile, Oferta, ClasificacionCandidato
from .forms import UserEditForm, ProfileEditForm, EmpresaProfileEditForm, OfertaForm

def index(request):
    if request.user.is_authenticated and request.user.profile.role == 'empresa':
        postulantes = Profile.objects.filter(role='postulante').select_related('user')
        clasificaciones = ClasificacionCandidato.objects.filter(empresa=request.user.profile)
        clasif_dict = {c.postulante_id: c.estado for c in clasificaciones}
        
        columnas = {
            'pendiente': [],
            'entrevista_pendiente': [],
            'entrevistado': [],
            'cumple': [],
            'no_cumple': []
        }
        
        for p in postulantes:
            estado = clasif_dict.get(p.id, 'pendiente')
            p.estado_actual = estado
            columnas[estado].append(p)
            
        return render(request, 'core/index_empresa.html', {
            'columnas': columnas
        })

    query = request.GET.get('q', '')
    ubicacion = request.GET.get('u', '')
    
    ofertas = Oferta.objects.filter(estado=True)
    if query:
        ofertas = ofertas.filter(titulo__icontains=query)
    if ubicacion:
        ofertas = ofertas.filter(ubicacion__icontains=ubicacion)
        
    ofertas = ofertas.order_by('-fecha_publicacion')[:6]
    return render(request, 'core/index.html', {
        'ofertas': ofertas,
        'q': query,
        'u': ubicacion
    })

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
    
    # Seleccionar formulario y plantilla base según el rol
    if profile.role == 'empresa':
        ProfileFormClass = EmpresaProfileEditForm
        template_name = 'core/editar_perfil_empresa.html'
        ofertas = Oferta.objects.filter(empresa=profile).order_by('-fecha_publicacion')
    else:
        ProfileFormClass = ProfileEditForm
        template_name = 'core/editar_perfil.html'
        ofertas = None

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileFormClass(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('perfil')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileFormClass(instance=profile)
        
    return render(request, template_name, {
        'user_form': user_form,
        'profile_form': profile_form,
        'ofertas': ofertas
    })

@login_required
def eliminar_cv(request):
    if request.method == 'POST':
        profile = getattr(request.user, 'profile', None)
        if profile and profile.hoja_de_vida:
            profile.hoja_de_vida.delete(save=True) # Deletes the file and sets field to empty
            messages.success(request, 'Hoja de vida eliminada exitosamente.')
        else:
            messages.error(request, 'No se pudo eliminar la hoja de vida o no existe.')
    return redirect('editar_perfil')

@login_required
def crear_oferta(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'empresa':
        messages.error(request, 'No tienes permiso para crear ofertas.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = OfertaForm(request.POST)
        if form.is_valid():
            oferta = form.save(commit=False)
            oferta.empresa = profile
            oferta.save()
            messages.success(request, '¡Vacante publicada exitosamente!')
            return redirect('editar_perfil')
    else:
        form = OfertaForm()
        
    return render(request, 'core/crear_oferta.html', {'form': form})

@login_required
def eliminar_oferta(request, oferta_id):
    if request.method == 'POST':
        oferta = get_object_or_404(Oferta, id=oferta_id, empresa=request.user.profile)
        oferta.delete()
        messages.success(request, "Vacante eliminada exitosamente.")
    return redirect('editar_perfil')

@login_required
@require_POST
def actualizar_estado_candidato(request):
    if request.user.profile.role != 'empresa':
        return JsonResponse({'error': 'No autorizado'}, status=403)
        
    try:
        data = json.loads(request.body)
        postulante_id = data.get('postulante_id')
        nuevo_estado = data.get('estado')
        
        if not postulante_id or not nuevo_estado:
            return JsonResponse({'error': 'Faltan datos'}, status=400)
            
        postulante = get_object_or_404(Profile, id=postulante_id, role='postulante')
        
        clasificacion, created = ClasificacionCandidato.objects.get_or_create(
            empresa=request.user.profile,
            postulante=postulante,
            defaults={'estado': nuevo_estado}
        )
        
        if not created:
            clasificacion.estado = nuevo_estado
            clasificacion.save()
            
        return JsonResponse({'success': True, 'estado': nuevo_estado})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


