const { useState, useMemo, useEffect } = React;

const jsonHeaders = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
};

const fetchDashboard = () =>
  axios.get('/admin/api/dashboard', { headers: { Accept: 'application/json' }, withCredentials: true });

function useToast() {
  const [toast, setToast] = useState(null);

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3600);
  };

  return { toast, showToast };
}

function Toast({ toast }) {
  if (!toast) return null;
  const icon = toast.type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check';
  return (
    <div className={`floating-toast show toast-${toast.type === 'error' ? 'danger' : 'success'} sticky-toast`}>
      <span className="toast-icon"><i className={`fa-solid ${icon}`}></i></span>
      <span>{toast.message}</span>
    </div>
  );
}

function LoadingOverlay({ active }) {
  if (!active) return null;
  return (
    <div className="loading-overlay">
      <div className="spinner-border text-light" role="status">
        <span className="visually-hidden">Cargando...</span>
      </div>
    </div>
  );
}

function Section({ title, subtitle, icon, children, actions }) {
  return (
    <section className="admin-card">
      <header className="admin-card__header">
        <div>
          <span className="chip chip-dark"><i className={`fa-solid ${icon} me-2`}></i>{title}</span>
          {subtitle && <p className="text-white-50 mb-0 mt-2">{subtitle}</p>}
        </div>
        {actions}
      </header>
      <div className="admin-card__body">{children}</div>
    </section>
  );
}

function StudentForm({ onSubmit, loading }) {
  const [form, setForm] = useState({ nombre: '', dni: '', celular: '' });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await onSubmit({ ...form });
    setForm({ nombre: '', dni: '', celular: '' });
  };

  return (
    <form className="row g-3" onSubmit={handleSubmit}>
      <div className="col-12">
        <label className="form-label">Nombre y apellidos</label>
        <div className="input-icon">
          <span className="input-icon__icon"><i className="fa-solid fa-user"></i></span>
          <input
            required
            className="form-control"
            name="nombre"
            value={form.nombre}
            onChange={handleChange}
            placeholder="Ej. Laura Campos"
          />
        </div>
      </div>
      <div className="col-md-6">
        <label className="form-label">DNI</label>
        <div className="input-icon">
          <span className="input-icon__icon"><i className="fa-solid fa-id-card"></i></span>
          <input
            required
            className="form-control"
            name="dni"
            value={form.dni}
            onChange={handleChange}
            placeholder="Documento de identidad"
          />
        </div>
      </div>
      <div className="col-md-6">
        <label className="form-label">Celular</label>
        <div className="input-icon">
          <span className="input-icon__icon"><i className="fa-solid fa-phone"></i></span>
          <input
            className="form-control"
            name="celular"
            value={form.celular}
            onChange={handleChange}
            placeholder="Opcional"
          />
        </div>
      </div>
      <div className="col-12 d-grid d-sm-flex justify-content-sm-end gap-3">
        <button className="btn btn-glow" type="submit" disabled={loading}>
          <i className="fa-solid fa-user-plus me-2"></i>Registrar alumno
        </button>
      </div>
    </form>
  );
}

function CourseForm({ onSubmit, loading }) {
  const [form, setForm] = useState({ nombre: '', horas_lectivas: 0, horas_academicas: 0, creditos: 0 });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await onSubmit({ ...form });
    setForm({ nombre: '', horas_lectivas: 0, horas_academicas: 0, creditos: 0 });
  };

  return (
    <form className="row g-3" onSubmit={handleSubmit}>
      <div className="col-12">
        <label className="form-label">Nombre del curso</label>
        <div className="input-icon">
          <span className="input-icon__icon"><i className="fa-solid fa-graduation-cap"></i></span>
          <input
            required
            className="form-control"
            name="nombre"
            value={form.nombre}
            onChange={handleChange}
            placeholder="Ej. Gestión de Proyectos"
          />
        </div>
      </div>
      <div className="col-md-4">
        <label className="form-label">Horas lectivas</label>
        <input
          required
          type="number"
          min="0"
          className="form-control"
          name="horas_lectivas"
          value={form.horas_lectivas}
          onChange={handleChange}
        />
      </div>
      <div className="col-md-4">
        <label className="form-label">Horas académicas</label>
        <input
          required
          type="number"
          min="0"
          className="form-control"
          name="horas_academicas"
          value={form.horas_academicas}
          onChange={handleChange}
        />
      </div>
      <div className="col-md-4">
        <label className="form-label">Créditos</label>
        <input
          required
          type="number"
          min="0"
          className="form-control"
          name="creditos"
          value={form.creditos}
          onChange={handleChange}
        />
      </div>
      <div className="col-12 d-grid d-sm-flex justify-content-sm-end gap-3">
        <button className="btn btn-secondary btn-modern" type="submit" disabled={loading}>
          <i className="fa-solid fa-plus me-2"></i>Agregar curso
        </button>
      </div>
    </form>
  );
}

function EnrollmentForm({ onSubmit, alumnos, cursos, loading }) {
  const [form, setForm] = useState({ alumno_id: '', curso_id: '', numero_registro: '', estado: 'En Curso', certificado: null });

  const handleChange = (event) => {
    const { name, value, files } = event.target;
    if (name === 'certificado') {
      setForm((prev) => ({ ...prev, certificado: files && files[0] ? files[0] : null }));
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('alumno_id', form.alumno_id);
    formData.append('curso_id', form.curso_id);
    formData.append('numero_registro', form.numero_registro);
    formData.append('estado', form.estado);
    if (form.certificado) {
      formData.append('certificado', form.certificado);
    }
    await onSubmit(formData);
    setForm({ alumno_id: '', curso_id: '', numero_registro: '', estado: 'En Curso', certificado: null });
    event.target.reset();
  };

  return (
    <form className="row g-3" onSubmit={handleSubmit}>
      <div className="col-lg-4">
        <label className="form-label">Alumno</label>
        <select className="form-select" name="alumno_id" required value={form.alumno_id} onChange={handleChange}>
          <option value="">Selecciona un alumno</option>
          {alumnos.map((alumno) => (
            <option key={alumno.id} value={alumno.id}>
              {alumno.nombre} ({alumno.dni})
            </option>
          ))}
        </select>
      </div>
      <div className="col-lg-4">
        <label className="form-label">Curso</label>
        <select className="form-select" name="curso_id" required value={form.curso_id} onChange={handleChange}>
          <option value="">Selecciona un curso</option>
          {cursos.map((curso) => (
            <option key={curso.id} value={curso.id}>
              {curso.nombre}
            </option>
          ))}
        </select>
      </div>
      <div className="col-lg-4">
        <label className="form-label">Número de registro</label>
        <input
          className="form-control"
          name="numero_registro"
          required
          value={form.numero_registro}
          onChange={handleChange}
          placeholder="Ej. REG-2024-001"
        />
      </div>
      <div className="col-lg-4">
        <label className="form-label">Estado</label>
        <select className="form-select" name="estado" value={form.estado} onChange={handleChange}>
          <option value="En Curso">En Curso</option>
          <option value="Finalizado">Finalizado</option>
        </select>
      </div>
      <div className="col-lg-4">
        <label className="form-label">Certificado (PDF)</label>
        <input className="form-control" type="file" name="certificado" accept="application/pdf" onChange={handleChange} />
      </div>
      <div className="col-12 d-grid d-sm-flex justify-content-sm-end gap-3">
        <button className="btn btn-success" type="submit" disabled={loading}>
          <i className="fa-solid fa-link me-2"></i>Asignar curso
        </button>
      </div>
    </form>
  );
}

function StudentRow({ alumno, onUpdate, onDelete, loading }) {
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState({ nombre: alumno.nombre, dni: alumno.dni, celular: alumno.celular || '' });

  useEffect(() => {
    setForm({ nombre: alumno.nombre, dni: alumno.dni, celular: alumno.celular || '' });
  }, [alumno]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    await onUpdate(alumno.id, form);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (confirm('¿Eliminar este alumno y sus inscripciones asociadas?')) {
      await onDelete(alumno.id);
    }
  };

  return (
    <tr>
      <td>{isEditing ? <input className="form-control form-control-sm" name="nombre" value={form.nombre} onChange={handleChange} /> : alumno.nombre}</td>
      <td>{isEditing ? <input className="form-control form-control-sm" name="dni" value={form.dni} onChange={handleChange} /> : alumno.dni}</td>
      <td>{isEditing ? <input className="form-control form-control-sm" name="celular" value={form.celular} onChange={handleChange} /> : alumno.celular || '—'}</td>
      <td className="text-end">
        {isEditing ? (
          <div className="btn-group btn-group-sm">
            <button className="btn btn-success" onClick={handleSave} disabled={loading}><i className="fa-solid fa-floppy-disk"></i></button>
            <button className="btn btn-outline-light" onClick={() => setIsEditing(false)} disabled={loading}><i className="fa-solid fa-xmark"></i></button>
          </div>
        ) : (
          <div className="btn-group btn-group-sm">
            <button className="btn btn-outline-light" onClick={() => setIsEditing(true)} disabled={loading}><i className="fa-solid fa-pen"></i></button>
            <button className="btn btn-danger" onClick={handleDelete} disabled={loading}><i className="fa-solid fa-trash"></i></button>
          </div>
        )}
      </td>
    </tr>
  );
}

function CourseRow({ curso, onUpdate, onDelete, loading }) {
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState({
    nombre: curso.nombre,
    horas_lectivas: curso.horas_lectivas,
    horas_academicas: curso.horas_academicas,
    creditos: curso.creditos,
  });

  useEffect(() => {
    setForm({
      nombre: curso.nombre,
      horas_lectivas: curso.horas_lectivas,
      horas_academicas: curso.horas_academicas,
      creditos: curso.creditos,
    });
  }, [curso]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    await onUpdate(curso.id, form);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (confirm('¿Eliminar este curso? Se actualizarán las inscripciones relacionadas.')) {
      await onDelete(curso.id);
    }
  };

  return (
    <tr>
      <td>{isEditing ? <input className="form-control form-control-sm" name="nombre" value={form.nombre} onChange={handleChange} /> : curso.nombre}</td>
      <td>{isEditing ? <input className="form-control form-control-sm" type="number" min="0" name="horas_lectivas" value={form.horas_lectivas} onChange={handleChange} /> : curso.horas_lectivas}</td>
      <td>{isEditing ? <input className="form-control form-control-sm" type="number" min="0" name="horas_academicas" value={form.horas_academicas} onChange={handleChange} /> : curso.horas_academicas}</td>
      <td>{curso.horas}</td>
      <td>{isEditing ? <input className="form-control form-control-sm" type="number" min="0" name="creditos" value={form.creditos} onChange={handleChange} /> : curso.creditos}</td>
      <td className="text-end">
        {isEditing ? (
          <div className="btn-group btn-group-sm">
            <button className="btn btn-success" onClick={handleSave} disabled={loading}><i className="fa-solid fa-floppy-disk"></i></button>
            <button className="btn btn-outline-light" onClick={() => setIsEditing(false)} disabled={loading}><i className="fa-solid fa-xmark"></i></button>
          </div>
        ) : (
          <div className="btn-group btn-group-sm">
            <button className="btn btn-outline-light" onClick={() => setIsEditing(true)} disabled={loading}><i className="fa-solid fa-pen"></i></button>
            <button className="btn btn-danger" onClick={handleDelete} disabled={loading}><i className="fa-solid fa-trash"></i></button>
          </div>
        )}
      </td>
    </tr>
  );
}

function EnrollmentRow({ inscripcion, onUpdate, onDelete, loading }) {
  const [form, setForm] = useState({ numero_registro: inscripcion.numero_registro, estado: inscripcion.estado, certificado: null });

  useEffect(() => {
    setForm({ numero_registro: inscripcion.numero_registro, estado: inscripcion.estado, certificado: null });
  }, [inscripcion]);

  const handleChange = (event) => {
    const { name, value, files } = event.target;
    if (name === 'certificado') {
      setForm((prev) => ({ ...prev, certificado: files && files[0] ? files[0] : null }));
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSave = async () => {
    const payload = new FormData();
    payload.append('numero_registro', form.numero_registro);
    payload.append('estado', form.estado);
    if (form.certificado) {
      payload.append('certificado', form.certificado);
    }
    await onUpdate(inscripcion.id, payload);
    setForm((prev) => ({ ...prev, certificado: null }));
  };

  const handleDelete = async () => {
    if (confirm('¿Eliminar esta inscripción?')) {
      await onDelete(inscripcion.id);
    }
  };

  return (
    <tr>
      <td>
        <span className="fw-semibold">{inscripcion.alumno_nombre}</span>
        <div className="small text-white-50">{inscripcion.numero_registro}</div>
      </td>
      <td>
        <span className="fw-semibold">{inscripcion.curso_nombre}</span>
        <div className="small text-white-50">{inscripcion.creditos} créditos</div>
      </td>
      <td>
        <select className="form-select form-select-sm" name="estado" value={form.estado} onChange={handleChange}>
          <option value="En Curso">En Curso</option>
          <option value="Finalizado">Finalizado</option>
        </select>
      </td>
      <td>
        <input
          className="form-control form-control-sm"
          name="numero_registro"
          value={form.numero_registro}
          onChange={handleChange}
        />
      </td>
      <td>
        <div className="d-flex flex-column gap-2">
          <input className="form-control form-control-sm" type="file" name="certificado" accept="application/pdf" onChange={handleChange} />
          {inscripcion.certificado_url ? (
            <a className="btn btn-outline-light btn-sm" href={inscripcion.certificado_url} target="_blank" rel="noopener noreferrer">
              <i className="fa-solid fa-file-pdf me-2"></i>Ver actual
            </a>
          ) : (
            <span className="badge rounded-pill text-bg-secondary align-self-start">Sin archivo</span>
          )}
        </div>
      </td>
      <td className="text-end">
        <div className="btn-group btn-group-sm">
          <button className="btn btn-success" onClick={handleSave} disabled={loading}><i className="fa-solid fa-cloud-arrow-up"></i></button>
          <button className="btn btn-danger" onClick={handleDelete} disabled={loading}><i className="fa-solid fa-trash"></i></button>
        </div>
      </td>
    </tr>
  );
}

function DashboardApp() {
  const initialDataElement = document.getElementById('initial-data');
  const initialData = initialDataElement ? JSON.parse(initialDataElement.textContent) : { alumnos: [], cursos: [], inscripciones: [] };
  const [alumnos, setAlumnos] = useState(initialData.alumnos || []);
  const [cursos, setCursos] = useState(initialData.cursos || []);
  const [inscripciones, setInscripciones] = useState(initialData.inscripciones || []);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const { toast, showToast } = useToast();

  const filteredAlumnos = useMemo(() => {
    if (!search) return alumnos;
    return alumnos.filter((alumno) => alumno.nombre.toLowerCase().includes(search.toLowerCase()) || alumno.dni.toLowerCase().includes(search.toLowerCase()));
  }, [alumnos, search]);

  const filteredCursos = useMemo(() => {
    if (!search) return cursos;
    return cursos.filter((curso) => curso.nombre.toLowerCase().includes(search.toLowerCase()));
  }, [cursos, search]);

  useEffect(() => {
    if (window.gsap) {
      window.gsap.fromTo(
        '.admin-card',
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6, stagger: 0.1, ease: 'power3.out' }
      );
    }
  }, []);

  const refreshDashboard = async () => {
    const { data } = await fetchDashboard();
    setAlumnos(data.alumnos || []);
    setCursos(data.cursos || []);
    setInscripciones(data.inscripciones || []);
  };

  const handleRequest = async (callback, successMessage) => {
    try {
      setLoading(true);
      const result = await callback();
      await refreshDashboard();
      if (successMessage) {
        showToast('success', successMessage);
      } else if (result && result.message) {
        showToast('success', result.message);
      }
      return result;
    } catch (error) {
      const message = error?.response?.data?.message || 'Ocurrió un error. Inténtalo nuevamente.';
      showToast('error', message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const createAlumno = (payload) =>
    handleRequest(
      async () => {
        const { data } = await axios.post('/admin/alumnos', payload, {
          headers: jsonHeaders,
          withCredentials: true,
        });
        setAlumnos((prev) => [data.alumno, ...prev]);
        return data;
      },
      'Alumno registrado'
    );

  const updateAlumno = (id, payload) =>
    handleRequest(
      async () => {
        const { data } = await axios.put(`/admin/alumnos/${id}`, payload, {
          headers: jsonHeaders,
          withCredentials: true,
        });
        setAlumnos((prev) => prev.map((alumno) => (alumno.id === id ? data.alumno : alumno)));
        return data;
      },
      'Alumno actualizado'
    );

  const deleteAlumno = (id) =>
    handleRequest(
      async () => {
        await axios.delete(`/admin/alumnos/${id}`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        });
      },
      'Alumno eliminado'
    );

  const createCurso = (payload) =>
    handleRequest(
      async () => {
        const { data } = await axios.post('/admin/cursos', payload, {
          headers: jsonHeaders,
          withCredentials: true,
        });
        setCursos((prev) => [data.curso, ...prev]);
        return data;
      },
      'Curso agregado'
    );

  const updateCurso = (id, payload) =>
    handleRequest(
      async () => {
        const { data } = await axios.put(`/admin/cursos/${id}`, payload, {
          headers: jsonHeaders,
          withCredentials: true,
        });
        setCursos((prev) => prev.map((curso) => (curso.id === id ? data.curso : curso)));
        return data;
      },
      'Curso actualizado'
    );

  const deleteCurso = (id) =>
    handleRequest(
      async () => {
        await axios.delete(`/admin/cursos/${id}`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        });
      },
      'Curso eliminado'
    );

  const createInscripcion = (formData) =>
    handleRequest(
      async () => {
        const { data } = await axios.post('/admin/inscripciones', formData, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        });
        setInscripciones((prev) => [data.inscripcion, ...prev]);
        return data;
      },
      'Inscripción creada'
    );

  const updateInscripcion = (id, formData) =>
    handleRequest(
      async () => {
        const { data } = await axios.post(`/admin/inscripciones/${id}`, formData, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        });
        setInscripciones((prev) => prev.map((inscripcion) => (inscripcion.id === id ? data.inscripcion : inscripcion)));
        return data;
      },
      'Inscripción actualizada'
    );

  const deleteInscripcion = (id) =>
    handleRequest(
      async () => {
        await axios.delete(`/admin/inscripciones/${id}`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        });
      },
      'Inscripción eliminada'
    );

  return (
    <div className="admin-dashboard__content">
      <Toast toast={toast} />
      <LoadingOverlay active={loading} />
      <div className="admin-grid">
        <Section title="Registrar alumno" subtitle="Crea perfiles en segundos" icon="fa-user-plus">
          <StudentForm onSubmit={createAlumno} loading={loading} />
        </Section>
        <Section title="Agregar curso" subtitle="Define horas lectivas y académicas" icon="fa-book">
          <CourseForm onSubmit={createCurso} loading={loading} />
        </Section>
        <Section title="Asignar curso" subtitle="Sube certificados y gestiona estados" icon="fa-diagram-project">
          <EnrollmentForm onSubmit={createInscripcion} alumnos={alumnos} cursos={cursos} loading={loading} />
        </Section>
      </div>

      <div className="admin-table-card admin-card">
        <header className="admin-card__header">
          <div>
            <span className="chip chip-dark"><i className="fa-solid fa-filter me-2"></i>Buscar en registros</span>
            <p className="text-white-50 mb-0 mt-2">Filtra por nombre, DNI o curso para localizar información rápidamente.</p>
          </div>
          <div className="search-bar">
            <i className="fa-solid fa-magnifying-glass"></i>
            <input
              type="search"
              placeholder="Buscar alumnos o cursos"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </header>
      </div>

      <div className="admin-table-card admin-card">
        <header className="admin-card__header">
          <div>
            <span className="chip chip-dark"><i className="fa-solid fa-users me-2"></i>Alumnos registrados</span>
          </div>
        </header>
        <div className="table-responsive">
          <table className="table table-hover align-middle">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>DNI</th>
                <th>Celular</th>
                <th className="text-end">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlumnos.length > 0 ? (
                filteredAlumnos.map((alumno) => (
                  <StudentRow key={alumno.id} alumno={alumno} onUpdate={updateAlumno} onDelete={deleteAlumno} loading={loading} />
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="text-center text-white-50 py-4">No se encontraron alumnos con el término buscado.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="admin-table-card admin-card">
        <header className="admin-card__header">
          <div>
            <span className="chip chip-dark"><i className="fa-solid fa-books me-2"></i>Cursos disponibles</span>
          </div>
        </header>
        <div className="table-responsive">
          <table className="table table-hover align-middle">
            <thead>
              <tr>
                <th>Curso</th>
                <th>Horas lectivas</th>
                <th>Horas académicas</th>
                <th>Total horas</th>
                <th>Créditos</th>
                <th className="text-end">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredCursos.length > 0 ? (
                filteredCursos.map((curso) => (
                  <CourseRow key={curso.id} curso={curso} onUpdate={updateCurso} onDelete={deleteCurso} loading={loading} />
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="text-center text-white-50 py-4">No hay cursos que coincidan con la búsqueda.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="admin-table-card admin-card">
        <header className="admin-card__header">
          <div>
            <span className="chip chip-dark"><i className="fa-solid fa-handshake-simple me-2"></i>Inscripciones activas</span>
          </div>
        </header>
        <div className="table-responsive">
          <table className="table table-striped align-middle">
            <thead>
              <tr>
                <th>Alumno</th>
                <th>Curso</th>
                <th>Estado</th>
                <th>N° registro</th>
                <th>Certificado</th>
                <th className="text-end">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {inscripciones.length > 0 ? (
                inscripciones.map((inscripcion) => (
                  <EnrollmentRow key={inscripcion.id} inscripcion={inscripcion} onUpdate={updateInscripcion} onDelete={deleteInscripcion} loading={loading} />
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="text-center text-white-50 py-4">Aún no se han registrado inscripciones.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const mountNode = document.getElementById('admin-app');
if (mountNode) {
  const root = ReactDOM.createRoot(mountNode);
  root.render(<DashboardApp />);
}
