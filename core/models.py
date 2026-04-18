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
    empresa_mapa_url = models.URLField(blank=True, verbose_name="Enlace de Google Maps")
    empresa_capacidad_empleados = models.CharField(max_length=100, blank=True)
    empresa_logo = models.ImageField(upload_to='empresas_logos/', null=True, blank=True)
    social_linkedin = models.URLField(blank=True)
    social_instagram = models.CharField(max_length=255, blank=True)
    social_twitter = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username} ({self.role})"

class Resena(models.Model):
    CALIFICACION_CHOICES = [(i, i) for i in range(1, 6)]

    destinatario = models.ForeignKey(
        Profile, on_delete=models.CASCADE,
        related_name='resenas_recibidas',
        verbose_name='Perfil reseñado'
    )
    autor = models.ForeignKey(
        Profile, on_delete=models.CASCADE,
        related_name='resenas_escritas',
        verbose_name='Autor de la reseña'
    )
    calificacion = models.IntegerField(choices=CALIFICACION_CHOICES, default=5)
    comentario = models.TextField(verbose_name='Comentario')
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('destinatario', 'autor')
        ordering = ['-fecha']
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'

    def __str__(self):
        return f"Reseña de {self.autor.nombre_visualizacion or self.autor.user.username} → {self.destinatario.nombre_visualizacion or self.destinatario.user.username} ({self.calificacion}★)"

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
    ETIQUETA_CHOICES = (
        ('tecnologia', 'Tecnología e Informática'),
        ('diseño_web', 'Diseño Web / UI-UX'),
        ('administracion', 'Administración / Gestión'),
        ('ventas', 'Ventas y Marketing'),
        ('contabilidad', 'Contabilidad y Finanzas'),
        ('educacion', 'Educación / Docencia'),
        ('salud', 'Salud y Medicina'),
        ('ingenieria', 'Ingeniería y Construcción'),
        ('logistica', 'Logística y Transporte'),
        ('moda', 'Moda y Textil'),
        ('gastronomia', 'Gastronomía y Turismo'),
        ('legal', 'Legal y Jurídico'),
        ('recursos_humanos', 'Recursos Humanos'),
        ('otro', 'Otro / General'),
    )

    empresa = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ofertas')
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    modalidad = models.CharField(max_length=50, choices=MODALIDAD_CHOICES, default='presencial')
    tipo_contrato = models.CharField(max_length=50, choices=CONTRATO_CHOICES, default='tiempo_completo')
    ubicacion = models.CharField(max_length=255, blank=True)
    ubicacion_mapa_url = models.URLField(blank=True, verbose_name="Enlace Google Maps de la ubicación")
    sueldo = models.CharField(max_length=100, blank=True, verbose_name="Sueldo (opcional)")
    etiqueta = models.CharField(
        max_length=50,
        choices=ETIQUETA_CHOICES,
        default='otro',
        verbose_name='Categoría / Etiqueta'
    )
    estado = models.BooleanField(default=True, verbose_name="Oferta Activa")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.empresa.empresa_nombre}"

class ClasificacionCandidato(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Por Clasificar / Sin Revisar'),
        ('entrevista_pendiente', 'Entrevista Pendiente'),
        ('entrevistado', 'Entrevistado'),
        ('cumple', 'Cumple Requisitos'),
        ('no_cumple', 'No Cumple Requisitos'),
    )
    empresa = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='clasificaciones_hechas')
    postulante = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='mis_clasificaciones')
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='pendiente')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('empresa', 'postulante')

    def __str__(self):
        return f"{self.empresa.empresa_nombre} -> {self.postulante.user.username} ({self.estado})"

class Postulacion(models.Model):
    postulante = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='postulaciones')
    oferta = models.ForeignKey(Oferta, on_delete=models.CASCADE, related_name='aplicaciones')
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('postulante', 'oferta')

    def __str__(self):
        return f"{self.postulante.user.username} aplica a {self.oferta.titulo}"

class OfertaFoto(models.Model):
    oferta = models.ForeignKey(Oferta, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='ofertas_fotos/')
    pie = models.CharField(max_length=200, blank=True, verbose_name='Pie de foto (opcional)')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return f"Foto de {self.oferta.titulo} (#{self.id})"

# ── Modelos de Configuración y Verificación ──

class ConfiguracionPlataforma(models.Model):
    requiere_verificacion_correo = models.BooleanField(
        default=True,
        verbose_name='Exigir verificación por correo al registrarse'
    )
    
    class Meta:
        verbose_name = 'Configuración de la Plataforma'
        verbose_name_plural = 'Configuración de la Plataforma'

    def __str__(self):
        return "Ajustes Generales"

    def save(self, *args, **kwargs):
        # Asegurarse de que solo haya un registro de configuración (Singleton)
        if hasattr(self.__class__, 'objects') and self.__class__.objects.exists() and not self.pk:
            self.pk = self.__class__.objects.first().pk
        super().save(*args, **kwargs)

class CodigoVerificacion(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='codigo_verificacion')
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    def ha_expirado(self):
        from django.utils import timezone
        import datetime
        return timezone.now() > self.creado_en + datetime.timedelta(minutes=15)
        
    def __str__(self):
        return f"Código {self.codigo} para {self.user.username}"

