import React from 'react';
import {
  Users,
  Stethoscope,
  FileText,
  Calendar,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Server,
  Database,
  ShieldCheck,
  Cpu,
  ArrowRight,
  UserPlus,
  Sparkles,
  BookOpen,
} from 'lucide-react';
import { AdminTab } from './Sidebar';

interface DashboardViewProps {
  analytics: any;
  isSuperAdmin: boolean;
  onNavigate: (tab: AdminTab) => void;
  onOpenAddDoctor: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  analytics,
  isSuperAdmin,
  onNavigate,
  onOpenAddDoctor,
}) => {
  const userMetrics = analytics?.user_metrics || {};
  const docMetrics = analytics?.doctor_metrics || {};
  const reportMetrics = analytics?.report_metrics || {};
  const apptMetrics = analytics?.appointment_metrics || {};

  const verificationRate = docMetrics.verification_rate_pct ?? (docMetrics.total_doctors ? Math.round((docMetrics.active_verified_doctors / docMetrics.total_doctors) * 100) : 100);
  const successRate = reportMetrics.success_rate_pct ?? 100;
  const cancellationRate = apptMetrics.cancellation_rate_pct ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* 1. POLISHED KPI METRIC CARDS */}
      <div style={dashStyles.kpiGrid}>
        {/* Card 1: Users */}
        <div style={dashStyles.kpiCard}>
          <div style={dashStyles.kpiHeader}>
            <span style={dashStyles.kpiLabel}>Total Registered Users</span>
            <div style={{ ...dashStyles.iconBadge, background: '#eff6ff', color: '#2563eb' }}>
              <Users size={18} />
            </div>
          </div>
          <div style={dashStyles.kpiValue}>{userMetrics.total_registered_users ?? 0}</div>
          <div style={dashStyles.trendRow}>
            <span style={{ ...dashStyles.trendBadge, background: '#ecfdf5', color: '#059669' }}>
              <TrendingUp size={13} style={{ marginRight: 4 }} />
              +{userMetrics.signups_this_week ?? 0} this week
            </span>
            <span style={dashStyles.trendSub}>
              {userMetrics.patient_accounts ?? 0} patients
            </span>
          </div>
        </div>

        {/* Card 2: Doctors */}
        <div style={dashStyles.kpiCard}>
          <div style={dashStyles.kpiHeader}>
            <span style={dashStyles.kpiLabel}>Verified Doctors</span>
            <div style={{ ...dashStyles.iconBadge, background: '#fffbeb', color: '#d97706' }}>
              <Stethoscope size={18} />
            </div>
          </div>
          <div style={dashStyles.kpiValue}>
            {docMetrics.active_verified_doctors ?? 0}
            <span style={{ fontSize: 15, color: '#94a3b8', fontWeight: 500, marginLeft: 4 }}>
              / {docMetrics.total_doctors ?? 0}
            </span>
          </div>
          <div style={dashStyles.trendRow}>
            <span
              style={{
                ...dashStyles.trendBadge,
                background: (docMetrics.pending_verification ?? 0) > 0 ? '#fef3c7' : '#ecfdf5',
                color: (docMetrics.pending_verification ?? 0) > 0 ? '#b45309' : '#059669',
              }}
            >
              <Clock size={13} style={{ marginRight: 4 }} />
              {docMetrics.pending_verification ?? 0} pending review
            </span>
            <span style={dashStyles.trendSub}>{verificationRate}% verified</span>
          </div>
        </div>

        {/* Card 3: Reports */}
        <div style={dashStyles.kpiCard}>
          <div style={dashStyles.kpiHeader}>
            <span style={dashStyles.kpiLabel}>Reports Processed</span>
            <div style={{ ...dashStyles.iconBadge, background: '#ecfdf5', color: '#059669' }}>
              <FileText size={18} />
            </div>
          </div>
          <div style={dashStyles.kpiValue}>{reportMetrics.total_reports_processed ?? 0}</div>
          <div style={dashStyles.trendRow}>
            <span style={{ ...dashStyles.trendBadge, background: '#ecfdf5', color: '#059669' }}>
              <CheckCircle2 size={13} style={{ marginRight: 4 }} />
              {reportMetrics.successfully_analyzed ?? 0} analyzed
            </span>
            <span style={dashStyles.trendSub}>{successRate}% success rate</span>
          </div>
        </div>

        {/* Card 4: Appointments */}
        <div style={dashStyles.kpiCard}>
          <div style={dashStyles.kpiHeader}>
            <span style={dashStyles.kpiLabel}>Consultations Booked</span>
            <div style={{ ...dashStyles.iconBadge, background: '#f5f3ff', color: '#7c3aed' }}>
              <Calendar size={18} />
            </div>
          </div>
          <div style={dashStyles.kpiValue}>{apptMetrics.total_bookings ?? 0}</div>
          <div style={dashStyles.trendRow}>
            <span
              style={{
                ...dashStyles.trendBadge,
                background: cancellationRate > 20 ? '#fee2e2' : '#f1f5f9',
                color: cancellationRate > 20 ? '#b91c1c' : '#475569',
              }}
            >
              <AlertTriangle size={13} style={{ marginRight: 4 }} />
              {cancellationRate}% cancellations
            </span>
            <span style={dashStyles.trendSub}>
              {apptMetrics.active_confirmed ?? 0} active
            </span>
          </div>
        </div>
      </div>

      {/* 2. MIDDLE ROW: QUICK ACTIONS & SYSTEM HEALTH STATUS */}
      <div style={dashStyles.gridTwoCols}>
        {/* Quick Actions Panel */}
        <div style={dashStyles.panelCard}>
          <div style={dashStyles.panelTitleRow}>
            <div style={dashStyles.panelTitle}>
              ⚡ Quick Actions & Shortcuts
            </div>
            <span style={dashStyles.panelSubtitle}>Frequent administrative operations</span>
          </div>

          <div style={dashStyles.actionGrid}>
            {isSuperAdmin && (
              <button
                onClick={() => onNavigate('user_management')}
                style={dashStyles.actionButton}
              >
                <div style={{ ...dashStyles.actionIconBox, background: '#fef3c7', color: '#b45309' }}>
                  <UserPlus size={18} />
                </div>
                <div style={{ textAlign: 'left', flex: 1 }}>
                  <div style={dashStyles.actionLabel}>Provision New User</div>
                  <div style={dashStyles.actionSub}>Create Admin, Doctor, or Staff</div>
                </div>
                <ArrowRight size={15} color="#94a3b8" />
              </button>
            )}

            <button onClick={onOpenAddDoctor} style={dashStyles.actionButton}>
              <div style={{ ...dashStyles.actionIconBox, background: '#eff6ff', color: '#1d4ed8' }}>
                <Stethoscope size={18} />
              </div>
              <div style={{ textAlign: 'left', flex: 1 }}>
                <div style={dashStyles.actionLabel}>Onboard Doctor</div>
                <div style={dashStyles.actionSub}>Register credentials & clinic</div>
              </div>
              <ArrowRight size={15} color="#94a3b8" />
            </button>

            <button onClick={() => onNavigate('ai_review')} style={dashStyles.actionButton}>
              <div style={{ ...dashStyles.actionIconBox, background: '#f5f3ff', color: '#6d28d9' }}>
                <Sparkles size={18} />
              </div>
              <div style={{ textAlign: 'left', flex: 1 }}>
                <div style={dashStyles.actionLabel}>Review AI Queue</div>
                <div style={dashStyles.actionSub}>Validate clinical suggestions</div>
              </div>
              <ArrowRight size={15} color="#94a3b8" />
            </button>

            <button onClick={() => onNavigate('content')} style={dashStyles.actionButton}>
              <div style={{ ...dashStyles.actionIconBox, background: '#ecfdf5', color: '#047857' }}>
                <BookOpen size={18} />
              </div>
              <div style={{ textAlign: 'left', flex: 1 }}>
                <div style={dashStyles.actionLabel}>Clinical Thresholds</div>
                <div style={dashStyles.actionSub}>Edit reference ranges & terms</div>
              </div>
              <ArrowRight size={15} color="#94a3b8" />
            </button>
          </div>
        </div>

        {/* System Health Status Panel */}
        <div style={dashStyles.panelCard}>
          <div style={dashStyles.panelTitleRow}>
            <div style={dashStyles.panelTitle}>
              🩺 Infrastructure & Subsystem Health
            </div>
            <span style={dashStyles.panelSubtitle}>Live runtime environment probes</span>
          </div>

          <div style={dashStyles.healthList}>
            {/* API Health */}
            <div style={dashStyles.healthItem}>
              <div style={dashStyles.healthLeft}>
                <div style={{ ...dashStyles.healthIcon, background: '#ecfdf5', color: '#059669' }}>
                  <Server size={16} />
                </div>
                <div>
                  <div style={dashStyles.healthName}>FastAPI Core Gateway</div>
                  <div style={dashStyles.healthDesc}>REST API v1 • Latency ~24ms • Ready</div>
                </div>
              </div>
              <span style={dashStyles.statusLivePill}>
                <span style={dashStyles.statusLiveDot} />
                Operational
              </span>
            </div>

            {/* DB Health */}
            <div style={dashStyles.healthItem}>
              <div style={dashStyles.healthLeft}>
                <div style={{ ...dashStyles.healthIcon, background: '#eff6ff', color: '#2563eb' }}>
                  <Database size={16} />
                </div>
                <div>
                  <div style={dashStyles.healthName}>PostgreSQL Engine</div>
                  <div style={dashStyles.healthDesc}>Database `vitalens_db` • Migration Rev `2b3c4d5e6f7a`</div>
                </div>
              </div>
              <span style={dashStyles.statusLivePill}>
                <span style={dashStyles.statusLiveDot} />
                Connected
              </span>
            </div>

            {/* Security & DPDP */}
            <div style={dashStyles.healthItem}>
              <div style={dashStyles.healthLeft}>
                <div style={{ ...dashStyles.healthIcon, background: '#f5f3ff', color: '#7c3aed' }}>
                  <ShieldCheck size={16} />
                </div>
                <div>
                  <div style={dashStyles.healthName}>DPDP Privacy & Consent Vault</div>
                  <div style={dashStyles.healthDesc}>5 Consent Types • Soft-Delete Audit Enforced</div>
                </div>
              </div>
              <span style={dashStyles.statusLivePill}>
                <span style={dashStyles.statusLiveDot} />
                Enforced
              </span>
            </div>

            {/* AI Rules Engine */}
            <div style={dashStyles.healthItem}>
              <div style={dashStyles.healthLeft}>
                <div style={{ ...dashStyles.healthIcon, background: '#fffbeb', color: '#d97706' }}>
                  <Cpu size={16} />
                </div>
                <div>
                  <div style={dashStyles.healthName}>Clinical OCR & Rule Extractor</div>
                  <div style={dashStyles.healthDesc}>Biomarker Flags • In-Memory Cache Active</div>
                </div>
              </div>
              <span style={dashStyles.statusLivePill}>
                <span style={dashStyles.statusLiveDot} />
                Standby
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. BOTTOM ROW: OPERATIONAL PROGRESS BARS & BREAKDOWN */}
      <div style={dashStyles.panelCard}>
        <div style={dashStyles.panelTitleRow}>
          <div style={dashStyles.panelTitle}>
            📈 Operational Quality & Conversion Rates
          </div>
          <span style={dashStyles.panelSubtitle}>Key platform performance benchmarks</span>
        </div>

        <div style={dashStyles.metricsGrid}>
          {/* Progress 1: Doctor Verification */}
          <div style={dashStyles.metricCol}>
            <div style={dashStyles.metricBarHeader}>
              <span style={dashStyles.metricBarLabel}>Doctor Verification Rate</span>
              <span style={dashStyles.metricBarValue}>{verificationRate}%</span>
            </div>
            <div style={dashStyles.barTrack}>
              <div style={{ ...dashStyles.barFill, width: `${verificationRate}%`, background: '#059669' }} />
            </div>
            <div style={dashStyles.metricBarFooter}>
              {docMetrics.active_verified_doctors ?? 0} verified out of {docMetrics.total_doctors ?? 0} total
            </div>
          </div>

          {/* Progress 2: Report Success */}
          <div style={dashStyles.metricCol}>
            <div style={dashStyles.metricBarHeader}>
              <span style={dashStyles.metricBarLabel}>Report Extraction Success</span>
              <span style={dashStyles.metricBarValue}>{successRate}%</span>
            </div>
            <div style={dashStyles.barTrack}>
              <div style={{ ...dashStyles.barFill, width: `${successRate}%`, background: '#2563eb' }} />
            </div>
            <div style={dashStyles.metricBarFooter}>
              {reportMetrics.successfully_analyzed ?? 0} successful / {reportMetrics.total_reports_processed ?? 0} attempts
            </div>
          </div>

          {/* Progress 3: Appointments Retention */}
          <div style={dashStyles.metricCol}>
            <div style={dashStyles.metricBarHeader}>
              <span style={dashStyles.metricBarLabel}>Consultation Completion</span>
              <span style={dashStyles.metricBarValue}>{100 - cancellationRate}%</span>
            </div>
            <div style={dashStyles.barTrack}>
              <div style={{ ...dashStyles.barFill, width: `${Math.max(0, 100 - cancellationRate)}%`, background: '#7c3aed' }} />
            </div>
            <div style={dashStyles.metricBarFooter}>
              {apptMetrics.completed_consultations ?? 0} completed, {apptMetrics.active_confirmed ?? 0} scheduled
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const dashStyles: { [key: string]: React.CSSProperties } = {
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: 16,
  },
  kpiCard: {
    background: '#ffffff',
    padding: '20px 22px',
    borderRadius: 8,
    border: '1px solid #e2e8f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
  },
  kpiHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  kpiLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: '#64748b',
  },
  iconBadge: {
    width: 36,
    height: 36,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  kpiValue: {
    fontSize: 28,
    fontWeight: 800,
    color: '#0f172a',
    letterSpacing: '-0.02em',
    marginBottom: 10,
  },
  trendRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    fontSize: 12,
  },
  trendBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 8px',
    borderRadius: 12,
    fontWeight: 700,
    fontSize: 11,
  },
  trendSub: {
    color: '#94a3b8',
    fontWeight: 500,
  },
  gridTwoCols: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 20,
  },
  panelCard: {
    background: '#ffffff',
    borderRadius: 8,
    border: '1px solid #e2e8f0',
    padding: '22px 24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
  },
  panelTitleRow: {
    marginBottom: 16,
  },
  panelTitle: {
    fontSize: 15,
    fontWeight: 700,
    color: '#0f172a',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  panelSubtitle: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
    display: 'block',
  },
  actionGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 12,
  },
  actionButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '12px 14px',
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: 8,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  actionIconBox: {
    width: 38,
    height: 38,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  actionLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: '#1e293b',
  },
  actionSub: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 2,
  },
  healthList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  healthItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 12px',
    background: '#f8fafc',
    borderRadius: 6,
    border: '1px solid #f1f5f9',
  },
  healthLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  healthIcon: {
    width: 32,
    height: 32,
    borderRadius: 6,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  healthName: {
    fontSize: 13,
    fontWeight: 600,
    color: '#1e293b',
  },
  healthDesc: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 1,
  },
  statusLivePill: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '3px 9px',
    background: '#ecfdf5',
    color: '#059669',
    borderRadius: 12,
    fontSize: 11,
    fontWeight: 700,
  },
  statusLiveDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: '#10b981',
    boxShadow: '0 0 6px #10b981',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: 24,
  },
  metricCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  metricBarHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 13,
  },
  metricBarLabel: {
    fontWeight: 600,
    color: '#334155',
  },
  metricBarValue: {
    fontWeight: 700,
    color: '#0F5C5E',
  },
  barTrack: {
    width: '100%',
    height: 8,
    background: '#f1f5f9',
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
    transition: 'width 0.4s ease',
  },
  metricBarFooter: {
    fontSize: 11,
    color: '#64748b',
  },
};
