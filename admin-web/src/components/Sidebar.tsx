import React from 'react';
import {
  LayoutDashboard,
  Stethoscope,
  Users,
  Calendar,
  BookOpen,
  Sparkles,
  ShieldCheck,
  LogOut,
  CalendarCheck,
  UserCheck,
  Activity,
} from 'lucide-react';

export type AdminTab =
  | 'dashboard'
  | 'doctors'
  | 'patients'
  | 'appointments'
  | 'content'
  | 'ai_review'
  | 'user_management'
  | 'ai_trace';

export type DoctorTab =
  | 'doc_overview'
  | 'doc_appointments'
  | 'doc_schedule'
  | 'doc_patients';

interface SidebarProps {
  role: string | null;
  activeTab: string;
  onSelectTab: (tab: any) => void;
  onLogout: () => void;
  isDoctor: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  role,
  activeTab,
  onSelectTab,
  onLogout,
  isDoctor,
}) => {
  const isSuperAdmin = role === 'SUPER_ADMIN';

  // Format clean role pill label
  const getRoleBadge = () => {
    switch (role) {
      case 'SUPER_ADMIN':
        return {
          label: 'Super Admin',
          style: {
            background: 'rgba(245, 158, 11, 0.15)',
            color: '#fbbf24',
            border: '1px solid rgba(245, 158, 11, 0.35)',
          },
          dotColor: '#fbbf24',
        };
      case 'ADMIN':
        return {
          label: 'Platform Admin',
          style: {
            background: 'rgba(56, 189, 248, 0.15)',
            color: '#38bdf8',
            border: '1px solid rgba(56, 189, 248, 0.35)',
          },
          dotColor: '#38bdf8',
        };
      case 'DOCTOR':
        return {
          label: 'Healthcare Provider',
          style: {
            background: 'rgba(45, 212, 191, 0.15)',
            color: '#2dd4bf',
            border: '1px solid rgba(45, 212, 191, 0.35)',
          },
          dotColor: '#2dd4bf',
        };
      case 'SUPPORT_STAFF':
        return {
          label: 'Operations Staff',
          style: {
            background: 'rgba(192, 132, 252, 0.15)',
            color: '#c084fc',
            border: '1px solid rgba(192, 132, 252, 0.35)',
          },
          dotColor: '#c084fc',
        };
      default:
        return {
          label: role || 'Unknown Role',
          style: {
            background: 'rgba(148, 163, 184, 0.15)',
            color: '#94a3b8',
            border: '1px solid rgba(148, 163, 184, 0.3)',
          },
          dotColor: '#94a3b8',
        };
    }
  };

  const roleBadge = getRoleBadge();

  return (
    <div style={sidebarStyles.sidebar}>
      {/* Brand Header & Clean Consolidated Role Badge */}
      <div style={sidebarStyles.brandContainer}>
        <img
          src="/assets/vitalens-logo-on-dark.png"
          alt="VitaLens"
          style={sidebarStyles.logo}
        />
        <div style={sidebarStyles.badgeWrapper}>
          <div style={{ ...sidebarStyles.pillBadge, ...roleBadge.style }}>
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: roleBadge.dotColor,
                display: 'inline-block',
                marginRight: 6,
                boxShadow: `0 0 6px ${roleBadge.dotColor}`,
              }}
            />
            {roleBadge.label}
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <div style={sidebarStyles.navContainer}>
        {isDoctor ? (
          // Doctor Portal Navigation
          <>
            <div style={sidebarStyles.categoryHeader}>CLINICAL WORKSPACE</div>
            <button
              onClick={() => onSelectTab('doc_overview')}
              style={activeTab === 'doc_overview' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <LayoutDashboard size={17} style={sidebarStyles.icon} />
              Practice Overview
            </button>
            <button
              onClick={() => onSelectTab('doc_appointments')}
              style={activeTab === 'doc_appointments' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <CalendarCheck size={17} style={sidebarStyles.icon} />
              My Appointments
            </button>
            <button
              onClick={() => onSelectTab('doc_schedule')}
              style={activeTab === 'doc_schedule' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <Calendar size={17} style={sidebarStyles.icon} />
              Schedule & Availability
            </button>
            <button
              onClick={() => onSelectTab('doc_patients')}
              style={activeTab === 'doc_patients' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <UserCheck size={17} style={sidebarStyles.icon} />
              Consented Patients
            </button>
          </>
        ) : (
          // Admin & Super Admin Portal Navigation
          <>
            {/* Category: General Operations */}
            <div style={sidebarStyles.categoryHeader}>PLATFORM OPERATIONS</div>

            <button
              onClick={() => onSelectTab('dashboard')}
              style={activeTab === 'dashboard' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <LayoutDashboard size={17} style={sidebarStyles.icon} />
              Dashboard
            </button>

            <button
              onClick={() => onSelectTab('doctors')}
              style={activeTab === 'doctors' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <Stethoscope size={17} style={sidebarStyles.icon} />
              Doctors Management
            </button>

            <button
              onClick={() => onSelectTab('patients')}
              style={activeTab === 'patients' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <Users size={17} style={sidebarStyles.icon} />
              Patients Management
            </button>

            <button
              onClick={() => onSelectTab('appointments')}
              style={activeTab === 'appointments' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <Calendar size={17} style={sidebarStyles.icon} />
              Appointments Management
            </button>

            <button
              onClick={() => onSelectTab('content')}
              style={activeTab === 'content' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <BookOpen size={17} style={sidebarStyles.icon} />
              Clinical Content & Glossary
            </button>

            <button
              onClick={() => onSelectTab('ai_review')}
              style={activeTab === 'ai_review' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
            >
              <Sparkles size={17} style={sidebarStyles.icon} />
              AI Recommendation Review
            </button>

            {/* Category: Super Admin Exclusive */}
            {isSuperAdmin && (
              <>
                <div style={{ ...sidebarStyles.categoryHeader, marginTop: 16 }}>
                  SUPER ADMIN EXCLUSIVE
                </div>
                <button
                  onClick={() => onSelectTab('user_management')}
                  style={activeTab === 'user_management' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
                >
                  <ShieldCheck size={17} style={sidebarStyles.icon} />
                  User Management
                </button>
                <button
                  onClick={() => onSelectTab('ai_trace')}
                  style={activeTab === 'ai_trace' ? sidebarStyles.activeNavButton : sidebarStyles.navButton}
                >
                  <Activity size={17} style={sidebarStyles.icon} />
                  AI Trace
                </button>
              </>
            )}
          </>
        )}
      </div>

      {/* Logout Footer */}
      <div style={sidebarStyles.footer}>
        <button onClick={onLogout} style={sidebarStyles.logoutButton}>
          <LogOut size={15} style={{ marginRight: 6 }} />
          Sign Out
        </button>
      </div>
    </div>
  );
};

const sidebarStyles: { [key: string]: React.CSSProperties } = {
  sidebar: {
    width: 250,
    background: '#0F5C5E',
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0,
    height: '100vh',
    position: 'sticky',
    top: 0,
    borderRight: '1px solid rgba(255, 255, 255, 0.08)',
  },
  brandContainer: {
    padding: '18px 18px 14px 18px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
  },
  logo: {
    width: 140,
    height: 'auto',
    display: 'block',
    marginBottom: 10,
  },
  badgeWrapper: {
    display: 'flex',
    alignItems: 'center',
  },
  pillBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '4px 10px',
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.02em',
  },
  navContainer: {
    padding: '14px 10px',
    display: 'flex',
    flexDirection: 'column',
    gap: 3,
    overflowY: 'auto',
    flex: 1,
  },
  categoryHeader: {
    fontSize: 10,
    fontWeight: 700,
    color: '#7ea8a9',
    letterSpacing: '0.08em',
    padding: '8px 12px 4px 12px',
    textTransform: 'uppercase',
  },
  navButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    width: '100%',
    padding: '9px 12px',
    background: 'transparent',
    border: 'none',
    color: '#cbd5e1',
    textAlign: 'left',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    borderRadius: 6,
    transition: 'all 0.15s ease',
  },
  activeNavButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    width: '100%',
    padding: '9px 12px',
    background: 'rgba(255, 255, 255, 0.16)',
    border: 'none',
    color: '#ffffff',
    textAlign: 'left',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    borderRadius: 6,
    boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
  },
  icon: {
    flexShrink: 0,
    opacity: 0.9,
  },
  footer: {
    marginTop: 'auto',
    padding: 14,
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
  },
  logoutButton: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '8px 12px',
    background: 'rgba(0, 0, 0, 0.25)',
    color: '#fca5a5',
    border: '1px solid rgba(252, 165, 165, 0.25)',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 600,
    transition: 'background 0.15s ease',
  },
};
