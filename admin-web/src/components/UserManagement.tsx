import React, { useState, useEffect } from 'react';
import { adminApi } from '../api/adminApi';

interface UserManagementProps {
  onNotify: (msg: string, type: 'success' | 'error') => void;
}

export const UserManagement: React.FC<UserManagementProps> = ({ onNotify }) => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [selectedUser, setSelectedUser] = useState<any>(null);

  // Create User Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'ADMIN',
    phone: '',
  });

  // Change Role Modal
  const [roleModalUser, setRoleModalUser] = useState<any>(null);
  const [targetRole, setTargetRole] = useState('ADMIN');

  useEffect(() => {
    loadUsers();
  }, [roleFilter]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getUsers({
        search: search.trim() || undefined,
        role: roleFilter || undefined,
      });
      setUsers(data);
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to fetch users.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadUsers();
  };

  const handleToggleStatus = async (user: any) => {
    const action = user.is_active ? 'suspend' : 'reactivate';
    if (!confirm(`Are you sure you want to ${action} user "${user.email}"?`)) return;
    try {
      await adminApi.toggleUserStatus(user.id, !user.is_active);
      onNotify(`User "${user.email}" ${action}ed successfully.`, 'success');
      loadUsers();
    } catch (err: any) {
      onNotify(err.response?.data?.detail || `Failed to ${action} user.`, 'error');
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createUser(newUser);
      onNotify(`Account created successfully for ${newUser.email} (${newUser.role})`, 'success');
      setShowCreateModal(false);
      setNewUser({ full_name: '', email: '', password: '', role: 'ADMIN', phone: '' });
      loadUsers();
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to create user account.', 'error');
    }
  };

  const handleRoleChangeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roleModalUser) return;
    try {
      await adminApi.updateUserRole(roleModalUser.id, targetRole);
      onNotify(`Role for ${roleModalUser.email} updated to ${targetRole}.`, 'success');
      setRoleModalUser(null);
      loadUsers();
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to update user role.', 'error');
    }
  };

  const handleViewDetail = async (userId: string) => {
    try {
      const detail = await adminApi.getUserDetail(userId);
      setSelectedUser(detail);
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to load user details.', 'error');
    }
  };

  const getRoleBadgeStyle = (role: string) => {
    switch (role) {
      case 'SUPER_ADMIN':
        return { background: '#fef3c7', color: '#92400e', border: '1px solid #f59e0b' };
      case 'ADMIN':
        return { background: '#dbeafe', color: '#1e40af', border: '1px solid #93c5fd' };
      case 'DOCTOR':
        return { background: '#ccfbf1', color: '#115e59', border: '1px solid #5eead4' };
      case 'SUPPORT_STAFF':
        return { background: '#f3e8ff', color: '#6b21a8', border: '1px solid #d8b4fe' };
      default:
        return { background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header Banner */}
      <div style={styles.headerBanner}>
        <div>
          <h2 style={{ margin: '0 0 6px 0', fontSize: 22, color: '#0F5C5E', display: 'flex', alignItems: 'center', gap: 8 }}>
            🛡️ Full User Management
            <span style={styles.superAdminTag}>SUPER ADMIN EXCLUSIVE</span>
          </h2>
          <p style={{ margin: 0, fontSize: 14, color: '#64748b' }}>
            System-wide identity directory: control user roles, provision administrator staff, and enforce account suspensions.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          style={styles.primaryButton}
        >
          ➕ Provision Staff / Admin
        </button>
      </div>

      {/* Search and Filters */}
      <div style={styles.filterRow}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 10, flex: 1 }}>
          <input
            type="text"
            placeholder="Search by full name or email address..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ ...styles.input, flex: 1 }}
          />
          <button type="submit" style={styles.secondaryButton}>
            🔍 Search
          </button>
        </form>

        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          style={{ ...styles.input, width: 180 }}
        >
          <option value="">All Roles</option>
          <option value="SUPER_ADMIN">SUPER_ADMIN</option>
          <option value="ADMIN">ADMIN</option>
          <option value="SUPPORT_STAFF">SUPPORT_STAFF</option>
          <option value="DOCTOR">DOCTOR</option>
          <option value="PATIENT">PATIENT</option>
        </select>

        <button onClick={loadUsers} style={styles.secondaryButton}>
          🔄 Refresh
        </button>
      </div>

      {/* Main Grid: Table & Optional Detail Drawer */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedUser ? '1fr 380px' : '1fr', gap: 16 }}>
        <div style={styles.card}>
          {loading ? (
            <div style={{ padding: 24, textAlign: 'center', color: '#0F5C5E', fontWeight: 600 }}>Loading users...</div>
          ) : (
            <table style={styles.table}>
              <thead>
                <tr style={styles.thRow}>
                  <th style={styles.th}>User / Contact</th>
                  <th style={styles.th}>Role</th>
                  <th style={styles.th}>Status</th>
                  <th style={styles.th}>Created</th>
                  <th style={styles.th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: 24, textAlign: 'center', color: '#888' }}>
                      No users match the search criteria.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} style={styles.tr}>
                      <td style={styles.td}>
                        <div style={{ fontWeight: 600, color: '#1e293b' }}>{u.full_name}</div>
                        <div style={{ fontSize: 12, color: '#64748b' }}>{u.email}</div>
                        {u.phone && <div style={{ fontSize: 11, color: '#94a3b8' }}>📞 {u.phone}</div>}
                      </td>
                      <td style={styles.td}>
                        <span style={{ ...styles.badge, ...getRoleBadgeStyle(u.role) }}>
                          {u.role}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: 4,
                            fontSize: 12,
                            fontWeight: 600,
                            background: u.is_active ? '#dcfce7' : '#fee2e2',
                            color: u.is_active ? '#15803d' : '#b91c1c',
                          }}
                        >
                          {u.is_active ? 'Active' : 'Suspended'}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <span style={{ fontSize: 12, color: '#64748b' }}>
                          {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          <button
                            onClick={() => handleViewDetail(u.id)}
                            style={{ ...styles.actionBtn, background: '#0F5C5E', color: '#fff' }}
                            title="View metrics & activity"
                          >
                            Details
                          </button>
                          <button
                            onClick={() => {
                              setRoleModalUser(u);
                              setTargetRole(u.role);
                            }}
                            style={{ ...styles.actionBtn, background: '#4338ca', color: '#fff' }}
                            title="Change role"
                          >
                            Role
                          </button>
                          <button
                            onClick={() => handleToggleStatus(u)}
                            style={{
                              ...styles.actionBtn,
                              background: u.is_active ? '#b91c1c' : '#15803d',
                              color: '#fff',
                            }}
                          >
                            {u.is_active ? 'Suspend' : 'Reactivate'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Selected User Detail Drawer */}
        {selectedUser && (
          <div style={{ ...styles.card, background: '#f8fafc', height: 'fit-content' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ margin: 0, fontSize: 16, color: '#0F5C5E' }}>User Operational Profile</h3>
              <button onClick={() => setSelectedUser(null)} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 16 }}>
                ✖
              </button>
            </div>
            <div style={{ fontSize: 13, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div><strong>Name:</strong> {selectedUser.full_name}</div>
              <div><strong>Email:</strong> {selectedUser.email}</div>
              <div>
                <strong>Role:</strong>{' '}
                <span style={{ ...styles.badge, ...getRoleBadgeStyle(selectedUser.role) }}>
                  {selectedUser.role}
                </span>
              </div>
              <div>
                <strong>Status:</strong>{' '}
                <span style={{ color: selectedUser.is_active ? '#15803d' : '#b91c1c', fontWeight: 600 }}>
                  {selectedUser.is_active ? 'Active' : 'Suspended'}
                </span>
              </div>
              <div><strong>User ID:</strong> <code style={{ fontSize: 11, background: '#e2e8f0', padding: '2px 4px', borderRadius: 3 }}>{selectedUser.id}</code></div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '4px 0' }} />
              <div><strong>Medical Reports:</strong> {selectedUser.summary_metrics?.reports_count ?? 0}</div>
              <div><strong>Appointments:</strong> {selectedUser.summary_metrics?.appointments_count ?? 0}</div>
              <div><strong>Symptom Logs:</strong> {selectedUser.summary_metrics?.symptom_logs_count ?? 0}</div>
              <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '4px 0' }} />
              <div style={{ fontSize: 11, color: '#64748b' }}>
                Joined: {selectedUser.created_at ? new Date(selectedUser.created_at).toLocaleString() : 'N/A'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* MODAL: PROVISION NEW USER */}
      {showCreateModal && (
        <div style={styles.modalOverlay}>
          <div style={{ ...styles.modalContent, maxWidth: 480 }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#0F5C5E' }}>Provision Staff or Admin Account</h3>
            <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={styles.label}>Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jane Sharma"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  style={styles.input}
                />
              </div>

              <div>
                <label style={styles.label}>Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. jsharma@vitalens.health"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  style={styles.input}
                />
              </div>

              <div>
                <label style={styles.label}>Temporary Password</label>
                <input
                  type="password"
                  required
                  placeholder="Minimum 6 characters"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  style={styles.input}
                />
              </div>

              <div>
                <label style={styles.label}>Phone Number (Optional)</label>
                <input
                  type="text"
                  placeholder="+91 98765 43210"
                  value={newUser.phone}
                  onChange={(e) => setNewUser({ ...newUser, phone: e.target.value })}
                  style={styles.input}
                />
              </div>

              <div>
                <label style={styles.label}>System Role</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  style={styles.input}
                >
                  <option value="ADMIN">ADMIN (Operations & Verification)</option>
                  <option value="SUPPORT_STAFF">SUPPORT_STAFF (Read-Only Support)</option>
                  <option value="PATIENT">PATIENT (Standard Patient Account)</option>
                  <option value="DOCTOR">DOCTOR (Healthcare Provider)</option>
                  <option value="SUPER_ADMIN">SUPER_ADMIN (Full Platform Authority)</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  style={styles.secondaryButton}
                >
                  Cancel
                </button>
                <button type="submit" style={styles.primaryButton}>
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CHANGE USER ROLE */}
      {roleModalUser && (
        <div style={styles.modalOverlay}>
          <div style={{ ...styles.modalContent, maxWidth: 420 }}>
            <h3 style={{ margin: '0 0 12px 0', color: '#0F5C5E' }}>Change User Role</h3>
            <p style={{ margin: '0 0 16px 0', fontSize: 13, color: '#64748b' }}>
              Target User: <strong>{roleModalUser.email}</strong> (Current Role: <code>{roleModalUser.role}</code>)
            </p>
            <form onSubmit={handleRoleChangeSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={styles.label}>Select New Role</label>
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  style={styles.input}
                >
                  <option value="ADMIN">ADMIN</option>
                  <option value="SUPPORT_STAFF">SUPPORT_STAFF</option>
                  <option value="PATIENT">PATIENT</option>
                  <option value="DOCTOR">DOCTOR</option>
                  <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setRoleModalUser(null)}
                  style={styles.secondaryButton}
                >
                  Cancel
                </button>
                <button type="submit" style={styles.primaryButton}>
                  Update Role
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  headerBanner: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    background: '#fff',
    padding: '20px 24px',
    borderRadius: 8,
    border: '1px solid #e2e8f0',
  },
  superAdminTag: {
    fontSize: 10,
    fontWeight: 800,
    padding: '3px 8px',
    borderRadius: 4,
    background: '#fef3c7',
    color: '#92400e',
    border: '1px solid #f59e0b',
    letterSpacing: '0.05em',
  },
  filterRow: {
    display: 'flex',
    gap: 12,
    alignItems: 'center',
    background: '#fff',
    padding: '14px 18px',
    borderRadius: 8,
    border: '1px solid #e2e8f0',
  },
  card: {
    background: '#fff',
    borderRadius: 8,
    border: '1px solid #e2e8f0',
    padding: 16,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'left',
    fontSize: 13,
  },
  thRow: {
    background: '#f8fafc',
    borderBottom: '2px solid #e2e8f0',
  },
  th: {
    padding: '12px 14px',
    fontWeight: 600,
    color: '#475569',
  },
  tr: {
    borderBottom: '1px solid #f1f5f9',
  },
  td: {
    padding: '12px 14px',
    verticalAlign: 'middle',
  },
  badge: {
    display: 'inline-block',
    padding: '3px 8px',
    borderRadius: 4,
    fontSize: 11,
    fontWeight: 700,
  },
  actionBtn: {
    border: 'none',
    padding: '5px 10px',
    borderRadius: 4,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 600,
    transition: 'opacity 0.15s ease',
  },
  primaryButton: {
    background: '#0F5C5E',
    color: '#fff',
    border: 'none',
    padding: '9px 16px',
    borderRadius: 6,
    fontWeight: 600,
    fontSize: 13,
    cursor: 'pointer',
  },
  secondaryButton: {
    background: '#f1f5f9',
    color: '#334155',
    border: '1px solid #cbd5e1',
    padding: '9px 14px',
    borderRadius: 6,
    fontWeight: 600,
    fontSize: 13,
    cursor: 'pointer',
  },
  input: {
    padding: '8px 12px',
    borderRadius: 6,
    border: '1px solid #cbd5e1',
    fontSize: 13,
    width: '100%',
    boxSizing: 'border-box',
  },
  label: {
    display: 'block',
    fontSize: 12,
    fontWeight: 600,
    color: '#334155',
    marginBottom: 4,
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
    zIndex: 9999,
  },
  modalContent: {
    background: '#fff',
    padding: 24,
    borderRadius: 8,
    width: '100%',
    boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
  },
};
