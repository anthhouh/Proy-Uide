from django import forms
from django.contrib.auth.models import User
from .models import Profile

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
