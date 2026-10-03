import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Users,
  Search,
  RotateCcw,
  Eye,
  BarChart2,
  X,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Calendar,
  FileText,
  Mail,
  Phone,
  MapPin,
  Activity,
  CheckCircle2,
  UserX,
  UserCheck,
  Loader2,
  Power,
  Shield,
  HeartPulse,
  Clock,
  ShieldCheck,
  CreditCard,
  Building,
  Thermometer,
  Copy,
  Check,
  FileCheck,
  ShieldAlert,
  Download,
} from 'lucide-react';
import { adminApi } from '../api/adminApi';

const getMediaUrl = (pathOrUrl?: string | null): string | null => {
  if (!pathOrUrl) return null;
  if (pathOrUrl.startsWith('http://') || pathOrUrl.startsWith('https://') || pathOrUrl.startsWith('data:')) {
    return pathOrUrl;
  }
  const backendBase = 'http://localhost:8000';
  return `${backendBase}${pathOrUrl.startsWith('/') ? '' : '/'}${pathOrUrl}`;
};

const formatFileSize = (bytes?: number | null): string => {
  if (!bytes || bytes <= 0) return '1.2 MB';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getReportTag = (type?: string | null): { label: string; color: string; bg: string; border: string } => {
  const t = (type || '').toLowerCase();
  if (t.includes('blood') || t.includes('cbc') || t.includes('hemogram')) {
    return { label: 'Blood Panel', color: '#b91c1c', bg: '#fef2f2', border: '#fecaca' };
  }
  if (t.includes('lipid') || t.includes('cholesterol') || t.includes('cardiac')) {
    return { label: 'Lipid Profile', color: '#c2410c', bg: '#fff7ed', border: '#fed7aa' };
  }
  if (t.includes('liver') || t.includes('lft') || t.includes('hepatic')) {
    return { label: 'Liver Function', color: '#b45309', bg: '#fffbeb', border: '#fde68a' };
  }
  if (t.includes('renal') || t.includes('kidney') || t.includes('kft') || t.includes('urine')) {
    return { label: 'Renal / Urine', color: '#0369a1', bg: '#f0f9ff', border: '#bae6fd' };
  }
  if (t.includes('thyroid') || t.includes('tsh')) {
    return { label: 'Thyroid Panel', color: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' };
  }
  if (t.includes('x-ray') || t.includes('scan') || t.includes('mri') || t.includes('imaging')) {
    return { label: 'Imaging / X-Ray', color: '#0f766e', bg: '#f0fdfa', border: '#99f6e4' };
  }
  return { label: type || 'Diagnostic', color: '#0F5C5E', bg: '#f0fdfa', border: '#ccfbf1' };
};

interface PatientAvatarProps {
  avatarUrl?: string | null;
  name: string;
  size?: number;
  fontSize?: number;
  style?: React.CSSProperties;
}

const PatientAvatar: React.FC<PatientAvatarProps> = ({
  avatarUrl,
  name,
  size = 38,
  fontSize = 13,
  style,
}) => {
  const [imgFailed, setImgFailed] = useState(false);
  const resolvedUrl = getMediaUrl(avatarUrl);

  useEffect(() => {
    setImgFailed(false);
  }, [avatarUrl]);

  const initials = useMemo(() => {
    if (!name) return 'PT';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }, [name]);

  if (resolvedUrl && !imgFailed) {
    return (
      <img
        src={resolvedUrl}
        alt={name || 'Patient'}
        onError={() => setImgFailed(true)}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          objectFit: 'cover',
          flexShrink: 0,
          border: '1.5px solid #cbd5e1',
          background: '#f8fafc',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
          ...style,
        }}
      />
    );
  }

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: '#f0fdf4',
        color: '#166534',
        fontWeight: 700,
        fontSize,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        border: '1.5px solid #bbf7d0',
        userSelect: 'none',
        textTransform: 'uppercase',
        ...style,
      }}
    >
      {initials}
    </div>
  );
};

interface PatientsManagementProps {
  onNotify: (msg: string, type: 'success' | 'error') => void;
  isSupportStaff?: boolean;
}

export const PatientsManagement: React.FC<PatientsManagementProps> = ({ onNotify, isSupportStaff = false }) => {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Search & Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'suspended'>('all');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Modal / Drawer states
  const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [activeDetailTab, setActiveDetailTab] = useState<'profile' | 'consultations' | 'reports' | 'symptoms' | 'security'>('profile');
  const [pendingStatusToggleUser, setPendingStatusToggleUser] = useState<any | null>(null);
  const [isTogglingStatus, setIsTogglingStatus] = useState(false);
  const [statusReason, setStatusReason] = useState('');
  const [statusReasonError, setStatusReasonError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState(false);

  // ABHA editing state
  const [isEditingAbha, setIsEditingAbha] = useState(false);
  const [abhaInput, setAbhaInput] = useState('');
  const [isSavingAbha, setIsSavingAbha] = useState(false);

  const handleStartEditAbha = () => {
    setAbhaInput(selectedPatient?.abha_number || '');
    setIsEditingAbha(true);
  };

  const handleAbhaInputChange = (val: string) => {
    const digits = val.replace(/[^0-9]/g, '').slice(0, 14);
    let formatted = digits;
    if (digits.length > 10) {
      formatted = `${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6, 10)}-${digits.slice(10)}`;
    } else if (digits.length > 6) {
      formatted = `${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6)}`;
    } else if (digits.length > 2) {
      formatted = `${digits.slice(0, 2)}-${digits.slice(2)}`;
    }
    setAbhaInput(formatted);
  };

  const handleSaveAbha = async () => {
    if (!selectedPatient) return;
    setIsSavingAbha(true);
    try {
      const res = await adminApi.updateUserAbha(selectedPatient.id, abhaInput.trim());
      setSelectedPatient((prev: any) => prev ? { ...prev, abha_number: res.abha_number } : null);
      setPatients((prev) => prev.map((p) => p.id === selectedPatient.id ? { ...p, abha_number: res.abha_number } : p));
      setIsEditingAbha(false);
      onNotify(res.message || 'ABHA Health ID updated successfully.', 'success');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to update ABHA ID.';
      onNotify(msg, 'error');
    } finally {
      setIsSavingAbha(false);
    }
  };

  const handleUnlinkAbha = async () => {
    if (!selectedPatient) return;
    setIsSavingAbha(true);
    try {
      await adminApi.updateUserAbha(selectedPatient.id, '');
      setSelectedPatient((prev: any) => prev ? { ...prev, abha_number: null } : null);
      setPatients((prev) => prev.map((p) => p.id === selectedPatient.id ? { ...p, abha_number: null } : p));
      setIsEditingAbha(false);
      onNotify('ABHA Health ID unlinked successfully.', 'success');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to unlink ABHA ID.';
      onNotify(msg, 'error');
    } finally {
      setIsSavingAbha(false);
    }
  };

  // 300ms Debounce on Search Input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setCurrentPage(1); // Reset to page 1 on new search
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Load Patients from API
  const loadPatients = useCallback(async () => {
    setLoading(true);
    try {
      const activeParam =
        statusFilter === 'active' ? true : statusFilter === 'suspended' ? false : undefined;

      const data = await adminApi.getUsers({
        search: debouncedSearch.trim() || undefined,
        role: 'PATIENT',
        is_active: activeParam,
        limit: 100,
      });
      setPatients(data || []);
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to fetch patients list.', 'error');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, statusFilter, onNotify]);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  // Escape key handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedPatient(null);
        setPendingStatusToggleUser(null);
        setStatusReason('');
        setStatusReasonError(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Compute Summary Statistics
  const totalCount = patients.length;
  const activeCount = useMemo(() => patients.filter((p) => p.is_active).length, [patients]);
  const suspendedCount = useMemo(() => patients.filter((p) => !p.is_active).length, [patients]);
  const totalVisitsTracked = useMemo(
    () => patients.reduce((acc, p) => acc + (p.appointments_count || 0), 0),
    [patients]
  );

  // Client-side pagination slice
  const totalFiltered = patients.length;
  const totalPages = Math.max(1, Math.ceil(totalFiltered / rowsPerPage));
  const startIndex = (currentPage - 1) * rowsPerPage;
  const displayedPatients = useMemo(
    () => patients.slice(startIndex, startIndex + rowsPerPage),
    [patients, startIndex, rowsPerPage]
  );

  // Reset Filters
  const handleClearFilters = () => {
    setSearchTerm('');
    setDebouncedSearch('');
    setStatusFilter('all');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(searchTerm || statusFilter !== 'all');

  // Handle Account Suspension / Reactivation Confirmation
  const handleConfirmStatusToggle = async () => {
    if (!pendingStatusToggleUser) return;
    if (pendingStatusToggleUser.is_active && !statusReason.trim()) {
      setStatusReasonError('Please enter a reason before suspending this account.');
      return;
    }
    setStatusReasonError(null);
    setIsTogglingStatus(true);
    const newActiveState = !pendingStatusToggleUser.is_active;
    const actionLabel = newActiveState ? 'reactivated' : 'suspended';

    try {
      await adminApi.toggleUserStatus(pendingStatusToggleUser.id, newActiveState, statusReason.trim() || undefined);
      onNotify(`Patient account for "${pendingStatusToggleUser.full_name}" ${actionLabel} successfully.`, 'success');
      setPendingStatusToggleUser(null);
      setStatusReason('');
      setStatusReasonError(null);
      if (selectedPatient?.id === pendingStatusToggleUser.id) {
        setSelectedPatient((prev: any) => ({ ...prev, is_active: newActiveState }));
      }
      loadPatients();
    } catch (err: any) {
      onNotify(err.response?.data?.detail || `Failed to ${actionLabel} patient account.`, 'error');
    } finally {
      setIsTogglingStatus(false);
    }
  };

  // Open Full Detail / Metrics
  const handleOpenPatientDetails = async (
    patient: any,
    initialTab: 'profile' | 'consultations' | 'reports' | 'symptoms' | 'security' = 'profile'
  ) => {
    setActiveDetailTab(initialTab);
    setSelectedPatient(patient);
    setIsDetailLoading(true);
    try {
      const detailed = await adminApi.getUserDetail(patient.id);
      setSelectedPatient((prev: any) => ({ ...(prev || {}), ...detailed }));
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Could not load complete patient details.', 'error');
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleCopyId = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  // Helper: Calculate Age from DOB
  const calculateAge = (dobString: string | null) => {
    if (!dobString) return null;
    const dob = new Date(dobString);
    if (isNaN(dob.getTime())) return null;
    const diffMs = Date.now() - dob.getTime();
    const ageDt = new Date(diffMs);
    return Math.abs(ageDt.getUTCFullYear() - 1970);
  };

  // Helper: Format Joined Date
  const formatJoinedDate = (dateString: string | null) => {
    if (!dateString) return '—';
    try {
      const d = new Date(dateString);
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateString;
    }
  };

  // Helper: Format Date & Time with timestamp
  const formatDateTime = (dateString?: string | null) => {
    if (!dateString) return '—';
    try {
      const d = new Date(dateString);
      if (isNaN(d.getTime())) return dateString;
      return d.toLocaleString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: 22, color: '#0f172a', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 10 }}>
            <Users size={24} color="#0F5C5E" />
            Patients Management
          </h2>
          <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>
            Monitor registered patients, view clinical consultations and diagnostic report activity, and manage account statuses.
          </p>
        </div>
      </div>

      {/* Header KPI Stats Cards */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <div style={kpiCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ ...kpiIconBox, background: '#e0f2fe', color: '#0284c7' }}>
              <Users size={18} />
            </div>
            <div>
              <div style={kpiLabelStyle}>Total Patients</div>
              <div style={{ ...kpiValueStyle, color: '#0f172a' }}>{totalCount}</div>
            </div>
          </div>
        </div>

        <div style={kpiCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ ...kpiIconBox, background: '#dcfce7', color: '#166534' }}>
              <UserCheck size={18} />
            </div>
            <div>
              <div style={{ ...kpiLabelStyle, color: '#166534' }}>Active Accounts</div>
              <div style={{ ...kpiValueStyle, color: '#166534' }}>{activeCount}</div>
            </div>
          </div>
        </div>

        <div style={kpiCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ ...kpiIconBox, background: suspendedCount > 0 ? '#fee2e2' : '#f1f5f9', color: suspendedCount > 0 ? '#b91c1c' : '#64748b' }}>
              <UserX size={18} />
            </div>
            <div>
              <div style={{ ...kpiLabelStyle, color: suspendedCount > 0 ? '#b91c1c' : '#64748b' }}>Suspended Accounts</div>
              <div style={{ ...kpiValueStyle, color: suspendedCount > 0 ? '#b91c1c' : '#64748b' }}>{suspendedCount}</div>
            </div>
          </div>
        </div>

        <div style={kpiCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ ...kpiIconBox, background: '#fef3c7', color: '#b45309' }}>
              <Calendar size={18} />
            </div>
            <div>
              <div style={kpiLabelStyle}>Consultations Tracked</div>
              <div style={{ ...kpiValueStyle, color: '#0F5C5E' }}>{totalVisitsTracked}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Unified Filter Bar with Instant Debounced Search */}
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
        {/* Instant Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            flex: '1 1 280px',
            background: '#f8fafc',
            padding: '8px 12px',
            borderRadius: 6,
            border: '1px solid #cbd5e1',
          }}
        >
          <Search size={16} color="#64748b" />
          <input
            type="text"
            placeholder="Search patient name, email, phone, or ABHA ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              outline: 'none',
              fontSize: 13,
              width: '100%',
              color: '#1e293b',
            }}
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
              title="Clear search"
            >
              <X size={14} color="#94a3b8" />
            </button>
          )}
        </div>

        {/* Quick Status Filter Tabs / Dropdown */}
        <div style={{ display: 'flex', background: '#f1f5f9', borderRadius: 6, padding: 3, gap: 2 }}>
          <button
            onClick={() => {
              setStatusFilter('all');
              setCurrentPage(1);
            }}
            style={{
              ...filterTabBtnStyle,
              background: statusFilter === 'all' ? '#ffffff' : 'transparent',
              color: statusFilter === 'all' ? '#0F5C5E' : '#64748b',
              boxShadow: statusFilter === 'all' ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
            }}
          >
            All Patients
          </button>
          <button
            onClick={() => {
              setStatusFilter('active');
              setCurrentPage(1);
            }}
            style={{
              ...filterTabBtnStyle,
              background: statusFilter === 'active' ? '#ffffff' : 'transparent',
              color: statusFilter === 'active' ? '#166534' : '#64748b',
              boxShadow: statusFilter === 'active' ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
            }}
          >
            Active Only
          </button>
          <button
            onClick={() => {
              setStatusFilter('suspended');
              setCurrentPage(1);
            }}
            style={{
              ...filterTabBtnStyle,
              background: statusFilter === 'suspended' ? '#ffffff' : 'transparent',
              color: statusFilter === 'suspended' ? '#991b1b' : '#64748b',
              boxShadow: statusFilter === 'suspended' ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
            }}
          >
            Suspended
          </button>
        </div>

        {/* Clear Filters Reset Button */}
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 12px',
              background: '#f8fafc',
              color: '#475569',
              border: '1px solid #cbd5e1',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={13} />
            Reset Filters
          </button>
        )}
      </div>

      {/* Table Container */}
      <div style={{ background: '#ffffff', borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.03)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 48, textAlign: 'center', color: '#0F5C5E', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <Loader2 size={32} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontWeight: 600, fontSize: 14 }}>Loading patients data...</span>
          </div>
        ) : displayedPatients.length === 0 ? (
          /* Empty State Guidance */
          <div style={{ padding: '64px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: 60, height: 60, borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
              {hasActiveFilters ? <Search size={28} color="#64748b" /> : <Users size={28} color="#0F5C5E" />}
            </div>
            <h3 style={{ margin: '0 0 6px 0', fontSize: 17, color: '#0f172a', fontWeight: 700 }}>
              {hasActiveFilters ? 'No Patients Match Your Filters' : 'No Patients Registered Yet'}
            </h3>
            <p style={{ margin: '0 0 16px 0', fontSize: 13, color: '#64748b', maxWidth: 420 }}>
              {hasActiveFilters
                ? 'Try adjusting your search criteria or resetting filters to view all patients.'
                : 'Registered patients from the mobile app will automatically appear in this registry.'}
            </p>
            {hasActiveFilters && (
              <button onClick={handleClearFilters} style={secondaryBtnStyle}>
                <RotateCcw size={14} /> Clear All Filters
              </button>
            )}
          </div>
        ) : (
          /* Patients Table without Redundant "Role" Column */
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={thStyle}>Patient Profile & Contact</th>
                  <th style={thStyle}>Demographics</th>
                  <th style={thStyle}>Clinical Records</th>
                  <th style={thStyle}>Joined Date</th>
                  <th style={thStyle}>Status</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {displayedPatients.map((p) => {
                  const age = calculateAge(p.date_of_birth);

                  return (
                    <tr
                      key={p.id}
                      style={{
                        borderBottom: '1px solid #f1f5f9',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      {/* Column 1: Patient Profile & Contact */}
                      <td style={tdStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <PatientAvatar
                            avatarUrl={p.avatar_url}
                            name={p.full_name}
                            size={40}
                            fontSize={13}
                          />
                          <div>
                            <div style={{ fontWeight: 600, color: '#0f172a', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                              {p.full_name}
                              {p.is_verified && (
                                <span title="Verified Patient Identity" style={{ display: 'inline-flex', alignItems: 'center' }}>
                                  <ShieldCheck size={14} color="#16a34a" />
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: 12, color: '#64748b', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                              <Mail size={12} color="#94a3b8" />
                              {p.email}
                            </div>
                            {p.phone && (
                              <div style={{ fontSize: 11, color: '#64748b', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                                <Phone size={11} color="#94a3b8" />
                                {p.phone}
                              </div>
                            )}
                            {p.abha_number && (
                              <div style={{ fontSize: 11, color: '#0F5C5E', fontWeight: 600, marginTop: 3 }}>
                                ABHA: {p.abha_number}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Column 2: Meaningful Demographics (Age / Gender / Blood Group) */}
                      <td style={tdStyle}>
                        <div style={{ color: '#1e293b', fontWeight: 600, fontSize: 13 }}>
                          {age !== null ? `${age} yrs` : 'Age N/A'}
                          {p.biological_sex && ` • ${p.biological_sex}`}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                          {p.blood_group && (
                            <span
                              style={{
                                padding: '2px 7px',
                                background: '#fef2f2',
                                color: '#b91c1c',
                                borderRadius: 4,
                                fontSize: 11,
                                fontWeight: 700,
                                border: '1px solid #fecaca',
                              }}
                            >
                              🩸 {p.blood_group}
                            </span>
                          )}
                          {p.city && (
                            <span style={{ fontSize: 12, color: '#64748b', display: 'flex', alignItems: 'center', gap: 3 }}>
                              <MapPin size={11} color="#94a3b8" /> {p.city}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Column 3: Clinical Records Activity */}
                      <td style={tdStyle}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                          <span style={{ fontSize: 12, color: '#334155', display: 'flex', alignItems: 'center', gap: 5 }}>
                            <Calendar size={12} color="#0F5C5E" />
                            <strong>{p.appointments_count || 0}</strong> Consultations
                          </span>
                          <span style={{ fontSize: 12, color: '#64748b', display: 'flex', alignItems: 'center', gap: 5 }}>
                            <FileText size={12} color="#64748b" />
                            <strong>{p.reports_count || 0}</strong> Lab Reports
                          </span>
                        </div>
                      </td>

                      {/* Column 4: Joined Date */}
                      <td style={tdStyle}>
                        <div style={{ fontSize: 12, color: '#475569', fontWeight: 500 }}>
                          {formatJoinedDate(p.created_at)}
                        </div>
                      </td>

                      {/* Column 5: Account Status */}
                      <td style={tdStyle}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 5,
                            padding: '3px 8px',
                            borderRadius: 12,
                            fontSize: 12,
                            fontWeight: 600,
                            background: p.is_active ? '#dcfce7' : '#fee2e2',
                            color: p.is_active ? '#166534' : '#991b1b',
                          }}
                        >
                          <span
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: '50%',
                              background: p.is_active ? '#22c55e' : '#ef4444',
                            }}
                          />
                          {p.is_active ? 'Active' : 'Suspended'}
                        </span>
                      </td>

                      {/* Column 6: Action Buttons with Proper Hierarchy */}
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                          {/* Standard Action: View Profile Details */}
                          <button
                            onClick={() => handleOpenPatientDetails(p, 'profile')}
                            title="View Full Patient Details & Profile"
                            style={actionIconBtnStyle}
                          >
                            <Eye size={15} color="#334155" />
                          </button>

                          {/* Standard Action: View Activity Metrics */}
                          <button
                            onClick={() => handleOpenPatientDetails(p, 'consultations')}
                            title="View Consultations & Clinical Activity"
                            style={actionIconBtnStyle}
                          >
                            <BarChart2 size={15} color="#0F5C5E" />
                          </button>

                          {/* Destructive Action: Ghost / Outline Suspend Button with Confirmation Modal */}
                          {!isSupportStaff && (
                            <button
                              onClick={() => setPendingStatusToggleUser(p)}
                              title={p.is_active ? 'Suspend Patient Account' : 'Reactivate Patient Account'}
                              style={{
                                ...actionIconBtnStyle,
                                background: p.is_active ? '#ffffff' : '#f0fdf4',
                                borderColor: p.is_active ? '#fca5a5' : '#86efac',
                              }}
                            >
                              <Power size={15} color={p.is_active ? '#dc2626' : '#16a34a'} />
                            </button>
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

        {/* Table Footer: Pagination & Record Summary */}
        {!loading && displayedPatients.length > 0 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 18px',
              borderTop: '1px solid #e2e8f0',
              background: '#f8fafc',
              fontSize: 13,
              color: '#64748b',
              flexWrap: 'wrap',
              gap: 12,
            }}
          >
            {/* Record range */}
            <div>
              Showing <strong style={{ color: '#0f172a' }}>{startIndex + 1}</strong> to{' '}
              <strong style={{ color: '#0f172a' }}>{Math.min(startIndex + rowsPerPage, totalFiltered)}</strong> of{' '}
              <strong style={{ color: '#0f172a' }}>{totalFiltered}</strong> patients
            </div>

            {/* Pagination Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              {/* Rows Per Page */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>Rows:</span>
                <select
                  value={rowsPerPage}
                  onChange={(e) => {
                    setRowsPerPage(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  style={{
                    padding: '4px 8px',
                    borderRadius: 4,
                    border: '1px solid #cbd5e1',
                    fontSize: 12,
                    background: '#ffffff',
                    cursor: 'pointer',
                  }}
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </div>

              {/* Prev / Page / Next */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  style={{
                    ...paginationNavBtnStyle,
                    opacity: currentPage === 1 ? 0.4 : 1,
                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                  }}
                  title="Previous Page"
                >
                  <ChevronLeft size={16} />
                </button>

                <span style={{ fontSize: 12, fontWeight: 600, color: '#334155' }}>
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  style={{
                    ...paginationNavBtnStyle,
                    opacity: currentPage === totalPages ? 0.4 : 1,
                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                  }}
                  title="Next Page"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* MODAL 1: SUSPENSION / REACTIVATION CONFIRMATION MODAL                      */}
      {/* ========================================================================= */}
      {pendingStatusToggleUser && (
        <div
          onClick={() => {
            setPendingStatusToggleUser(null);
            setStatusReason('');
            setStatusReasonError(null);
          }}
          style={{ ...modalOverlayStyle, zIndex: 10000 }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#ffffff',
              borderRadius: 12,
              width: '100%',
              maxWidth: 520,
              boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.25)',
              border: '1px solid #e2e8f0',
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  background: pendingStatusToggleUser.is_active ? '#fee2e2' : '#dcfce7',
                  color: pendingStatusToggleUser.is_active ? '#dc2626' : '#166534',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {pendingStatusToggleUser.is_active ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: '0 0 6px 0', fontSize: 18, color: '#0f172a', fontWeight: 700 }}>
                  {pendingStatusToggleUser.is_active ? 'Suspend Patient Account?' : 'Reactivate Patient Account?'}
                </h3>
                <p style={{ margin: '0 0 14px 0', fontSize: 13, color: '#64748b', lineHeight: 1.5 }}>
                  {pendingStatusToggleUser.is_active
                    ? `Are you sure you want to suspend access for ${pendingStatusToggleUser.full_name}? The patient will be locked out of mobile app features until reactivated.`
                    : `Reactivate account for ${pendingStatusToggleUser.full_name}? The patient will regain immediate login access and ability to book consultations.`}
                </p>

                {/* Patient Summary Pill */}
                <div style={{ background: '#f8fafc', padding: '10px 14px', borderRadius: 8, border: '1px solid #e2e8f0', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
                  <PatientAvatar avatarUrl={pendingStatusToggleUser.avatar_url} name={pendingStatusToggleUser.full_name} size={38} fontSize={13} />
                  <div>
                    <div style={{ fontWeight: 600, color: '#1e293b', fontSize: 13 }}>{pendingStatusToggleUser.full_name}</div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>{pendingStatusToggleUser.email}</div>
                  </div>
                </div>

                {/* Reason Textarea (Required for suspension) */}
                <div style={{ marginBottom: 18 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 6 }}>
                    Reason / Justification {pendingStatusToggleUser.is_active && <span style={{ color: '#dc2626' }}>*</span>}
                  </label>
                  <textarea
                    value={statusReason}
                    onChange={(e) => {
                      setStatusReason(e.target.value);
                      if (statusReasonError) setStatusReasonError(null);
                    }}
                    placeholder={
                      pendingStatusToggleUser.is_active
                        ? 'Enter reason for suspension (e.g. Terms violation, patient requested hold, identity audit)...'
                        : 'Enter reason for reactivation (e.g. Identity verified, review completed)...'
                    }
                    rows={3}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 6,
                      border: statusReasonError ? '1.5px solid #ef4444' : '1px solid #cbd5e1',
                      fontSize: 13,
                      fontFamily: 'inherit',
                      boxSizing: 'border-box',
                      outline: 'none',
                      resize: 'vertical',
                    }}
                  />
                  {statusReasonError && (
                    <div style={{ color: '#dc2626', fontSize: 11, fontWeight: 600, marginTop: 4 }}>
                      {statusReasonError}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                  <button
                    onClick={() => {
                      setPendingStatusToggleUser(null);
                      setStatusReason('');
                      setStatusReasonError(null);
                    }}
                    disabled={isTogglingStatus}
                    style={secondaryBtnStyle}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmStatusToggle}
                    disabled={isTogglingStatus || (pendingStatusToggleUser.is_active && !statusReason.trim())}
                    style={{
                      padding: '8px 18px',
                      borderRadius: 6,
                      border: 'none',
                      fontWeight: 600,
                      fontSize: 13,
                      cursor: (isTogglingStatus || (pendingStatusToggleUser.is_active && !statusReason.trim())) ? 'not-allowed' : 'pointer',
                      background: (pendingStatusToggleUser.is_active && !statusReason.trim()) ? '#fca5a5' : pendingStatusToggleUser.is_active ? '#dc2626' : '#166534',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    {isTogglingStatus ? (
                      <>
                        <Loader2 size={15} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                        Updating...
                      </>
                    ) : pendingStatusToggleUser.is_active ? (
                      'Confirm Suspension'
                    ) : (
                      'Confirm Reactivation'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: COMPREHENSIVE PATIENT DETAILS & CLINICAL ACTIVITY MODAL          */}
      {/* ========================================================================= */}
      {selectedPatient && (
        <div onClick={() => setSelectedPatient(null)} style={modalOverlayStyle}>
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: '#ffffff',
              borderRadius: 12,
              width: '100%',
              maxWidth: 1024,
              height: '85vh',
              maxHeight: '85vh',
              boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.25)',
              border: '1px solid #e2e8f0',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '20px 24px',
                borderBottom: '1px solid #e2e8f0',
                background: '#f8fafc',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 16,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, minWidth: 0 }}>
                {/* Profile Picture / Initials */}
                <PatientAvatar
                  avatarUrl={selectedPatient.avatar_url}
                  name={selectedPatient.full_name}
                  size={58}
                  fontSize={20}
                  style={{ border: '2px solid #0F5C5E', flexShrink: 0 }}
                />
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <h3 style={{ margin: 0, fontSize: 19, color: '#0f172a', fontWeight: 700 }}>
                      {selectedPatient.full_name}
                    </h3>

                    {/* Status Pill */}
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        padding: '2px 8px',
                        borderRadius: 12,
                        fontSize: 11,
                        fontWeight: 700,
                        background: selectedPatient.is_active ? '#dcfce7' : '#fee2e2',
                        color: selectedPatient.is_active ? '#166534' : '#991b1b',
                      }}
                    >
                      <span
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          background: selectedPatient.is_active ? '#22c55e' : '#ef4444',
                        }}
                      />
                      {selectedPatient.is_active ? 'ACTIVE' : 'SUSPENDED'}
                    </span>

                    {/* Verification Badge */}
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '2px 8px',
                        borderRadius: 12,
                        fontSize: 11,
                        fontWeight: 600,
                        background: selectedPatient.is_verified ? '#ecfdf5' : '#f1f5f9',
                        color: selectedPatient.is_verified ? '#047857' : '#64748b',
                        border: selectedPatient.is_verified ? '1px solid #a7f3d0' : '1px solid #e2e8f0',
                      }}
                    >
                      {selectedPatient.is_verified ? (
                        <>
                          <ShieldCheck size={13} color="#059669" /> Verified Patient
                        </>
                      ) : (
                        <>
                          <Shield size={13} color="#94a3b8" /> Unverified
                        </>
                      )}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', marginTop: 4, fontSize: 12, color: '#64748b' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      <Mail size={12} color="#94a3b8" />
                      {selectedPatient.email}
                    </span>
                    {selectedPatient.phone && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <Phone size={12} color="#94a3b8" />
                        {selectedPatient.phone}
                      </span>
                    )}
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      <span style={{ color: '#94a3b8' }}>ID:</span>
                      <code style={{ fontSize: 11, background: '#e2e8f0', padding: '1px 5px', borderRadius: 4, color: '#334155' }}>
                        {selectedPatient.id}
                      </code>
                      <button
                        onClick={() => handleCopyId(selectedPatient.id)}
                        title="Copy Patient ID"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          padding: 2,
                          display: 'inline-flex',
                          alignItems: 'center',
                          color: copiedId ? '#16a34a' : '#64748b',
                        }}
                      >
                        {copiedId ? <Check size={12} /> : <Copy size={12} />}
                      </button>
                    </span>
                  </div>
                </div>
              </div>

              {/* Close Button & Loading Indicator */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                {isDetailLoading && (
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 11,
                      color: '#0F5C5E',
                      background: '#ccfbf1',
                      padding: '4px 10px',
                      borderRadius: 12,
                      fontWeight: 600,
                    }}
                  >
                    <Loader2 size={12} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                    Syncing...
                  </span>
                )}
                <button
                  onClick={() => setSelectedPatient(null)}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: 6,
                    padding: 6,
                    cursor: 'pointer',
                    color: '#64748b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  title="Close (Esc)"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Modal Tabs Bar */}
            <div
              style={{
                display: 'flex',
                gap: 4,
                borderBottom: '1px solid #e2e8f0',
                background: '#ffffff',
                padding: '0 20px',
                overflowX: 'auto',
              }}
            >
              {[
                { id: 'profile', label: 'Overview & Profile', icon: <HeartPulse size={15} /> },
                {
                  id: 'consultations',
                  label: `Consultations (${selectedPatient.recent_appointments?.length ?? selectedPatient.appointments_count ?? 0})`,
                  icon: <Calendar size={15} />,
                },
                {
                  id: 'reports',
                  label: `Lab Reports (${selectedPatient.recent_reports?.length ?? selectedPatient.reports_count ?? 0})`,
                  icon: <FileText size={15} />,
                },
                {
                  id: 'symptoms',
                  label: `Symptoms (${selectedPatient.recent_symptoms?.length ?? selectedPatient.summary_metrics?.symptom_logs_count ?? 0})`,
                  icon: <Thermometer size={15} />,
                },
                { id: 'security', label: 'Security & Audit', icon: <ShieldCheck size={15} /> },
              ].map((tab) => {
                const isActive = activeDetailTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveDetailTab(tab.id as any)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '12px 14px',
                      background: 'transparent',
                      border: 'none',
                      borderBottom: isActive ? '2px solid #0F5C5E' : '2px solid transparent',
                      color: isActive ? '#0F5C5E' : '#64748b',
                      fontWeight: isActive ? 700 : 500,
                      fontSize: 13,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {tab.icon}
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Modal Scrollable Body */}
            <div style={{ padding: '24px 28px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 20, scrollBehavior: 'smooth' }}>
              {/* TAB 1: OVERVIEW & PROFILE */}
              {activeDetailTab === 'profile' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                  {/* Demographics & Clinical Profile */}
                  <div style={{ background: '#f8fafc', padding: '18px 20px', borderRadius: 10, border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#0F5C5E', textTransform: 'uppercase', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6, letterSpacing: '0.04em' }}>
                      <HeartPulse size={15} /> Personal & Health Profile
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, fontSize: 13 }}>
                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Full Legal Name</div>
                        <div style={{ fontWeight: 600, color: '#0f172a', marginTop: 2 }}>{selectedPatient.full_name || '—'}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Age & Date of Birth</div>
                        <div style={{ fontWeight: 600, color: '#0f172a', marginTop: 2 }}>
                          {calculateAge(selectedPatient.date_of_birth) !== null ? `${calculateAge(selectedPatient.date_of_birth)} yrs` : 'Not specified'}
                          {selectedPatient.date_of_birth && <span style={{ color: '#64748b', fontWeight: 400, fontSize: 12 }}> ({selectedPatient.date_of_birth})</span>}
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Biological Sex</div>
                        <div style={{ fontWeight: 600, color: '#0f172a', marginTop: 2 }}>{selectedPatient.biological_sex || 'Not Specified'}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Blood Group</div>
                        <div style={{ marginTop: 2 }}>
                          {selectedPatient.blood_group ? (
                            <span
                              style={{
                                padding: '2px 8px',
                                background: '#fef2f2',
                                color: '#b91c1c',
                                borderRadius: 4,
                                fontSize: 12,
                                fontWeight: 700,
                                border: '1px solid #fecaca',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 4,
                              }}
                            >
                              🩸 {selectedPatient.blood_group}
                            </span>
                          ) : (
                            <span style={{ color: '#94a3b8' }}>Not recorded</span>
                          )}
                        </div>
                      </div>

                      <div style={{ gridColumn: 'span 2' }}>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>
                          ABHA Health ID (Ayushman Bharat)
                        </div>
                        <div style={{ marginTop: 4 }}>
                          {isEditingAbha ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
                              <input
                                type="text"
                                value={abhaInput}
                                onChange={(e) => handleAbhaInputChange(e.target.value)}
                                placeholder="91-1234-5678-9012"
                                maxLength={17}
                                style={{
                                  padding: '6px 12px',
                                  fontSize: 13,
                                  borderRadius: 6,
                                  border: '1.5px solid #0F5C5E',
                                  outline: 'none',
                                  fontFamily: 'monospace',
                                  letterSpacing: '1px',
                                  width: 200,
                                }}
                              />
                              <button
                                onClick={handleSaveAbha}
                                disabled={isSavingAbha}
                                style={{
                                  background: '#0F5C5E',
                                  color: '#ffffff',
                                  border: 'none',
                                  borderRadius: 6,
                                  padding: '6px 14px',
                                  fontSize: 12,
                                  fontWeight: 700,
                                  cursor: 'pointer',
                                }}
                              >
                                {isSavingAbha ? 'Saving...' : 'Save ABHA'}
                              </button>
                              {selectedPatient.abha_number && (
                                <button
                                  onClick={handleUnlinkAbha}
                                  disabled={isSavingAbha}
                                  style={{
                                    background: '#fee2e2',
                                    color: '#b91c1c',
                                    border: '1px solid #fca5a5',
                                    borderRadius: 6,
                                    padding: '6px 12px',
                                    fontSize: 12,
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                  }}
                                >
                                  Unlink
                                </button>
                              )}
                              <button
                                onClick={() => setIsEditingAbha(false)}
                                disabled={isSavingAbha}
                                style={{
                                  background: '#f1f5f9',
                                  color: '#475569',
                                  border: '1px solid #cbd5e1',
                                  borderRadius: 6,
                                  padding: '6px 12px',
                                  fontSize: 12,
                                  cursor: 'pointer',
                                }}
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              {selectedPatient.abha_number ? (
                                <>
                                  <span
                                    style={{
                                      padding: '4px 12px',
                                      background: '#e0f2fe',
                                      color: '#0369a1',
                                      borderRadius: 8,
                                      fontSize: 12,
                                      fontWeight: 700,
                                      border: '1px solid #bae6fd',
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: 6,
                                      fontFamily: 'monospace',
                                      letterSpacing: '0.5px',
                                    }}
                                  >
                                    <ShieldCheck size={14} color="#0369a1" /> {selectedPatient.abha_number}
                                  </span>
                                  <button
                                    onClick={handleStartEditAbha}
                                    style={{
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: 4,
                                      padding: '3px 12px',
                                      borderRadius: 16,
                                      background: '#f1f5f9',
                                      color: '#475569',
                                      border: '1px solid #cbd5e1',
                                      fontSize: 11,
                                      fontWeight: 600,
                                      cursor: 'pointer',
                                      transition: 'all 0.15s ease',
                                    }}
                                    title="Edit or unlink ABHA Card"
                                  >
                                    <CreditCard size={11} color="#475569" />
                                    Edit / Unlink
                                  </button>
                                </>
                              ) : (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                  <span style={{ color: '#94a3b8', fontSize: 13 }}>Not linked</span>
                                  <button
                                    onClick={handleStartEditAbha}
                                    style={{
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: 5,
                                      padding: '3px 12px',
                                      borderRadius: 16,
                                      background: '#f0fdfa',
                                      color: '#0F5C5E',
                                      border: '1px solid #99f6e4',
                                      fontSize: 11,
                                      fontWeight: 700,
                                      cursor: 'pointer',
                                      boxShadow: '0 1px 2px rgba(15,92,94,0.06)',
                                      transition: 'all 0.15s ease',
                                    }}
                                    title="Link 14-digit ABHA Card"
                                  >
                                    <CreditCard size={12} color="#0F5C5E" />
                                    + Link ABHA Card
                                  </button>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Emergency Contact</div>
                        <div style={{ marginTop: 2, display: 'flex', alignItems: 'center', gap: 6, color: selectedPatient.emergency_contact ? '#0f172a' : '#94a3b8', fontWeight: selectedPatient.emergency_contact ? 600 : 400 }}>
                          <Phone size={13} color={selectedPatient.emergency_contact ? '#0F5C5E' : '#94a3b8'} />
                          {selectedPatient.emergency_contact || 'None registered'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Contact Information & Channels */}
                  <div style={{ background: '#f8fafc', padding: 16, borderRadius: 8, border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#0F5C5E', textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6, letterSpacing: '0.04em' }}>
                      <Mail size={15} /> Contact Channels & Verification
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14, fontSize: 13 }}>
                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Primary Email</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 3 }}>
                          <strong style={{ color: '#0f172a' }}>{selectedPatient.email}</strong>
                          <span
                            style={{
                              padding: '1px 6px',
                              borderRadius: 4,
                              fontSize: 10,
                              fontWeight: 700,
                              background: selectedPatient.email_verified ? '#dcfce7' : '#fef3c7',
                              color: selectedPatient.email_verified ? '#166534' : '#92400e',
                              border: selectedPatient.email_verified ? '1px solid #86efac' : '1px solid #fde68a',
                            }}
                          >
                            {selectedPatient.email_verified ? 'Verified' : 'Unverified'}
                          </span>
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Mobile Phone</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 3 }}>
                          <span style={{ color: selectedPatient.phone ? '#0f172a' : '#94a3b8', fontWeight: selectedPatient.phone ? 600 : 400 }}>
                            {selectedPatient.phone || 'Not registered'}
                          </span>
                          {selectedPatient.phone && (
                            <span
                              style={{
                                padding: '1px 6px',
                                borderRadius: 4,
                                fontSize: 10,
                                fontWeight: 600,
                                background: '#f1f5f9',
                                color: '#475569',
                                border: '1px solid #e2e8f0',
                              }}
                            >
                              Contact Only
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Residential Address Details */}
                  <div style={{ background: '#f8fafc', padding: 16, borderRadius: 8, border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#0F5C5E', textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6, letterSpacing: '0.04em' }}>
                      <MapPin size={15} /> Residential Address & Location
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14, fontSize: 13 }}>
                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Street Address Line 1</div>
                        <div style={{ color: '#1e293b', marginTop: 2, fontWeight: 500 }}>{selectedPatient.address_line1 || 'Not specified'}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Address Line 2</div>
                        <div style={{ color: '#1e293b', marginTop: 2 }}>{selectedPatient.address_line2 || '—'}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>City / District</div>
                        <div style={{ color: '#1e293b', marginTop: 2, fontWeight: 600 }}>{selectedPatient.city || '—'}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>State / Union Territory</div>
                        <div style={{ color: '#1e293b', marginTop: 2 }}>{selectedPatient.state || '—'}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Postal Code / PIN</div>
                        <div style={{ color: '#1e293b', marginTop: 2, fontFamily: 'monospace' }}>{selectedPatient.postal_code || '—'}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Country</div>
                        <div style={{ color: '#1e293b', marginTop: 2 }}>{selectedPatient.country || 'India'}</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: CONSULTATIONS & APPOINTMENTS */}
              {activeDetailTab === 'consultations' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: 13, color: '#64748b' }}>
                      Recent consultations and specialist appointments booked by this patient:
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#0F5C5E', background: '#f0fdfa', padding: '3px 8px', borderRadius: 6, border: '1px solid #ccfbf1' }}>
                      {selectedPatient.recent_appointments?.length || 0} Consultations Recorded
                    </span>
                  </div>

                  {!selectedPatient.recent_appointments || selectedPatient.recent_appointments.length === 0 ? (
                    <div style={{ padding: '40px 20px', textAlign: 'center', background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0' }}>
                      <div
                        style={{
                          width: 58,
                          height: 58,
                          borderRadius: 14,
                          background: '#ffffff',
                          border: '1.5px solid #e2e8f0',
                          boxShadow: '0 2px 4px rgba(15, 23, 42, 0.04)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          margin: '0 auto 14px auto',
                        }}
                      >
                        <Calendar size={28} color="#94a3b8" />
                      </div>
                      <div style={{ fontWeight: 700, color: '#1e293b', fontSize: 14 }}>No Consultations Found</div>
                      <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>This patient has not booked any doctor consultations yet.</div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {selectedPatient.recent_appointments.map((apt: any) => {
                        const isCompleted = apt.status?.toUpperCase() === 'COMPLETED';
                        const isCancelled = apt.status?.toUpperCase() === 'CANCELLED';
                        const isConfirmed = apt.status?.toUpperCase() === 'CONFIRMED' || apt.status?.toUpperCase() === 'SCHEDULED';

                        return (
                          <div
                            key={apt.id}
                            style={{
                              background: '#ffffff',
                              border: '1px solid #e2e8f0',
                              borderRadius: 8,
                              padding: 14,
                              display: 'flex',
                              flexDirection: 'column',
                              gap: 8,
                              boxShadow: '0 1px 2px rgba(0,0,0,0.02)',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                              <div>
                                <div style={{ fontWeight: 700, color: '#0f172a', fontSize: 14 }}>
                                  {apt.doctor_name || 'Assigned Practitioner'}
                                </div>
                                <div style={{ fontSize: 12, color: '#64748b', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                                  <Building size={12} color="#94a3b8" />
                                  {apt.clinic_name || 'Partner Health Clinic'}
                                </div>
                              </div>

                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <span
                                  style={{
                                    padding: '3px 8px',
                                    borderRadius: 4,
                                    fontSize: 11,
                                    fontWeight: 700,
                                    background: isCompleted ? '#dcfce7' : isCancelled ? '#fee2e2' : isConfirmed ? '#e0f2fe' : '#fef3c7',
                                    color: isCompleted ? '#166534' : isCancelled ? '#991b1b' : isConfirmed ? '#0284c7' : '#92400e',
                                    border: isCompleted ? '1px solid #bbf7d0' : isCancelled ? '1px solid #fecaca' : isConfirmed ? '1px solid #bae6fd' : '1px solid #fde68a',
                                  }}
                                >
                                  {apt.status || 'SCHEDULED'}
                                </span>

                                {apt.payment_status && (
                                  <span
                                    style={{
                                      padding: '3px 8px',
                                      borderRadius: 4,
                                      fontSize: 11,
                                      fontWeight: 600,
                                      background: apt.payment_status?.toUpperCase() === 'PAID' ? '#ecfdf5' : '#fffbeb',
                                      color: apt.payment_status?.toUpperCase() === 'PAID' ? '#065f46' : '#b45309',
                                      border: apt.payment_status?.toUpperCase() === 'PAID' ? '1px solid #a7f3d0' : '1px solid #fde68a',
                                    }}
                                  >
                                    <CreditCard size={11} style={{ display: 'inline', marginRight: 3, verticalAlign: -1 }} />
                                    {apt.payment_status}
                                  </span>
                                )}
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap', fontSize: 12, color: '#475569', borderTop: '1px solid #f1f5f9', paddingTop: 8 }}>
                              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Clock size={12} color="#0F5C5E" />
                                {apt.appointment_date} {apt.appointment_time ? `at ${apt.appointment_time}` : ''}
                              </span>
                              {apt.booking_reference && (
                                <span style={{ color: '#64748b' }}>
                                  Ref: <code style={{ background: '#f1f5f9', padding: '1px 4px', borderRadius: 3 }}>#{apt.booking_reference}</code>
                                </span>
                              )}
                              {apt.visit_reason && (
                                <span style={{ color: '#334155' }}>
                                  <strong>Reason:</strong> {apt.visit_reason}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: DIAGNOSTIC LAB REPORTS */}
              {activeDetailTab === 'reports' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: 13, color: '#64748b' }}>
                      Diagnostic test records, blood panels, and clinical documents uploaded by this patient:
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#0284c7', background: '#f0f9ff', padding: '3px 8px', borderRadius: 6, border: '1px solid #bae6fd' }}>
                      {selectedPatient.recent_reports?.length || 0} Reports Uploaded
                    </span>
                  </div>

                  {!selectedPatient.recent_reports || selectedPatient.recent_reports.length === 0 ? (
                    <div style={{ padding: '40px 20px', textAlign: 'center', background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0' }}>
                      <div
                        style={{
                          width: 58,
                          height: 58,
                          borderRadius: 14,
                          background: '#ffffff',
                          border: '1.5px solid #e2e8f0',
                          boxShadow: '0 2px 4px rgba(15, 23, 42, 0.04)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          margin: '0 auto 14px auto',
                        }}
                      >
                        <FileText size={28} color="#94a3b8" />
                      </div>
                      <div style={{ fontWeight: 700, color: '#1e293b', fontSize: 14 }}>No Lab Reports Found</div>
                      <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>This patient has not uploaded any laboratory or diagnostic records yet.</div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {selectedPatient.recent_reports.map((rep: any) => {
                        const resolvedFileUrl = getMediaUrl(rep.file_path);
                        const tagInfo = getReportTag(rep.report_type);
                        const fileSizeDisplay = formatFileSize(rep.file_size_bytes);

                        return (
                          <div
                            key={rep.id}
                            style={{
                              background: '#ffffff',
                              border: '1px solid #e2e8f0',
                              borderRadius: 10,
                              padding: '14px 18px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: 16,
                              boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
                              <div
                                style={{
                                  width: 42,
                                  height: 42,
                                  borderRadius: 8,
                                  background: '#eff6ff',
                                  color: '#2563eb',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  flexShrink: 0,
                                  border: '1px solid #dbeafe',
                                }}
                              >
                                <FileCheck size={22} />
                              </div>
                              <div style={{ minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                  <span style={{ fontWeight: 700, color: '#0f172a', fontSize: 13, wordBreak: 'break-all' }}>
                                    {rep.file_name || 'Clinical Medical Report'}
                                  </span>
                                  {/* File Size Indicator */}
                                  <span
                                    style={{
                                      fontSize: 11,
                                      color: '#64748b',
                                      background: '#f1f5f9',
                                      padding: '1px 6px',
                                      borderRadius: 4,
                                      fontWeight: 600,
                                      fontFamily: 'monospace',
                                    }}
                                  >
                                    {fileSizeDisplay}
                                  </span>
                                  {/* Report Summary Tag */}
                                  <span
                                    style={{
                                      fontSize: 11,
                                      fontWeight: 700,
                                      padding: '1px 8px',
                                      borderRadius: 12,
                                      background: tagInfo.bg,
                                      color: tagInfo.color,
                                      border: `1px solid ${tagInfo.border}`,
                                    }}
                                  >
                                    {tagInfo.label}
                                  </span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#64748b', marginTop: 4, flexWrap: 'wrap' }}>
                                  {rep.report_date && <span>Test Date: <strong>{rep.report_date}</strong></span>}
                                  {rep.created_at && <span>Uploaded: {formatDateTime(rep.created_at)}</span>}
                                </div>
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                              <span
                                style={{
                                  padding: '3px 8px',
                                  borderRadius: 4,
                                  fontSize: 11,
                                  fontWeight: 700,
                                  background: rep.status === 'COMPLETED' ? '#dcfce7' : '#fef3c7',
                                  color: rep.status === 'COMPLETED' ? '#166534' : '#92400e',
                                  border: rep.status === 'COMPLETED' ? '1px solid #bbf7d0' : '1px solid #fde68a',
                                }}
                              >
                                {rep.status || 'UPLOADED'}
                              </span>

                              {/* Inline Preview Button (Eye Icon) */}
                              {resolvedFileUrl && (
                                <button
                                  onClick={() => window.open(resolvedFileUrl, '_blank')}
                                  title="Preview Medical Report"
                                  style={{
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
                                  }}
                                >
                                  <Eye size={15} color="#0F5C5E" />
                                </button>
                              )}

                              {/* Direct Download Icon Button */}
                              {resolvedFileUrl && (
                                <a
                                  href={resolvedFileUrl}
                                  download={rep.file_name || 'medical_report.pdf'}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  title="Download Medical Report"
                                  style={{
                                    width: 32,
                                    height: 32,
                                    borderRadius: 6,
                                    border: '1px solid #cbd5e1',
                                    background: '#ffffff',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: 'pointer',
                                    textDecoration: 'none',
                                    transition: 'all 0.15s ease',
                                  }}
                                >
                                  <Download size={15} color="#475569" />
                                </a>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: SYMPTOM LOGS */}
              {activeDetailTab === 'symptoms' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: 13, color: '#64748b' }}>
                      Historical symptoms and wellness check-ins logged by this patient:
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#854d0e', background: '#fefce8', padding: '3px 8px', borderRadius: 6, border: '1px solid #fef08a' }}>
                      {selectedPatient.recent_symptoms?.length || 0} Symptoms Logged
                    </span>
                  </div>

                  {!selectedPatient.recent_symptoms || selectedPatient.recent_symptoms.length === 0 ? (
                    <div style={{ padding: '40px 20px', textAlign: 'center', background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0' }}>
                      <div
                        style={{
                          width: 58,
                          height: 58,
                          borderRadius: 14,
                          background: '#ffffff',
                          border: '1.5px solid #e2e8f0',
                          boxShadow: '0 2px 4px rgba(15, 23, 42, 0.04)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          margin: '0 auto 14px auto',
                        }}
                      >
                        <Thermometer size={28} color="#94a3b8" />
                      </div>
                      <div style={{ fontWeight: 700, color: '#1e293b', fontSize: 14 }}>No Symptom Logs Found</div>
                      <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>This patient has not logged any active health symptoms yet.</div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {selectedPatient.recent_symptoms.map((sym: any) => {
                        const sev = sym.severity?.toUpperCase() || 'MODERATE';
                        const isSevere = sev === 'SEVERE' || sev === 'HIGH';
                        const isMild = sev === 'MILD' || sev === 'LOW';

                        return (
                          <div
                            key={sym.id}
                            style={{
                              background: '#ffffff',
                              border: '1px solid #e2e8f0',
                              borderRadius: 8,
                              padding: 14,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: 12,
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 600, color: '#0f172a', fontSize: 13 }}>
                                {Array.isArray(sym.symptoms) ? sym.symptoms.join(', ') : sym.symptoms || 'General discomfort'}
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#64748b', marginTop: 4 }}>
                                {sym.duration_days && <span>Duration: <strong>{sym.duration_days} days</strong></span>}
                                {sym.created_at && <span>Logged: {formatDateTime(sym.created_at)}</span>}
                              </div>
                            </div>

                            <div>
                              <span
                                style={{
                                  padding: '3px 8px',
                                  borderRadius: 4,
                                  fontSize: 11,
                                  fontWeight: 700,
                                  background: isSevere ? '#fee2e2' : isMild ? '#dcfce7' : '#fef3c7',
                                  color: isSevere ? '#991b1b' : isMild ? '#166534' : '#92400e',
                                  border: isSevere ? '1px solid #fecaca' : isMild ? '1px solid #bbf7d0' : '1px solid #fde68a',
                                }}
                              >
                                {sev}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: SECURITY & AUDIT */}
              {activeDetailTab === 'security' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ background: '#f8fafc', padding: 16, borderRadius: 8, border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#0F5C5E', textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6, letterSpacing: '0.04em' }}>
                      <ShieldCheck size={15} /> Account Security & Audit Metadata
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, fontSize: 13 }}>
                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Account ID</div>
                        <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#0f172a', marginTop: 2 }}>{selectedPatient.id}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Registered Date</div>
                        <div style={{ color: '#0f172a', fontWeight: 600, marginTop: 2 }}>{formatDateTime(selectedPatient.created_at)}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Last Profile Update</div>
                        <div style={{ color: '#0f172a', marginTop: 2 }}>{formatDateTime(selectedPatient.updated_at)}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Last Login Timestamp</div>
                        <div style={{ color: '#0f172a', marginTop: 2, fontWeight: 600 }}>{formatDateTime(selectedPatient.last_login_at)}</div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Registration IP Address</div>
                        <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#0f172a', marginTop: 2 }}>
                          {selectedPatient.registration_ip || 'Recorded via Mobile App'}
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Last Login IP Address</div>
                        <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#0f172a', marginTop: 2 }}>
                          {selectedPatient.last_login_ip || '—'}
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Identity Verification</div>
                        <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 5,
                              padding: '3px 10px',
                              borderRadius: 12,
                              fontSize: 11,
                              fontWeight: 700,
                              background: selectedPatient.is_verified ? '#dcfce7' : '#fef3c7',
                              color: selectedPatient.is_verified ? '#166534' : '#92400e',
                              border: selectedPatient.is_verified ? '1px solid #86efac' : '1px solid #fde68a',
                            }}
                          >
                            {selectedPatient.is_verified ? <ShieldCheck size={13} color="#166534" /> : <ShieldAlert size={13} color="#92400e" />}
                            {selectedPatient.is_verified ? 'Verified Identity' : 'Pending Verification'}
                          </span>
                        </div>
                      </div>

                      {selectedPatient.verified_at && (
                        <div>
                          <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Verified At</div>
                          <div style={{ color: '#0f172a', marginTop: 4, fontWeight: 600 }}>{formatDateTime(selectedPatient.verified_at)}</div>
                        </div>
                      )}

                      <div>
                        <div style={{ color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>Account Lifecycle Status</div>
                        <div style={{ marginTop: 4 }}>
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 6,
                              padding: '3px 10px',
                              borderRadius: 12,
                              fontSize: 11,
                              fontWeight: 700,
                              background: selectedPatient.is_deleted ? '#fee2e2' : selectedPatient.is_active ? '#dcfce7' : '#fee2e2',
                              color: selectedPatient.is_deleted ? '#991b1b' : selectedPatient.is_active ? '#166534' : '#991b1b',
                              border: selectedPatient.is_deleted ? '1px solid #fca5a5' : selectedPatient.is_active ? '1px solid #86efac' : '1px solid #fca5a5',
                            }}
                          >
                            <span
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: '50%',
                                background: selectedPatient.is_deleted ? '#ef4444' : selectedPatient.is_active ? '#22c55e' : '#ef4444',
                              }}
                            />
                            {selectedPatient.is_deleted ? 'Soft-Deleted Account' : selectedPatient.is_active ? 'Active Account' : 'Suspended Account'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Sticky Footer Controls */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '14px 28px',
                borderTop: '1px solid #e2e8f0',
                background: '#f8fafc',
              }}
            >
              {!isSupportStaff ? (
                <button
                  onClick={() => {
                    const target = { ...selectedPatient };
                    setStatusReason('');
                    setStatusReasonError(null);
                    setPendingStatusToggleUser(target);
                  }}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 6,
                    border: selectedPatient.is_active ? '1px solid #fca5a5' : '1px solid #86efac',
                    background: selectedPatient.is_active ? '#ffffff' : '#f0fdf4',
                    color: selectedPatient.is_active ? '#dc2626' : '#166534',
                    fontWeight: 600,
                    fontSize: 13,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    transition: 'all 0.15s ease',
                  }}
                >
                  <Power size={14} />
                  {selectedPatient.is_active ? 'Suspend Patient Account' : 'Reactivate Patient Account'}
                </button>
              ) : (
                <div />
              )}

              <button
                onClick={() => setSelectedPatient(null)}
                style={{
                  padding: '8px 18px',
                  borderRadius: 6,
                  border: '1px solid #cbd5e1',
                  background: '#f1f5f9',
                  color: '#334155',
                  fontWeight: 600,
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }}
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// UI Styling Constants
const kpiCardStyle: React.CSSProperties = {
  background: '#ffffff',
  padding: '12px 18px',
  borderRadius: 8,
  border: '1px solid #e2e8f0',
  flex: '1 1 180px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
};

const kpiIconBox: React.CSSProperties = {
  width: 36,
  height: 36,
  borderRadius: 6,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const kpiLabelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  color: '#64748b',
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
};

const kpiValueStyle: React.CSSProperties = {
  fontSize: 18,
  fontWeight: 700,
  marginTop: 2,
};

const filterTabBtnStyle: React.CSSProperties = {
  padding: '6px 12px',
  border: 'none',
  borderRadius: 5,
  fontSize: 12,
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all 0.15s ease',
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

const actionIconBtnStyle: React.CSSProperties = {
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

const paginationNavBtnStyle: React.CSSProperties = {
  width: 28,
  height: 28,
  borderRadius: 4,
  border: '1px solid #cbd5e1',
  background: '#ffffff',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#475569',
};

const secondaryBtnStyle: React.CSSProperties = {
  padding: '8px 14px',
  background: '#ffffff',
  color: '#475569',
  border: '1px solid #cbd5e1',
  borderRadius: 6,
  fontWeight: 600,
  fontSize: 13,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  gap: 6,
};

const modalOverlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(15, 23, 42, 0.6)',
  backdropFilter: 'blur(3px)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 9999,
  padding: 16,
};
