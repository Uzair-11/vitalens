import React, { useState, useEffect, useCallback } from 'react';
import {
  Stethoscope,
  Search,
  Filter,
  RotateCcw,
  Plus,
  X,
  CheckCircle2,
  XCircle,
  Power,
  Trash2,
  Eye,
  Key,
  Mail,
  Phone,
  Building,
  MapPin,
  ShieldCheck,
  Clock,
  AlertCircle,
  Loader2,
  Award,
  FileText,
} from 'lucide-react';
import { adminApi } from '../api/adminApi';

interface DoctorsManagementProps {
  onNotify: (msg: string, type: 'success' | 'error') => void;
  isSupportStaff?: boolean;
}

export const DoctorsManagement: React.FC<DoctorsManagementProps> = ({ onNotify, isSupportStaff = false }) => {
  const [doctors, setDoctors] = useState<any[]>([]);
  const [specialties, setSpecialties] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [search, setSearch] = useState('');
  const [specialtyFilter, setSpecialtyFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'true' | 'false'>('all');

  // Modal States
  const [showAddModal, setShowAddModal] = useState(false);
  const [submittingDoctor, setSubmittingDoctor] = useState(false);
  const [viewDoctorCredentials, setViewDoctorCredentials] = useState<any | null>(null);

  // Form State for New Doctor
  const initialDoctorState = {
    full_name: '',
    email: '',
    phone: '',
    registration_number: '',
    registration_council: '',
    state_code: '',
    specialty_id: '',
    qualification: '',
    experience_years: 5,
    clinic_name: '',
    address: '',
    city: 'Ahmedabad',
    consultation_fee: 800,
    temporary_password: '',
    languages: 'English, Hindi',
    bio: '',
  };
  const [newDoctor, setNewDoctor] = useState(initialDoctorState);

  // Escape key handler for closing modals
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showAddModal) setShowAddModal(false);
        if (viewDoctorCredentials) setViewDoctorCredentials(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showAddModal, viewDoctorCredentials]);

  // Load Initial Data
  const loadSpecialtiesAndDoctors = useCallback(async () => {
    setLoading(true);
    try {
      const [specData, docData] = await Promise.all([
        adminApi.getSpecialties(),
        adminApi.getDoctors({
          name: search.trim() || undefined,
          specialty_id: specialtyFilter || undefined,
          verification_status: statusFilter || undefined,
          is_active: activeFilter === 'all' ? undefined : activeFilter === 'true',
        }),
      ]);
      setSpecialties(specData || []);
      setDoctors(docData || []);
      if (specData && specData.length > 0 && !newDoctor.specialty_id) {
        setNewDoctor((prev) => ({ ...prev, specialty_id: specData[0].id }));
      }
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to load doctors or specialties data.', 'error');
    } finally {
      setLoading(false);
    }
  }, [search, specialtyFilter, statusFilter, activeFilter, onNotify]);

  useEffect(() => {
    loadSpecialtiesAndDoctors();
  }, [loadSpecialtiesAndDoctors]);

  // Reset Filters
  const handleClearFilters = () => {
    setSearch('');
    setSpecialtyFilter('');
    setStatusFilter('');
    setActiveFilter('all');
  };

  const hasActiveFilters = Boolean(search || specialtyFilter || statusFilter || activeFilter !== 'all');

  // Generate Random Password
  const handleGeneratePassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%';
    let pwd = '';
    for (let i = 0; i < 12; i++) {
      pwd += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setNewDoctor((prev) => ({ ...prev, temporary_password: pwd }));
  };

  // Create Doctor Account Submit
  const handleCreateDoctorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingDoctor(true);
    try {
      const langArray = newDoctor.languages
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await adminApi.createDoctor({
        email: newDoctor.email.trim(),
        temporary_password: newDoctor.temporary_password.trim() || undefined,
        full_name: newDoctor.full_name.trim(),
        phone: newDoctor.phone.trim() || undefined,
        registration_number: newDoctor.registration_number.trim() || undefined,
        registration_council: newDoctor.registration_council.trim() || undefined,
        state_code: newDoctor.state_code.trim() || undefined,
        specialty_id: newDoctor.specialty_id || (specialties[0]?.id ?? ''),
        qualification: newDoctor.qualification.trim(),
        experience_years: Number(newDoctor.experience_years) || 0,
        clinic_name: newDoctor.clinic_name.trim() || 'VitaLens Partner Health Clinic',
        address: newDoctor.address.trim() || `${newDoctor.city.trim() || 'Ahmedabad'}, India`,
        city: newDoctor.city.trim() || 'Ahmedabad',
        consultation_fee: Number(newDoctor.consultation_fee) || 800,
        bio: newDoctor.bio.trim() || undefined,
        languages: langArray.length > 0 ? langArray : ['English'],
      });

      onNotify(`Doctor account for "${newDoctor.full_name}" created successfully. Credentials generated.`, 'success');
      setShowAddModal(false);
      setNewDoctor({
        ...initialDoctorState,
        specialty_id: specialties[0]?.id || '',
      });
      loadSpecialtiesAndDoctors();
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to create doctor account.', 'error');
    } finally {
      setSubmittingDoctor(false);
    }
  };

  // Verify Doctor
  const handleVerifyDoctor = async (doctorId: string, newStatus: 'VERIFIED' | 'REJECTED') => {
    try {
      await adminApi.verifyDoctor(doctorId, newStatus);
      onNotify(`Practitioner status updated to ${newStatus}.`, 'success');
      loadSpecialtiesAndDoctors();
      if (viewDoctorCredentials?.id === doctorId) {
        setViewDoctorCredentials((prev: any) => ({ ...prev, verification_status: newStatus }));
      }
    } catch (err: any) {
      onNotify(err.response?.data?.detail || `Failed to update verification status to ${newStatus}.`, 'error');
    }
  };

  // Toggle Active
  const handleToggleStatus = async (doctorId: string, currentActive: boolean) => {
    try {
      await adminApi.toggleDoctorStatus(doctorId, !currentActive);
      onNotify(`Practitioner account ${!currentActive ? 'activated' : 'deactivated'}.`, 'success');
      loadSpecialtiesAndDoctors();
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to toggle practitioner status.', 'error');
    }
  };

  // Delete Doctor
  const handleDeleteDoctor = async (doc: any) => {
    if (!window.confirm(`Are you sure you want to remove Dr. ${doc.full_name}? This will revoke practitioner access.`)) {
      return;
    }
    try {
      await adminApi.deleteDoctor(doc.id);
      onNotify(`Practitioner Dr. ${doc.full_name} removed successfully.`, 'success');
      loadSpecialtiesAndDoctors();
      if (viewDoctorCredentials?.id === doc.id) {
        setViewDoctorCredentials(null);
      }
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to remove practitioner.', 'error');
    }
  };

  // Compute Quick Metrics
  const totalCount = doctors.length;
  const verifiedCount = doctors.filter((d) => d.verification_status === 'VERIFIED').length;
  const pendingCount = doctors.filter((d) => d.verification_status === 'PENDING').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Header & Metrics Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: 22, color: '#0f172a', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Stethoscope size={24} color="#0F5C5E" />
            Doctors Management
          </h2>
          <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>
            Onboard, review credentials, verify medical licenses, and manage healthcare practitioners on VitaLens.
          </p>
        </div>

        {!isSupportStaff && (
          <button
            onClick={() => {
              setNewDoctor({
                ...initialDoctorState,
                specialty_id: specialties[0]?.id || '',
              });
              setShowAddModal(true);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 18px',
              background: '#0F5C5E',
              color: '#ffffff',
              border: 'none',
              borderRadius: 6,
              fontWeight: 600,
              fontSize: 13,
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(15, 92, 94, 0.2)',
              transition: 'background 0.15s ease',
            }}
          >
            <Plus size={16} />
            + Add New Doctor
          </button>
        )}
      </div>

      {/* Quick Status Chips */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <div style={quickMetricStyle}>
          <span style={{ fontSize: 12, color: '#64748b', fontWeight: 600 }}>Total Practitioners</span>
          <span style={{ fontSize: 18, color: '#0F5C5E', fontWeight: 700 }}>{totalCount}</span>
        </div>
        <div style={quickMetricStyle}>
          <span style={{ fontSize: 12, color: '#166534', fontWeight: 600 }}>Verified & Active</span>
          <span style={{ fontSize: 18, color: '#166534', fontWeight: 700 }}>{verifiedCount}</span>
        </div>
        <div style={quickMetricStyle}>
          <span style={{ fontSize: 12, color: '#854d0e', fontWeight: 600 }}>Awaiting Verification</span>
          <span style={{ fontSize: 18, color: '#854d0e', fontWeight: 700 }}>{pendingCount}</span>
        </div>
      </div>

      {/* Unified Filter Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '12px 16px',
          background: '#ffffff',
          borderRadius: 8,
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
          flexWrap: 'wrap',
        }}
      >
        {/* Search Input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 240px', background: '#f8fafc', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1' }}>
          <Search size={16} color="#64748b" />
          <input
            type="text"
            placeholder="Search practitioner, clinic, or city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              outline: 'none',
              fontSize: 13,
              width: '100%',
              color: '#1e293b',
            }}
          />
          {search && (
            <button onClick={() => setSearch('')} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}>
              <X size={14} color="#94a3b8" />
            </button>
          )}
        </div>

        {/* Specialty Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 190 }}>
          <Filter size={15} color="#64748b" />
          <select
            value={specialtyFilter}
            onChange={(e) => setSpecialtyFilter(e.target.value)}
            style={{ ...selectStyle, maxWidth: 220 }}
          >
            <option value="">All Specialties ({specialties.length})</option>
            {specialties.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {/* Verification Status Dropdown */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ ...selectStyle, minWidth: 160 }}
        >
          <option value="">All Verifications</option>
          <option value="VERIFIED">Verified</option>
          <option value="PENDING">Pending Review</option>
          <option value="REJECTED">Rejected</option>
        </select>

        {/* Active Status Dropdown */}
        <select
          value={activeFilter}
          onChange={(e) => setActiveFilter(e.target.value as any)}
          style={{ ...selectStyle, minWidth: 130 }}
        >
          <option value="all">All States</option>
          <option value="true">Active Only</option>
          <option value="false">Inactive Only</option>
        </select>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 12px',
              background: '#f1f5f9',
              color: '#475569',
              border: '1px solid #cbd5e1',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={13} />
            Clear Filters
          </button>
        )}
      </div>

      {/* Main Content Area */}
      <div style={{ background: '#ffffff', borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.03)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 48, textAlign: 'center', color: '#0F5C5E', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <Loader2 size={32} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontWeight: 600, fontSize: 14 }}>Loading healthcare practitioners...</span>
          </div>
        ) : doctors.length === 0 ? (
          /* Dedicated Empty State Component */
          <div
            style={{
              padding: '64px 24px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: hasActiveFilters ? '#f1f5f9' : '#ecfdf5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 16,
              }}
            >
              {hasActiveFilters ? (
                <Search size={30} color="#64748b" />
              ) : (
                <Stethoscope size={30} color="#0F5C5E" />
              )}
            </div>

            <h3 style={{ margin: '0 0 8px 0', fontSize: 18, color: '#0f172a', fontWeight: 700 }}>
              {hasActiveFilters ? 'No Practitioners Found Matching Filters' : 'No Healthcare Practitioners Found'}
            </h3>

            <p style={{ margin: '0 0 20px 0', fontSize: 14, color: '#64748b', maxWidth: 460, lineHeight: 1.5 }}>
              {hasActiveFilters
                ? 'No doctors match the selected search, specialty, or verification status. Try adjusting or clearing your filters.'
                : 'Get started by onboarding your first healthcare practitioner to activate appointment booking and clinical care.'}
            </p>

            {hasActiveFilters ? (
              <button
                onClick={handleClearFilters}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '9px 16px',
                  background: '#0F5C5E',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: 13,
                  cursor: 'pointer',
                }}
              >
                <RotateCcw size={15} />
                Clear All Filters
              </button>
            ) : !isSupportStaff ? (
              <button
                onClick={() => {
                  setNewDoctor({
                    ...initialDoctorState,
                    specialty_id: specialties[0]?.id || '',
                  });
                  setShowAddModal(true);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '10px 20px',
                  background: '#0F5C5E',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: 14,
                  cursor: 'pointer',
                  boxShadow: '0 2px 6px rgba(15, 92, 94, 0.25)',
                }}
              >
                <Plus size={16} />
                + Add Your First Doctor
              </button>
            ) : null}
          </div>
        ) : (
          /* Practitioners Table */
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={thStyle}>Practitioner & Clinic</th>
                  <th style={thStyle}>Specialty & City</th>
                  <th style={thStyle}>Contact & License</th>
                  <th style={thStyle}>Consultation Fee</th>
                  <th style={thStyle}>Verification</th>
                  <th style={thStyle}>Status</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {doctors.map((doc) => {
                  const initials = doc.full_name
                    ? doc.full_name
                        .replace(/^Dr\.\s*/i, '')
                        .split(' ')
                        .map((n: string) => n[0])
                        .slice(0, 2)
                        .join('')
                        .toUpperCase()
                    : 'DR';

                  return (
                    <tr
                      key={doc.id}
                      style={{
                        borderBottom: '1px solid #f1f5f9',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      {/* Column 1: Stacked Name & Clinic */}
                      <td style={tdStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <div
                            style={{
                              width: 38,
                              height: 38,
                              borderRadius: '50%',
                              background: '#e0f2fe',
                              color: '#0369a1',
                              fontWeight: 700,
                              fontSize: 13,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0,
                              border: '1px solid #bae6fd',
                            }}
                          >
                            {initials}
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, color: '#0f172a', fontSize: 14 }}>
                              {doc.full_name}
                            </div>
                            <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                              <span style={{ fontWeight: 500, color: '#334155' }}>{doc.clinic_name}</span>
                              {doc.qualification && ` • ${doc.qualification}`}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Column 2: Specialty & City */}
                      <td style={tdStyle}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '3px 8px',
                            background: '#eff6ff',
                            color: '#1d4ed8',
                            borderRadius: 4,
                            fontSize: 12,
                            fontWeight: 600,
                            marginBottom: 4,
                          }}
                        >
                          {doc.specialty_name || 'General Practice'}
                        </span>
                        <div style={{ fontSize: 12, color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 }}>
                          <MapPin size={12} color="#94a3b8" />
                          {doc.city}
                        </div>
                      </td>

                      {/* Column 3: Contact & Medical License */}
                      <td style={tdStyle}>
                        {doc.email && (
                          <div style={{ fontSize: 12, color: '#334155', display: 'flex', alignItems: 'center', gap: 5 }}>
                            <Mail size={12} color="#64748b" />
                            {doc.email}
                          </div>
                        )}
                        {doc.phone && (
                          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2, display: 'flex', alignItems: 'center', gap: 5 }}>
                            <Phone size={12} color="#64748b" />
                            {doc.phone}
                          </div>
                        )}
                        {doc.registration_number && (
                          <div style={{ fontSize: 11, color: '#0F5C5E', fontWeight: 600, marginTop: 3 }}>
                            Lic: {doc.registration_number}
                          </div>
                        )}
                      </td>

                      {/* Column 4: Consultation Fee */}
                      <td style={tdStyle}>
                        <span style={{ fontWeight: 700, color: '#0f172a', fontSize: 14 }}>
                          ₹{doc.consultation_fee}
                        </span>
                        <div style={{ fontSize: 11, color: '#94a3b8' }}>per visit</div>
                      </td>

                      {/* Column 5: Verification Status */}
                      <td style={tdStyle}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            padding: '4px 9px',
                            borderRadius: 12,
                            fontSize: 12,
                            fontWeight: 600,
                            background:
                              doc.verification_status === 'VERIFIED'
                                ? '#dcfce7'
                                : doc.verification_status === 'PENDING'
                                ? '#fef9c3'
                                : '#fee2e2',
                            color:
                              doc.verification_status === 'VERIFIED'
                                ? '#166534'
                                : doc.verification_status === 'PENDING'
                                ? '#854d0e'
                                : '#991b1b',
                          }}
                        >
                          {doc.verification_status === 'VERIFIED' ? (
                            <ShieldCheck size={13} />
                          ) : doc.verification_status === 'PENDING' ? (
                            <Clock size={13} />
                          ) : (
                            <AlertCircle size={13} />
                          )}
                          {doc.verification_status}
                        </span>
                      </td>

                      {/* Column 6: Account Active Status */}
                      <td style={tdStyle}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 5,
                            fontSize: 12,
                            fontWeight: 600,
                            color: doc.is_active ? '#166534' : '#64748b',
                          }}
                        >
                          <span
                            style={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              background: doc.is_active ? '#22c55e' : '#cbd5e1',
                            }}
                          />
                          {doc.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>

                      {/* Column 7: Actions */}
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                          {/* View Credentials */}
                          <button
                            onClick={() => setViewDoctorCredentials(doc)}
                            title="View Credentials & Bio"
                            style={actionIconButtonStyle}
                          >
                            <Eye size={15} color="#334155" />
                          </button>

                          {!isSupportStaff && (
                            <>
                              {/* Verify Button */}
                              {doc.verification_status !== 'VERIFIED' && (
                                <button
                                  onClick={() => handleVerifyDoctor(doc.id, 'VERIFIED')}
                                  title="Approve & Verify Practitioner"
                                  style={{
                                    ...actionIconButtonStyle,
                                    background: '#dcfce7',
                                    borderColor: '#bbf7d0',
                                  }}
                                >
                                  <CheckCircle2 size={15} color="#166534" />
                                </button>
                              )}

                              {/* Reject Button */}
                              {doc.verification_status !== 'REJECTED' && (
                                <button
                                  onClick={() => handleVerifyDoctor(doc.id, 'REJECTED')}
                                  title="Reject Credentials"
                                  style={{
                                    ...actionIconButtonStyle,
                                    background: '#fee2e2',
                                    borderColor: '#fecaca',
                                  }}
                                >
                                  <XCircle size={15} color="#991b1b" />
                                </button>
                              )}

                              {/* Toggle Active / Deactivate */}
                              <button
                                onClick={() => handleToggleStatus(doc.id, doc.is_active)}
                                title={doc.is_active ? 'Deactivate Practitioner' : 'Activate Practitioner'}
                                style={{
                                  ...actionIconButtonStyle,
                                  background: doc.is_active ? '#f8fafc' : '#fef2f2',
                                }}
                              >
                                <Power size={15} color={doc.is_active ? '#64748b' : '#ef4444'} />
                              </button>

                              {/* Delete Doctor */}
                              <button
                                onClick={() => handleDeleteDoctor(doc)}
                                title="Remove Practitioner"
                                style={{
                                  ...actionIconButtonStyle,
                                  background: '#fff1f2',
                                  borderColor: '#ffe4e6',
                                }}
                              >
                                <Trash2 size={15} color="#e11d48" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* PAGE 2 / MODAL: ADD NEW DOCTOR MODAL                                      */}
      {/* ========================================================================= */}
      {showAddModal && (
        <div
          onClick={() => setShowAddModal(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 16,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#ffffff',
              borderRadius: 10,
              width: '100%',
              maxWidth: 680,
              maxHeight: '92vh',
              overflowY: 'auto',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
              border: '1px solid #e2e8f0',
              padding: 24,
            }}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16, borderBottom: '1px solid #f1f5f9', paddingBottom: 14 }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: 18, fontWeight: 700, color: '#0F5C5E', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Stethoscope size={20} />
                  Add New Doctor & Login Account
                </h3>
                <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>
                  Provisions a healthcare practitioner profile and creates their initial login credentials.
                </p>
              </div>

              {/* Explicit X Close Button */}
              <button
                onClick={() => setShowAddModal(false)}
                title="Close (Esc)"
                style={{
                  background: '#f1f5f9',
                  border: 'none',
                  borderRadius: 6,
                  width: 32,
                  height: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  color: '#64748b',
                }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleCreateDoctorSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              {/* Group 1: Practitioner Identity & Medical Credentials */}
              <div style={formSectionStyle}>
                <div style={sectionHeaderStyle}>
                  <Award size={15} color="#0F5C5E" />
                  <span>1. Practitioner Identity & Medical License</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>Full Name *</label>
                    <input
                      type="text"
                      placeholder="e.g. Dr. Rajesh Sharma"
                      value={newDoctor.full_name}
                      onChange={(e) => setNewDoctor({ ...newDoctor, full_name: e.target.value })}
                      required
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>Medical License / Reg No. *</label>
                    <input
                      type="text"
                      placeholder="e.g. G-34821 / MCI-2018-912"
                      value={newDoctor.registration_number}
                      onChange={(e) => setNewDoctor({ ...newDoctor, registration_number: e.target.value })}
                      required
                      style={inputStyle}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>Registration Council / State</label>
                    <input
                      type="text"
                      placeholder="e.g. Gujarat Medical Council"
                      value={newDoctor.registration_council}
                      onChange={(e) => setNewDoctor({ ...newDoctor, registration_council: e.target.value })}
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>Medical Specialty * ({specialties.length} Available in India)</label>
                    <select
                      value={newDoctor.specialty_id}
                      onChange={(e) => setNewDoctor({ ...newDoctor, specialty_id: e.target.value })}
                      required
                      style={inputStyle}
                    >
                      <option value="">-- Select Medical Specialty --</option>
                      {specialties.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>Qualifications *</label>
                    <input
                      type="text"
                      placeholder="e.g. MBBS, MD (Endocrinology)"
                      value={newDoctor.qualification}
                      onChange={(e) => setNewDoctor({ ...newDoctor, qualification: e.target.value })}
                      required
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>Experience (Years)</label>
                    <input
                      type="number"
                      min={0}
                      max={60}
                      value={newDoctor.experience_years}
                      onChange={(e) => setNewDoctor({ ...newDoctor, experience_years: parseInt(e.target.value) || 0 })}
                      style={inputStyle}
                    />
                  </div>
                </div>
              </div>

              {/* Group 2: Practice & Clinic Location */}
              <div style={formSectionStyle}>
                <div style={sectionHeaderStyle}>
                  <Building size={15} color="#0F5C5E" />
                  <span>2. Practice & Clinic Location</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>Clinic / Hospital Name</label>
                    <input
                      type="text"
                      placeholder="e.g. VitaLens Endocrine Clinic"
                      value={newDoctor.clinic_name}
                      onChange={(e) => setNewDoctor({ ...newDoctor, clinic_name: e.target.value })}
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>City</label>
                    <input
                      type="text"
                      placeholder="e.g. Ahmedabad"
                      value={newDoctor.city}
                      onChange={(e) => setNewDoctor({ ...newDoctor, city: e.target.value })}
                      style={inputStyle}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>Clinic Full Address</label>
                    <input
                      type="text"
                      placeholder="e.g. 402 Medical Arts Plaza, Bodakdev"
                      value={newDoctor.address}
                      onChange={(e) => setNewDoctor({ ...newDoctor, address: e.target.value })}
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>Consultation Fee (₹)</label>
                    <input
                      type="number"
                      min={0}
                      step={50}
                      value={newDoctor.consultation_fee}
                      onChange={(e) => setNewDoctor({ ...newDoctor, consultation_fee: parseFloat(e.target.value) || 0 })}
                      style={inputStyle}
                    />
                  </div>
                </div>
              </div>

              {/* Group 3: Login Account & Authentication Strategy */}
              <div style={formSectionStyle}>
                <div style={sectionHeaderStyle}>
                  <Key size={15} color="#0F5C5E" />
                  <span>3. Login Account & Authentication Credentials</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>Login Email Address *</label>
                    <input
                      type="email"
                      placeholder="doctor@vitalens.com"
                      value={newDoctor.email}
                      onChange={(e) => setNewDoctor({ ...newDoctor, email: e.target.value })}
                      required
                      style={inputStyle}
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>Mobile Phone Number *</label>
                    <input
                      type="tel"
                      placeholder="+91 98765 43210"
                      value={newDoctor.phone}
                      onChange={(e) => setNewDoctor({ ...newDoctor, phone: e.target.value })}
                      required
                      style={inputStyle}
                    />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <label style={{ ...labelStyle, margin: 0 }}>Initial / Temporary Password</label>
                    <button
                      type="button"
                      onClick={handleGeneratePassword}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#0F5C5E',
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      <Key size={13} />
                      Generate Secure Password
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder="Leave blank to auto-generate, or specify temporary password"
                    value={newDoctor.temporary_password}
                    onChange={(e) => setNewDoctor({ ...newDoctor, temporary_password: e.target.value })}
                    style={{ ...inputStyle, fontFamily: 'monospace' }}
                  />
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                    The practitioner will use this credential to log in and will be required to change it on initial sign-in.
                  </div>
                </div>
              </div>

              {/* Group 4: Additional Information */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={labelStyle}>Languages Spoken</label>
                  <input
                    type="text"
                    placeholder="English, Hindi, Gujarati"
                    value={newDoctor.languages}
                    onChange={(e) => setNewDoctor({ ...newDoctor, languages: e.target.value })}
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={labelStyle}>Practitioner Bio / Summary (Optional)</label>
                  <input
                    type="text"
                    placeholder="Brief professional summary..."
                    value={newDoctor.bio}
                    onChange={(e) => setNewDoctor({ ...newDoctor, bio: e.target.value })}
                    style={inputStyle}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8, paddingTop: 16, borderTop: '1px solid #f1f5f9' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  disabled={submittingDoctor}
                  style={secondaryButtonStyle}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingDoctor}
                  style={{
                    ...primaryButtonStyle,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    opacity: submittingDoctor ? 0.7 : 1,
                  }}
                >
                  {submittingDoctor ? (
                    <>
                      <Loader2 size={16} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                      Creating Account...
                    </>
                  ) : (
                    'Create Doctor Account'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: VIEW CREDENTIALS & PRACTITIONER DETAILS                            */}
      {/* ========================================================================= */}
      {viewDoctorCredentials && (
        <div
          onClick={() => setViewDoctorCredentials(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 16,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#ffffff',
              borderRadius: 10,
              width: '100%',
              maxWidth: 580,
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
              border: '1px solid #e2e8f0',
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderBottom: '1px solid #f1f5f9', paddingBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 40, height: 40, borderRadius: '50%', background: '#ecfdf5', color: '#0F5C5E', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Award size={20} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: 17, color: '#0f172a' }}>{viewDoctorCredentials.full_name}</h3>
                  <div style={{ fontSize: 12, color: '#64748b' }}>
                    {viewDoctorCredentials.specialty_name || 'General Practice'} • {viewDoctorCredentials.qualification}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setViewDoctorCredentials(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, background: '#f8fafc', padding: 14, borderRadius: 8 }}>
                <div>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>MEDICAL LICENSE NUMBER</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#0F5C5E', marginTop: 2 }}>
                    {viewDoctorCredentials.registration_number || 'Not Submitted'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>REGISTRATION COUNCIL</div>
                  <div style={{ fontSize: 13, color: '#1e293b', marginTop: 2 }}>
                    {viewDoctorCredentials.registration_council || 'State Medical Council'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>EMAIL ADDRESS</div>
                  <div style={{ fontSize: 13, color: '#1e293b', marginTop: 2 }}>{viewDoctorCredentials.email || 'None'}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>PHONE NUMBER</div>
                  <div style={{ fontSize: 13, color: '#1e293b', marginTop: 2 }}>{viewDoctorCredentials.phone || 'None'}</div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>CLINIC LOCATION & FEE</div>
                <div style={{ fontSize: 13, color: '#1e293b', marginTop: 2 }}>
                  {viewDoctorCredentials.clinic_name} — {viewDoctorCredentials.address || viewDoctorCredentials.city}
                </div>
                <div style={{ fontSize: 12, color: '#0F5C5E', fontWeight: 600, marginTop: 2 }}>
                  Consultation Fee: ₹{viewDoctorCredentials.consultation_fee}
                </div>
              </div>

              {viewDoctorCredentials.bio && (
                <div>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>PROFESSIONAL BIO</div>
                  <p style={{ margin: '4px 0 0 0', fontSize: 13, color: '#334155', lineHeight: 1.5 }}>
                    {viewDoctorCredentials.bio}
                  </p>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 14, borderTop: '1px solid #f1f5f9' }}>
                <span
                  style={{
                    padding: '4px 10px',
                    borderRadius: 12,
                    fontSize: 12,
                    fontWeight: 700,
                    background:
                      viewDoctorCredentials.verification_status === 'VERIFIED'
                        ? '#dcfce7'
                        : viewDoctorCredentials.verification_status === 'PENDING'
                        ? '#fef9c3'
                        : '#fee2e2',
                    color:
                      viewDoctorCredentials.verification_status === 'VERIFIED'
                        ? '#166534'
                        : viewDoctorCredentials.verification_status === 'PENDING'
                        ? '#854d0e'
                        : '#991b1b',
                  }}
                >
                  Status: {viewDoctorCredentials.verification_status}
                </span>

                <div style={{ display: 'flex', gap: 8 }}>
                  {!isSupportStaff && viewDoctorCredentials.verification_status !== 'VERIFIED' && (
                    <button
                      onClick={() => handleVerifyDoctor(viewDoctorCredentials.id, 'VERIFIED')}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '7px 14px',
                        background: '#166534',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      <CheckCircle2 size={14} />
                      Verify Doctor
                    </button>
                  )}
                  {!isSupportStaff && viewDoctorCredentials.verification_status !== 'REJECTED' && (
                    <button
                      onClick={() => handleVerifyDoctor(viewDoctorCredentials.id, 'REJECTED')}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '7px 14px',
                        background: '#991b1b',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      <XCircle size={14} />
                      Reject
                    </button>
                  )}
                  <button
                    onClick={() => setViewDoctorCredentials(null)}
                    style={secondaryButtonStyle}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// UI Styling Constants
const quickMetricStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  padding: '8px 14px',
  background: '#ffffff',
  borderRadius: 6,
  border: '1px solid #e2e8f0',
};

const selectStyle: React.CSSProperties = {
  padding: '8px 12px',
  border: '1px solid #cbd5e1',
  borderRadius: 6,
  fontSize: 13,
  background: '#ffffff',
  color: '#1e293b',
  outline: 'none',
  cursor: 'pointer',
};

const thStyle: React.CSSProperties = {
  padding: '12px 16px',
  fontWeight: 600,
  color: '#475569',
  fontSize: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
};

const tdStyle: React.CSSProperties = {
  padding: '14px 16px',
  verticalAlign: 'middle',
};

const actionIconButtonStyle: React.CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: 6,
  border: '1px solid #cbd5e1',
  background: '#ffffff',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  transition: 'all 0.15s ease',
};

const formSectionStyle: React.CSSProperties = {
  background: '#f8fafc',
  padding: 16,
  borderRadius: 8,
  border: '1px solid #e2e8f0',
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
};

const sectionHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  fontSize: 13,
  fontWeight: 700,
  color: '#0F5C5E',
  marginBottom: 2,
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  fontWeight: 600,
  color: '#475569',
  marginBottom: 4,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  border: '1px solid #cbd5e1',
  borderRadius: 6,
  fontSize: 13,
  color: '#1e293b',
  background: '#ffffff',
  boxSizing: 'border-box',
  outline: 'none',
};

const primaryButtonStyle: React.CSSProperties = {
  padding: '9px 18px',
  background: '#0F5C5E',
  color: '#ffffff',
  border: 'none',
  borderRadius: 6,
  fontWeight: 600,
  fontSize: 13,
  cursor: 'pointer',
};

const secondaryButtonStyle: React.CSSProperties = {
  padding: '9px 16px',
  background: '#ffffff',
  color: '#475569',
  border: '1px solid #cbd5e1',
  borderRadius: 6,
  fontWeight: 600,
  fontSize: 13,
  cursor: 'pointer',
};
