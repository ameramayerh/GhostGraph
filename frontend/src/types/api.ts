export interface Engagement {
  id: number;
  name: string;
  scope: string;
  authorized_by: string;
  status: string;
  total_findings: number;
  filtered_findings: number;
}

export interface Finding {
  id: number;
  title: string;
  description: string;
  file_path: string;
  line_number: number;
  code_snippet: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low' | 'Unknown';
  category: string;
  is_false_positive: boolean;
  filtering_status: 'Pending' | 'In Progress' | 'Reviewed' | 'Not Run' | 'Error';
  ai_explanation?: string | null;
  business_impact?: string | null;
  remediation?: string | null;
  code_patch?: string | null;
  confidence_level?: string | null;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  action: string;
  user: string;
  details: string;
}

export interface EngagementDetails {
  engagement?: Engagement;
  findings: Finding[];
  audit_logs: AuditLog[];
}

export interface SeverityMetric {
  name: string;
  value: number;
  color: string;
}

export interface CategoryMetric {
  name: string;
  count: number;
}

export interface AnalyticsData {
  totalAssets: number;
  activeEngagements: number;
  criticalRisks: number;
  severityData: SeverityMetric[];
  categoryData: CategoryMetric[];
}

export interface ThreatIntelRecord {
  id: string;
  source: string;
  type: string;
  description: string;
}
