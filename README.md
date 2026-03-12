# SRS – Sistema de Bolsa de Empleo de Loja

## 1. Introducción

### 1.1 Propósito
El propósito de este documento es describir los requerimientos del sistema Bolsa de Empleo Loja, una plataforma web que permitirá conectar empresas que ofrecen trabajo con personas que buscan empleo en la ciudad de Loja.

### 1.2 Alcance
El sistema permitirá:
- Publicar ofertas de empleo.
- Buscar trabajos disponibles.
- Registrar usuarios (empresas y postulantes).
- Postular a empleos en línea.

La plataforma estará disponible como aplicación web accesible desde navegadores.

### 1.3 Definiciones
- **Postulante**: Persona que busca empleo.
- **Empresa**: Organización que publica ofertas laborales.
- **Oferta laboral**: Publicación de un puesto de trabajo disponible.

## 2. Descripción General

### 2.1 Perspectiva del sistema
El sistema será una plataforma web centralizada donde empresas publican vacantes y los usuarios pueden buscar y postular a ellas.

### 2.2 Tipos de usuarios
- **Administrador**
  - Gestiona usuarios
  - Modera publicaciones
  - Elimina contenido inapropiado
- **Empresa**
  - Publica ofertas de trabajo
  - Gestiona postulaciones
- **Postulante**
  - Crea perfil
  - Busca empleos
  - Aplica a ofertas

## 3. Requerimientos Funcionales

- **RF1 – Registro de usuarios**: El sistema debe permitir que los usuarios se registren como Empresa o Postulante.
- **RF2 – Inicio de sesión**: El sistema debe permitir a los usuarios autenticarse mediante correo y contraseña.
- **RF3 – Publicación de empleos**: Las empresas deben poder crear ofertas laborales, editarlas y eliminarlas.
- **RF4 – Búsqueda de empleo**: Los postulantes deben poder buscar empleos por categoría, empresa, tipo de trabajo y ubicación.
- **RF5 – Postulación**: Los usuarios deben poder postularse a una oferta laboral enviando su información.
- **RF6 – Gestión de postulaciones**: Las empresas podrán ver la lista de candidatos que aplicaron a su oferta.

## 4. Requerimientos No Funcionales

- **RNF1 – Seguridad**: El sistema debe proteger los datos de los usuarios mediante autenticación y almacenamiento seguro.
- **RNF2 – Disponibilidad**: La plataforma debe estar disponible 24/7.
- **RNF3 – Usabilidad**: La interfaz debe ser simple y fácil de usar.
- **RNF4 – Rendimiento**: El sistema debe responder a las solicitudes en menos de 3 segundos.

## 5. Requerimientos de Base de Datos

El sistema debe almacenar:

- **Usuarios**: id_usuario, nombre, email, contraseña, tipo_usuario.
- **Empresas**: id_empresa, nombre_empresa, dirección, contacto.
- **Empleos**: id_empleo, título, descripción, empresa, fecha_publicación.
- **Postulaciones**: id_postulación, usuario, empleo, fecha.

## 6. Restricciones
- El sistema será desarrollado como aplicación web.
- Usará base de datos relacional.
- Compatible con navegadores modernos.
