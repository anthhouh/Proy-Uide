// core/static/core/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navbar dinámico
    const navLinks = document.getElementById('navLinks');
    const user = Auth.getSession();

    if (user) {
        navLinks.innerHTML = `
            <a href="/">Inicio</a>
            <a href="/buscar_empleos/">Buscar empleos</a>
            <span style="margin-left:auto; margin-right: 15px; color:var(--text-muted);">Hola, ${user.nombre}</span>
            <div class="nav-auth-links">
                <a href="/dashboard/" class="btn btn-primary" style="padding:0.5rem 1rem;">Mi Panel</a>
                <a href="#" id="logoutBtn" class="btn btn-ghost" style="color:var(--error-color); padding:0.5rem 1rem;">Salir</a>
            </div>
        `;
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            Auth.logout();
        });
    } else {
        navLinks.innerHTML = `
            <a href="/">Inicio</a>
            <a href="/buscar_empleos/">Buscar empleos</a>
            <a href="/registro/">Publicar empleo</a>
            <div class="nav-auth-links" style="margin-left:auto;">
                <a href="/login/" class="btn btn-ghost" style="padding:0.5rem 1rem;">Iniciar sesión</a>
                <a href="/registro/" class="btn btn-primary" style="padding:0.5rem 1rem;">Registro</a>
            </div>
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
                document.getElementById('registerError').textContent = res.error;
                document.getElementById('registerError').style.display = 'block';
            } else {
                window.location.href = '/dashboard/';
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

    // 4. Lógica de Index (Inicio) y Buscar Empleos
    if (path === '/' || path === '/buscar_empleos/') {
        const isSearchPage = path === '/buscar_empleos/';
        const containerId = isSearchPage ? 'searchJobsList' : 'jobList';
        const container = document.getElementById(containerId);

        const loadJobs = (query = '') => {
            if (!container) return;
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
                container.innerHTML = '<p style="grid-column: 1/-1; text-align:center; padding: 2rem; color:var(--text-muted);">No se encontraron ofertas laborales.</p>';
                return;
            }

            container.innerHTML = empleos.map(job => {
                const empresaRaw = DB.getAll(DB_KEYS.EMPRESAS).find(e => e.usuario_id === job.empresa_user_id) || {};
                const empresaName = empresaRaw.nombre_empresa || 'Empresa Confidencial';

                if (isSearchPage) {
                    // Plantilla para buscar_empleos.html (.job-card-h)
                    const postulaciones = DB.getPostulacionesByEmpleo(job.id).length;
                    return `
                    <div class="job-card-h">
                        <div class="job-logo">
                            <span style="color:#0ea5e9;">🎯</span>
                        </div>
                        <div class="job-info-main">
                            <div class="job-h-title">
                                <h3>${job.titulo}</h3>
                                <span class="badge badge-green" style="font-size:0.625rem; font-weight:700;">NUEVO</span>
                            </div>
                            <div class="job-h-company">
                                ${empresaName} <span>• ${job.ubicacion}</span>
                            </div>
                            <div class="job-h-badges">
                                <span class="job-badge">📂 ${job.categoria}</span>
                                <span class="job-badge badge-action">⚡ Postulación rápida</span>
                            </div>
                            <div class="job-h-candidates">
                                <span style="font-weight:600; color:var(--primary-color)">${postulaciones}</span> &nbsp;candidatos ya aplicaron
                            </div>
                        </div>
                        <div class="job-h-right">
                            <div>
                                <div class="job-h-salary">Confirmar base</div>
                                <div class="job-h-time">${new Date(job.fecha || Date.now()).toLocaleDateString()}</div>
                            </div>
                            <button class="btn btn-outline view-job-btn" data-id="${job.id}" style="background:#0f172a; color:white; border-color:#0f172a;">Ver detalles</button>
                        </div>
                    </div>`;
                } else {
                    // Plantilla para index.html (.job-card grid)
                    return `
                    <div class="job-card">
                        <div class="job-icon-header">
                            <div class="job-icon">🏢</div>
                            <span class="badge badge-green">NUEVO</span>
                        </div>
                        <h3 class="job-title" style="margin-bottom:0.5rem; color:var(--text-main); font-size:1.125rem;">${job.titulo}</h3>
                        <div class="job-company" style="font-size:0.875rem; color:var(--text-muted); margin-bottom:1rem;">${empresaName}</div>
                        <div class="job-details" style="display:flex; gap:1rem; font-size:0.875rem; color:var(--text-muted); margin-bottom:1.5rem;">
                            <span>📍 ${job.ubicacion}</span>
                            <span>📂 ${job.categoria}</span>
                        </div>
                        <button class="btn btn-outline btn-block view-job-btn" data-id="${job.id}" style="border-width:2px; font-weight:600; padding:0.5rem 1rem;">Ver más</button>
                    </div>`;
                }
            }).join('');

            // Agregar eventos a botones de ver detalles
            document.querySelectorAll('.view-job-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    sessionStorage.setItem('current_job_id', e.target.dataset.id || e.currentTarget.dataset.id);
                    window.location.href = '/empleo/';
                });
            });
        };

        // Cargar empleos iniciales
        loadJobs();

        // Buscador superior en Index
        if (!isSearchPage) {
            const searchBtn = document.getElementById('searchBtn');
            const searchInput = document.getElementById('searchInput');

            searchBtn?.addEventListener('click', () => {
                loadJobs(searchInput.value);
            });
            searchInput?.addEventListener('keyup', (e) => {
                if (e.key === 'Enter') loadJobs(searchInput.value);
            });
        }
    }

    // 5. Dashboard Logic
    if (path === '/dashboard/') {
        if (!user) {
            window.location.href = '/login/';
            return;
        }

        const dashPostulante = document.getElementById('dashboardPostulante');
        const dashEmpresa = document.getElementById('dashboardEmpresa');

        if (user.rol === 'empresa') {
            if(dashPostulante) dashPostulante.style.display = 'none';
            if(dashEmpresa) dashEmpresa.style.display = 'block';

            const dashActions = document.getElementById('dashActions');
            const myJobListContainer = document.getElementById('myJobList');
            
            dashActions.innerHTML = `
                <button class="btn btn-primary" id="btnNewJobModal" style="background:#10b981; border-color:#10b981;">+ Publicar nueva oferta</button>
            `;

            // Setup Modal for New Job
            const modal = document.getElementById('newJobModal');
            document.getElementById('btnNewJobModal').addEventListener('click', () => {
                modal.style.display = 'flex';
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
                if(!myJobListContainer) return;
                const empleos = DB.getAll(DB_KEYS.EMPLEOS).filter(j => j.empresa_user_id === user.id);
                if (empleos.length === 0) {
                    myJobListContainer.innerHTML = '<p style="color:var(--text-muted);">No has publicado ofertas aún.</p>';
                    return;
                }

                myJobListContainer.innerHTML = empleos.map(job => {
                    const postulatesCount = DB.getPostulacionesByEmpleo(job.id).length;
                    return `
                    <div class="job-card" style="padding:1.5rem; border:1px solid var(--border-color); border-radius:var(--radius-lg); background:white;">
                        <h3 style="font-size:1.125rem; font-weight:700; margin-bottom:0.5rem; color:var(--text-main);">${job.titulo}</h3>
                        <p class="job-meta" style="color:var(--text-muted); font-size:0.875rem; margin-bottom:1rem;">
                            Postulantes recibidos: <strong style="color:var(--text-main);">${postulatesCount}</strong>
                        </p>
                        <div style="display:flex; gap:0.5rem;">
                            <button class="btn btn-primary btn-applicants" data-id="${job.id}" style="font-size:0.875rem; padding:0.5rem 1rem;">Ver Postulantes</button>
                            <button class="btn btn-outline" style="border-color:var(--error-color); color:var(--error-color); font-size:0.875rem; padding:0.5rem 1rem;" onclick="deleteJob('${job.id}')">Eliminar Oferta</button>
                        </div>
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
                                return `<li>
                                    <div><strong>${applicant.nombre}</strong> <br><span style="color:var(--text-muted); font-size:0.875rem;">${applicant.email}</span></div>
                                    <div style="font-size:0.875rem; color:var(--text-muted);">${new Date(p.fecha).toLocaleDateString()}</div>
                                </li>`;
                            }).join('');
                        }
                        appModal.style.display = 'flex';
                    });
                });
            };

            window.deleteJob = (id) => {
                if (confirm('¿Seguro quieres eliminar esta oferta?')) {
                    DB.delete(DB_KEYS.EMPLEOS, id);
                    renderEmpresaJobs();
                }
            };

            renderEmpresaJobs();

        } else if (user.rol === 'postulante') {
            if(dashEmpresa) dashEmpresa.style.display = 'none';
            if(dashPostulante) dashPostulante.style.display = 'block';

            // Actualizar header nombre
            const titlePost = document.getElementById('dashTitlePost');
            if(titlePost) {
                // Modificar el parrafo debajo del title
                const p = titlePost.nextElementSibling;
                if(p) {
                    p.innerHTML = `Bienvenido de nuevo, ${user.nombre}.`;
                }
            }

            const recContainer = document.getElementById('recommendedJobsList');
            const timelineContainer = document.getElementById('postulacionesTimeline');
            if(!recContainer) return;

            // Ver tareas aplicadas
            const postulates = DB.getPostulacionesByUser(user.id);

            // Actualizar Resumen de Actividad
            const statPostulaciones = document.getElementById('statPostulaciones');
            if (statPostulaciones) statPostulaciones.textContent = postulates.length;

            const statVistas = document.getElementById('statVistas');
            if (statVistas) {
                const vistas = DB.getAll(DB_KEYS.VISTAS_PERFIL) || [];
                const misVistas = vistas.filter(v => v.usuario_id === user.id);
                statVistas.textContent = misVistas.length;
            }

            const statGuardadas = document.getElementById('statGuardadas');
            if (statGuardadas) {
                const guardadas = DB.getAll(DB_KEYS.OFERTAS_GUARDADAS) || [];
                const misGuardadas = guardadas.filter(g => g.usuario_id === user.id);
                statGuardadas.textContent = misGuardadas.length;
            }

            if (postulates.length === 0) {
                recContainer.innerHTML = '<p style="padding:1rem; color:var(--text-muted);">No te has postulado a ninguna oferta todavía. Explora empleos en Búsqueda Rápida.</p>';
                if (timelineContainer) timelineContainer.innerHTML = '<p style="font-size:0.875rem; color:var(--text-muted);">Aún no hay actividad.</p>';
                return;
            }

            recContainer.innerHTML = postulates.map(p => {
                const job = DB.getById(DB_KEYS.EMPLEOS, p.empleo_id);
                if(!job) return ''; 
                const empresaRaw = DB.getAll(DB_KEYS.EMPRESAS).find(e => e.usuario_id === job.empresa_user_id) || {};
                const empresaName = empresaRaw.nombre_empresa || 'Empresa Confidencial';

                return `
                <div class="job-card-rec">
                    <div class="job-logo-rec">
                        <span style="color:var(--primary-color); font-size:1.5rem;">💼</span>
                    </div>
                    <div class="job-info-rec">
                        <div class="job-title-row">
                            <h4>${job.titulo}</h4>
                            <span class="badge badge-green" style="font-size:0.625rem; font-weight:700;">POSTULADO</span>
                        </div>
                        <div class="job-meta-rec">
                            ${empresaName} • ${job.ubicacion}
                        </div>
                        <div class="job-tags-rec">
                            <span class="tag-rec">${job.categoria}</span>
                        </div>
                    </div>
                    <div class="job-action-rec">
                        <div class="job-time-rec">${new Date(p.fecha).toLocaleDateString()}</div>
                        <button class="btn btn-outline view-job-btn" data-id="${job.id}" style="background:#f8fafc;">Ver Oferta</button>
                    </div>
                </div>
                `;
            }).join('');

            document.querySelectorAll('.view-job-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    sessionStorage.setItem('current_job_id', e.target.dataset.id || e.currentTarget.dataset.id);
                    window.location.href = '/empleo/';
                });
            });

            if (timelineContainer) {
                const sortedPostulates = [...postulates].sort((a,b) => new Date(b.fecha) - new Date(a.fecha));
                timelineContainer.innerHTML = sortedPostulates.slice(0, 5).map((p, index) => {
                    const job = DB.getById(DB_KEYS.EMPLEOS, p.empleo_id);
                    if(!job) return '';
                    
                    const colors = ['green', 'blue', 'gray'];
                    const colorClass = colors[index % colors.length];
                    
                    const dateObj = new Date(p.fecha);
                    const today = new Date();
                    let dateStr = dateObj.toLocaleDateString();
                    if (dateObj.toDateString() === today.toDateString()) {
                        dateStr = "Hoy";
                    } else {
                        const diffTime = Math.abs(today - dateObj);
                        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24)); 
                        if (diffDays === 1) dateStr = "Ayer";
                    }

                    return `
                        <div class="timeline-item ${colorClass}">
                            <div class="timeline-dot"></div>
                            <div class="timeline-content">
                                <div class="timeline-job">${job.titulo}</div>
                                <div class="timeline-status">Enviado</div>
                            </div>
                            <div class="timeline-time">${dateStr}</div>
                        </div>
                    `;
                }).join('');
            }
        }
    }

    // 6. Vista de Detalle de Empleo (/empleo/)
    if (path === '/empleo/') {
        const jobId = sessionStorage.getItem('current_job_id');
        const container = document.getElementById('jobDetailContainer');

        if (!jobId && container) {
            container.innerHTML = '<p>No se ha seleccionado ninguna oferta.</p>';
            return;
        }

        const job = DB.getById(DB_KEYS.EMPLEOS, jobId);
        if (!job && container) {
            container.innerHTML = '<p>La oferta ya no existe.</p>';
            return;
        }

        if(container) {
            const empresa = DB.getAll(DB_KEYS.EMPRESAS).find(e => e.usuario_id === job.empresa_user_id) || {};

            container.innerHTML = `
                <div class="job-header" style="margin-bottom:2rem; padding-bottom:1rem; border-bottom:1px solid var(--border-color);">
                    <h2 style="font-size:2rem; font-weight:800; margin-bottom:1rem;">${job.titulo}</h2>
                    <div class="job-meta" style="display:flex; gap:1.5rem; color:var(--text-muted); font-size:0.875rem;">
                        <span>🏢 ${empresa.nombre_empresa || 'Empresa Anónima'}</span>
                        <span>📍 ${job.ubicacion}</span>
                        <span>📂 ${job.categoria}</span>
                    </div>
                </div>
                <div class="job-body">
                    <h3 style="font-size:1.25rem; font-weight:700; margin-bottom:1rem;">Descripción del Puesto</h3>
                    <p style="white-space: pre-wrap; line-height:1.6; color:var(--text-main);">${job.descripcion}</p>
                </div>
                <div style="margin-top: 3rem;" id="applySection">
                    <!-- Botón aplicar -->
                </div>
            `;

            const applySection = document.getElementById('applySection');
            
            if (!user) {
                applySection.innerHTML = `<p style="color:var(--text-muted);">Para postularte debes <a href="/login/" class="text-primary font-semibold">Iniciar Sesión</a> o <a href="/registro/" class="text-primary font-semibold">Registrarte</a>.</p>`;
            } else if (user.rol === 'postulante') {
                const userPostuls = DB.getPostulacionesByUser(user.id);
                const yaPostulado = userPostuls.some(p => p.empleo_id === jobId);

                if (yaPostulado) {
                    applySection.innerHTML = `<button class="btn btn-outline" disabled style="background:#f1f5f9; cursor:not-allowed;">Ya te has postulado a este empleo</button>`;
                } else {
                    applySection.innerHTML = `<button class="btn btn-primary" id="btnApply" style="font-size:1.125rem; padding:1rem 2rem;">Postularme Ahora</button>`;
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
                applySection.innerHTML = `<p style="color:var(--text-muted);">Las cuentas de Empresa no pueden postularse a ofertas de trabajo.</p>`;
            }
        }
    }
});
