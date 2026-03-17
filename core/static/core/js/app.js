// core/static/core/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navbar dinámico
    const navLinks = document.getElementById('navLinks');
    const user = Auth.getSession();

    if (user) {
        navLinks.innerHTML = `
            <span style="margin-right: 15px;">Hola, ${user.nombre} (${user.rol})</span>
            <a href="/dashboard/" class="btn btn-primary">Mi Panel</a>
            <a href="#" id="logoutBtn" style="color: #de350b;">Salir</a>
        `;
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            Auth.logout();
        });
    } else {
        navLinks.innerHTML = `
            <a href="/login/">Iniciar Sesión</a>
            <a href="/registro/" class="btn btn-primary">Registrarse</a>
        `;
    }

    const path = window.location.pathname;

    // 2. Lógica de Registro (/registro/)
    if (path === '/registro/') {
        const regForm = document.getElementById('registerForm');
        
        regForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            const rol = document.getElementById('regRole').value;
            const nombre = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;

            if (password.length < 6) {
                alert('La contraseña debe tener al menos 6 caracteres.');
                return;
            }

            const res = Auth.registrar({ rol, nombre, email, password });
            
            if (res.error) {
                alert(res.error);
            } else {
                window.location.href = '/dashboard/';
            }
        });

        // Cambiar placeholder de nombre si es empresa
        const roleSelect = document.getElementById('regRole');
        const lblName = document.getElementById('lblRegName');
        const inputName = document.getElementById('regName');
        
        roleSelect?.addEventListener('change', (e) => {
            if (e.target.value === 'empresa') {
                lblName.textContent = 'Nombre de la Empresa';
                inputName.placeholder = 'Mi Empresa S.A.';
            } else {
                lblName.textContent = 'Nombre Completo';
                inputName.placeholder = 'Ingresa tu nombre';
            }
        });
    }

    // 3. Lógica de Login (/login/)
    if (path === '/login/') {
        const loginForm = document.getElementById('loginForm');
        const loginError = document.getElementById('loginError');

        loginForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;

            const res = Auth.login(email, password);
            if (res.error) {
                loginError.textContent = res.error;
                loginError.style.display = 'block';
            } else {
                window.location.href = '/dashboard/';
            }
        });
    }

    // 4. Lógica de Index (Buscar Empleos)
    if (path === '/') {
        const loadJobs = (query = '') => {
            const jobListContainer = document.getElementById('jobList');
            let empleos = DB.getAll(DB_KEYS.EMPLEOS);
            
            if (query) {
                const q = query.toLowerCase();
                empleos = empleos.filter(job => 
                    job.titulo.toLowerCase().includes(q) || 
                    job.categoria.toLowerCase().includes(q) || 
                    job.ubicacion.toLowerCase().includes(q)
                );
            }

            if (empleos.length === 0) {
                jobListContainer.innerHTML = '<p>No se encontraron ofertas laborales.</p>';
                return;
            }

            jobListContainer.innerHTML = empleos.map(job => {
                const empresaRaw = DB.getAll(DB_KEYS.EMPRESAS).find(e => e.usuario_id === job.empresa_user_id) || {};
                return `
                <div class="job-card">
                    <h3>${job.titulo}</h3>
                    <div class="job-meta">
                        <span>🏢 ${empresaRaw.nombre_empresa || 'Empresa Anónima'}</span><br>
                        <span>📍 ${job.ubicacion}</span> • <span>📂 ${job.categoria}</span>
                    </div>
                    <button class="btn btn-secondary view-job-btn" data-id="${job.id}">Ver Detalles</button>
                </div>
                `;
            }).join('');

            // Agregar eventos
            document.querySelectorAll('.view-job-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    sessionStorage.setItem('current_job_id', e.target.dataset.id);
                    window.location.href = '/empleo/';
                });
            });
        };

        // Cargar empleos iniciales
        loadJobs();

        // Buscador
        const searchBtn = document.getElementById('searchBtn');
        const searchInput = document.getElementById('searchInput');

        searchBtn?.addEventListener('click', () => {
            loadJobs(searchInput.value);
        });

        searchInput?.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') loadJobs(searchInput.value);
        });
    }

    // 5. Dashboard Logic
    if (path === '/dashboard/') {
        if (!user) {
            window.location.href = '/login/';
            return;
        }

        const dashActions = document.getElementById('dashActions');
        const myJobListContainer = document.getElementById('myJobList');
        const sectionTitle = document.getElementById('sectionTitle');
        const dashTitle = document.getElementById('dashTitle');

        if (user.rol === 'empresa') {
            dashTitle.textContent = 'Panel de Empresa';
            sectionTitle.textContent = 'Mis Ofertas Publicadas';
            
            dashActions.innerHTML = `
                <button class="btn btn-primary" id="btnNewJobModal">Nueva Oferta</button>
            `;

            // Setup Modal for New Job
            const modal = document.getElementById('newJobModal');
            document.getElementById('btnNewJobModal').addEventListener('click', () => {
                modal.style.display = 'block';
            });
            modal.querySelector('.close-btn').addEventListener('click', () => {
                modal.style.display = 'none';
            });

            // Handle Job Save
            const newJobForm = document.getElementById('newJobForm');
            newJobForm?.addEventListener('submit', (e) => {
                e.preventDefault();
                const nuevoEmpleo = {
                    titulo: document.getElementById('jobTitle').value,
                    descripcion: document.getElementById('jobDesc').value,
                    categoria: document.getElementById('jobCategory').value,
                    ubicacion: document.getElementById('jobLocation').value,
                    empresa_user_id: user.id,
                    fecha: new Date().toISOString()
                };
                
                DB.add(DB_KEYS.EMPLEOS, nuevoEmpleo);
                modal.style.display = 'none';
                newJobForm.reset();
                renderEmpresaJobs();
            });

            // Applicants Modal setup
            const appModal = document.getElementById('applicantsModal');
            document.getElementById('closeApplicants').addEventListener('click', () => {
                 appModal.style.display = 'none';
            });

            // Render jobs
            const renderEmpresaJobs = () => {
                const empleos = DB.getAll(DB_KEYS.EMPLEOS).filter(j => j.empresa_user_id === user.id);
                if (empleos.length === 0) {
                    myJobListContainer.innerHTML = '<p>No has publicado ofertas aún.</p>';
                    return;
                }

                myJobListContainer.innerHTML = empleos.map(job => {
                    const postulatesCount = DB.getPostulacionesByEmpleo(job.id).length;
                    return `
                    <div class="job-card">
                        <h3>${job.titulo}</h3>
                        <p class="job-meta">POSTULANTES: ${postulatesCount}</p>
                        <button class="btn btn-secondary btn-applicants" data-id="${job.id}">Ver Postulantes</button>
                        <button class="btn btn-secondary" style="border-color:var(--error-color); color:var(--error-color);" onclick="deleteJob('${job.id}')">Eliminar</button>
                    </div>
                    `;
                }).join('');

                // View Applicants
                document.querySelectorAll('.btn-applicants').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const jId = e.target.dataset.id;
                        const postuls = DB.getPostulacionesByEmpleo(jId);
                        const list = document.getElementById('applicantsList');
                        
                        if (postuls.length === 0) {
                            list.innerHTML = '<li>No hay postulantes.</li>';
                        } else {
                            list.innerHTML = postuls.map(p => {
                                const applicant = DB.getAll(DB_KEYS.USUARIOS).find(u => u.id === p.usuario_id);
                                return `<li><strong>${applicant.nombre}</strong> (${applicant.email}) - Postuló: ${new Date(p.fecha).toLocaleDateString()}</li>`;
                            }).join('');
                        }
                        appModal.style.display = 'block';
                    });
                });
            };

            // Globals function to be called from inline onclick hack just above
            window.deleteJob = (id) => {
                if (confirm('¿Seguro quieres eliminar esta oferta?')) {
                    DB.delete(DB_KEYS.EMPLEOS, id);
                    renderEmpresaJobs();
                }
            };

            renderEmpresaJobs();

        } else if (user.rol === 'postulante') {
            dashTitle.textContent = 'Mi Perfil';
            sectionTitle.textContent = 'Mis Postulaciones';

            // Ver tareas aplicadas
            const postulates = DB.getPostulacionesByUser(user.id);
            if (postulates.length === 0) {
                myJobListContainer.innerHTML = '<p>No te has postulado a ninguna oferta todavía.</p>';
                return;
            }

            myJobListContainer.innerHTML = postulates.map(p => {
                const job = DB.getById(DB_KEYS.EMPLEOS, p.empleo_id);
                if(!job) return ''; // By safety if deleted
                return `
                <div class="job-card">
                    <h3>${job.titulo}</h3>
                    <p class="job-meta">Postulante desde: ${new Date(p.fecha).toLocaleDateString()}</p>
                    <button class="btn btn-secondary view-job-btn" data-id="${job.id}">Ver Oferta</button>
                </div>
                `;
            }).join('');

            document.querySelectorAll('.view-job-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    sessionStorage.setItem('current_job_id', e.target.dataset.id);
                    window.location.href = '/empleo/';
                });
            });
        }
    }

    // 6. Vista de Detalle de Empleo (/empleo/)
    if (path === '/empleo/') {
        const jobId = sessionStorage.getItem('current_job_id');
        const container = document.getElementById('jobDetailContainer');

        if (!jobId) {
            container.innerHTML = '<p>No se ha seleccionado ninguna oferta.</p>';
            return;
        }

        const job = DB.getById(DB_KEYS.EMPLEOS, jobId);
        if (!job) {
            container.innerHTML = '<p>La oferta ya no existe.</p>';
            return;
        }

        const empresa = DB.getAll(DB_KEYS.EMPRESAS).find(e => e.usuario_id === job.empresa_user_id) || {};

        container.innerHTML = `
            <div class="job-header">
                <h2>${job.titulo}</h2>
                <div class="job-meta">
                    <span>🏢 ${empresa.nombre_empresa || 'Empresa'}</span>
                    <span>📍 ${job.ubicacion}</span>
                    <span>📂 ${job.categoria}</span>
                </div>
            </div>
            <div class="job-body">
                <h3>Descripción del Puesto</h3>
                <p style="white-space: pre-wrap; margin-top:1rem;">${job.descripcion}</p>
            </div>
            <div style="margin-top: 2rem;" id="applySection">
                <!-- Se mostrará botón aplicar o mensaje de requerido login -->
            </div>
        `;

        const applySection = document.getElementById('applySection');
        
        if (!user) {
            applySection.innerHTML = `<p>Para postularte debes <a href="/login/">Iniciar Sesión</a> o <a href="/registro/">Registrarte</a>.</p>`;
        } else if (user.rol === 'postulante') {
            // Checkear si ya se ha postulado
            const userPostuls = DB.getPostulacionesByUser(user.id);
            const yaPostulado = userPostuls.some(p => p.empleo_id === jobId);

            if (yaPostulado) {
                applySection.innerHTML = `<button class="btn btn-secondary" disabled>Ya te has postulado a este empleo</button>`;
            } else {
                applySection.innerHTML = `<button class="btn btn-primary" id="btnApply">Postularme Ahora</button>`;
                document.getElementById('btnApply').addEventListener('click', () => {
                    DB.add(DB_KEYS.POSTULACIONES, {
                        usuario_id: user.id,
                        empleo_id: jobId,
                        fecha: new Date().toISOString()
                    });
                    alert('¡Postulación exitosa!');
                    window.location.reload();
                });
            }
        } else {
            applySection.innerHTML = `<p>Las Empresas no pueden postular empresas a ofertas de trabajo.</p>`;
        }
    }

});
