from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('empleo/', views.empleo, name='empleo'),
    path('buscar_empleos/', views.buscar_empleos, name='buscar_empleos'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/eliminar-cv/', views.eliminar_cv, name='eliminar_cv'),
    path('perfil/crear-oferta/', views.crear_oferta, name='crear_oferta'),
    path('oferta/editar/<int:oferta_id>/', views.editar_oferta, name='editar_oferta'),
    path('oferta/eliminar/<int:oferta_id>/', views.eliminar_oferta, name='eliminar_oferta'),
    path('oferta/aplicar/<int:oferta_id>/', views.aplicar_oferta, name='aplicar_oferta'),
    path('oferta/<int:oferta_id>/', views.detalle_oferta, name='detalle_oferta'),
    path('api/candidato/estado/', views.actualizar_estado_candidato, name='actualizar_estado_candidato'),
    path('perfil/<int:profile_id>/resena/', views.crear_resena, name='crear_resena'),
    path('resena/<int:resena_id>/eliminar/', views.eliminar_resena, name='eliminar_resena'),
    path('ajax/login/', views.ajax_login, name='ajax_login'),
    path('ajax/registro/', views.ajax_registro, name='ajax_registro'),
    path('ajax/verificar/', views.ajax_verificar_codigo, name='ajax_verificar'),
    path('ajax/reset/solicitar/', views.ajax_solicitar_reset, name='ajax_solicitar_reset'),
    path('ajax/reset/verificar/', views.ajax_verificar_reset, name='ajax_verificar_reset'),
    path('ajax/reset/cambiar/', views.ajax_cambiar_password, name='ajax_cambiar_password'),
]
