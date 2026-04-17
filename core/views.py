from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Profile, Oferta, ClasificacionCandidato, Postulacion
from .forms import UserEditForm, ProfileEditForm, EmpresaProfileEditForm, OfertaForm

def index(request):
    user_profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None

    if user_profile and user_profile.role == 'empresa':
        postulantes_ids = Postulacion.objects.filter(oferta__empresa=user_profile).values_list('postulante_id', flat=True).distinct()
        postulantes = Profile.objects.filter(id__in=postulantes_ids).select_related('user')
        clasificaciones = ClasificacionCandidato.objects.filter(empresa=user_profile)
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
        mis_ofertas = Oferta.objects.filter(empresa=user_profile).order_by('-fecha_publicacion')
            
        return render(request, 'core/index_empresa.html', {
            'columnas': columnas,
            'mis_ofertas': mis_ofertas
        })

    query = request.GET.get('q', '')
    ubicacion = request.GET.get('u', '')
    
    ofertas = Oferta.objects.filter(estado=True)
    if query:
        ofertas = ofertas.filter(titulo__unaccent__icontains=query)
    if ubicacion:
        ofertas = ofertas.filter(ubicacion__unaccent__icontains=ubicacion)
        
    ofertas = ofertas.order_by('-fecha_publicacion')[:6]
    
    # Extraer postulaciones del usuario si es postulante
    mis_postulaciones = []
    postulaciones_ids = []
    if user_profile and user_profile.role == 'postulante':
        mis_postulaciones = Postulacion.objects.filter(postulante=user_profile).select_related('oferta', 'oferta__empresa').order_by('-fecha_postulacion')
        postulaciones_ids = list(mis_postulaciones.values_list('oferta_id', flat=True))

    return render(request, 'core/index.html', {
        'ofertas': ofertas,
        'q': query,
        'u': ubicacion,
        'mis_postulaciones': mis_postulaciones,
        'postulaciones_ids': postulaciones_ids
    })

def registro(request):
    if request.method == 'POST':
        nombre = request.POST.get('name')
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'postulante')
        
        if not username:
            messages.error(request, 'El nombre de usuario es obligatorio.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Ese nombre de usuario ya está en uso. Elige otro.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'El correo ya está registrado.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user, role=role, nombre_visualizacion=nombre)
            # Iniciar sesión automáticamente
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
    
    return render(request, 'core/registro.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Buscar el usuario por email para obtener su username real
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')
            
    return render(request, 'core/login.html')

def user_logout(request):
    auth_logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    context = {}
    if request.user.profile.role == 'empresa':
        postulantes_ids = Postulacion.objects.filter(oferta__empresa=request.user.profile).values_list('postulante_id', flat=True).distinct()
        postulantes = Profile.objects.filter(id__in=postulantes_ids).select_related('user')
        clasificaciones = ClasificacionCandidato.objects.filter(empresa=request.user.profile)
        clasif_dict = {c.postulante_id: c.estado for c in clasificaciones}
        
        postulantes_pendientes = []
        for p in postulantes:
            if clasif_dict.get(p.id, 'pendiente') == 'pendiente':
                postulantes_pendientes.append(p)
                
        context['postulantes_pendientes'] = postulantes_pendientes
        
        # Calculate stats for the dashboard
        context['stats_empresa'] = {
            'pendientes': len(postulantes_pendientes),
            'entrevistas': list(clasif_dict.values()).count('entrevista_pendiente') + list(clasif_dict.values()).count('entrevistado'),
            'cumplen': list(clasif_dict.values()).count('cumple')
        }
        
    return render(request, 'core/dashboard.html', context)

def empleo(request):
    return render(request, 'core/empleo.html')

def buscar_empleos(request):
    query = request.GET.get('q', '')
    ubicacion = request.GET.get('u', '')
    
    ofertas = Oferta.objects.filter(estado=True)
    if query:
        ofertas = ofertas.filter(titulo__unaccent__icontains=query)
    if ubicacion:
        ofertas = ofertas.filter(ubicacion__unaccent__icontains=ubicacion)
        
    ofertas = ofertas.order_by('-fecha_publicacion')

    postulaciones_ids = []
    user_profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    if user_profile and user_profile.role == 'postulante':
        postulaciones_ids = list(Postulacion.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True))

    return render(request, 'core/buscar_empleos.html', {
        'ofertas': ofertas,
        'q': query,
        'u': ubicacion,
        'postulaciones_ids': postulaciones_ids,
        'total_vacantes': ofertas.count()
    })

@login_required
def perfil(request):
    profile_id = request.GET.get('id')
    if profile_id:
        profile = get_object_or_404(Profile, id=profile_id)
    else:
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
def editar_oferta(request, oferta_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'empresa':
        messages.error(request, 'No tienes permiso para editar ofertas.')
        return redirect('dashboard')
        
    oferta = get_object_or_404(Oferta, id=oferta_id, empresa=profile)
    
    if request.method == 'POST':
        form = OfertaForm(request.POST, instance=oferta)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Vacante actualizada exitosamente!')
            return redirect('editar_perfil')
    else:
        form = OfertaForm(instance=oferta)
        
    return render(request, 'core/editar_oferta.html', {'form': form, 'oferta': oferta})

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
        
        # Validar que el postulante realmente ha aplicado a una oferta de esta empresa
        if not Postulacion.objects.filter(oferta__empresa=request.user.profile, postulante=postulante).exists():
            return JsonResponse({'error': 'El candidato no ha postulado a tu empresa'}, status=403)
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

@login_required
def aplicar_oferta(request, oferta_id):
    if request.user.profile.role != 'postulante':
        messages.error(request, 'Solo los postulantes pueden aplicar a ofertas.')
        return redirect('index')
        
    oferta = get_object_or_404(Oferta, id=oferta_id)
    postulacion, created = Postulacion.objects.get_or_create(postulante=request.user.profile, oferta=oferta)
    
    if created:
        messages.success(request, f'¡Has postulado exitosamente a {oferta.titulo}!')
    else:
        messages.info(request, 'Ya habías postulado a esta oferta anteriormente.')
        
    return redirect('index')


