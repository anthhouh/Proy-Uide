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
