import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Search,
  Filter,
  RefreshCw,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronRight,
  ChevronDown,
  Cpu,
  Database,
  FileText,
  Sliders,
  PlayCircle,
  Copy,
  Check,
  Zap,
  ArrowRight,
  ShieldAlert,
  Code
} from 'lucide-react';
import { adminApi } from '../api/adminApi';

interface AITraceViewProps {
  onNotify: (msg: string, type: 'success' | 'error') => void;
}

// Preset Report #2 Biomarkers for Diagnostic Simulation
const REPORT_2_BIOMARKERS = [
  { test_name: 'TSH', canonical_name: 'tsh', value_numeric: 6.8, unit: 'uIU/mL', flag: 'HIGH', reference_text: '0.45 - 4.5' },
  { test_name: 'Free T4', canonical_name: 'free_t4', value_numeric: 0.72, unit: 'ng/dL', flag: 'LOW', reference_text: '0.82 - 1.77' },
  { test_name: 'Ferritin', canonical_name: 'ferritin', value_numeric: 9, unit: 'ng/mL', flag: 'LOW', reference_text: '15 - 150' },
  { test_name: 'Serum Iron', canonical_name: 'iron', value_numeric: 42, unit: 'ug/dL', flag: 'LOW', reference_text: '60 - 170' },
  { test_name: 'Hemoglobin', canonical_name: 'hemoglobin', value_numeric: 11.2, unit: 'g/dL', flag: 'LOW', reference_text: '12.0 - 16.0' },
  { test_name: 'RBC Count', canonical_name: 'rbc_count', value_numeric: 3.78, unit: 'M/uL', flag: 'LOW', reference_text: '4.0 - 5.2' },
  { test_name: 'Hematocrit', canonical_name: 'hematocrit', value_numeric: 34.1, unit: '%', flag: 'LOW', reference_text: '37.0 - 48.0' },
  { test_name: 'WBC Count', canonical_name: 'wbc_count', value_numeric: 12400, unit: '/uL', flag: 'HIGH', reference_text: '4500 - 11000' },
  { test_name: 'Platelet Count', canonical_name: 'platelets', value_numeric: 472000, unit: '/uL', flag: 'HIGH', reference_text: '150000 - 450000' },
  { test_name: 'Total Bilirubin', canonical_name: 'bilirubin_total', value_numeric: 1.4, unit: 'mg/dL', flag: 'HIGH', reference_text: '0.2 - 1.2' },
  { test_name: 'LDL Cholesterol', canonical_name: 'ldl_cholesterol', value_numeric: 112, unit: 'mg/dL', flag: 'HIGH', reference_text: '< 100' },
];

export const AITraceView: React.FC<AITraceViewProps> = ({ onNotify }) => {
  const [traces, setTraces] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<any>(null);
  const [traceDetailLoading, setTraceDetailLoading] = useState(false);

  // Search & Filter
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [specialtyFilter, setSpecialtyFilter] = useState('');

  // Live SSE
  const [isLiveStream, setIsLiveStream] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Expanded Steps in Detail View
  const [expandedSteps, setExpandedSteps] = useState<{ [key: number]: boolean }>({
    4: true,
    5: true,
    6: true,
    7: true,
    8: true,
    9: true,
    10: true,
  });

  // Raw JSON Mode
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  // Diagnostic Simulator Modal
  const [showSimModal, setShowSimModal] = useState(false);
  const [simLoading, setSimLoading] = useState(false);
  const [simConcern, setSimConcern] = useState('Severe fatigue, dizziness, and frequent headaches');
  const [simSymptoms, setSimSymptoms] = useState('fatigue, dizziness, headache');
  const [simSeverity, setSimSeverity] = useState(6);
  const [simDuration, setSimDuration] = useState(14);
  const [simBodyRegion, setSimBodyRegion] = useState('Head and Neurological');

  useEffect(() => {
    loadTraces();
    loadStats();
  }, [statusFilter, specialtyFilter]);

  // Connect SSE Live Stream
  useEffect(() => {
    if (!isLiveStream) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    const token = localStorage.getItem('vitalens_admin_token');
    if (!token) return;

    const sseUrl = `http://localhost:8000/api/v1/admin/ai-trace/stream/live?token=${encodeURIComponent(token)}`;
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'TRACE_COMPLETED') {
          loadTraces();
          loadStats();
        } else if (payload.type === 'STEP_UPDATE' && payload.trace_id === selectedTraceId) {
          loadTraceDetail(payload.trace_id);
        }
      } catch (err) {
        // Ignored keep-alive or malformed ping
      }
    };

    es.onerror = () => {
      // Reconnection handled automatically by browser EventSource
    };

    return () => {
      if (es) es.close();
    };
  }, [isLiveStream, selectedTraceId]);

  const loadTraces = async () => {
    setLoading(true);
    try {
      const data = await adminApi.listAITraces({
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        specialty: specialtyFilter || undefined,
        limit: 50,
      });
      setTraces(data.items || []);
      if (data.items?.length > 0 && !selectedTraceId) {
        setSelectedTraceId(data.items[0].trace_id);
        loadTraceDetail(data.items[0].trace_id);
      }
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to load AI traces.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await adminApi.getAITraceStats();
      setStats(data);
    } catch (err) {
      // Non-critical
    }
  };

  const loadTraceDetail = async (traceId: string) => {
    setTraceDetailLoading(true);
    try {
      const data = await adminApi.getAITraceDetail(traceId);
      setSelectedTrace(data);
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Failed to load trace detail.', 'error');
    } finally {
      setTraceDetailLoading(false);
    }
  };

  const handleSelectTrace = (traceId: string) => {
    setSelectedTraceId(traceId);
    loadTraceDetail(traceId);
  };

  const handleCopyTraceId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleStep = (stepNum: number) => {
    setExpandedSteps((prev) => ({ ...prev, [stepNum]: !prev[stepNum] }));
  };

  // Diagnostic Simulator Preset Handlers
  const applyPreset = (presetType: 'A' | 'B' | 'C') => {
    if (presetType === 'A') {
      setSimConcern('Chronic fatigue, lightheadedness and constant dull headache');
      setSimSymptoms('fatigue, dizziness, headache');
      setSimSeverity(6);
      setSimDuration(14);
      setSimBodyRegion('Head and Neurological');
    } else if (presetType === 'B') {
      setSimConcern('Noticeable swelling in the front of neck accompanied by fatigue');
      setSimSymptoms('neck swelling, fatigue, cold sensitivity');
      setSimSeverity(5);
      setSimDuration(30);
      setSimBodyRegion('Neck & Throat');
    } else if (presetType === 'C') {
      setSimConcern('Routine annual lab checkup and general follow-up');
      setSimSymptoms('');
      setSimSeverity(2);
      setSimDuration(3);
      setSimBodyRegion('Whole Body');
    }
  };

  const handleRunSimulation = async () => {
    setSimLoading(true);
    try {
      const symptomsArray = simSymptoms
        ? simSymptoms.split(',').map((s) => s.trim()).filter(Boolean)
        : [];

      const result = await adminApi.simulateAITrace({
        primary_concern: simConcern,
        symptoms_list: symptomsArray,
        body_region: simBodyRegion,
        severity_score: simSeverity,
        duration_days: simDuration,
        biomarkers: REPORT_2_BIOMARKERS,
      });

      onNotify(`Trace ${result.trace_id} executed successfully!`, 'success');
      setShowSimModal(false);
      await loadTraces();
      await loadStats();
      setSelectedTraceId(result.trace_id);
      await loadTraceDetail(result.trace_id);
    } catch (err: any) {
      onNotify(err.response?.data?.detail || 'Simulation execution failed.', 'error');
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Top Header & Telemetry Bar */}
      <div style={styles.header}>
        <div style={styles.titleSection}>
          <div style={styles.badgeRow}>
            <span style={styles.superAdminBadge}>SUPER ADMIN EXCLUSIVE</span>
            <span style={styles.liveIndicator}>
              <span
                style={{
                  ...styles.pulsingDot,
                  backgroundColor: isLiveStream ? '#10b981' : '#64748b',
                }}
              />
              {isLiveStream ? 'LIVE STREAM ACTIVE' : 'STREAM PAUSED'}
            </span>
          </div>
          <h1 style={styles.pageTitle}>AI Pipeline Trace & Observability</h1>
          <p style={styles.pageSubtitle}>
            End-to-end technical inspection of VitaLensSpecialtyNet neural inference, canonical feature mappings, and clinical triage decisions.
          </p>
        </div>

        <div style={styles.headerActions}>
          <button
            onClick={() => setIsLiveStream(!isLiveStream)}
            style={{
              ...styles.toggleStreamBtn,
              borderColor: isLiveStream ? '#10b981' : '#475569',
              color: isLiveStream ? '#10b981' : '#94a3b8',
            }}
          >
            <Zap size={15} style={{ marginRight: 6 }} />
            {isLiveStream ? 'Pause Stream' : 'Resume Stream'}
          </button>

          <button
            onClick={() => setShowSimModal(true)}
            style={styles.simulateBtn}
          >
            <PlayCircle size={16} style={{ marginRight: 6 }} />
            Diagnostic Simulator
          </button>

          <button
            onClick={() => {
              loadTraces();
              loadStats();
              if (selectedTraceId) loadTraceDetail(selectedTraceId);
            }}
            style={styles.refreshBtn}
            title="Refresh Trace Logs"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* KPI Stats Bar */}
      {stats && (
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statLabel}>Total Traces</div>
            <div style={styles.statValue}>{stats.total_traces?.toLocaleString()}</div>
            <div style={styles.statSub}>Logged executions</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statLabel}>Success Status</div>
            <div style={{ ...styles.statValue, color: '#10b981' }}>
              {stats.status_breakdown?.SUCCESS || 0}
            </div>
            <div style={styles.statSub}>
              {stats.status_breakdown?.WARNING || 0} warnings &middot; {stats.status_breakdown?.FAILED || 0} failed
            </div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statLabel}>Avg Processing Latency</div>
            <div style={{ ...styles.statValue, color: '#38bdf8' }}>
              {stats.average_duration_ms} <span style={{ fontSize: '0.875rem' }}>ms</span>
            </div>
            <div style={styles.statSub}>Full 11-step pipeline duration</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statLabel}>Emergency Intercepts</div>
            <div style={{ ...styles.statValue, color: '#f59e0b' }}>
              {stats.emergency_intercepts || 0}
            </div>
            <div style={styles.statSub}>Urgent red-flag overrides</div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div style={styles.filterBar}>
        <div style={styles.searchBox}>
          <Search size={16} style={{ color: '#94a3b8', marginRight: 8 }} />
          <input
            type="text"
            placeholder="Search by Trace ID (e.g. VL-20261003-XXXXXX) or symptom..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadTraces()}
            style={styles.searchInput}
          />
        </div>

        <div style={styles.filterPills}>
          <button
            onClick={() => setStatusFilter('')}
            style={statusFilter === '' ? styles.activeFilterPill : styles.filterPill}
          >
            All Statuses
          </button>
          <button
            onClick={() => setStatusFilter('SUCCESS')}
            style={statusFilter === 'SUCCESS' ? styles.activeFilterPill : styles.filterPill}
          >
            Success
          </button>
          <button
            onClick={() => setStatusFilter('WARNING')}
            style={statusFilter === 'WARNING' ? styles.activeFilterPill : styles.filterPill}
          >
            Warnings
          </button>
          <button
            onClick={() => setStatusFilter('FAILED')}
            style={statusFilter === 'FAILED' ? styles.activeFilterPill : styles.filterPill}
          >
            Failed
          </button>
        </div>

        <div style={styles.specialtyDropdown}>
          <Filter size={15} style={{ color: '#94a3b8', marginRight: 6 }} />
          <select
            value={specialtyFilter}
            onChange={(e) => setSpecialtyFilter(e.target.value)}
            style={styles.selectInput}
          >
            <option value="">All Specialties</option>
            <option value="Endocrinology">Endocrinology</option>
            <option value="Hematology">Hematology</option>
            <option value="Gastroenterology">Gastroenterology</option>
            <option value="Cardiology">Cardiology</option>
            <option value="Nephrology">Nephrology</option>
            <option value="Neurology">Neurology</option>
            <option value="Pulmonology">Pulmonology</option>
            <option value="General Medicine">General Medicine</option>
          </select>
        </div>
      </div>

      {/* Main Split Layout: Left Trace List, Right Deep-Dive */}
      <div style={styles.mainGrid}>
        {/* Left Trace List */}
        <div style={styles.leftPane}>
          <div style={styles.paneHeader}>
            <span style={styles.paneTitle}>EXECUTION SESSIONS ({traces.length})</span>
          </div>

          <div style={styles.traceList}>
            {loading && traces.length === 0 ? (
              <div style={styles.emptyState}>Loading traces...</div>
            ) : traces.length === 0 ? (
              <div style={styles.emptyState}>
                No AI traces found matching your criteria. Click "Diagnostic Simulator" to create one.
              </div>
            ) : (
              traces.map((t) => {
                const isSelected = t.trace_id === selectedTraceId;
                return (
                  <div
                    key={t.id || t.trace_id}
                    onClick={() => handleSelectTrace(t.trace_id)}
                    style={{
                      ...styles.traceCard,
                      ...(isSelected ? styles.traceCardSelected : {}),
                    }}
                  >
                    <div style={styles.cardTopRow}>
                      <span style={styles.traceIdBadge}>{t.trace_id}</span>
                      <span
                        style={{
                          ...styles.statusBadge,
                          ...(t.status === 'SUCCESS'
                            ? styles.statusSuccess
                            : t.status === 'WARNING'
                            ? styles.statusWarning
                            : styles.statusFailed),
                        }}
                      >
                        {t.status}
                      </span>
                    </div>

                    <div style={styles.cardConcern}>
                      {t.primary_concern || 'No primary concern stated'}
                    </div>

                    <div style={styles.cardBottomRow}>
                      <div style={styles.specialtyChip}>
                        <span style={styles.specialtyName}>{t.top_specialty || 'General Medicine'}</span>
                        {t.confidence_score && (
                          <span style={styles.confPercent}>
                            {(t.confidence_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                      <div style={styles.durationChip}>
                        <Clock size={11} style={{ marginRight: 3 }} />
                        {t.total_duration_ms?.toFixed(1)} ms
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Detail Pane */}
        <div style={styles.rightPane}>
          {traceDetailLoading ? (
            <div style={styles.emptyState}>Loading trace telemetry...</div>
          ) : !selectedTrace ? (
            <div style={styles.emptyState}>Select an execution trace from the left panel to inspect.</div>
          ) : (
            <div style={styles.detailContainer}>
              {/* Detail Header Banner */}
              <div style={styles.detailHeader}>
                <div style={styles.detailHeaderLeft}>
                  <div style={styles.traceTitleRow}>
                    <span style={styles.detailTraceId}>{selectedTrace.trace_id}</span>
                    <button
                      onClick={() => handleCopyTraceId(selectedTrace.trace_id)}
                      style={styles.copyBtn}
                      title="Copy Trace ID"
                    >
                      {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                    </button>
                    <span
                      style={{
                        ...styles.statusBadge,
                        ...(selectedTrace.status === 'SUCCESS'
                          ? styles.statusSuccess
                          : selectedTrace.status === 'WARNING'
                          ? styles.statusWarning
                          : styles.statusFailed),
                      }}
                    >
                      {selectedTrace.status}
                    </span>
                  </div>
                  <div style={styles.metaRow}>
                    <span>Created: {new Date(selectedTrace.created_at).toLocaleString()}</span>
                    <span>&middot;</span>
                    <span>Role: {selectedTrace.user_role}</span>
                    <span>&middot;</span>
                    <span>Endpoint: {selectedTrace.endpoint}</span>
                    <span>&middot;</span>
                    <span>Duration: {selectedTrace.total_duration_ms} ms</span>
                  </div>
                </div>

                <div style={styles.detailHeaderRight}>
                  <button
                    onClick={() => setShowRawJson(!showRawJson)}
                    style={{
                      ...styles.viewJsonBtn,
                      backgroundColor: showRawJson ? '#334155' : 'transparent',
                    }}
                  >
                    <Code size={14} style={{ marginRight: 5 }} />
                    {showRawJson ? 'Visual Timeline' : 'Raw JSON'}
                  </button>
                </div>
              </div>

              {/* Model & Architecture Summary Card */}
              <div style={styles.modelMetaCard}>
                <div style={styles.metaBlock}>
                  <span style={styles.metaKey}>Inference Engine</span>
                  <span style={styles.metaVal}>{selectedTrace.model_metadata?.model_name || 'VitaLensSpecialtyNet'}</span>
                </div>
                <div style={styles.metaBlock}>
                  <span style={styles.metaKey}>Model Weights</span>
                  <span style={styles.metaVal}>{selectedTrace.model_metadata?.model_version || 'specialty-net-v1.0.0'}</span>
                </div>
                <div style={styles.metaBlock}>
                  <span style={styles.metaKey}>Preprocessor</span>
                  <span style={styles.metaVal}>{selectedTrace.model_metadata?.preprocessing_version || 'feature-pipeline-v1.0'}</span>
                </div>
                <div style={styles.metaBlock}>
                  <span style={styles.metaKey}>Resulting Specialty</span>
                  <span style={{ ...styles.metaVal, color: '#38bdf8', fontWeight: 700 }}>
                    {selectedTrace.top_specialty} ({(selectedTrace.confidence_score * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>

              {/* Main Content: Raw JSON or 11-Step Interactive Pipeline */}
              {showRawJson ? (
                <div style={styles.rawJsonBox}>
                  <pre style={styles.preformatted}>
                    {JSON.stringify(selectedTrace, null, 2)}
                  </pre>
                </div>
              ) : (
                <div style={styles.timelineContainer}>
                  <div style={styles.timelineHeader}>
                    <span>11-STEP CLINICAL INFERENCE PIPELINE</span>
                    <span style={styles.stepCountBadge}>
                      {selectedTrace.steps?.length || 0} STEPS EXECUTED
                    </span>
                  </div>

                  <div style={styles.stepsList}>
                    {selectedTrace.steps?.map((step: any) => {
                      const isExpanded = expandedSteps[step.step_number];
                      return (
                        <div key={step.step_number} style={styles.stepCard}>
                          {/* Step Header Accordion */}
                          <div
                            onClick={() => toggleStep(step.step_number)}
                            style={styles.stepHeader}
                          >
                            <div style={styles.stepHeaderLeft}>
                              <span style={styles.stepNumPill}>{step.step_number}</span>
                              <span style={styles.stepName}>{step.step_name.replace(/_/g, ' ')}</span>
                              <span
                                style={{
                                  ...styles.stepStatusBadge,
                                  ...(step.status === 'SUCCESS'
                                    ? styles.stepStatusSuccess
                                    : step.status === 'WARNING'
                                    ? styles.stepStatusWarning
                                    : styles.stepStatusFailed),
                                }}
                              >
                                {step.status}
                              </span>
                            </div>

                            <div style={styles.stepHeaderRight}>
                              <span style={styles.stepDuration}>
                                {step.duration_ms} ms
                              </span>
                              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            </div>
                          </div>

                          {/* Step Content */}
                          {isExpanded && (
                            <div style={styles.stepBody}>
                              {/* Step 1: Request Received */}
                              {step.step_name === 'REQUEST_RECEIVED' && (
                                <div style={styles.detailGrid}>
                                  <div><strong>Endpoint:</strong> {step.details?.endpoint}</div>
                                  <div><strong>Operation:</strong> {step.details?.operation}</div>
                                  <div><strong>User Role:</strong> {step.details?.authenticated_role}</div>
                                  <div><strong>Client IP:</strong> {step.details?.client_ip || 'N/A'}</div>
                                </div>
                              )}

                              {/* Step 2: User Input */}
                              {step.step_name === 'USER_INPUT' && (
                                <div>
                                  <div style={styles.detailRow}>
                                    <strong>Primary Concern:</strong> {step.details?.main_concern}
                                  </div>
                                  <div style={styles.detailRow}>
                                    <strong>Symptoms List:</strong>{' '}
                                    {step.details?.selected_symptoms?.length > 0
                                      ? step.details?.selected_symptoms?.join(', ')
                                      : 'None specified'}
                                  </div>
                                  <div style={styles.detailGrid}>
                                    <div><strong>Affected Region:</strong> {step.details?.body_region}</div>
                                    <div><strong>Severity:</strong> {step.details?.severity_score}</div>
                                    <div><strong>Duration:</strong> {step.details?.duration_days} days</div>
                                  </div>
                                </div>
                              )}

                              {/* Step 3: Report Data */}
                              {step.step_name === 'REPORT_DATA' && (
                                <div>
                                  <div style={{ marginBottom: 8 }}>
                                    <strong>Report ID:</strong> {step.details?.report_id} &middot;{' '}
                                    <strong>Extracted Biomarkers:</strong> {step.details?.biomarker_count}
                                  </div>
                                  {step.details?.biomarkers?.length > 0 && (
                                    <div style={styles.tableScroll}>
                                      <table style={styles.miniTable}>
                                        <thead>
                                          <tr>
                                            <th>Test Name</th>
                                            <th>Value</th>
                                            <th>Ref Range</th>
                                            <th>Flag</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {step.details?.biomarkers.map((b: any, idx: number) => (
                                            <tr key={idx}>
                                              <td>{b.test_name}</td>
                                              <td>{b.value} {b.unit}</td>
                                              <td>{b.reference_text || `${b.reference_min || ''} - ${b.reference_max || ''}`}</td>
                                              <td>
                                                <span
                                                  style={{
                                                    ...styles.flagTag,
                                                    ...(b.flag === 'HIGH' ? styles.flagHigh : b.flag === 'LOW' ? styles.flagLow : {}),
                                                  }}
                                                >
                                                  {b.flag}
                                                </span>
                                              </td>
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* Step 4: Clinical Flagging */}
                              {step.step_name === 'CLINICAL_FLAGGING' && (
                                <div>
                                  <div style={styles.badgeSummaryRow}>
                                    <span style={styles.summaryBadge}>Total: {step.details?.total_evaluated}</span>
                                    <span style={{ ...styles.summaryBadge, color: '#f87171' }}>
                                      High: {step.details?.high_count}
                                    </span>
                                    <span style={{ ...styles.summaryBadge, color: '#60a5fa' }}>
                                      Low: {step.details?.low_count}
                                    </span>
                                    <span style={{ ...styles.summaryBadge, color: '#4ade80' }}>
                                      Normal: {step.details?.normal_count}
                                    </span>
                                  </div>
                                </div>
                              )}

                              {/* Step 5: Canonical Feature Mapping */}
                              {step.step_name === 'CANONICAL_FEATURE_MAPPING' && (
                                <div>
                                  <div style={{ marginBottom: 10, fontSize: '0.8125rem', color: '#94a3b8' }}>
                                    Evaluated 20 canonical biomarkers for the neural network. Mapped from report:{' '}
                                    <strong style={{ color: '#38bdf8' }}>{step.details?.mapped_from_report_count}</strong> &middot; Defaulted normal midpoint:{' '}
                                    <strong style={{ color: '#94a3b8' }}>{step.details?.defaulted_midpoint_count}</strong> &middot; Unmapped:{' '}
                                    <strong style={{ color: '#f87171' }}>{step.details?.unmapped_count}</strong>
                                  </div>

                                  <div style={styles.tableScroll}>
                                    <table style={styles.miniTable}>
                                      <thead>
                                        <tr>
                                          <th>Canonical Feature</th>
                                          <th>Source Test</th>
                                          <th>Value</th>
                                          <th>Flag</th>
                                          <th>Mapping Status</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {step.details?.mapping_table?.map((m: any, idx: number) => (
                                          <tr key={idx}>
                                            <td><code>{m.canonical_feature}</code></td>
                                            <td>{m.source_name || '—'}</td>
                                            <td>{m.value}</td>
                                            <td>{m.flag}</td>
                                            <td>
                                              <span
                                                style={{
                                                  ...styles.mappingTag,
                                                  ...(m.status === 'MAPPED_FROM_REPORT'
                                                    ? styles.mappingMapped
                                                    : styles.mappingDefaulted),
                                                }}
                                              >
                                                {m.status}
                                              </span>
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}

                              {/* Step 6: Symptom Encoding */}
                              {step.step_name === 'SYMPTOM_ENCODING' && (
                                <div>
                                  <div style={{ marginBottom: 8 }}>
                                    <strong>Full Input Text:</strong>
                                    <div style={styles.codeSnippet}>{step.details?.full_text_input}</div>
                                  </div>
                                  <div style={{ marginBottom: 6 }}>
                                    <strong>Matched TF-IDF Vocabulary Tokens ({step.details?.matched_term_count}):</strong>
                                  </div>
                                  <div style={styles.tokenPillContainer}>
                                    {step.details?.matched_tfidf_terms?.length > 0 ? (
                                      step.details?.matched_tfidf_terms.map((t: string, idx: number) => (
                                        <span key={idx} style={styles.tokenPill}>
                                          {t}
                                        </span>
                                      ))
                                    ) : (
                                      <span style={{ color: '#64748b', fontSize: '0.8125rem' }}>
                                        No vocabulary words matched from text corpus.
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* Step 7: Final Feature Vector */}
                              {step.step_name === 'FINAL_FEATURE_VECTOR' && (
                                <div>
                                  <div style={styles.featureDimsRow}>
                                    <span style={styles.dimChip}>Total Features: {step.details?.total_feature_count}</span>
                                    <span style={styles.dimChip}>TF-IDF Text: {step.details?.text_features_dim}</span>
                                    <span style={styles.dimChip}>Dense Biomarkers & Meta: {step.details?.dense_features_dim}</span>
                                  </div>

                                  <div style={styles.tableScroll}>
                                    <table style={styles.miniTable}>
                                      <thead>
                                        <tr>
                                          <th>Biomarker Feature</th>
                                          <th>Raw Value</th>
                                          <th>Flag Enc</th>
                                          <th>Scaled Value (Z-Score)</th>
                                          <th>Scaled Flag</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {step.details?.dense_features_breakdown?.map((d: any, idx: number) => (
                                          <tr key={idx}>
                                            <td><code>{d.feature}</code></td>
                                            <td>{d.raw_value}</td>
                                            <td>{d.raw_flag_encoded}</td>
                                            <td style={{ color: Math.abs(d.scaled_value) > 2 ? '#f59e0b' : '#94a3b8' }}>
                                              {d.scaled_value}
                                            </td>
                                            <td>{d.scaled_flag}</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}

                              {/* Step 8: Model Inference */}
                              {step.step_name === 'MODEL_INFERENCE' && (
                                <div style={styles.detailGrid}>
                                  <div><strong>Model:</strong> {step.details?.model_name}</div>
                                  <div><strong>Version:</strong> {step.details?.model_version}</div>
                                  <div><strong>Inference Hardware:</strong> {step.details?.device}</div>
                                  <div><strong>Execution Latency:</strong> {step.details?.inference_duration_ms} ms</div>
                                </div>
                              )}

                              {/* Step 9: Model Output */}
                              {step.step_name === 'MODEL_OUTPUT' && (
                                <div>
                                  <div style={{ marginBottom: 10 }}>
                                    <strong>Predicted Class:</strong>{' '}
                                    <span style={{ color: '#38bdf8', fontWeight: 600 }}>
                                      {step.details?.top_prediction}
                                    </span>{' '}
                                    ({step.details?.confidence_percentage})
                                  </div>

                                  <div style={styles.probBarsContainer}>
                                    {step.details?.all_specialty_probabilities?.map((p: any, idx: number) => {
                                      const isWinner = p.specialty === step.details?.top_prediction;
                                      const percent = (p.probability * 100).toFixed(1);
                                      return (
                                        <div key={idx} style={styles.probRow}>
                                          <div style={styles.probLabel}>
                                            <span style={{ color: isWinner ? '#38bdf8' : '#cbd5e1', fontWeight: isWinner ? 600 : 400 }}>
                                              {p.specialty}
                                            </span>
                                            <span style={styles.probValue}>{percent}%</span>
                                          </div>
                                          <div style={styles.probBarTrack}>
                                            <div
                                              style={{
                                                ...styles.probBarFill,
                                                width: `${percent}%`,
                                                backgroundColor: isWinner ? '#0284c7' : '#334155',
                                              }}
                                            />
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              {/* Step 10: Final Decision */}
                              {step.step_name === 'FINAL_DECISION' && (
                                <div>
                                  <div style={styles.detailGrid}>
                                    <div><strong>Decision Pipeline:</strong> {step.details?.decision_status}</div>
                                    <div><strong>Final Specialist:</strong> {step.details?.final_specialty}</div>
                                    <div><strong>Emergency Intercept:</strong> {step.details?.is_emergency_flagged ? 'YES (OVERRIDE)' : 'NO'}</div>
                                    <div><strong>Fallback Rule Used:</strong> {step.details?.fallback_used ? 'YES' : 'NO'}</div>
                                  </div>
                                  {step.details?.emergency_message && (
                                    <div style={styles.alertBanner}>
                                      <AlertTriangle size={15} style={{ marginRight: 6 }} />
                                      {step.details?.emergency_message}
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* Step 11: API Response */}
                              {step.step_name === 'API_RESPONSE' && (
                                <div>
                                  <div style={{ marginBottom: 6 }}>
                                    <strong>HTTP Status:</strong> {step.details?.http_status}
                                  </div>
                                  <div style={styles.codeSnippet}>
                                    {JSON.stringify(step.details?.response_body, null, 2)}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Diagnostic Simulation Modal */}
      {showSimModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>AI Pipeline Diagnostic Simulator</h2>
              <button onClick={() => setShowSimModal(false)} style={styles.closeBtn}>
                &times;
              </button>
            </div>

            <p style={styles.modalSubtitle}>
              Run isolated tests through the production PyTorch inference engine and generate detailed technical traces without touching patient records.
            </p>

            {/* Diagnostic Presets for Report #2 */}
            <div style={styles.presetSection}>
              <span style={styles.presetTitle}>REPORT #2 INVESTIGATION PRESETS:</span>
              <div style={styles.presetButtons}>
                <button onClick={() => applyPreset('A')} style={styles.presetBtn}>
                  <strong>Test A:</strong> Fatigue + Dizziness + Headache
                </button>
                <button onClick={() => applyPreset('B')} style={styles.presetBtn}>
                  <strong>Test B:</strong> Neck Swelling + Fatigue
                </button>
                <button onClick={() => applyPreset('C')} style={styles.presetBtn}>
                  <strong>Test C:</strong> Routine Follow-up / No Symptoms
                </button>
              </div>
            </div>

            {/* Simulation Form Inputs */}
            <div style={styles.formGroup}>
              <label style={styles.label}>Primary Patient Concern:</label>
              <input
                type="text"
                value={simConcern}
                onChange={(e) => setSimConcern(e.target.value)}
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Reported Symptoms (comma separated):</label>
              <input
                type="text"
                value={simSymptoms}
                onChange={(e) => setSimSymptoms(e.target.value)}
                style={styles.input}
              />
            </div>

            <div style={styles.formRow}>
              <div style={{ flex: 1, marginRight: 10 }}>
                <label style={styles.label}>Severity Score (1-10):</label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={simSeverity}
                  onChange={(e) => setSimSeverity(Number(e.target.value))}
                  style={styles.input}
                />
              </div>
              <div style={{ flex: 1, marginRight: 10 }}>
                <label style={styles.label}>Duration (days):</label>
                <input
                  type="number"
                  min={1}
                  value={simDuration}
                  onChange={(e) => setSimDuration(Number(e.target.value))}
                  style={styles.input}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>Body Region:</label>
                <input
                  type="text"
                  value={simBodyRegion}
                  onChange={(e) => setSimBodyRegion(e.target.value)}
                  style={styles.input}
                />
              </div>
            </div>

            {/* Attached Biomarkers Preview */}
            <div style={{ marginTop: 14 }}>
              <div style={styles.label}>Attached Biomarkers (Report #2 — 11 Anomaly Tests):</div>
              <div style={styles.simBiomarkerPills}>
                {REPORT_2_BIOMARKERS.map((b, idx) => (
                  <span key={idx} style={styles.biomarkerPill}>
                    {b.test_name}: <strong>{b.value_numeric}</strong> ({b.flag})
                  </span>
                ))}
              </div>
            </div>

            <div style={styles.modalFooter}>
              <button onClick={() => setShowSimModal(false)} style={styles.cancelBtn}>
                Cancel
              </button>
              <button
                onClick={handleRunSimulation}
                disabled={simLoading}
                style={styles.runSimBtn}
              >
                {simLoading ? 'Executing Inference...' : 'Run Simulation & Generate Trace'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Inline CSS in JS Styles
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    padding: '24px',
    backgroundColor: '#0f172a',
    color: '#f8fafc',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid #1e293b',
    paddingBottom: '18px',
  },
  titleSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  badgeRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  superAdminBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    color: '#fbbf24',
    border: '1px solid rgba(245, 158, 11, 0.35)',
    fontSize: '0.6875rem',
    fontWeight: 700,
    padding: '2px 8px',
    borderRadius: '4px',
    letterSpacing: '0.05em',
  },
  liveIndicator: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '0.6875rem',
    fontWeight: 700,
    color: '#94a3b8',
    letterSpacing: '0.05em',
  },
  pulsingDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    marginRight: '6px',
  },
  pageTitle: {
    fontSize: '1.625rem',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  pageSubtitle: {
    fontSize: '0.875rem',
    color: '#94a3b8',
    margin: 0,
    maxWidth: '750px',
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  toggleStreamBtn: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    border: '1px solid',
    borderRadius: '6px',
    padding: '8px 14px',
    fontSize: '0.8125rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  simulateBtn: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#0284c7',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    padding: '8px 16px',
    fontSize: '0.8125rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  refreshBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1e293b',
    color: '#94a3b8',
    border: '1px solid #334155',
    borderRadius: '6px',
    padding: '8px 10px',
    cursor: 'pointer',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '14px',
  },
  statCard: {
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '8px',
    padding: '14px 16px',
  },
  statLabel: {
    fontSize: '0.75rem',
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    fontWeight: 600,
  },
  statValue: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: '#f8fafc',
    marginTop: '4px',
  },
  statSub: {
    fontSize: '0.75rem',
    color: '#64748b',
    marginTop: '4px',
  },
  filterBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '8px',
    padding: '10px 14px',
  },
  searchBox: {
    display: 'flex',
    alignItems: 'center',
    flex: 1,
    maxWidth: '400px',
  },
  searchInput: {
    backgroundColor: 'transparent',
    border: 'none',
    color: '#f8fafc',
    fontSize: '0.875rem',
    outline: 'none',
    width: '100%',
  },
  filterPills: {
    display: 'flex',
    gap: '8px',
  },
  filterPill: {
    backgroundColor: 'transparent',
    border: '1px solid #334155',
    color: '#94a3b8',
    borderRadius: '20px',
    padding: '4px 12px',
    fontSize: '0.75rem',
    cursor: 'pointer',
  },
  activeFilterPill: {
    backgroundColor: 'rgba(14, 165, 233, 0.15)',
    border: '1px solid #0ea5e9',
    color: '#38bdf8',
    borderRadius: '20px',
    padding: '4px 12px',
    fontSize: '0.75rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  specialtyDropdown: {
    display: 'flex',
    alignItems: 'center',
  },
  selectInput: {
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    color: '#f8fafc',
    borderRadius: '6px',
    padding: '4px 10px',
    fontSize: '0.8125rem',
    outline: 'none',
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '360px 1fr',
    gap: '20px',
    minHeight: '600px',
  },
  leftPane: {
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '8px',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  paneHeader: {
    padding: '12px 16px',
    borderBottom: '1px solid #334155',
    backgroundColor: '#0f172a',
  },
  paneTitle: {
    fontSize: '0.75rem',
    fontWeight: 700,
    color: '#94a3b8',
    letterSpacing: '0.05em',
  },
  traceList: {
    overflowY: 'auto',
    maxHeight: '750px',
    display: 'flex',
    flexDirection: 'column',
  },
  traceCard: {
    padding: '12px 14px',
    borderBottom: '1px solid #334155',
    cursor: 'pointer',
    transition: 'background-color 0.15s',
  },
  traceCardSelected: {
    backgroundColor: 'rgba(14, 165, 233, 0.12)',
    borderLeft: '4px solid #0ea5e9',
  },
  cardTopRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '6px',
  },
  traceIdBadge: {
    fontFamily: 'monospace',
    fontSize: '0.8125rem',
    fontWeight: 600,
    color: '#38bdf8',
  },
  statusBadge: {
    fontSize: '0.6875rem',
    fontWeight: 700,
    padding: '2px 6px',
    borderRadius: '4px',
  },
  statusSuccess: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    color: '#34d399',
    border: '1px solid rgba(16, 185, 129, 0.3)',
  },
  statusWarning: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    color: '#fbbf24',
    border: '1px solid rgba(245, 158, 11, 0.3)',
  },
  statusFailed: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    color: '#f87171',
    border: '1px solid rgba(239, 68, 68, 0.3)',
  },
  cardConcern: {
    fontSize: '0.8125rem',
    color: '#cbd5e1',
    marginBottom: '8px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  cardBottomRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  specialtyChip: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    backgroundColor: '#0f172a',
    padding: '2px 8px',
    borderRadius: '4px',
  },
  specialtyName: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#e2e8f0',
  },
  confPercent: {
    fontSize: '0.6875rem',
    color: '#38bdf8',
    fontWeight: 600,
  },
  durationChip: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '0.6875rem',
    color: '#94a3b8',
  },
  rightPane: {
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '8px',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  detailContainer: {
    padding: '20px',
    overflowY: 'auto',
    maxHeight: '800px',
  },
  detailHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid #334155',
    paddingBottom: '16px',
    marginBottom: '16px',
  },
  detailHeaderLeft: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  traceTitleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  detailTraceId: {
    fontFamily: 'monospace',
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#38bdf8',
  },
  copyBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    cursor: 'pointer',
    padding: '4px',
  },
  metaRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '0.75rem',
    color: '#94a3b8',
  },
  detailHeaderRight: {
    display: 'flex',
    alignItems: 'center',
  },
  viewJsonBtn: {
    display: 'flex',
    alignItems: 'center',
    border: '1px solid #475569',
    color: '#cbd5e1',
    borderRadius: '6px',
    padding: '6px 12px',
    fontSize: '0.75rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  modelMetaCard: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '12px',
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    borderRadius: '6px',
    padding: '12px 16px',
    marginBottom: '20px',
  },
  metaBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: '3px',
  },
  metaKey: {
    fontSize: '0.6875rem',
    color: '#94a3b8',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  metaVal: {
    fontSize: '0.875rem',
    color: '#f8fafc',
    fontWeight: 500,
  },
  timelineContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  timelineHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '0.75rem',
    fontWeight: 700,
    color: '#94a3b8',
    letterSpacing: '0.05em',
  },
  stepCountBadge: {
    backgroundColor: '#334155',
    color: '#38bdf8',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '0.6875rem',
  },
  stepsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  stepCard: {
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    borderRadius: '6px',
    overflow: 'hidden',
  },
  stepHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 14px',
    cursor: 'pointer',
    backgroundColor: 'rgba(30, 41, 59, 0.4)',
  },
  stepHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  stepNumPill: {
    backgroundColor: '#334155',
    color: '#f8fafc',
    width: '22px',
    height: '22px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.6875rem',
    fontWeight: 700,
  },
  stepName: {
    fontSize: '0.8125rem',
    fontWeight: 600,
    color: '#f8fafc',
  },
  stepStatusBadge: {
    fontSize: '0.625rem',
    fontWeight: 700,
    padding: '1px 6px',
    borderRadius: '3px',
  },
  stepStatusSuccess: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    color: '#34d399',
  },
  stepStatusWarning: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    color: '#fbbf24',
  },
  stepStatusFailed: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    color: '#f87171',
  },
  stepHeaderRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    color: '#94a3b8',
  },
  stepDuration: {
    fontSize: '0.75rem',
    color: '#94a3b8',
  },
  stepBody: {
    padding: '14px',
    borderTop: '1px solid #1e293b',
    fontSize: '0.8125rem',
    color: '#cbd5e1',
  },
  detailGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '10px',
  },
  detailRow: {
    marginBottom: '8px',
  },
  codeSnippet: {
    backgroundColor: '#020617',
    border: '1px solid #1e293b',
    padding: '8px 12px',
    borderRadius: '4px',
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#38bdf8',
    overflowX: 'auto',
    marginTop: '4px',
  },
  tableScroll: {
    overflowX: 'auto',
    marginTop: '8px',
  },
  miniTable: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.75rem',
    textAlign: 'left',
  },
  flagTag: {
    padding: '1px 5px',
    borderRadius: '3px',
    fontSize: '0.6875rem',
    fontWeight: 600,
  },
  flagHigh: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    color: '#f87171',
  },
  flagLow: {
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: '#60a5fa',
  },
  mappingTag: {
    padding: '2px 6px',
    borderRadius: '3px',
    fontSize: '0.6875rem',
    fontWeight: 600,
  },
  mappingMapped: {
    backgroundColor: 'rgba(14, 165, 233, 0.2)',
    color: '#38bdf8',
  },
  mappingDefaulted: {
    backgroundColor: 'rgba(100, 116, 139, 0.2)',
    color: '#94a3b8',
  },
  badgeSummaryRow: {
    display: 'flex',
    gap: '12px',
  },
  summaryBadge: {
    backgroundColor: '#1e293b',
    padding: '4px 10px',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: 600,
  },
  tokenPillContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  tokenPill: {
    backgroundColor: '#1e293b',
    color: '#38bdf8',
    border: '1px solid #334155',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '0.6875rem',
    fontFamily: 'monospace',
  },
  featureDimsRow: {
    display: 'flex',
    gap: '10px',
    marginBottom: '10px',
  },
  dimChip: {
    backgroundColor: '#1e293b',
    color: '#38bdf8',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: 600,
  },
  probBarsContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  probRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  probLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.75rem',
  },
  probValue: {
    fontFamily: 'monospace',
    fontWeight: 600,
  },
  probBarTrack: {
    width: '100%',
    height: '6px',
    backgroundColor: '#1e293b',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  probBarFill: {
    height: '100%',
    borderRadius: '3px',
    transition: 'width 0.3s ease',
  },
  alertBanner: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    border: '1px solid rgba(245, 158, 11, 0.3)',
    color: '#fbbf24',
    padding: '8px 12px',
    borderRadius: '4px',
    marginTop: '10px',
    fontSize: '0.75rem',
  },
  rawJsonBox: {
    backgroundColor: '#020617',
    border: '1px solid #334155',
    borderRadius: '6px',
    padding: '16px',
    overflowX: 'auto',
  },
  preformatted: {
    margin: 0,
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#38bdf8',
  },
  emptyState: {
    padding: '40px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '0.875rem',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
  },
  modalContent: {
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '8px',
    width: '90%',
    maxWidth: '680px',
    maxHeight: '90vh',
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#f8fafc',
    margin: 0,
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    fontSize: '1.5rem',
    cursor: 'pointer',
  },
  modalSubtitle: {
    fontSize: '0.8125rem',
    color: '#94a3b8',
    margin: 0,
  },
  presetSection: {
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    borderRadius: '6px',
    padding: '12px',
  },
  presetTitle: {
    fontSize: '0.6875rem',
    fontWeight: 700,
    color: '#38bdf8',
    letterSpacing: '0.05em',
    marginBottom: '8px',
    display: 'block',
  },
  presetButtons: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  presetBtn: {
    backgroundColor: '#1e293b',
    border: '1px solid #334155',
    color: '#cbd5e1',
    borderRadius: '4px',
    padding: '8px 12px',
    fontSize: '0.75rem',
    textAlign: 'left',
    cursor: 'pointer',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  formRow: {
    display: 'flex',
  },
  label: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#cbd5e1',
  },
  input: {
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    borderRadius: '4px',
    color: '#f8fafc',
    padding: '8px 10px',
    fontSize: '0.8125rem',
    outline: 'none',
  },
  simBiomarkerPills: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    marginTop: '6px',
  },
  biomarkerPill: {
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    color: '#94a3b8',
    padding: '3px 8px',
    borderRadius: '4px',
    fontSize: '0.6875rem',
  },
  modalFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
    marginTop: '16px',
  },
  cancelBtn: {
    backgroundColor: 'transparent',
    border: '1px solid #475569',
    color: '#cbd5e1',
    borderRadius: '4px',
    padding: '8px 14px',
    fontSize: '0.8125rem',
    cursor: 'pointer',
  },
  runSimBtn: {
    backgroundColor: '#0284c7',
    border: 'none',
    color: '#ffffff',
    borderRadius: '4px',
    padding: '8px 16px',
    fontSize: '0.8125rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
};
