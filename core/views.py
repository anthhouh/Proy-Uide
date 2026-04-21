from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.mail import send_mail
import json
import random
from django.utils import timezone
from .models import Profile, Oferta, ClasificacionCandidato, Postulacion, Resena, OfertaFoto, ConfiguracionPlataforma, EmpleoGuardado, EmpleoDescartado, Notificacion, BloqueoPostulacion
from datetime import timedelta
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
        terms = query.split()
        q_obj = Q()
        for term in terms:
            q_obj &= (
                Q(titulo__unaccent__icontains=term) |
                Q(descripcion__unaccent__icontains=term) |
                Q(etiqueta__unaccent__icontains=term) |
                Q(ubicacion__unaccent__icontains=term) |
                Q(empresa__empresa_nombre__unaccent__icontains=term) |
                Q(empresa__nombre_visualizacion__unaccent__icontains=term)
            )
        ofertas = ofertas.filter(q_obj).distinct()
    if ubicacion:
        ofertas = ofertas.filter(ubicacion__unaccent__icontains=ubicacion)

    recomendaciones = []
    if user_profile and user_profile.role == 'postulante':
        descartadas = EmpleoDescartado.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True)
        ofertas = ofertas.exclude(id__in=descartadas)
        
        # Calcular recomendaciones
        if user_profile.preferencias_etiquetas:
            tags = [t.strip() for t in user_profile.preferencias_etiquetas.split(',') if t.strip()]
            if tags:
                tiene_preferencias = True
                recomendaciones = Oferta.objects.filter(estado=True, etiqueta__in=tags).exclude(id__in=descartadas).order_by('-fecha_publicacion')[:3]
        
    ofertas = ofertas.order_by('-fecha_publicacion')[:6]
    
    # Extraer postulaciones del usuario si es postulante
    mis_postulaciones = []
    postulaciones_ids = []
    guardadas_ids = []
    if user_profile and user_profile.role == 'postulante':
        qs_post = Postulacion.objects.filter(postulante=user_profile).select_related('oferta', 'oferta__empresa').order_by('-fecha_postulacion')
        mis_postulaciones = list(qs_post)
        postulaciones_ids = [p.oferta_id for p in mis_postulaciones]
        guardadas_ids = list(EmpleoGuardado.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True))
        clasificaciones = ClasificacionCandidato.objects.filter(postulante=user_profile)
        clasif_dict = {c.empresa_id: c.estado for c in clasificaciones}
        for app in mis_postulaciones:
            estado = clasif_dict.get(app.oferta.empresa_id, 'pendiente')
            app.puede_retirar = (estado == 'pendiente')

    # Etiquetas aleatorias para explorar
    etiquetas_todas = [e for e in Oferta.ETIQUETA_CHOICES if e[0] != 'otro']
    etiquetas_aleatorias = random.sample(etiquetas_todas, min(4, len(etiquetas_todas)))

    return render(request, 'core/index.html', {
        'ofertas': ofertas,
        'q': query,
        'u': ubicacion,
        'mis_postulaciones': mis_postulaciones,
        'postulaciones_ids': postulaciones_ids,
        'guardadas_ids': guardadas_ids,
        'recomendaciones': recomendaciones,
        'tiene_preferencias': locals().get('tiene_preferencias', False),
        'explorar_etiquetas': etiquetas_aleatorias
    })

def registro(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        nombre   = request.POST.get('name')
        username = request.POST.get('username', '').strip()
        email    = request.POST.get('email')
        password = request.POST.get('password')
        role     = request.POST.get('role', 'postulante')
        
        if not username:
            messages.error(request, 'El nombre de usuario es obligatorio.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Ese nombre de usuario ya está en uso. Elige otro.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'El correo ya está registrado.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user, role=role, nombre_visualizacion=nombre)
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('index')
    # Redirect to homepage with modal auto-open
    return redirect('/?auth=registro')

def user_login(request):
    # Si ya está autenticado, ir directo al dashboard
    if request.user.is_authenticated:
        return redirect('index')

    next_url = request.GET.get('next', '')

    # Si viene de @login_required (?next=...), mostrar aviso como toast
    if request.method == 'GET' and next_url:
        messages.warning(request, 'Debes iniciar sesión para acceder a esa sección.')

    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '')

        # Buscar el usuario por email
        user_obj = User.objects.filter(email=email).first()
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
        else:
            user = None

        if user is not None:
            auth_login(request, user)
            return redirect(next_url) if next_url else redirect('index')
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')

    # Redirect GET requests to homepage with modal
    return redirect('/?auth=login')

def user_logout(request):
    auth_logout(request)
    return redirect('index')

@require_POST
def ajax_login(request):
    """AJAX endpoint for modal login."""
    email    = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    next_url = request.POST.get('next', '')

    user_obj = User.objects.filter(email=email).first()
    user = authenticate(request, username=user_obj.username, password=password) if user_obj else None

    if user is not None:
        if getattr(user, 'profile', None) and user.profile.requiere_2fa:
            codigo_generado = str(random.randint(100000, 999999))
            try:
                send_mail(
                    'Código de Seguridad para Iniciar Sesión',
                    f'Hola {user.username},\n\nTu código de verificación de dos pasos es: {codigo_generado}\n\nIngresa este código para acceder a tu cuenta. El código expira en 5 minutos.\n\nSaludos,\nEl equipo',
                    None,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                return JsonResponse({'ok': False, 'error': f"Error de correo: {str(e)[:100]}"})
                
            request.session['login_2fa'] = {
                'user_id': user.id,
                'codigo': codigo_generado,
                'timestamp': timezone.now().timestamp(),
                'next_url': next_url
            }
            # Siempre imprimimos en consola para facilitar pruebas locales
            print(f"\n=========================================")
            print(f"CÓDIGO 2FA LOGIN PARA {user.email}: {codigo_generado}")
            print(f"=========================================\n")
            
            return JsonResponse({'ok': True, 'requires_2fa': True, 'email': user.email})

        auth_login(request, user)
        return JsonResponse({'ok': True, 'redirect': next_url or '/'})
    return JsonResponse({'ok': False, 'error': 'Correo o contraseña incorrectos.'}, status=400)

@require_POST
def ajax_verificar_login_2fa(request):
    """AJAX endpoint to verify 2FA code during login."""
    codigo = request.POST.get('code', '').strip()
    
    pendiente = request.session.get('login_2fa')
    if not pendiente:
        return JsonResponse({'ok': False, 'error': 'No hay un inicio de sesión pendiente o expiró.'}, status=400)
        
    tiempo_creado = pendiente.get('timestamp', 0)
    if timezone.now().timestamp() > tiempo_creado + 300: # 5 minutos
        del request.session['login_2fa']
        return JsonResponse({'ok': False, 'error': 'El código ha expirado. Estaba configurado para durar 5 minutos.'}, status=400)
        
    if pendiente.get('codigo') != codigo:
        return JsonResponse({'ok': False, 'error': 'Código incorrecto. Verifica e intenta de nuevo.'}, status=400)
        
    # Login successful
    user = User.objects.filter(id=pendiente['user_id']).first()
    if user:
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        next_url = pendiente.get('next_url', '')
        del request.session['login_2fa']
        return JsonResponse({'ok': True, 'redirect': next_url or '/'})
    return JsonResponse({'ok': False, 'error': 'El usuario ya no existe.'}, status=400)

@require_POST
def ajax_registro(request):
    """AJAX endpoint for modal registration."""
    nombre   = request.POST.get('name', '').strip()
    username = request.POST.get('username', '').strip()
    email    = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    role     = request.POST.get('role', 'postulante')

    if not username:
        return JsonResponse({'ok': False, 'error': 'El nombre de usuario es obligatorio.'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'ok': False, 'error': 'Ese nombre de usuario ya está en uso.'}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({'ok': False, 'error': 'El correo ya está registrado.'}, status=400)

    config = ConfiguracionPlataforma.objects.first()
    requires_verification = config.requiere_verificacion_correo if config else True
    
    if requires_verification:
        codigo_generado = str(random.randint(100000, 999999))
        
        try:
            send_mail(
                'Tu código de verificación - Empleos Loja',
                f'Hola {nombre},\n\nTu código de verificación es: {codigo_generado}\n\nIngresa este código para activar tu cuenta. El código expira en 15 minutos.\n\nSaludos,\nEl equipo de Empleos Loja',
                None,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            # En producción, devolvemos el error a la pantalla
            return JsonResponse({'ok': False, 'error': f"Error de correo: {str(e)[:100]}... Revisa credenciales SMTP."})
            
        # Guardar en sesión en lugar de la Base de Datos
        request.session['registro_pendiente'] = {
            'username': username,
            'email': email,
            'password': password,
            'nombre': nombre,
            'role': role,
            'codigo': codigo_generado,
            'timestamp': timezone.now().timestamp()
        }
        
        # Siempre imprimimos en consola para facilitar pruebas locales
        print(f"\n=========================================")
        print(f"CÓDIGO DE VERIFICACIÓN PARA {email}: {codigo_generado}")
        print(f"=========================================\n")
        
        return JsonResponse({'ok': True, 'requires_verification': True, 'username': username})
    else:
        # Si no requiere verificación, creamos directo el usuario oficial
        user = User.objects.create_user(username=username, email=email, password=password)
        emp_name = nombre if role == 'empresa' else ''
        Profile.objects.create(user=user, role=role, nombre_visualizacion=nombre, empresa_nombre=emp_name)
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return JsonResponse({'ok': True, 'redirect': '/'})

@require_POST
def ajax_verificar_codigo(request):
    """AJAX endpoint to verify email code."""
    username = request.POST.get('username', '').strip()
    codigo   = request.POST.get('code', '').strip()
    
    if not username or not codigo:
        return JsonResponse({'ok': False, 'error': 'Faltan datos.'}, status=400)
        
    pendiente = request.session.get('registro_pendiente')
    if not pendiente or pendiente.get('username') != username:
        return JsonResponse({'ok': False, 'error': 'No hay un registro pendiente o la sesión expiró.'}, status=400)
        
    tiempo_creado = pendiente.get('timestamp', 0)
    if timezone.now().timestamp() > tiempo_creado + 900: # 15 minutos = 900 segundos
        del request.session['registro_pendiente']
        return JsonResponse({'ok': False, 'error': 'El código ha expirado. Por favor, regístrate de nuevo.'}, status=400)
        
    if pendiente.get('codigo') != codigo:
        return JsonResponse({'ok': False, 'error': 'Código incorrecto. Verifica el número e intenta nuevamente.'}, status=400)
        
    # El código es correcto. ¡Crear permanentemente el usuario!
    user = User.objects.create_user(
        username=pendiente['username'], 
        email=pendiente['email'], 
        password=pendiente['password']
    )
    emp_name_2 = pendiente['nombre'] if pendiente['role'] == 'empresa' else ''
    Profile.objects.create(
        user=user, 
        role=pendiente['role'], 
        nombre_visualizacion=pendiente['nombre'],
        empresa_nombre=emp_name_2
    )
    
    # Limpiar sesión temporal y loguear
    del request.session['registro_pendiente']
    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return JsonResponse({'ok': True, 'redirect': '/'})

@require_POST
def ajax_solicitar_reset(request):
    """Paso 1: Valida correo, genera código en sesión, envía email."""
    email = request.POST.get('email', '').strip()
    if not email:
        return JsonResponse({'ok': False, 'error': 'El correo es obligatorio.'}, status=400)
    
    user = User.objects.filter(email=email).first()
    if not user:
        # Por seguridad y UX en apps chicas indicamos que no existe.
        return JsonResponse({'ok': False, 'error': 'No existe una cuenta registrada con este correo.'}, status=404)
        
    codigo_generado = str(random.randint(100000, 999999))
    
    try:
        send_mail(
            'Recuperación de Contraseña - Empleos Loja',
            f'Hola {user.profile.nombre_visualizacion},\n\nTu código para restablecer tu contraseña es: {codigo_generado}\n\nIngresa este código en la plataforma. El código expira en 15 minutos.\n\nSi no fuiste tú, ignora este correo.\n\nSaludos,\nEl equipo de Empleos Loja',
            None,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f"Error de correo SMTP: {str(e)[:100]}"})
        
    request.session['reset_pendiente'] = {
        'email': email,
        'codigo': codigo_generado,
        'timestamp': timezone.now().timestamp(),
        'verificado': False
    }
    
    # Siempre imprimimos en consola para facilitar pruebas locales
    print(f"\n======== RECUPERACIÓN =========")
    print(f"CÓDIGO PARA {email}: {codigo_generado}")
    print(f"===============================\n")
    
    return JsonResponse({'ok': True, 'email': email})

@require_POST
def ajax_verificar_reset(request):
    """Paso 2: Valida el código de 6 dígitos para la recuperación."""
    email = request.POST.get('email', '').strip()
    codigo = request.POST.get('code', '').strip()
    
    pendiente = request.session.get('reset_pendiente')
    if not pendiente or pendiente.get('email') != email:
        return JsonResponse({'ok': False, 'error': 'Sesión expirada. Por favor, solicita un código nuevo.'}, status=400)
        
    tiempo_creado = pendiente.get('timestamp', 0)
    if timezone.now().timestamp() > tiempo_creado + 900: # 15 min
        del request.session['reset_pendiente']
        return JsonResponse({'ok': False, 'error': 'El código ha expirado. Solicita uno nuevo.'}, status=400)
        
    if pendiente.get('codigo') != codigo:
        return JsonResponse({'ok': False, 'error': 'Código incorrecto. Verifica el número e intenta nuevamente.'}, status=400)
        
    # Validado exitosamente, autorizamos el cambio
    request.session['reset_pendiente']['verificado'] = True
    request.session.modified = True
    
    return JsonResponse({'ok': True})

@require_POST
def ajax_cambiar_password(request):
    """Paso 3: Realiza el cambio físico de la contraseña despues de verificar."""
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    
    if len(password) < 6:
        return JsonResponse({'ok': False, 'error': 'La contraseña debe tener al menos 6 caracteres.'}, status=400)
        
    pendiente = request.session.get('reset_pendiente')
    if not pendiente or pendiente.get('email') != email or not pendiente.get('verificado'):
        return JsonResponse({'ok': False, 'error': 'No estás autorizado para cambiar la contraseña o la sesión expiró.'}, status=403)
        
    user = User.objects.filter(email=email).first()
    if user:
        user.set_password(password)
        user.save()
        
    # Limpiamos la caché de recuperación
    if 'reset_pendiente' in request.session:
        del request.session['reset_pendiente']
        
    return JsonResponse({'ok': True})

@login_required
def dashboard(request):
    if request.user.profile.role != 'empresa':
        messages.info(request, 'El panel de control es exclusivo para empresas.')
        return redirect('index')
        
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

@login_required
@require_POST
def toggle_guardar_empleo(request, oferta_id):
    if request.user.profile.role != 'postulante':
        return JsonResponse({'error': 'Solo los postulantes pueden guardar ofertas'}, status=403)
        
    oferta = get_object_or_404(Oferta, id=oferta_id)
    guardado, created = EmpleoGuardado.objects.get_or_create(postulante=request.user.profile, oferta=oferta)
    
    if created:
        return JsonResponse({'status': 'guardado', 'message': 'Oferta guardada correctamente.'})
    else:
        guardado.delete()
        return JsonResponse({'status': 'desguardado', 'message': 'Oferta eliminada de guardados.'})

@login_required
def ofertas_guardadas(request):
    if request.user.profile.role != 'postulante':
        messages.error(request, 'Solo los postulantes tienen ofertas guardadas.')
        return redirect('index')
        
    empleos = EmpleoGuardado.objects.filter(postulante=request.user.profile).select_related('oferta', 'oferta__empresa')
    
    return render(request, 'core/ofertas_guardadas.html', {
        'empleos_guardados': empleos
    })

@login_required
@require_POST
def descartar_oferta(request, oferta_id):
    if request.user.profile.role != 'postulante':
        return JsonResponse({'error': 'Solo los postulantes pueden descartar ofertas'}, status=403)
        
    oferta = get_object_or_404(Oferta, id=oferta_id)
    EmpleoDescartado.objects.get_or_create(postulante=request.user.profile, oferta=oferta)
    
    # Si estaba guardada, la eliminamos de guardadas por coherencia
    EmpleoGuardado.objects.filter(postulante=request.user.profile, oferta=oferta).delete()
    
    return JsonResponse({'status': 'descartado', 'message': 'Oferta descartada exitosamente.'})

@login_required
@require_POST
def restaurar_oferta(request, oferta_id):
    if request.user.profile.role != 'postulante':
        return JsonResponse({'error': 'Solo postulantes'}, status=403)
    EmpleoDescartado.objects.filter(postulante=request.user.profile, oferta_id=oferta_id).delete()
    return JsonResponse({'status': 'restaurado'})

@login_required
@require_POST
def refrescar_recomendaciones(request):
    user_profile = request.user.profile
    if user_profile.role != 'postulante':
        return JsonResponse({'error': 'Solo postulantes'}, status=403)
        
    recomendaciones = []
    if user_profile.preferencias_etiquetas:
        tags = [t.strip() for t in user_profile.preferencias_etiquetas.split(',') if t.strip()]
        if tags:
            descartadas = EmpleoDescartado.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True)
            recomendaciones = Oferta.objects.filter(estado=True, etiqueta__in=tags).exclude(id__in=descartadas).order_by('?')[:3]
            
    guardadas_ids = list(EmpleoGuardado.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True))
    
    return render(request, 'core/_recomendaciones_partial.html', {
        'recomendaciones': recomendaciones,
        'guardadas_ids': guardadas_ids
    })

@login_required
def preferencias(request):
    if request.user.profile.role != 'postulante':
        messages.error(request, 'Solo los postulantes tienen preferencias.')
        return redirect('index')
        
    profile = request.user.profile
    if request.method == 'POST':
        tags = request.POST.getlist('etiquetas')
        profile.preferencias_etiquetas = ','.join(tags)
        profile.save()
        messages.success(request, 'Tus preferencias han sido actualizadas.')
        return redirect('preferencias')
        
    descartadas = EmpleoDescartado.objects.filter(postulante=profile).select_related('oferta', 'oferta__empresa')
    # Use Oferta.ETIQUETA_CHOICES
    from .models import Oferta
    etiquetas_choices = Oferta.ETIQUETA_CHOICES
    user_tags = [t.strip() for t in profile.preferencias_etiquetas.split(',')] if profile.preferencias_etiquetas else []
    
    return render(request, 'core/preferencias.html', {
        'descartadas': descartadas,
        'etiquetas_choices': etiquetas_choices,
        'user_tags': user_tags,
    })

def empleo(request):
    return render(request, 'core/empleo.html')

def buscar_empleos(request):
    query = request.GET.get('q', '').strip()
    cat = request.GET.get('cat', '')
    mod = request.GET.get('mod', '')

    ofertas = Oferta.objects.filter(estado=True).select_related('empresa')

    if query:
        ofertas = ofertas.filter(
            Q(titulo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(ubicacion__icontains=query) |
            Q(empresa__empresa_nombre__icontains=query) |
            Q(empresa__nombre_visualizacion__icontains=query)
        ).distinct()

    if cat:
        ofertas = ofertas.filter(etiqueta=cat)
    if mod:
        ofertas = ofertas.filter(modalidad=mod)

    user_profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    
    if user_profile and user_profile.role == 'postulante':
        descartadas = EmpleoDescartado.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True)
        ofertas = ofertas.exclude(id__in=descartadas)

    ofertas = ofertas.order_by('-fecha_publicacion')

    postulaciones_ids = []
    guardadas_ids = []
    user_profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    if user_profile and user_profile.role == 'postulante':
        postulaciones_ids = list(Postulacion.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True))
        guardadas_ids = list(EmpleoGuardado.objects.filter(postulante=user_profile).values_list('oferta_id', flat=True))

    ofertas = list(ofertas)
    total = len(ofertas)

    return render(request, 'core/buscar_empleos.html', {
        'ofertas': ofertas,
        'q': query,
        'cat': cat,
        'mod': mod,
        'postulaciones_ids': postulaciones_ids,
        'guardadas_ids': guardadas_ids,
        'total_vacantes': total
    })

@login_required
def perfil(request):
    profile_id = request.GET.get('id')
    if profile_id:
        profile = get_object_or_404(Profile, id=profile_id)
    else:
        profile, created = Profile.objects.get_or_create(user=request.user)

    viewer = getattr(request.user, 'profile', None)
    is_own_profile = (viewer == profile)

    # ── Lógica de permiso para reseñar ──────────────────────────────────────
    puede_resenar = False
    ya_reseno = False
    resena_propia = None

    if viewer and not is_own_profile:
        if viewer.role == 'empresa' and profile.role == 'postulante':
            # Empresa puede reseñar si el postulante aplicó a alguna de sus ofertas
            puede_resenar = Postulacion.objects.filter(
                oferta__empresa=viewer, postulante=profile
            ).exists()
        elif viewer.role == 'postulante' and profile.role == 'empresa':
            # Postulante puede reseñar si aplicó a alguna oferta de esa empresa
            puede_resenar = Postulacion.objects.filter(
                postulante=viewer, oferta__empresa=profile
            ).exists()

        if puede_resenar:
            resena_propia = Resena.objects.filter(autor=viewer, destinatario=profile).first()
            ya_reseno = resena_propia is not None

    resenas = Resena.objects.filter(destinatario=profile).select_related('autor', 'autor__user')
    promedio = None
    if resenas.exists():
        total = sum(r.calificacion for r in resenas)
        promedio = round(total / resenas.count(), 1)

    return render(request, 'core/perfil.html', {
        'profile': profile,
        'is_own_profile': is_own_profile,
        'puede_resenar': puede_resenar,
        'ya_reseno': ya_reseno,
        'resena_propia': resena_propia,
        'resenas': resenas,
        'promedio': promedio,
    })


@login_required
@require_POST
def crear_resena(request, profile_id):
    """Crea o actualiza una reseña del usuario autenticado al perfil indicado."""
    destinatario = get_object_or_404(Profile, id=profile_id)
    autor = request.user.profile

    # Validaciones de seguridad
    if autor == destinatario:
        messages.error(request, 'No puedes reseñarte a ti mismo.')
        return redirect('perfil')

    # Verificar que existe interacción
    tiene_permiso = False
    if autor.role == 'empresa' and destinatario.role == 'postulante':
        tiene_permiso = Postulacion.objects.filter(
            oferta__empresa=autor, postulante=destinatario
        ).exists()
    elif autor.role == 'postulante' and destinatario.role == 'empresa':
        tiene_permiso = Postulacion.objects.filter(
            postulante=autor, oferta__empresa=destinatario
        ).exists()

    if not tiene_permiso:
        messages.error(request, 'No tienes permiso para reseñar este perfil.')
        return redirect(f'/perfil/?id={profile_id}')

    calificacion = int(request.POST.get('calificacion', 5))
    comentario = request.POST.get('comentario', '').strip()

    if not comentario:
        messages.error(request, 'El comentario no puede estar vacío.')
        return redirect(f'/perfil/?id={profile_id}')

    if not (1 <= calificacion <= 5):
        messages.error(request, 'La calificación debe ser entre 1 y 5.')
        return redirect(f'/perfil/?id={profile_id}')

    resena, created = Resena.objects.update_or_create(
        autor=autor,
        destinatario=destinatario,
        defaults={'calificacion': calificacion, 'comentario': comentario}
    )

    if created:
        messages.success(request, '¡Reseña publicada exitosamente!')
    else:
        messages.success(request, 'Tu reseña ha sido actualizada.')

    # ── Notificar al destinatario de la reseña ──
    autor_nombre = autor.nombre_visualizacion or autor.user.username
    estrellas = '⭐' * calificacion
    Notificacion.objects.create(
        destinatario=destinatario.user,
        tipo='nueva_resena',
        mensaje=f'{autor_nombre} te dejó una reseña de {calificacion} {estrellas}.',
        link=f'/perfil/?id={destinatario.id}'
    )

    return redirect(f'/perfil/?id={profile_id}')


@login_required
@require_POST
def eliminar_resena(request, resena_id):
    """Elimina una reseña, solo si el usuario actual es el autor."""
    resena = get_object_or_404(Resena, id=resena_id)
    if resena.autor != request.user.profile:
        messages.error(request, 'No tienes permiso para eliminar esta reseña.')
        return redirect('perfil')
    destinatario_id = resena.destinatario.id
    resena.delete()
    messages.success(request, 'Reseña eliminada.')
    return redirect(f'/perfil/?id={destinatario_id}')

@login_required
def editar_perfil(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if profile.role == 'empresa':
        ProfileFormClass = EmpresaProfileEditForm
        template_name = 'core/editar_perfil_empresa.html'
        ofertas = Oferta.objects.filter(empresa=profile).order_by('-fecha_publicacion')
    else:
        ProfileFormClass = ProfileEditForm
        template_name = 'core/editar_perfil.html'
        ofertas = None

    if request.method == 'POST':
        # Solo guardamos profile_form
        profile_form = ProfileFormClass(request.POST, request.FILES, instance=profile)
        
        # Para compatibilidad si todavia hay forms enviando user_form
        user_form = UserEditForm(request.POST, instance=request.user)
        if request.POST.get('username') or request.POST.get('email'):
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('perfil')
        else:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Perfil corporativo actualizado exitosamente.')
                return redirect('perfil')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileFormClass(instance=profile)
        
    return render(request, template_name, {
        'user_form': user_form,
        'profile_form': profile_form,
        'ofertas': ofertas
    })

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserEditForm

@login_required
def configuracion_privacidad(request):
    if request.method == 'POST':
        if 'user_update' in request.POST:
            user_form = UserEditForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Información de cuenta actualizada.')
                return redirect('configuracion')
        elif 'password_update' in request.POST:
            user_form = UserEditForm(instance=request.user)
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Contraseña actualizada exitosamente.')
                return redirect('configuracion')
        elif 'security_update' in request.POST:
            pwd_confirm = request.POST.get('password_confirm', '')
            if not request.user.check_password(pwd_confirm):
                messages.error(request, 'Contraseña incorrecta. No se guardaron los cambios de seguridad.')
                return redirect('configuracion')
                
            requiere_2fa_val = request.POST.get('requiere_2fa') == '1'
            if request.user.profile.requiere_2fa != requiere_2fa_val:
                request.user.profile.requiere_2fa = requiere_2fa_val
                request.user.profile.save()
                if requiere_2fa_val:
                    messages.success(request, 'Verificación en dos pasos activada. Asegúrate de recordar tu contraseña.')
                else:
                    messages.success(request, 'Verificación en dos pasos desactivada.')
            return redirect('configuracion')
    else:
        user_form = UserEditForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
        
    return render(request, 'core/configuracion.html', {
        'user_form': user_form,
        'password_form': password_form,
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
            # Guardar fotos de galeria (max 8)
            fotos = request.FILES.getlist('galeria_fotos')
            for i, foto in enumerate(fotos[:8]):
                OfertaFoto.objects.create(oferta=oferta, imagen=foto, orden=i)
            messages.success(request, '¡Vacante publicada exitosamente!')
            return redirect('index')
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
            # Eliminar fotos marcadas
            eliminar_ids = request.POST.getlist('eliminar_foto')
            if eliminar_ids:
                OfertaFoto.objects.filter(id__in=eliminar_ids, oferta=oferta).delete()
            # Agregar nuevas fotos
            fotos_nuevas = request.FILES.getlist('galeria_fotos')
            existentes = oferta.fotos.count()
            for i, foto in enumerate(fotos_nuevas[:max(0, 8 - existentes)]):
                OfertaFoto.objects.create(oferta=oferta, imagen=foto, orden=existentes + i)
            messages.success(request, '¡Vacante actualizada exitosamente!')
            return redirect('index')
    else:
        form = OfertaForm(instance=oferta)
        
    return render(request, 'core/editar_oferta.html', {
        'form': form,
        'oferta': oferta,
        'fotos': oferta.fotos.all(),
    })

@login_required
def eliminar_oferta(request, oferta_id):
    if request.method == 'POST':
        oferta = get_object_or_404(Oferta, id=oferta_id, empresa=request.user.profile)
        oferta.delete()
        messages.success(request, "Vacante eliminada exitosamente.")
    return redirect('index')

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
    perfil_postulante = request.user.profile

    # ── Verificar bloqueo de 15 días ──
    bloqueo = BloqueoPostulacion.objects.filter(postulante=perfil_postulante, oferta=oferta).first()
    if bloqueo:
        dias_transcurridos = (timezone.now() - bloqueo.fecha_bloqueo).days
        dias_restantes = 15 - dias_transcurridos
        if dias_restantes > 0:
            messages.error(request, f'No puedes postular a esta oferta aún. Podrás volver a intentarlo en {dias_restantes} día(s).')
            return redirect('detalle_oferta', oferta_id=oferta.id)
        else:
            # Bloqueo expirado: limpiarlo para permitir nueva postulación
            bloqueo.delete()

    if oferta.max_postulantes is not None and oferta.aplicaciones.count() >= oferta.max_postulantes:
        messages.error(request, 'No puedes aplicar. Esta oferta ha alcanzado el límite máximo de postulantes permitidos.')
        return redirect('detalle_oferta', oferta_id=oferta.id)

    postulacion, created = Postulacion.objects.get_or_create(postulante=perfil_postulante, oferta=oferta)

    if created:
        messages.success(request, f'¡Has postulado exitosamente a {oferta.titulo}!')
        # ── Notificar a la empresa ──
        nombre_postulante = perfil_postulante.nombre_visualizacion or request.user.username
        Notificacion.objects.create(
            destinatario=oferta.empresa.user,
            tipo='nueva_postulacion',
            mensaje=f'📨 {nombre_postulante} aplicó a tu vacante "{oferta.titulo}".',
            link='/'
        )
    else:
        messages.info(request, 'Ya habías postulado a esta oferta anteriormente.')

    # Redirect back to the detail page after applying
    next_url = request.GET.get('next', 'index')
    return redirect(next_url)


def detalle_oferta(request, oferta_id):
    """Public-facing job detail page."""
    oferta = get_object_or_404(Oferta, id=oferta_id, estado=True)
    fotos = oferta.fotos.all()
    
    ya_postulo = False
    guardada = False
    puede_retirar = False
    user_profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    if user_profile and user_profile.role == 'postulante':
        ya_postulo = Postulacion.objects.filter(postulante=user_profile, oferta=oferta).exists()
        guardada = EmpleoGuardado.objects.filter(postulante=user_profile, oferta=oferta).exists()
        if ya_postulo:
            clasif = ClasificacionCandidato.objects.filter(empresa=oferta.empresa, postulante=user_profile).first()
            if not clasif or clasif.estado == 'pendiente':
                puede_retirar = True
                
    limite_alcanzado = False
    if oferta.max_postulantes is not None and oferta.aplicaciones.count() >= oferta.max_postulantes:
        limite_alcanzado = True
    
    return render(request, 'core/detalle_oferta.html', {
        'oferta': oferta,
        'fotos': fotos,
        'ya_postulo': ya_postulo,
        'puede_retirar': puede_retirar,
        'guardada': guardada,
        'limite_alcanzado': limite_alcanzado,
        'user_profile': user_profile,
    })


@login_required
@require_POST
def retirar_postulacion(request, oferta_id):
    if request.user.profile.role != 'postulante':
        return JsonResponse({'status': 'error', 'message': 'Acción no permitida.'}, status=403)
        
    oferta = get_object_or_404(Oferta, id=oferta_id)
    postulacion = Postulacion.objects.filter(postulante=request.user.profile, oferta=oferta).first()
    
    if not postulacion:
        return JsonResponse({'status': 'error', 'message': 'No has postulado a esta oferta.'}, status=400)
        
    clasificacion = ClasificacionCandidato.objects.filter(empresa=oferta.empresa, postulante=request.user.profile).first()
    if clasificacion and clasificacion.estado != 'pendiente':
        return JsonResponse({'status': 'error', 'message': 'No puedes retirar tu postulación porque la empresa ya evaluó tu perfil.'}, status=400)
    
    postulacion.delete()
    return JsonResponse({'status': 'retirado'})

# ── Manejadores de errores HTTP personalizados ──
def error_404(request, exception=None):
    """Página 404 personalizada con ventana flotante."""
    from django.shortcuts import render as _render
    return _render(request, '404.html', status=404)

def error_500(request):
    """Página 500 personalizada con ventana flotante."""
    from django.shortcuts import render as _render
    return _render(request, '500.html', status=500)

def error_403(request, exception=None):
    """Página 403 personalizada con ventana flotante."""
    from django.shortcuts import render as _render
    return _render(request, '403.html', status=403)


# ── Centro de Notificaciones ──

@login_required
@require_POST
def ajax_enviar_resultados_kanban(request):
    """Envía notificaciones a todos los candidatos clasificados (no pendientes).
    Si el estado es 'no_cumple', elimina la postulación y registra un bloqueo de 15 días."""
    if request.user.profile.role != 'empresa':
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    empresa = request.user.profile
    mensajes_estado = {
        'entrevista_pendiente': '📅 La empresa "{empresa}" te ha seleccionado para una entrevista. ¡Prepárate!',
        'cumple': '✅ ¡Buenas noticias! La empresa "{empresa}" ha indicado que cumples los requisitos para la vacante.',
        'no_cumple': '❌ La empresa "{empresa}" ha revisado tu postulación e indica que no cumples los requisitos en esta ocasión. Podrás volver a postular en 15 días.',
    }

    # Obtener todos los candidatos clasificados de esta empresa
    clasificaciones = ClasificacionCandidato.objects.filter(
        empresa=empresa
    ).exclude(estado='pendiente').select_related('postulante__user')

    total_enviadas = 0
    for clasif in clasificaciones:
        postulante = clasif.postulante
        estado = clasif.estado
        plantilla = mensajes_estado.get(estado)
        if not plantilla:
            continue

        mensaje = plantilla.format(empresa=empresa.empresa_nombre or empresa.user.username)

        # Crear notificación (evitando duplicados recientes — últimas 24h)
        hace_24h = timezone.now() - timedelta(hours=24)
        ya_notificado = Notificacion.objects.filter(
            destinatario=postulante.user,
            tipo='resultado_kanban',
            mensaje=mensaje,
            fecha__gte=hace_24h
        ).exists()

        if not ya_notificado:
            Notificacion.objects.create(
                destinatario=postulante.user,
                tipo='resultado_kanban',
                mensaje=mensaje,
                link='/buscar_empleos/'
            )
            total_enviadas += 1

        # Si no cumple: eliminar postulación y registrar bloqueo
        if estado == 'no_cumple':
            # Buscar la postulación del candidato a cualquier oferta de esta empresa
            postulaciones = Postulacion.objects.filter(
                postulante=postulante,
                oferta__empresa=empresa
            )
            for post in postulaciones:
                BloqueoPostulacion.objects.get_or_create(
                    postulante=postulante,
                    oferta=post.oferta,
                    defaults={}
                )
                post.delete()
            # Limpiar clasificación
            clasif.delete()

    return JsonResponse({'ok': True, 'enviadas': total_enviadas})


@login_required
def ajax_notificaciones(request):
    """Devuelve las notificaciones del usuario."""
    base_qs = Notificacion.objects.filter(destinatario=request.user)
    no_leidas = base_qs.filter(leida=False).count()
    notifs = base_qs.order_by('-fecha')[:30]
    data = [
        {
            'id': n.id,
            'tipo': n.tipo,
            'mensaje': n.mensaje,
            'leida': n.leida,
            'link': n.link,
            'fecha': n.fecha.strftime('%d/%m/%Y %H:%M'),
        }
        for n in notifs
    ]
    return JsonResponse({'ok': True, 'notificaciones': data, 'no_leidas': no_leidas})


@login_required
@require_POST
def ajax_marcar_notificaciones(request):
    """Marca una o todas las notificaciones como leídas."""
    data = json.loads(request.body)
    notif_id = data.get('id')  # si None → marca todas
    if notif_id:
        Notificacion.objects.filter(id=notif_id, destinatario=request.user).update(leida=True)
    else:
        Notificacion.objects.filter(destinatario=request.user, leida=False).update(leida=True)
    return JsonResponse({'ok': True})


# ── Eliminación de Cuenta ──

@login_required
@require_POST
def ajax_solicitar_eliminacion(request):
    """Paso 1: verificar contraseña y enviar OTP al correo para eliminar la cuenta."""
    password = request.POST.get('password', '')
    
    if not request.user.check_password(password):
        return JsonResponse({'ok': False, 'error': 'La contraseña ingresada es incorrecta.'})
    
    # Generar OTP de 6 dígitos
    codigo = str(random.randint(100000, 999999))
    
    # Guardar en sesión con timestamp
    request.session['delete_account_otp'] = {
        'codigo': codigo,
        'timestamp': timezone.now().timestamp(),
        'user_id': request.user.id,
    }
    
    # Imprimir en consola para pruebas locales
    print(f"\n========== CÓDIGO ELIMINACIÓN DE CUENTA ==========")
    print(f"Usuario: {request.user.username} ({request.user.email})")
    print(f"Código OTP: {codigo}")
    print(f"==================================================\n")
    
    # Enviar por correo
    try:
        send_mail(
            '⚠️ Código de verificación para eliminar tu cuenta',
            (
                f'Hola {request.user.username},\n\n'
                f'Recibimos una solicitud para eliminar permanentemente tu cuenta.\n\n'
                f'Tu código de verificación es: {codigo}\n\n'
                f'Este código expirará en 10 minutos.\n\n'
                f'Si no realizaste esta solicitud, ignora este mensaje y cambia tu contraseña inmediatamente.\n\n'
                f'Saludos,\nEl equipo'
            ),
            None,
            [request.user.email],
            fail_silently=False,
        )
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error al enviar el correo: {str(e)[:120]}'})
    
    return JsonResponse({'ok': True})


@login_required
@require_POST
def ajax_verificar_eliminacion(request):
    """Paso 2: verificar el OTP y eliminar la cuenta definitivamente."""
    codigo_ingresado = request.POST.get('codigo', '').strip()
    
    otp_data = request.session.get('delete_account_otp')
    
    if not otp_data:
        return JsonResponse({'ok': False, 'error': 'No hay una solicitud de eliminación activa. Vuelve a intentarlo.'})
    
    # Verificar que el OTP pertenece al usuario actual
    if otp_data.get('user_id') != request.user.id:
        return JsonResponse({'ok': False, 'error': 'Sesión inválida.'})
    
    # Verificar expiración (10 minutos)
    tiempo_transcurrido = timezone.now().timestamp() - otp_data.get('timestamp', 0)
    if tiempo_transcurrido > 600:
        del request.session['delete_account_otp']
        return JsonResponse({'ok': False, 'error': 'El código ha expirado. Por favor, solicita uno nuevo.'})
    
    # Verificar el código
    if codigo_ingresado != otp_data.get('codigo'):
        return JsonResponse({'ok': False, 'error': 'Código incorrecto. Inténtalo de nuevo.'})
    
    # Todo correcto: eliminar la cuenta
    user = request.user
    auth_logout(request)
    user.delete()
    
    return JsonResponse({'ok': True, 'redirect': '/'})
