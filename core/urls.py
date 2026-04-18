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
]
