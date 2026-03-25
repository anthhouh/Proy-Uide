from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = (
        ('postulante', 'Postulante'),
        ('empresa', 'Empresa/Ofertante'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='postulante')
    nombre_visualizacion = models.CharField(max_length=255, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    descripcion = models.TextField(blank=True)
    cargo_titulo = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    hoja_de_vida = models.FileField(upload_to='cvs/', null=True, blank=True)
    
    # --- Nuevos campos para Empresa ---
    empresa_nombre = models.CharField(max_length=255, blank=True)
    empresa_ruc = models.CharField(max_length=50, blank=True)
    empresa_sitio_web = models.URLField(blank=True)
    empresa_direccion = models.CharField(max_length=255, blank=True)
    empresa_capacidad_empleados = models.CharField(max_length=100, blank=True)
    empresa_logo = models.ImageField(upload_to='empresas_logos/', null=True, blank=True)
    social_linkedin = models.URLField(blank=True)
    social_instagram = models.CharField(max_length=255, blank=True)
    social_twitter = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username} ({self.role})"

class Resena(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='resenas')
    autor = models.CharField(max_length=255)
    empresa = models.CharField(max_length=255, blank=True)
    calificacion = models.IntegerField(default=5)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.autor} para {self.profile.user.username}"

class Oferta(models.Model):
    MODALIDAD_CHOICES = (
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido'),
        ('presencial', 'Presencial'),
    )
    CONTRATO_CHOICES = (
        ('tiempo_completo', 'Tiempo Completo'),
        ('medio_tiempo', 'Medio Tiempo'),
        ('freelance', 'Freelance/Contrato'),
        ('pasantia', 'Pasantía/Prácticas'),
    )
    
    empresa = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ofertas')
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    modalidad = models.CharField(max_length=50, choices=MODALIDAD_CHOICES, default='presencial')
    tipo_contrato = models.CharField(max_length=50, choices=CONTRATO_CHOICES, default='tiempo_completo')
    ubicacion = models.CharField(max_length=255, blank=True)
    sueldo = models.CharField(max_length=100, blank=True, verbose_name="Sueldo (opcional)")
    estado = models.BooleanField(default=True, verbose_name="Oferta Activa")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.empresa.empresa_nombre}"
