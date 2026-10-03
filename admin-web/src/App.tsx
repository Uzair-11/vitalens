import React, { useState, useEffect } from 'react';
import { adminApi } from './api/adminApi';
import { Sidebar, AdminTab, DoctorTab } from './components/Sidebar';
import { UserManagement } from './components/UserManagement';
import { DashboardView } from './components/DashboardView';
import { DoctorsManagement } from './components/DoctorsManagement';
import { PatientsManagement } from './components/PatientsManagement';
import { AITraceView } from './components/AITraceView';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function App() {
  // Auth state
  const [token, setToken] = useState<string | null>(localStorage.getItem('vitalens_admin_token'));
  const [role, setRole] = useState<string | null>(localStorage.getItem('vitalens_admin_role'));

  // Helpers to read initial tab from URL hash or localStorage
  const getInitialAdminTab = (): AdminTab => {
    const rawHash = window.location.hash.replace('#', '') as AdminTab;
    const validTabs: AdminTab[] = ['dashboard', 'doctors', 'patients', 'appointments', 'content', 'ai_review', 'user_management', 'ai_trace'];
    if (rawHash && validTabs.includes(rawHash)) {
      return rawHash;
    }
    const saved = localStorage.getItem('vitalens_admin_tab') as AdminTab;
    if (saved && validTabs.includes(saved)) {
      return saved;
    }
    return 'dashboard';
  };

  const getInitialDoctorTab = (): DoctorTab => {
    const rawHash = window.location.hash.replace('#', '') as DoctorTab;
    const validTabs: DoctorTab[] = ['doc_overview', 'doc_appointments', 'doc_schedule', 'doc_patients'];
    if (rawHash && validTabs.includes(rawHash)) {
      return rawHash;
    }
    const saved = localStorage.getItem('vitalens_doctor_tab') as DoctorTab;
    if (saved && validTabs.includes(saved)) {
      return saved;
    }
    return 'doc_overview';
  };

  const [adminTab, setAdminTab] = useState<AdminTab>(getInitialAdminTab);
  const [doctorTab, setDoctorTab] = useState<DoctorTab>(getInitialDoctorTab);

  const handleSelectAdminTab = (tab: AdminTab) => {
    setAdminTab(tab);
    localStorage.setItem('vitalens_admin_tab', tab);
    if (window.location.hash !== `#${tab}`) {
      window.location.hash = tab;
    }
  };

  const handleSelectDoctorTab = (tab: DoctorTab) => {
    setDoctorTab(tab);
    localStorage.setItem('vitalens_doctor_tab', tab);
    if (window.location.hash !== `#${tab}`) {
      window.location.hash = tab;
    }
  };

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Login form
  const [email, setEmail] = useState('admin@vitalens.health');
  const [password, setPassword] = useState('admin123');

  // Admin Data states
  const [analytics, setAnalytics] = useState<any>(null);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [specialties, setSpecialties] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [biomarkers, setBiomarkers] = useState<any[]>([]);
  const [glossary, setGlossary] = useState<any[]>([]);
  const [aiReviews, setAiReviews] = useState<any[]>([]);

  // Search & Filter states
  const [doctorSearch, setDoctorSearch] = useState('');
  const [doctorStatusFilter, setDoctorStatusFilter] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [appointmentStatusFilter, setAppointmentStatusFilter] = useState('');
  const [biomarkerSearch, setBiomarkerSearch] = useState('');
  const [glossarySearch, setGlossarySearch] = useState('');

  // Doctor Portal Data states
  const [doctorMe, setDoctorMe] = useState<any>(null);
  const [doctorSchedule, setDoctorSchedule] = useState<any>(null);
  const [doctorAppointments, setDoctorAppointments] = useState<any[]>([]);
  const [doctorPatients, setDoctorPatients] = useState<any[]>([]);
  const [selectedPatientChart, setSelectedPatientChart] = useState<any>(null);
  const [activeConsultationAppt, setActiveConsultationAppt] = useState<any>(null);

  const initialDoctorState = {
    email: '',
    temporary_password: '',
    full_name: '',
    specialty_id: '',
    qualification: '',
    experience_years: 5,
    clinic_name: '',
    address: '',
    city: '',
    consultation_fee: 800,
    bio: '',
  };

  // Modals & Forms
  const [showCreateDoctorModal, setShowCreateDoctorModal] = useState(false);
  const [newDoctor, setNewDoctor] = useState(initialDoctorState);

  const resetDoctorForm = () => {
    setNewDoctor({
      ...initialDoctorState,
      specialty_id: specialties[0]?.id || '',
    });
  };

  const [showBiomarkerModal, setShowBiomarkerModal] = useState(false);
  const [newBiomarker, setNewBiomarker] = useState({
    test_name: '',
    canonical_name: '',
    category: 'General Panel',
    default_unit: '',
    ref_min: 0,
    ref_max: 100,
  });

  const [showGlossaryModal, setShowGlossaryModal] = useState(false);
  const [newGlossary, setNewGlossary] = useState({
    term: '',
    definition: '',
  });

  const [showScheduleBlockModal, setShowScheduleBlockModal] = useState(false);
  const [newBlock, setNewBlock] = useState({
    block_date: '',
    start_time: '',
    end_time: '',
    reason: 'Vacation / Personal Leave',
  });

  const [consultationNotes, setConsultationNotes] = useState({
    diagnosis: '',
    clinical_notes: '',
    prescriptions: '',
    follow_up_recommendation: '',
  });

  const isDoctor = role === 'DOCTOR';
  const isSupportStaff = role === 'SUPPORT_STAFF';

  // Clear banners
  useEffect(() => {
    if (errorMsg || successMsg) {
      const timer = setTimeout(() => {
        setErrorMsg(null);
        setSuccessMsg(null);
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [errorMsg, successMsg]);

  // Load data on auth or tab change
  useEffect(() => {
    if (token) {
      if (isDoctor) {
        loadDoctorData(doctorTab);
      } else {
        loadAdminData(adminTab);
      }
    }
  }, [token, role, adminTab, doctorTab]);

  // Listen for browser Back/Forward or manual hash navigation
  useEffect(() => {
    const handleHashChange = () => {
      const rawHash = window.location.hash.replace('#', '');
      const validAdminTabs: AdminTab[] = ['dashboard', 'doctors', 'patients', 'appointments', 'content', 'ai_review', 'user_management', 'ai_trace'];
      const validDoctorTabs: DoctorTab[] = ['doc_overview', 'doc_appointments', 'doc_schedule', 'doc_patients'];

      if (isDoctor) {
        if (validDoctorTabs.includes(rawHash as DoctorTab)) {
          setDoctorTab(rawHash as DoctorTab);
          localStorage.setItem('vitalens_doctor_tab', rawHash);
        }
      } else {
        if (validAdminTabs.includes(rawHash as AdminTab)) {
          setAdminTab(rawHash as AdminTab);
          localStorage.setItem('vitalens_admin_tab', rawHash);
        }
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [isDoctor]);

  // Keep URL hash synchronized on initial mount if logged in
  useEffect(() => {
    if (token) {
      const currentTab = isDoctor ? doctorTab : adminTab;
      if (window.location.hash !== `#${currentTab}`) {
        window.location.hash = currentTab;
      }
    }
  }, [token, isDoctor]);

  const loadAdminData = async (tab: AdminTab) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (tab === 'dashboard') {
        const data = await adminApi.getAnalytics();
        setAnalytics(data);
      } else if (tab === 'doctors') {
        const [docs, specs] = await Promise.all([
          adminApi.getDoctors({ name: doctorSearch || undefined, verification_status: doctorStatusFilter || undefined }),
          adminApi.getSpecialties(),
        ]);
        setDoctors(docs);
        setSpecialties(specs);
        if (specs.length > 0 && !newDoctor.specialty_id) {
          setNewDoctor((prev) => ({ ...prev, specialty_id: specs[0].id }));
        }
      } else if (tab === 'patients') {
        const data = await adminApi.getUsers({ search: userSearch || undefined, role: 'PATIENT' });
        setUsers(data);
      } else if (tab === 'appointments') {
        const data = await adminApi.getAppointments({ status: appointmentStatusFilter || undefined });
        setAppointments(data);
      } else if (tab === 'content') {
        const [bios, gloss] = await Promise.all([
          adminApi.getBiomarkers(biomarkerSearch || undefined),
          adminApi.getGlossary(glossarySearch || undefined),
        ]);
        setBiomarkers(bios);
        setGlossary(gloss);
      } else if (tab === 'ai_review') {
        const data = await adminApi.getAIReviews();
        setAiReviews(data);
      }
    } catch (err: any) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  const loadDoctorData = async (tab: DoctorTab) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (tab === 'doc_overview') {
        const data = await adminApi.getDoctorMe();
        setDoctorMe(data);
      } else if (tab === 'doc_schedule') {
        const data = await adminApi.getDoctorSchedule();
        setDoctorSchedule(data);
      } else if (tab === 'doc_appointments') {
        const data = await adminApi.getDoctorAppointments();
        setDoctorAppointments(data);
      } else if (tab === 'doc_patients') {
        const data = await adminApi.getDoctorAssignedPatients();
        setDoctorPatients(data);
      }
    } catch (err: any) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApiError = (err: any) => {
    if (err.response?.status === 403) {
      setErrorMsg(err.response?.data?.detail || 'Access Forbidden: You are not authorized for this resource.');
    } else {
      setErrorMsg(err.response?.data?.detail || err.message || 'Error communicating with server.');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await adminApi.login(email, password);
      setToken(data.access_token);
      setRole(data.role);
      const isDoc = data.role === 'DOCTOR';
      const initialTab = isDoc ? getInitialDoctorTab() : getInitialAdminTab();
      window.location.hash = initialTab;
      setSuccessMsg(`Welcome, ${data.role}! Signed in successfully.`);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    adminApi.logout();
    setToken(null);
    setRole(null);
    setSelectedUser(null);
    setSelectedPatientChart(null);
    setActiveConsultationAppt(null);
    localStorage.removeItem('vitalens_admin_tab');
    localStorage.removeItem('vitalens_doctor_tab');
    window.location.hash = '';
  };

  // ================= ADMIN ACTIONS =================
  const handleVerifyDoctor = async (doctorId: string, status: 'VERIFIED' | 'REJECTED') => {
    try {
      await adminApi.verifyDoctor(doctorId, status);
      setSuccessMsg(`Doctor status updated to ${status}.`);
      loadAdminData('doctors');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleToggleDoctorStatus = async (doctorId: string, currentActive: boolean) => {
    try {
      await adminApi.toggleDoctorStatus(doctorId, !currentActive);
      setSuccessMsg(`Doctor profile ${!currentActive ? 'activated' : 'deactivated'}.`);
      loadAdminData('doctors');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleCreateDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createDoctor({
        ...newDoctor,
        clinic_name: newDoctor.clinic_name.trim() || 'VitaLens Health Partner Clinic',
        city: newDoctor.city.trim() || 'Ahmedabad',
        address: newDoctor.address.trim() || 'Ahmedabad, Gujarat',
      });
      setSuccessMsg('Doctor profile & login credentials created successfully.');
      resetDoctorForm();
      setShowCreateDoctorModal(false);
      loadAdminData('doctors');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleToggleUserStatus = async (userId: string, currentActive: boolean) => {
    try {
      await adminApi.toggleUserStatus(userId, !currentActive);
      setSuccessMsg(`User account ${!currentActive ? 'reactivated' : 'suspended'}.`);
      loadAdminData('patients');
      if (selectedUser?.id === userId) {
        setSelectedUser((prev: any) => ({ ...prev, is_active: !currentActive }));
      }
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleViewUserDetail = async (userId: string) => {
    try {
      const detail = await adminApi.getUserDetail(userId);
      setSelectedUser(detail);
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleCancelAppointment = async (appointmentId: string) => {
    const reason = prompt('Enter administrative cancellation reason:', 'Schedule conflict resolution');
    if (!reason) return;
    try {
      await adminApi.cancelAppointment(appointmentId, reason);
      setSuccessMsg('Appointment cancelled and doctor slot released.');
      loadAdminData('appointments');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleCreateBiomarker = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createBiomarker(newBiomarker);
      setSuccessMsg('Biomarker reference added.');
      setShowBiomarkerModal(false);
      loadAdminData('content');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleDeleteBiomarker = async (id: string) => {
    if (!confirm('Are you sure you want to delete this biomarker reference?')) return;
    try {
      await adminApi.deleteBiomarker(id);
      setSuccessMsg('Biomarker reference deleted.');
      loadAdminData('content');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleCreateGlossary = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createGlossary(newGlossary);
      setSuccessMsg('Glossary term added.');
      setShowGlossaryModal(false);
      loadAdminData('content');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleDeleteGlossary = async (id: string) => {
    if (!confirm('Are you sure you want to delete this glossary term?')) return;
    try {
      await adminApi.deleteGlossary(id);
      setSuccessMsg('Glossary term deleted.');
      loadAdminData('content');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleReviewAI = async (id: string, action: 'APPROVE' | 'FLAG' | 'OVERRIDE') => {
    let overrideId: string | undefined = undefined;
    if (action === 'OVERRIDE') {
      const specPrompt = prompt('Enter target override Medical Specialty ID:');
      if (!specPrompt) return;
      overrideId = specPrompt.trim();
    }
    try {
      await adminApi.reviewAIRecommendation(id, action, overrideId);
      setSuccessMsg(`AI recommendation updated to ${action}.`);
      loadAdminData('ai_review');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  // ================= DOCTOR PORTAL ACTIONS =================
  const handleUpdateDoctorAppointmentStatus = async (apptId: string, status: string) => {
    let reason = undefined;
    if (status === 'CANCELLED') {
      const promptReason = prompt('Enter reason for cancellation / rejection:', 'Physician emergency leave');
      if (!promptReason) return;
      reason = promptReason;
    }
    try {
      await adminApi.updateDoctorAppointmentStatus(apptId, status, reason);
      setSuccessMsg(`Appointment status updated to ${status}.`);
      loadDoctorData('doc_appointments');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleOpenConsultationModal = async (appt: any) => {
    setActiveConsultationAppt(appt);
    setConsultationNotes({ diagnosis: '', clinical_notes: '', prescriptions: '', follow_up_recommendation: '' });
    try {
      const notes = await adminApi.getConsultationNotes(appt.id);
      if (notes) {
        setConsultationNotes({
          diagnosis: notes.diagnosis || '',
          clinical_notes: notes.clinical_notes || '',
          prescriptions: notes.prescriptions || '',
          follow_up_recommendation: notes.follow_up_recommendation || '',
        });
      }
    } catch {
      // Notes might not exist yet for this appointment
    }
  };

  const handleSaveConsultationNotes = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeConsultationAppt) return;
    try {
      await adminApi.saveConsultationNotes(activeConsultationAppt.id, consultationNotes);
      setSuccessMsg('Consultation notes saved successfully.');
      setActiveConsultationAppt(null);
      loadDoctorData('doc_appointments');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleViewPatientChart = async (patientId: string) => {
    try {
      const chart = await adminApi.getDoctorPatientChart(patientId);
      setSelectedPatientChart(chart);
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleAddScheduleBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.addScheduleBlock(newBlock);
      setSuccessMsg('Schedule blackout period recorded.');
      setShowScheduleBlockModal(false);
      loadDoctorData('doc_schedule');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  const handleRemoveScheduleBlock = async (blockId: string) => {
    if (!confirm('Remove this schedule block and restore availability?')) return;
    try {
      await adminApi.removeScheduleBlock(blockId);
      setSuccessMsg('Schedule block removed.');
      loadDoctorData('doc_schedule');
    } catch (err: any) {
      handleApiError(err);
    }
  };

  // ---------------- Render Login Screen ----------------
  if (!token) {
    return (
      <div style={styles.loginContainer}>
        <div style={styles.loginCard}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <img
              src="/assets/vitalens-logo-on-white.png"
              alt="VitaLens"
              style={{ width: 180, height: 'auto', marginBottom: 12, display: 'block', margin: '0 auto 12px auto' }}
            />
            <h1 style={{ color: '#0F5C5E', margin: '0 0 8px 0', fontSize: 22, fontWeight: 700 }}>Operations & Clinical Portal</h1>
            <p style={{ color: '#666', margin: 0, fontSize: 14 }}>Administration, Support & Doctor Workspace</p>
          </div>

          {errorMsg && <div style={styles.errorBanner}>{errorMsg}</div>}
          {successMsg && <div style={styles.successBanner}>{successMsg}</div>}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={styles.label}>Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={styles.input}
              />
            </div>

            <button type="submit" disabled={loading} style={styles.primaryButton}>
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ================= RENDER DOCTOR PORTAL =================
  if (isDoctor) {
    return (
      <div style={styles.appContainer}>
        {/* Doctor Sidebar */}
        <Sidebar
          role={role}
          activeTab={doctorTab}
          onSelectTab={(tab) => handleSelectDoctorTab(tab)}
          onLogout={handleLogout}
          isDoctor={true}
        />

        {/* Doctor Main Content */}
        <div style={styles.mainContent}>
          <div style={styles.topHeader}>
            <h2 style={{ margin: 0, fontSize: 20, color: '#1a1a1a' }}>
              {doctorTab === 'doc_overview' && 'Practice Overview & Today\'s Stats'}
              {doctorTab === 'doc_appointments' && 'Appointment Management'}
              {doctorTab === 'doc_schedule' && 'Weekly Working Hours & Blackout Blocks'}
              {doctorTab === 'doc_patients' && 'Consented Patient Charts'}
            </h2>
            <button onClick={() => loadDoctorData(doctorTab)} style={styles.secondaryButton}>
              🔄 Refresh
            </button>
          </div>

          {errorMsg && <div style={styles.errorBanner}>{errorMsg}</div>}
          {successMsg && <div style={styles.successBanner}>{successMsg}</div>}
          {loading && <div style={{ padding: 16, color: '#0F5C5E', fontWeight: 600 }}>Loading clinical data...</div>}

          {/* DOCTOR TAB: OVERVIEW */}
          {doctorTab === 'doc_overview' && doctorMe && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Doctor Profile Banner */}
              <div style={{ ...styles.card, background: 'linear-gradient(135deg, #0F5C5E 0%, #164e63 100%)', color: '#fff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h2 style={{ margin: '0 0 6px 0', fontSize: 22 }}>{doctorMe.full_name}</h2>
                    <p style={{ margin: '0 0 10px 0', fontSize: 14, color: '#e0f2fe' }}>
                      {doctorMe.specialty_name} • {doctorMe.qualification} • {doctorMe.experience_years} Years Experience
                    </p>
                    <div style={{ fontSize: 13, color: '#cbd5e1' }}>
                      🏥 {doctorMe.clinic_name} ({doctorMe.city}) | 💵 Fee: ${doctorMe.consultation_fee}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ padding: '4px 10px', background: '#dcfce7', color: '#166534', borderRadius: 4, fontWeight: 700, fontSize: 12 }}>
                      {doctorMe.verification_status}
                    </span>
                    <div style={{ marginTop: 8, fontSize: 13, color: '#e0f2fe' }}>
                      ⭐ {doctorMe.rating} ({doctorMe.review_count} reviews)
                    </div>
                  </div>
                </div>
              </div>

              {/* KPI Cards */}
              <div style={styles.kpiGrid}>
                <div style={styles.kpiCard}>
                  <div style={styles.kpiLabel}>Today's Appointments</div>
                  <div style={styles.kpiValue}>{doctorMe.today_stats?.today_appointments_count || 0}</div>
                  <div style={styles.kpiSub}>Scheduled for today</div>
                </div>
                <div style={styles.kpiCard}>
                  <div style={styles.kpiLabel}>Pending Requests</div>
                  <div style={{ ...styles.kpiValue, color: '#854d0e' }}>{doctorMe.today_stats?.pending_requests_count || 0}</div>
                  <div style={styles.kpiSub}>Awaiting doctor confirmation</div>
                </div>
                <div style={styles.kpiCard}>
                  <div style={styles.kpiLabel}>Completed Today</div>
                  <div style={{ ...styles.kpiValue, color: '#166534' }}>{doctorMe.today_stats?.completed_today_count || 0}</div>
                  <div style={styles.kpiSub}>Consultations completed</div>
                </div>
                <div style={styles.kpiCard}>
                  <div style={styles.kpiLabel}>Total Consultations</div>
                  <div style={styles.kpiValue}>{doctorMe.today_stats?.total_consultations_completed || 0}</div>
                  <div style={styles.kpiSub}>Across {doctorMe.today_stats?.active_patients_count || 0} distinct patients</div>
                </div>
              </div>
            </div>
          )}

          {/* DOCTOR TAB: APPOINTMENTS */}
          {doctorTab === 'doc_appointments' && (
            <div style={styles.card}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: 16, color: '#0F5C5E' }}>My Patient Consultations</h3>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>Date & Time</th>
                    <th style={styles.th}>Patient</th>
                    <th style={styles.th}>Reason</th>
                    <th style={styles.th}>Status</th>
                    <th style={styles.th}>Clinical Notes</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {doctorAppointments.map((a) => (
                    <tr key={a.id} style={styles.tr}>
                      <td style={styles.td}>
                        <div style={{ fontWeight: 600 }}>{a.appointment_date}</div>
                        <div style={{ fontSize: 12, color: '#666' }}>{a.appointment_time}</div>
                      </td>
                      <td style={styles.td}>
                        <div style={{ fontWeight: 600 }}>{a.patient_name}</div>
                        <div style={{ fontSize: 12, color: '#666' }}>{a.patient_email}</div>
                      </td>
                      <td style={styles.td}>{a.visit_reason || 'General Consultation'}</td>
                      <td style={styles.td}>
                        <span
                          style={{
                            ...styles.badge,
                            backgroundColor:
                              a.status === 'CONFIRMED'
                                ? '#dcfce7'
                                : a.status === 'COMPLETED'
                                ? '#e0f2fe'
                                : a.status === 'PENDING'
                                ? '#fef9c3'
                                : '#fee2e2',
                            color:
                              a.status === 'CONFIRMED'
                                ? '#166534'
                                : a.status === 'COMPLETED'
                                ? '#0369a1'
                                : a.status === 'PENDING'
                                ? '#854d0e'
                                : '#991b1b',
                          }}
                        >
                          {a.status}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <button
                          onClick={() => handleOpenConsultationModal(a)}
                          style={{ ...styles.actionBtn, background: a.has_consultation_notes ? '#166534' : '#0F5C5E', color: '#fff' }}
                        >
                          {a.has_consultation_notes ? '📝 Edit Notes' : '+ Add Notes'}
                        </button>
                      </td>
                      <td style={styles.td}>
                        <div style={{ display: 'flex', gap: 6 }}>
                          {a.status === 'PENDING' && (
                            <button
                              onClick={() => handleUpdateDoctorAppointmentStatus(a.id, 'CONFIRMED')}
                              style={{ ...styles.actionBtn, background: '#166534', color: '#fff' }}
                            >
                              Accept
                            </button>
                          )}
                          {a.status === 'CONFIRMED' && (
                            <button
                              onClick={() => handleUpdateDoctorAppointmentStatus(a.id, 'COMPLETED')}
                              style={{ ...styles.actionBtn, background: '#0369a1', color: '#fff' }}
                            >
                              Complete
                            </button>
                          )}
                          {(a.status === 'CONFIRMED' || a.status === 'PENDING') && (
                            <button
                              onClick={() => handleUpdateDoctorAppointmentStatus(a.id, 'CANCELLED')}
                              style={{ ...styles.actionBtn, background: '#991b1b', color: '#fff' }}
                            >
                              Cancel & Release
                            </button>
                          )}
                          <button
                            onClick={() => handleViewPatientChart(a.user_id)}
                            style={{ ...styles.actionBtn, background: '#334155', color: '#fff' }}
                          >
                            Chart
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* DOCTOR TAB: SCHEDULE */}
          {doctorTab === 'doc_schedule' && doctorSchedule && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Working Hours Card */}
              <div style={styles.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 16, color: '#0F5C5E' }}>Weekly Recurring Working Hours</h3>
                    <p style={{ margin: '4px 0 0 0', fontSize: 12, color: '#666' }}>
                      Active slots currently open for patient booking: <strong>{doctorSchedule.active_available_slots_count} slots</strong>
                    </p>
                  </div>
                </div>

                <table style={styles.table}>
                  <thead>
                    <tr style={styles.thRow}>
                      <th style={styles.th}>Day of Week</th>
                      <th style={styles.th}>Working Hours</th>
                      <th style={styles.th}>Slot Duration</th>
                      <th style={styles.th}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doctorSchedule.recurring_hours?.map((wh: any) => (
                      <tr key={wh.id} style={styles.tr}>
                        <td style={styles.td}><strong>{DAYS_OF_WEEK[wh.day_of_week]}</strong></td>
                        <td style={styles.td}>{wh.start_time} - {wh.end_time}</td>
                        <td style={styles.td}>{wh.slot_duration_minutes} mins</td>
                        <td style={styles.td}>
                          <span style={{ color: wh.is_active ? '#166534' : '#991b1b', fontWeight: 600 }}>
                            {wh.is_active ? 'Active' : 'Closed'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Schedule Blocks & Holidays */}
              <div style={styles.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 16, color: '#0F5C5E' }}>Upcoming Blackout Periods / Holidays</h3>
                    <p style={{ margin: '4px 0 0 0', fontSize: 12, color: '#666' }}>
                      Prevents patients from booking slots on vacation dates or conferences.
                    </p>
                  </div>
                  <button onClick={() => setShowScheduleBlockModal(true)} style={styles.primaryButton}>
                    + Add Date Block
                  </button>
                </div>

                <table style={styles.table}>
                  <thead>
                    <tr style={styles.thRow}>
                      <th style={styles.th}>Block Date</th>
                      <th style={styles.th}>Time Window</th>
                      <th style={styles.th}>Reason</th>
                      <th style={styles.th}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doctorSchedule.schedule_blocks?.length === 0 && (
                      <tr><td colSpan={4} style={{ padding: 16, textAlign: 'center', color: '#888' }}>No blackout dates currently scheduled.</td></tr>
                    )}
                    {doctorSchedule.schedule_blocks?.map((b: any) => (
                      <tr key={b.id} style={styles.tr}>
                        <td style={styles.td}><strong>{b.block_date}</strong></td>
                        <td style={styles.td}>{b.start_time && b.end_time ? `${b.start_time} - ${b.end_time}` : 'All Day (Full Block)'}</td>
                        <td style={styles.td}>{b.reason || 'Personal / Holiday'}</td>
                        <td style={styles.td}>
                          <button
                            onClick={() => handleRemoveScheduleBlock(b.id)}
                            style={{ ...styles.actionBtn, background: '#991b1b', color: '#fff' }}
                          >
                            Remove Block
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* DOCTOR TAB: PATIENTS */}
          {doctorTab === 'doc_patients' && (
            <div style={styles.card}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: 16, color: '#0F5C5E' }}>Assigned & Consented Patients</h3>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>Patient Name</th>
                    <th style={styles.th}>Email</th>
                    <th style={styles.th}>Phone</th>
                    <th style={styles.th}>Last Appointment</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {doctorPatients.length === 0 && (
                    <tr><td colSpan={5} style={{ padding: 16, textAlign: 'center', color: '#888' }}>No consented patient consultations recorded yet.</td></tr>
                  )}
                  {doctorPatients.map((p) => (
                    <tr key={p.patient_id} style={styles.tr}>
                      <td style={styles.td}><strong>{p.full_name}</strong></td>
                      <td style={styles.td}>{p.email}</td>
                      <td style={styles.td}>{p.phone || '-'}</td>
                      <td style={styles.td}>{p.last_appointment_date}</td>
                      <td style={styles.td}>
                        <button
                          onClick={() => handleViewPatientChart(p.patient_id)}
                          style={{ ...styles.actionBtn, background: '#0F5C5E', color: '#fff' }}
                        >
                          View Full Chart & Reports
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* MODAL: CONSULTATION NOTES */}
        {activeConsultationAppt && (
          <div style={styles.modalOverlay}>
            <div style={{ ...styles.modalContent, maxWidth: 640 }}>
              <h3 style={{ margin: '0 0 12px 0', color: '#0F5C5E' }}>
                Clinical Consultation Notes: {activeConsultationAppt.patient_name}
              </h3>
              <p style={{ margin: '0 0 16px 0', fontSize: 13, color: '#666' }}>
                Appointment: {activeConsultationAppt.appointment_date} at {activeConsultationAppt.appointment_time}
              </p>
              <form onSubmit={handleSaveConsultationNotes} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={styles.label}>Clinical Diagnosis / Assessment</label>
                  <input
                    type="text"
                    value={consultationNotes.diagnosis}
                    onChange={(e) => setConsultationNotes({ ...consultationNotes, diagnosis: e.target.value })}
                    placeholder="e.g. Mild Iron Deficiency Anemia, Essential Hypertension"
                    style={styles.input}
                  />
                </div>
                <div>
                  <label style={styles.label}>Clinical Notes & Examination Findings</label>
                  <textarea
                    rows={4}
                    value={consultationNotes.clinical_notes}
                    onChange={(e) => setConsultationNotes({ ...consultationNotes, clinical_notes: e.target.value })}
                    required
                    placeholder="Detailed doctor observation and examination notes..."
                    style={{ ...styles.input, height: 'auto' }}
                  />
                </div>
                <div>
                  <label style={styles.label}>Prescriptions & Treatment Regimen</label>
                  <textarea
                    rows={2}
                    value={consultationNotes.prescriptions}
                    onChange={(e) => setConsultationNotes({ ...consultationNotes, prescriptions: e.target.value })}
                    placeholder="Medications, dosage, and duration..."
                    style={{ ...styles.input, height: 'auto' }}
                  />
                </div>
                <div>
                  <label style={styles.label}>Follow-up Recommendations</label>
                  <input
                    type="text"
                    value={consultationNotes.follow_up_recommendation}
                    onChange={(e) => setConsultationNotes({ ...consultationNotes, follow_up_recommendation: e.target.value })}
                    placeholder="e.g. Recheck CBC in 4 weeks, low sodium diet"
                    style={styles.input}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
                  <button type="button" onClick={() => setActiveConsultationAppt(null)} style={styles.secondaryButton}>
                    Cancel
                  </button>
                  <button type="submit" style={styles.primaryButton}>
                    Save Clinical Notes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL: PATIENT CHART VIEW */}
        {selectedPatientChart && (
          <div style={styles.modalOverlay}>
            <div style={{ ...styles.modalContent, maxWidth: 720, maxHeight: '85vh', overflowY: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, color: '#0F5C5E' }}>Clinical Patient Chart: {selectedPatientChart.full_name}</h3>
                <button onClick={() => setSelectedPatientChart(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 18 }}>
                  ✖
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, background: '#f8fafc', padding: 14, borderRadius: 6, marginBottom: 16 }}>
                <div><strong>Email:</strong> {selectedPatientChart.email}</div>
                <div><strong>Phone:</strong> {selectedPatientChart.phone || 'N/A'}</div>
                <div><strong>Sex:</strong> {selectedPatientChart.biological_sex || 'N/A'}</div>
                <div><strong>Blood Group:</strong> {selectedPatientChart.blood_group || 'N/A'}</div>
              </div>

              <h4 style={{ margin: '16px 0 8px 0', color: '#334155' }}>Shared Medical Reports ({selectedPatientChart.shared_reports?.length || 0})</h4>
              {selectedPatientChart.shared_reports?.map((r: any) => (
                <div key={r.id} style={{ border: '1px solid #e2e8f0', borderRadius: 6, padding: 12, marginBottom: 10 }}>
                  <div style={{ fontWeight: 600, color: '#0F5C5E' }}>{r.report_title} ({r.report_type}) - {r.report_date}</div>
                  <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                    {r.biomarkers?.map((b: any, idx: number) => (
                      <span key={idx} style={{ display: 'inline-block', marginRight: 12, marginTop: 4 }}>
                        <strong>{b.test_name}:</strong> {b.value_numeric} {b.unit} ({b.flag})
                      </span>
                    ))}
                  </div>
                </div>
              ))}

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                <button onClick={() => setSelectedPatientChart(null)} style={styles.primaryButton}>
                  Close Chart
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL: ADD SCHEDULE BLOCK */}
        {showScheduleBlockModal && (
          <div style={styles.modalOverlay}>
            <div style={styles.modalContent}>
              <h3 style={{ margin: '0 0 16px 0', color: '#0F5C5E' }}>Add Blackout Date / Holiday</h3>
              <form onSubmit={handleAddScheduleBlock} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={styles.label}>Block Date</label>
                  <input
                    type="date"
                    value={newBlock.block_date}
                    onChange={(e) => setNewBlock({ ...newBlock, block_date: e.target.value })}
                    required
                    style={styles.input}
                  />
                </div>
                <div>
                  <label style={styles.label}>Reason</label>
                  <input
                    type="text"
                    value={newBlock.reason}
                    onChange={(e) => setNewBlock({ ...newBlock, reason: e.target.value })}
                    placeholder="e.g. Annual Medical Conference, Personal Holiday"
                    style={styles.input}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
                  <button type="button" onClick={() => setShowScheduleBlockModal(false)} style={styles.secondaryButton}>
                    Cancel
                  </button>
                  <button type="submit" style={styles.primaryButton}>
                    Save Blackout Period
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ================= RENDER ADMIN / SUPPORT STAFF PORTAL =================
  return (
    <div style={styles.appContainer}>
      {/* Sidebar Navigation */}
      <Sidebar
        role={role}
        activeTab={adminTab}
        onSelectTab={(tab) => handleSelectAdminTab(tab)}
        onLogout={handleLogout}
        isDoctor={false}
      />

      {/* Main Content Area */}
      <div style={styles.mainContent}>
        {/* Top Header */}
        <div style={styles.topHeader}>
          <h2 style={{ margin: 0, fontSize: 20, color: '#1a1a1a' }}>
            {adminTab === 'dashboard' && '📊 Operational Dashboard & Metrics'}
            {adminTab === 'doctors' && '👨‍⚕️ Doctors Management'}
            {adminTab === 'patients' && '👥 Patients Management'}
            {adminTab === 'appointments' && '📅 Appointments Management'}
            {adminTab === 'content' && '📖 Clinical Content & Glossary'}
            {adminTab === 'ai_review' && '🤖 AI Recommendation Review'}
            {adminTab === 'user_management' && '🛡️ Super Admin User Management'}
            {adminTab === 'ai_trace' && '⚡ Super Admin AI Trace & Observability'}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button onClick={() => loadAdminData(adminTab)} style={styles.secondaryButton}>
              🔄 Refresh Data
            </button>
          </div>
        </div>

        {/* Global Alert Banners */}
        {errorMsg && <div style={styles.errorBanner}>{errorMsg}</div>}
        {successMsg && <div style={styles.successBanner}>{successMsg}</div>}
        {loading && <div style={{ padding: 16, color: '#0F5C5E', fontWeight: 600 }}>Loading operations data...</div>}

        {/* TAB: DASHBOARD */}
        {adminTab === 'dashboard' && analytics && (
          <DashboardView
            analytics={analytics}
            isSuperAdmin={role === 'SUPER_ADMIN'}
            onNavigate={(tab) => handleSelectAdminTab(tab as AdminTab)}
            onOpenAddDoctor={() => {
              resetDoctorForm();
              setShowCreateDoctorModal(true);
            }}
          />
        )}

        {/* TAB: DOCTORS */}
        {adminTab === 'doctors' && (
          <DoctorsManagement
            onNotify={(msg, type) => (type === 'success' ? setSuccessMsg(msg) : setErrorMsg(msg))}
            isSupportStaff={isSupportStaff}
          />
        )}

        {/* TAB: PATIENTS */}
        {adminTab === 'patients' && (
          <PatientsManagement
            onNotify={(msg, type) => (type === 'success' ? setSuccessMsg(msg) : setErrorMsg(msg))}
            isSupportStaff={isSupportStaff}
          />
        )}

        {/* TAB: APPOINTMENTS */}
        {adminTab === 'appointments' && (
          <div style={styles.card}>
            <table style={styles.table}>
              <thead>
                <tr style={styles.thRow}>
                  <th style={styles.th}>Date & Time</th>
                  <th style={styles.th}>Patient</th>
                  <th style={styles.th}>Doctor</th>
                  <th style={styles.th}>Reason</th>
                  <th style={styles.th}>Status</th>
                  <th style={styles.th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((a) => (
                  <tr key={a.id} style={styles.tr}>
                    <td style={styles.td}>
                      <div style={{ fontWeight: 600 }}>{a.appointment_date}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>{a.appointment_time}</div>
                    </td>
                    <td style={styles.td}>{a.patient_name}</td>
                    <td style={styles.td}>{a.doctor_name}</td>
                    <td style={styles.td}>{a.visit_reason || 'Routine Consultation'}</td>
                    <td style={styles.td}><span style={styles.badge}>{a.status}</span></td>
                    <td style={styles.td}>
                      {!isSupportStaff && a.status === 'CONFIRMED' && (
                        <button
                          onClick={() => handleCancelAppointment(a.id)}
                          style={{ ...styles.actionBtn, background: '#991b1b', color: '#fff' }}
                        >
                          Cancel Slot
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB: CONTENT */}
        {adminTab === 'content' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div style={styles.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 16, color: '#0F5C5E' }}>Clinical Biomarker Reference Ranges</h3>
                {!isSupportStaff && (
                  <button onClick={() => setShowBiomarkerModal(true)} style={styles.primaryButton}>
                    + New Biomarker Range
                  </button>
                )}
              </div>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>Test Name</th>
                    <th style={styles.th}>Canonical Name</th>
                    <th style={styles.th}>Category</th>
                    <th style={styles.th}>Unit</th>
                    <th style={styles.th}>Reference Range</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {biomarkers.map((b) => (
                    <tr key={b.id} style={styles.tr}>
                      <td style={styles.td}><strong>{b.test_name}</strong></td>
                      <td style={styles.td}>{b.canonical_name}</td>
                      <td style={styles.td}>{b.category}</td>
                      <td style={styles.td}>{b.default_unit || '-'}</td>
                      <td style={styles.td}>{b.ref_min ?? '-'} to {b.ref_max ?? '-'}</td>
                      <td style={styles.td}>
                        {!isSupportStaff && (
                          <button
                            onClick={() => handleDeleteBiomarker(b.id)}
                            style={{ ...styles.actionBtn, background: '#991b1b', color: '#fff' }}
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={styles.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 16, color: '#0F5C5E' }}>Patient Terminology Glossary</h3>
                {!isSupportStaff && (
                  <button onClick={() => setShowGlossaryModal(true)} style={styles.primaryButton}>
                    + New Glossary Term
                  </button>
                )}
              </div>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>Medical Term</th>
                    <th style={styles.th}>Plain-English Definition</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {glossary.map((g) => (
                    <tr key={g.id} style={styles.tr}>
                      <td style={styles.td}><strong>{g.term}</strong></td>
                      <td style={styles.td}>{g.definition}</td>
                      <td style={styles.td}>
                        {!isSupportStaff && (
                          <button
                            onClick={() => handleDeleteGlossary(g.id)}
                            style={{ ...styles.actionBtn, background: '#991b1b', color: '#fff' }}
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB: AI REVIEW */}
        {adminTab === 'ai_review' && (
          <div style={styles.card}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: 16, color: '#0F5C5E' }}>AI Clinical Recommendation Review Queue</h3>
            <table style={styles.table}>
              <thead>
                <tr style={styles.thRow}>
                  <th style={styles.th}>Primary Concern</th>
                  <th style={styles.th}>Recommended Specialty</th>
                  <th style={styles.th}>Confidence</th>
                  <th style={styles.th}>Review Status</th>
                  <th style={styles.th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {aiReviews.map((r) => (
                  <tr key={r.id} style={styles.tr}>
                    <td style={styles.td}>{r.primary_concern || 'Lab Assessment'}</td>
                    <td style={styles.td}><strong>{r.specialty_name}</strong></td>
                    <td style={styles.td}>{Math.round((r.confidence_score || 0) * 100)}%</td>
                    <td style={styles.td}><span style={styles.badge}>{r.review_status}</span></td>
                    <td style={styles.td}>
                      {!isSupportStaff && (
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            onClick={() => handleReviewAI(r.id, 'APPROVE')}
                            style={{ ...styles.actionBtn, background: '#166534', color: '#fff' }}
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReviewAI(r.id, 'FLAG')}
                            style={{ ...styles.actionBtn, background: '#854d0e', color: '#fff' }}
                          >
                            Flag
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB: USER MANAGEMENT (SUPER ADMIN ONLY) */}
        {adminTab === 'user_management' && (
          <UserManagement
            onNotify={(msg, type) => (type === 'success' ? setSuccessMsg(msg) : setErrorMsg(msg))}
          />
        )}

        {/* TAB: AI TRACE & OBSERVABILITY (SUPER ADMIN ONLY) */}
        {adminTab === 'ai_trace' && (
          <AITraceView
            onNotify={(msg, type) => (type === 'success' ? setSuccessMsg(msg) : setErrorMsg(msg))}
          />
        )}
      </div>

      {/* MODAL: CREATE BIOMARKER */}
      {showBiomarkerModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <h3 style={{ margin: '0 0 16px 0', color: '#0F5C5E' }}>Create Biomarker Reference Range</h3>
            <form onSubmit={handleCreateBiomarker} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={styles.label}>Test Name</label>
                <input
                  type="text"
                  value={newBiomarker.test_name}
                  onChange={(e) => setNewBiomarker({ ...newBiomarker, test_name: e.target.value })}
                  required
                  style={styles.input}
                />
              </div>
              <div>
                <label style={styles.label}>Canonical Name</label>
                <input
                  type="text"
                  value={newBiomarker.canonical_name}
                  onChange={(e) => setNewBiomarker({ ...newBiomarker, canonical_name: e.target.value })}
                  required
                  style={styles.input}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
                <button type="button" onClick={() => setShowBiomarkerModal(false)} style={styles.secondaryButton}>
                  Cancel
                </button>
                <button type="submit" style={styles.primaryButton}>
                  Save Reference Range
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE GLOSSARY */}
      {showGlossaryModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <h3 style={{ margin: '0 0 16px 0', color: '#0F5C5E' }}>Create Glossary Term</h3>
            <form onSubmit={handleCreateGlossary} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={styles.label}>Medical Term</label>
                <input
                  type="text"
                  value={newGlossary.term}
                  onChange={(e) => setNewGlossary({ ...newGlossary, term: e.target.value })}
                  required
                  style={styles.input}
                />
              </div>
              <div>
                <label style={styles.label}>Plain-English Definition</label>
                <textarea
                  rows={3}
                  value={newGlossary.definition}
                  onChange={(e) => setNewGlossary({ ...newGlossary, definition: e.target.value })}
                  required
                  style={{ ...styles.input, height: 'auto' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
                <button type="button" onClick={() => setShowGlossaryModal(false)} style={styles.secondaryButton}>
                  Cancel
                </button>
                <button type="submit" style={styles.primaryButton}>
                  Save Term
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Minimalistic Functional Ops Styles
const styles: { [key: string]: React.CSSProperties } = {
  loginContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    background: '#f1f5f9',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  loginCard: {
    background: '#fff',
    padding: 32,
    borderRadius: 8,
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
    width: '100%',
    maxWidth: 440,
  },
  appContainer: {
    display: 'flex',
    minHeight: '100vh',
    fontFamily: 'Inter, system-ui, sans-serif',
    background: '#f8fafc',
  },
  sidebar: {
    width: 250,
    background: '#0F5C5E',
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0,
  },
  mainContent: {
    flex: 1,
    padding: 28,
    overflowY: 'auto',
  },
  topHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    paddingBottom: 16,
    borderBottom: '1px solid #e2e8f0',
  },
  navButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    width: '100%',
    padding: '10px 14px',
    background: 'transparent',
    border: 'none',
    color: '#cbd5e1',
    textAlign: 'left',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    borderRadius: 6,
  },
  activeNavButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    width: '100%',
    padding: '10px 14px',
    background: 'rgba(255,255,255,0.18)',
    border: 'none',
    color: '#fff',
    textAlign: 'left',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    borderRadius: 6,
  },
  logoutButton: {
    width: '100%',
    padding: '8px 12px',
    background: '#1c3d3e',
    color: '#fca5a5',
    border: '1px solid #2d5556',
    borderRadius: 4,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 600,
  },
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 16,
  },
  kpiCard: {
    background: '#fff',
    padding: 20,
    borderRadius: 6,
    border: '1px solid #e2e8f0',
  },
  kpiLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  kpiValue: {
    fontSize: 28,
    fontWeight: 700,
    color: '#0F5C5E',
    marginTop: 8,
  },
  kpiSub: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 6,
  },
  card: {
    background: '#fff',
    padding: 20,
    borderRadius: 6,
    border: '1px solid #e2e8f0',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 13,
  },
  thRow: {
    borderBottom: '2px solid #e2e8f0',
    background: '#f8fafc',
  },
  th: {
    textAlign: 'left',
    padding: '10px 12px',
    color: '#475569',
    fontWeight: 600,
    fontSize: 12,
  },
  tr: {
    borderBottom: '1px solid #f1f5f9',
  },
  td: {
    padding: '12px',
    color: '#334155',
    verticalAlign: 'middle',
  },
  tdBold: {
    padding: '10px 12px',
    color: '#1e293b',
    fontWeight: 600,
    background: '#f8fafc',
    width: '25%',
  },
  badge: {
    display: 'inline-block',
    padding: '3px 8px',
    borderRadius: 4,
    fontSize: 11,
    fontWeight: 700,
    background: '#e2e8f0',
    color: '#475569',
  },
  input: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #cbd5e1',
    borderRadius: 4,
    fontSize: 13,
    boxSizing: 'border-box',
  },
  select: {
    padding: '8px 12px',
    border: '1px solid #cbd5e1',
    borderRadius: 4,
    fontSize: 13,
    background: '#fff',
  },
  label: {
    display: 'block',
    fontSize: 12,
    fontWeight: 600,
    color: '#475569',
    marginBottom: 4,
  },
  primaryButton: {
    padding: '8px 16px',
    background: '#0F5C5E',
    color: '#fff',
    border: 'none',
    borderRadius: 4,
    fontWeight: 600,
    fontSize: 13,
    cursor: 'pointer',
  },
  secondaryButton: {
    padding: '8px 12px',
    background: '#fff',
    color: '#334155',
    border: '1px solid #cbd5e1',
    borderRadius: 4,
    fontWeight: 500,
    fontSize: 13,
    cursor: 'pointer',
  },
  actionBtn: {
    padding: '4px 8px',
    border: 'none',
    borderRadius: 3,
    fontSize: 11,
    fontWeight: 600,
    cursor: 'pointer',
  },
  errorBanner: {
    padding: '10px 14px',
    background: '#fee2e2',
    color: '#991b1b',
    borderRadius: 4,
    fontSize: 13,
    marginBottom: 16,
  },
  successBanner: {
    padding: '10px 14px',
    background: '#dcfce7',
    color: '#166534',
    borderRadius: 4,
    fontSize: 13,
    marginBottom: 16,
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  modalContent: {
    background: '#fff',
    padding: 24,
    borderRadius: 6,
    width: '100%',
    maxWidth: 540,
    boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
  },
};
