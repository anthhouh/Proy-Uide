// core/static/core/js/auth.js

const Auth = {
    SESSION_KEY: 'bolsa_empleo_sesion',

    registrar: (datos) => {
        const { rol, nombre, email, password } = datos;
        
        // Validar si el email ya existe
        if (DB.getUserByEmail(email)) {
            return { error: 'El correo ya está registrado.' };
        }

        // Crear usuario
        const newUser = DB.add(DB_KEYS.USUARIOS, {
            nombre, email, password, rol
        });

        // Si es empresa, guardar el registro adicional
        if (rol === 'empresa') {
            DB.add(DB_KEYS.EMPRESAS, {
                usuario_id: newUser.id,
                nombre_empresa: nombre,
                direccion: '',
                contacto: email
            });
        }

        return Auth.login(email, password);
    },

    login: (email, password) => {
        const user = DB.getUserByEmail(email);
        if (!user || user.password !== password) {
            return { error: 'Credenciales inválidas.' };
        }

        // Crear sesión
        const sessionData = {
            id: user.id,
            nombre: user.nombre,
            rol: user.rol,
            email: user.email
        };
        
        sessionStorage.setItem(Auth.SESSION_KEY, JSON.stringify(sessionData));
        return { success: true, user: sessionData };
    },

    logout: () => {
        sessionStorage.removeItem(Auth.SESSION_KEY);
        window.location.href = '/login/';
    },

    getSession: () => {
        const s = sessionStorage.getItem(Auth.SESSION_KEY);
        return s ? JSON.parse(s) : null;
    },

    isAuthenticated: () => {
        return !!Auth.getSession();
    }
};
