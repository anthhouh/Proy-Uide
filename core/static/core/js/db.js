// core/static/core/js/db.js
const DB_KEYS = {
    USUARIOS: 'bolsa_empleo_usuarios',
    EMPRESAS: 'bolsa_empleo_empresas',
    EMPLEOS: 'bolsa_empleo_empleos',
    POSTULACIONES: 'bolsa_empleo_postulaciones'
};

const DB = {
    // Inicializar bases de datos vacías si no existen
    init: () => {
        Object.values(DB_KEYS).forEach(key => {
            if (!localStorage.getItem(key)) {
                localStorage.setItem(key, JSON.stringify([]));
            }
        });
    },

    // Operaciones genéricas
    getAll: (key) => JSON.parse(localStorage.getItem(key)),
    
    save: (key, data) => localStorage.setItem(key, JSON.stringify(data)),
    
    add: (key, item) => {
        const data = DB.getAll(key);
        item.id = Date.now().toString(); // Generar ID único
        data.push(item);
        DB.save(key, data);
        return item;
    },
    
    getById: (key, id) => DB.getAll(key).find(item => item.id === id),

    update: (key, id, newData) => {
        const data = DB.getAll(key);
        const index = data.findIndex(item => item.id === id);
        if (index !== -1) {
            data[index] = { ...data[index], ...newData };
            DB.save(key, data);
            return data[index];
        }
        return null;
    },

    delete: (key, id) => {
        const data = DB.getAll(key);
        const filtered = data.filter(item => item.id !== id);
        DB.save(key, filtered);
    },

    // Consultas específicas
    getUserByEmail: (email) => DB.getAll(DB_KEYS.USUARIOS).find(u => u.email === email),
    
    getJobsByEmpresa: (empresaId) => DB.getAll(DB_KEYS.EMPLEOS).filter(j => j.empresa_id === empresaId),

    getPostulacionesByEmpleo: (empleoId) => DB.getAll(DB_KEYS.POSTULACIONES).filter(p => p.empleo_id === empleoId),
    
    getPostulacionesByUser: (userId) => DB.getAll(DB_KEYS.POSTULACIONES).filter(p => p.usuario_id === userId)
};

// Inicializar al cargar
DB.init();
