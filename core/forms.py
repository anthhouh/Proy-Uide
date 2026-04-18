from django import forms
from django.contrib.auth.models import User
from .models import Profile, Oferta

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. johndoe123'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
        }

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['nombre_visualizacion', 'cargo_titulo', 'telefono', 'foto_perfil', 'descripcion', 'hoja_de_vida']
        widgets = {
            'nombre_visualizacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. Andrés Jaramillo'}),
            'cargo_titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. Ingeniero de Software'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. +593 98 765 4321'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'hidden-file-input', 'id': 'foto_perfil_input'}),
            'hoja_de_vida': forms.FileInput(attrs={'class': 'hidden-file-input', 'id': 'cv_input', 'accept': '.pdf'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe tu perfil profesional, experiencia y habilidades...'}),
        }

    def clean_hoja_de_vida(self):
        file = self.cleaned_data.get('hoja_de_vida', False)
        if file:
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Solo se permiten archivos .PDF')
        return file

class EmpresaProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'nombre_visualizacion', 'cargo_titulo', 'telefono', 'foto_perfil', 'descripcion',
            'empresa_nombre', 'empresa_ruc', 'empresa_sitio_web', 'empresa_direccion',
            'empresa_mapa_url', 'empresa_capacidad_empleados', 'empresa_logo', 
            'social_linkedin', 'social_instagram', 'social_twitter'
        ]
        widgets = {
            'nombre_visualizacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. Elena Valdivieso'}),
            'cargo_titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. Head of People & Culture'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. +593 98 765 4321'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'hidden-file-input', 'id': 'foto_perfil_input', 'accept': 'image/*'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe a tu empresa...', 'maxlength': '600'}),
            'empresa_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. Innovatech Solutions'}),
            'empresa_ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. 1190234567001'}),
            'empresa_sitio_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.innovatech.com'}),
            'empresa_direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. Av. 10 de Agosto'}),
            'empresa_mapa_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Link a ubicación en Google Maps'}),
            'empresa_capacidad_empleados': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. 250'}),
            'empresa_logo': forms.FileInput(attrs={'class': 'hidden-file-input', 'id': 'logo_empresa_input', 'accept': 'image/*'}),
            'social_linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL LinkedIn'}),
            'social_instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario Instagram (ej. @innovatech)'}),
            'social_twitter': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario Twitter/X (ej. @innovatechloja)'}),
        }

class OfertaForm(forms.ModelForm):
    class Meta:
        model = Oferta
        fields = ['titulo', 'descripcion', 'modalidad', 'tipo_contrato', 'ubicacion', 'ubicacion_mapa_url', 'sueldo', 'etiqueta', 'estado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Desarrollador Backend Junior'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe los requisitos y responsabilidades de la vacante...'}),
            'modalidad': forms.Select(attrs={'class': 'form-control'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Loja, Ecuador o Remoto'}),
            'ubicacion_mapa_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://maps.google.com/... (enlace de Google Maps)'}),
            'sueldo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. $800 - $1200, a convenir...'}),
            'etiqueta': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
