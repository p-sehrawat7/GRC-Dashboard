"""
database/seed.py
----------------
Seeds the GRC database with realistic enterprise data.
Reads existing CSVs as a base, then expands to 40+ rows per table.
Also creates default users with hashed passwords.

Run:
    cd d:/grc-dashboard
    .venv/Scripts/python database/seed.py
"""

import os
import sys
import bcrypt
from datetime import datetime, timedelta

# Allow import of database package from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import engine, init_db, SessionLocal
from database.models import Risk, Control, AuditFinding, User, AuditLog

# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def _dt(days_offset: int) -> datetime:
    return datetime.utcnow() + timedelta(days=days_offset)

# ── Risk data (40 rows) ───────────────────────────────────────────────────────

RISKS = [
    ("R-01","Unauthorized access to customer financial data due to lack of MFA on admin accounts","Customer Financial Data","External Attacker","No MFA on admin access",5,4,20,"Critical","In Progress","A.9.4","Protect"),
    ("R-02","Delayed incident response due to absence of formal IR plan","Operations","Security Incident","No incident response procedure",4,3,12,"High","Mitigated","A.5.25","Respond"),
    ("R-03","Data leakage due to excessive employee access permissions","Customer PII","Insider Misuse","No periodic access review",4,3,12,"High","In Progress","A.9.1","Protect"),
    ("R-04","Regulatory non-compliance due to undocumented security policies","Compliance Data","Audit Failure","Lack of formal policies",3,3,9,"Medium","Accepted","A.5.1","Identify"),
    ("R-05","Ransomware attack encrypting critical business data via phishing email","Business Data","Ransomware","No email filtering or endpoint protection",5,4,20,"Critical","In Progress","A.8.7","Protect"),
    ("R-06","Supply chain compromise through unvetted third-party vendor access","Cloud Infrastructure","Supply Chain Attack","No vendor risk assessment process",4,4,16,"Critical","In Progress","A.5.22","Identify"),
    ("R-07","DDoS attack disrupting customer-facing web applications","Web Application","External Attacker","No DDoS mitigation controls",4,3,12,"High","Accepted","A.8.20","Protect"),
    ("R-08","Insider threat exfiltrating intellectual property via removable media","IP & Source Code","Malicious Insider","No DLP or USB policy enforcement",5,2,10,"High","In Progress","A.8.11","Protect"),
    ("R-09","Unpatched vulnerabilities in legacy systems exploited remotely","Legacy Systems","External Attacker","No patch management program",4,4,16,"Critical","In Progress","A.8.8","Protect"),
    ("R-10","Weak password policy enabling brute-force attacks on employee accounts","Employee Accounts","External Attacker","No password complexity enforcement",3,4,12,"High","In Progress","A.9.4","Protect"),
    ("R-11","Data breach due to unencrypted backup storage exposed on cloud","Backup Data","External Attacker","Backups stored without encryption",5,3,15,"Critical","Mitigated","A.8.13","Protect"),
    ("R-12","Lack of business continuity plan causing prolonged downtime post-incident","Business Operations","Any Major Incident","No BCP or DR plan",4,2,8,"Medium","Accepted","A.5.29","Recover"),
    ("R-13","Unauthorized physical access to server room by non-IT staff","Data Center","Physical Intrusion","No physical access controls",4,2,8,"Medium","Mitigated","A.7.1","Protect"),
    ("R-14","Loss of sensitive data due to lack of data classification policy","All Data Assets","Accidental Disclosure","No formal data classification framework",3,3,9,"Medium","Accepted","A.5.12","Identify"),
    ("R-15","Failure to detect malicious activity lacking SIEM or log monitoring","Network Infrastructure","Advanced Persistent Threat","No centralized log management",4,4,16,"Critical","In Progress","A.8.15","Detect"),
    ("R-16","Exposure of API keys in public code repositories","Source Code","External Attacker","Secrets committed to version control",5,3,15,"Critical","In Progress","A.8.9","Protect"),
    ("R-17","Uncontrolled use of personal devices accessing corporate systems","Corporate Network","Insider / External","No BYOD policy or MDM solution",3,4,12,"High","In Progress","A.6.7","Protect"),
    ("R-18","SQL injection vulnerability in customer-facing web application","Web Application","External Attacker","Insufficient input validation",5,3,15,"Critical","In Progress","A.8.28","Protect"),
    ("R-19","Misconfigured cloud storage buckets exposing sensitive files publicly","Cloud Storage","External Attacker","Public read permissions on S3 buckets",5,4,20,"Critical","In Progress","A.8.9","Protect"),
    ("R-20","Lack of multi-factor authentication on email accounts","Email System","Phishing / Account Takeover","No MFA on Microsoft 365 / Google Workspace",4,4,16,"Critical","In Progress","A.8.5","Protect"),
    ("R-21","Third-party software with known CVEs running in production","Application Stack","External Attacker","No SCA or dependency scanning",4,3,12,"High","In Progress","A.8.8","Protect"),
    ("R-22","Uncontrolled privileged remote access via RDP","IT Infrastructure","External Attacker","RDP exposed on public IP without VPN",5,4,20,"Critical","In Progress","A.8.20","Protect"),
    ("R-23","Employees sharing passwords for shared service accounts","Shared Accounts","Insider Misuse","No individual accountability on shared accounts",3,3,9,"Medium","Accepted","A.9.2","Protect"),
    ("R-24","Loss of mobile devices containing unencrypted corporate data","Mobile Devices","Lost / Stolen Device","No full-disk encryption on company mobiles",4,3,12,"High","In Progress","A.6.7","Protect"),
    ("R-25","Social engineering attack targeting finance team","Finance Team","Fraudster","No verification procedure for wire transfers",5,3,15,"Critical","In Progress","A.6.3","Protect"),
    ("R-26","DNS hijacking redirecting users to malicious sites","DNS Infrastructure","External Attacker","No DNSSEC implementation",4,2,8,"Medium","Accepted","A.8.20","Protect"),
    ("R-27","Cleartext transmission of sensitive data over HTTP","Web Services","Man-in-the-Middle","TLS not enforced on all endpoints",4,3,12,"High","In Progress","A.8.24","Protect"),
    ("R-28","Insufficient network segmentation allowing lateral movement","Network","External Attacker","Flat network architecture without VLANs",4,3,12,"High","In Progress","A.8.20","Protect"),
    ("R-29","Outdated firewall rules allowing unauthorised inbound traffic","Firewall","External Attacker","Firewall rule review not performed in 2 years",3,3,9,"Medium","In Progress","A.8.20","Protect"),
    ("R-30","Lack of security testing for new software releases","SDLC","External Attacker","No SAST / DAST in CI/CD pipeline",4,3,12,"High","In Progress","A.8.29","Identify"),
    ("R-31","Inadequate logging retention allowing loss of forensic evidence","Log Storage","Any Attacker","Logs purged after 7 days",3,2,6,"Low","Accepted","A.8.15","Detect"),
    ("R-32","Failure to revoke ex-employee system access promptly","IAM","Malicious Former Employee","No automated offboarding process",4,3,12,"High","In Progress","A.5.18","Protect"),
    ("R-33","Insecure API endpoints exposing internal data","API Gateway","External Attacker","No API authentication or rate limiting",5,3,15,"Critical","In Progress","A.8.24","Protect"),
    ("R-34","Lack of encryption for sensitive data in databases","Database","External Attacker","No encryption-at-rest on production DBs",5,3,15,"Critical","In Progress","A.8.24","Protect"),
    ("R-35","Compliance breach due to missing GDPR data subject request process","Customer Data","Regulator / Data Subject","No formal DSAR procedure",3,3,9,"Medium","Accepted","A.5.34","Identify"),
    ("R-36","Denial of service on internal HR portal due to lack of rate limiting","HR Systems","External Attacker","No rate limiting on authentication endpoints",3,2,6,"Low","Accepted","A.8.20","Protect"),
    ("R-37","Outdated anti-malware signatures on workstations","Workstations","Malware","AV signature updates delayed by >7 days",3,4,12,"High","In Progress","A.8.7","Protect"),
    ("R-38","Unmanaged IoT devices connected to corporate Wi-Fi","IoT / OT Network","External Attacker","No IoT network segmentation policy",4,3,12,"High","In Progress","A.8.20","Detect"),
    ("R-39","Lack of formal change management process causing outages","IT Operations","Misconfiguration","Unapproved changes deployed to production",3,3,9,"Medium","Accepted","A.8.32","Identify"),
    ("R-40","Failure to conduct annual security risk assessment","Risk Management","Governance Failure","No documented risk assessment methodology",3,2,6,"Low","Accepted","A.5.8","Identify"),
]

# ── Control data (40 rows) ────────────────────────────────────────────────────

CONTROLS = [
    ("C-01","Privileged Access Management","Privileged accounts controlled and reviewed quarterly","R-01","Preventive","Partial","Needs Improvement","Admin access list exists","MFA not enforced on all admin accounts","High","A.9.4","Protect"),
    ("C-02","Access Control Policy","Access restricted based on business need-to-know","R-03","Preventive","Partial","Needs Improvement","Role-based access defined","Access reviews not conducted periodically","High","A.9.1","Protect"),
    ("C-03","Incident Response Plan","Formal IR procedures established and tested annually","R-02","Corrective","Implemented","Effective","IR plan document v2.1","Tabletop exercise completed Q4 2024","Medium","A.5.25","Respond"),
    ("C-04","Information Security Policy","Policies approved by management and communicated","R-04","Preventive","Partial","Needs Improvement","Draft policy available","Policies not formally approved or communicated","Medium","A.5.1","Identify"),
    ("C-05","Logging and Monitoring (SIEM)","Event logs recorded and centrally monitored via SIEM","R-15","Detective","Missing","Ineffective","None","No centralized monitoring or SIEM alerting","High","A.8.15","Detect"),
    ("C-06","Security Awareness Training","All employees receive annual security awareness training","R-03","Preventive","Missing","Ineffective","None","No formal security training program in place","High","A.6.3","Protect"),
    ("C-07","Email Filtering and Anti-Phishing","Advanced email filtering to block phishing","R-05","Preventive","Partial","Needs Improvement","Basic spam filter active","No sandboxing or advanced threat protection","High","A.8.7","Protect"),
    ("C-08","Endpoint Detection and Response (EDR)","EDR solution deployed on all endpoints","R-05","Detective","Missing","Ineffective","None","No EDR solution deployed on endpoints","Critical","A.8.7","Detect"),
    ("C-09","Vendor Risk Management","Third-party vendors assessed before onboarding","R-06","Preventive","Missing","Ineffective","None","No formal vendor assessment questionnaire used","Critical","A.5.22","Identify"),
    ("C-10","DDoS Mitigation","Cloud-based DDoS protection for web applications","R-07","Preventive","Implemented","Effective","Cloudflare Pro configured","DDoS WAF rules active and tuned","Medium","A.8.20","Protect"),
    ("C-11","Data Loss Prevention (DLP)","DLP tools to prevent unauthorized data exfiltration","R-08","Preventive","Missing","Ineffective","None","No DLP policy or technology deployed","High","A.8.11","Protect"),
    ("C-12","Patch Management Program","Monthly vulnerability scanning and patching","R-09","Preventive","Partial","Needs Improvement","Quarterly patching for critical systems","Legacy systems on extended support without patches","High","A.8.8","Protect"),
    ("C-13","Password Policy Enforcement","Enforce minimum 12-character passwords with MFA","R-10","Preventive","Partial","Needs Improvement","Password policy document exists","Not enforced technically via AD Group Policy","Medium","A.9.4","Protect"),
    ("C-14","Encrypted Backup and Recovery","All backups encrypted at rest and recovery tested","R-11","Recovery","Implemented","Effective","AES-256 encryption on cloud backups","Backup restoration tested Q3 2024","Low","A.8.13","Recover"),
    ("C-15","Business Continuity Plan (BCP)","BCP and DR plan covering recovery within RTO/RPO targets","R-12","Recovery","Partial","Needs Improvement","BCP draft v1.0","BCP not tested or formally approved","Medium","A.5.29","Recover"),
    ("C-16","Secrets Management","API keys stored in vault, not in source control","R-16","Preventive","Missing","Ineffective","None","No secrets management tool deployed","Critical","A.8.9","Protect"),
    ("C-17","Mobile Device Management (MDM)","Corporate MDM policy enforcing encryption on all mobile devices","R-17","Preventive","Partial","Needs Improvement","Partial MDM rollout","Personal devices not enrolled in MDM","High","A.6.7","Protect"),
    ("C-18","Web Application Firewall (WAF)","WAF deployed in front of customer-facing web application","R-18","Preventive","Implemented","Effective","Cloudflare WAF enabled","WAF rules reviewed quarterly","Low","A.8.28","Protect"),
    ("C-19","Cloud Security Posture Management (CSPM)","Automated scanning for cloud misconfiguration","R-19","Detective","Missing","Ineffective","None","No CSPM tool in use","Critical","A.8.9","Detect"),
    ("C-20","MFA for Email and SaaS Applications","MFA enforced on all corporate email and SaaS platforms","R-20","Preventive","Partial","Needs Improvement","MFA enabled for admins only","Standard users excluded from MFA policy","High","A.8.5","Protect"),
    ("C-21","Software Composition Analysis (SCA)","Automated dependency scanning in CI/CD pipeline","R-21","Detective","Missing","Ineffective","None","No SCA tooling configured","High","A.8.8","Identify"),
    ("C-22","VPN and Remote Access Control","All remote access routed through corporate VPN with MFA","R-22","Preventive","Partial","Needs Improvement","VPN deployed for IT admins","Business users connect directly without VPN","High","A.8.20","Protect"),
    ("C-23","Service Account Management","Individual service accounts with least-privilege permissions","R-23","Preventive","Implemented","Effective","Service account inventory maintained","Password sharing eliminated for critical services","Low","A.9.2","Protect"),
    ("C-24","Full Disk Encryption on Endpoints","BitLocker / FileVault enforced on all company devices","R-24","Preventive","Partial","Needs Improvement","Encryption applied to developer laptops","Finance and HR laptops not encrypted","High","A.6.7","Protect"),
    ("C-25","Business Email Compromise Controls","Transaction verification procedure for high-value transfers","R-25","Preventive","Missing","Ineffective","None","No callback verification process defined","Critical","A.6.3","Protect"),
    ("C-26","DNSSEC Implementation","DNSSEC enabled on all corporate-owned domains","R-26","Preventive","Implemented","Effective","DNSSEC configured for primary domain","Secondary domains pending migration","Low","A.8.20","Protect"),
    ("C-27","TLS Enforcement","HTTPS enforced across all web services and APIs","R-27","Preventive","Partial","Needs Improvement","TLS 1.3 on public endpoints","Internal services still using HTTP","High","A.8.24","Protect"),
    ("C-28","Network Segmentation","VLAN segmentation separating production from corporate network","R-28","Preventive","Missing","Ineffective","None","Flat network; no VLAN implementation","Critical","A.8.20","Protect"),
    ("C-29","Firewall Rule Review","Quarterly review and cleanup of firewall rules","R-29","Preventive","Partial","Needs Improvement","Last review 18 months ago","Stale permit rules not removed","Medium","A.8.20","Protect"),
    ("C-30","Secure SDLC (SAST/DAST)","Static and dynamic application security testing in pipeline","R-30","Detective","Missing","Ineffective","None","No security gates in CI/CD","High","A.8.29","Identify"),
    ("C-31","Log Retention Policy","Security logs retained for minimum 12 months","R-31","Detective","Partial","Needs Improvement","7-day retention configured","Retention policy not aligned with compliance requirements","Medium","A.8.15","Detect"),
    ("C-32","Automated Offboarding Process","Automated revocation of access on HR system termination event","R-32","Preventive","Missing","Ineffective","None","Manual offboarding; average delay of 3 days","High","A.5.18","Protect"),
    ("C-33","API Security Gateway","API gateway enforcing authentication, rate limiting, and logging","R-33","Preventive","Partial","Needs Improvement","API gateway deployed","Rate limiting and auth not configured on all routes","High","A.8.24","Protect"),
    ("C-34","Database Encryption at Rest","Transparent data encryption on all production databases","R-34","Preventive","Missing","Ineffective","None","Production databases not encrypted at rest","Critical","A.8.24","Protect"),
    ("C-35","GDPR DSAR Process","Documented and tested data subject access request procedure","R-35","Preventive","Partial","Needs Improvement","Draft DSAR template exists","No formal owner or SLA defined","Medium","A.5.34","Identify"),
    ("C-36","Authentication Rate Limiting","Lockout and rate limiting on all authentication endpoints","R-36","Preventive","Implemented","Effective","Account lockout after 5 failed attempts","Rate limiting active on all auth endpoints","Low","A.8.20","Protect"),
    ("C-37","Anti-Malware Management","Automated AV signature updates pushed to all workstations","R-37","Preventive","Partial","Needs Improvement","AV deployed on 90% of workstations","Signature update frequency not enforced","High","A.8.7","Protect"),
    ("C-38","IoT Network Isolation","Separate Wi-Fi SSID and VLAN for IoT devices","R-38","Preventive","Missing","Ineffective","None","IoT devices on production Wi-Fi network","High","A.8.20","Detect"),
    ("C-39","Change Management Process","Formal CAB approval required for all production changes","R-39","Preventive","Partial","Needs Improvement","CAB process documented","Bypass of CAB process observed in 30% of changes","Medium","A.8.32","Identify"),
    ("C-40","Annual Risk Assessment","Documented enterprise risk assessment conducted annually","R-40","Preventive","Partial","Needs Improvement","Risk register maintained","Assessment methodology not formally approved","Low","A.5.8","Identify"),
]

# ── Findings data (40 rows) ───────────────────────────────────────────────────

FINDINGS = [
    ("F-01","R-01","C-01","MFA Not Enforced on Admin Accounts","Critical","Open",-45,"IT Security Team","Multi-factor authentication not enabled on 8 of 12 privileged admin accounts."),
    ("F-02","R-05","C-08","No EDR Solution Deployed","Critical","Open",-30,"IT Operations","EDR solution not deployed. Ransomware activity would go undetected on endpoints."),
    ("F-03","R-06","C-09","Vendor Risk Assessments Not Performed","Critical","Open",5,"Procurement","Third-party vendors granted network access without security questionnaire."),
    ("F-04","R-15","C-05","No SIEM or Centralized Log Monitoring","Critical","In Remediation",25,"SOC Team","No centralized SIEM. Security events from firewalls and servers not correlated."),
    ("F-05","R-09","C-12","Legacy Systems Unpatched Beyond 90 Days","High","Open",-55,"IT Operations","17 legacy servers running Windows Server 2012 with no patches applied in 90+ days."),
    ("F-06","R-03","C-06","Security Awareness Training Not Conducted","High","Open",-15,"HR & Security","Annual security awareness training not completed. Only 23% of employees have completed."),
    ("F-07","R-08","C-11","No DLP Controls for Data Exfiltration","High","Open",10,"Data Governance","USB ports unrestricted and no DLP email monitoring."),
    ("F-08","R-10","C-13","Password Policy Not Technically Enforced","High","In Remediation",-10,"IT Security Team","Password complexity rules exist in policy but Group Policy not configured to enforce."),
    ("F-09","R-02","C-03","Incident Response Tabletop Exercise Overdue","Medium","Closed",-70,"CISO Office","Annual IR tabletop exercise not conducted. Now closed after Q4 exercise completion."),
    ("F-10","R-04","C-04","Security Policy Not Formally Approved","Medium","Open",45,"Compliance","Draft security policy not approved by Board. Non-compliant with ISO 27001 A.5.1."),
    ("F-11","R-12","C-15","BCP Not Tested or Approved","Medium","Open",55,"Business Continuity","BCP in draft form. No formal DR test conducted. RTO and RPO targets unvalidated."),
    ("F-12","R-07","C-10","DDoS Protection Configuration Review Required","Medium","Closed",-85,"Network Team","DDoS protection rules review completed and updated. Cloudflare WAF configured."),
    ("F-13","R-03","C-02","Access Reviews Not Conducted in 12 Months","High","Open",-20,"IAM Team","Periodic access reviews for privileged and standard user accounts not performed."),
    ("F-14","R-11","C-14","Backup Restoration Test Due","Low","Closed",-95,"IT Operations","Quarterly backup restoration test completed successfully. AES-256 encryption verified."),
    ("F-15","R-14","C-04","Data Classification Policy Missing","Medium","Open",70,"Data Governance","No formal data classification scheme defined. Required for GDPR and ISO 27001."),
    ("F-16","R-16","C-16","API Keys Found in Public GitHub Repository","Critical","Open",-60,"CISO Office","Production AWS access keys committed to a public GitHub repository and exposed."),
    ("F-17","R-17","C-17","Personal Devices Accessing Corporate Email Without MDM","High","Open",20,"IT Operations","100+ personal devices accessing corporate data without MDM enrollment."),
    ("F-18","R-18","C-18","SQL Injection in Customer Portal Identified by Pentest","Critical","In Remediation",15,"Application Security","Penetration test identified SQL injection in /api/search endpoint."),
    ("F-19","R-19","C-19","Public S3 Bucket Exposing Customer Invoices","Critical","Open",-25,"Cloud Team","S3 bucket with customer invoice data configured with public-read ACL."),
    ("F-20","R-20","C-20","MFA Not Enforced on Standard User Email Accounts","High","Open",-5,"IT Security Team","MFA enforced for only 40 of 320 active email accounts."),
    ("F-21","R-21","C-21","Open-Source Libraries with Critical CVEs in Production","High","Open",-15,"DevOps","Three open-source libraries with CVSS 9.0+ in production application bundle."),
    ("F-22","R-22","C-22","RDP Exposed on Public IP Without VPN","Critical","Open",-40,"IT Operations","TCP/3389 open on datacenter firewall accessible from the public internet."),
    ("F-23","R-24","C-24","Finance Laptops Without Full Disk Encryption","High","Open",30,"IT Security Team","12 finance team laptops confirmed without BitLocker enabled."),
    ("F-24","R-25","C-25","No Callback Verification for High-Value Wire Transfers","Critical","Open",20,"Finance","No secondary verification process for wire transfers above £10,000."),
    ("F-25","R-27","C-27","Internal APIs Transmitting Data Over HTTP","High","In Remediation",25,"AppSec","Three internal microservice APIs communicating over unencrypted HTTP."),
    ("F-26","R-28","C-28","Flat Network Architecture Allowing Lateral Movement","Critical","Open",60,"Network Team","No network segmentation between production, staging, and corporate VLANs."),
    ("F-27","R-29","C-29","Firewall Rules Not Reviewed for 18 Months","Medium","Open",30,"Network Team","Firewall rule set contains 47 stale permit rules from decommissioned systems."),
    ("F-28","R-30","C-30","No Security Testing in CI/CD Pipeline","High","Open",40,"DevOps","No SAST, DAST, or SCA tooling integrated into continuous integration pipeline."),
    ("F-29","R-32","C-32","Stale User Accounts for 14 Ex-Employees","High","Open",-10,"IAM Team","14 accounts for employees terminated more than 30 days ago remain active."),
    ("F-30","R-33","C-33","Unauthenticated Internal API Routes Accessible","High","In Remediation",35,"AppSec","Internal reporting API routes accessible without authentication or IP whitelisting."),
    ("F-31","R-34","C-34","Production Databases Not Encrypted at Rest","Critical","Open",50,"DBA Team","MySQL production cluster running without transparent data encryption enabled."),
    ("F-32","R-35","C-35","No Formal GDPR DSAR Process Defined","Medium","Open",80,"Compliance","Data subject access requests handled ad hoc with no SLA or documented procedure."),
    ("F-33","R-37","C-37","AV Signatures Not Updated on 15% of Workstations","High","Open",-8,"IT Operations","34 workstations running antivirus definitions older than 30 days."),
    ("F-34","R-38","C-38","IoT Devices on Production Network","High","Open",45,"Network Team","Smart TVs and printer fleet connected to production VLAN with domain controllers."),
    ("F-35","R-39","C-39","CAB Bypass Observed in Production Deployments","Medium","Open",35,"IT Operations","Change log shows 6 production deployments in January without CAB approval."),
    ("F-36","R-02","C-03","Playbook for Ransomware Response Missing","High","Open",25,"CISO Office","IR plan lacks specific ransomware containment and recovery playbook."),
    ("F-37","R-05","C-07","Phishing Simulation Pass Rate Below Target","High","In Remediation",20,"Security Awareness","Latest phishing simulation: 34% click rate, target is below 5%."),
    ("F-38","R-04","C-04","Acceptable Use Policy Not Signed by Employees","Medium","Open",60,"HR & Security","Only 58% of employees have signed the Acceptable Use Policy in the last 12 months."),
    ("F-39","R-31","C-31","Log Retention Below Compliance Requirement","Medium","Open",40,"SOC Team","Current 7-day log retention does not meet PCI-DSS 12-month requirement."),
    ("F-40","R-40","C-40","Annual Risk Assessment Not Completed","Low","Open",90,"Risk Manager","Formal annual risk assessment not completed for current financial year."),
]

# ── Users ─────────────────────────────────────────────────────────────────────

USERS = [
    ("admin",   "admin123",  "admin"),
    ("auditor", "audit123",  "auditor"),
    ("viewer",  "view123",   "viewer"),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        # Skip if already seeded
        if db.query(Risk).count() > 0:
            print("Database already seeded — skipping.")
            return

        print("Seeding risks...")
        for row in RISKS:
            db.add(Risk(
                risk_id=row[0], risk_description=row[1], asset=row[2],
                threat=row[3], vulnerability=row[4], impact=row[5],
                likelihood=row[6], risk_score=row[7], risk_level=row[8],
                treatment_status=row[9], iso_clause=row[10], nist_function=row[11],
                created_by="system",
            ))
        db.flush()

        print("Seeding controls...")
        for row in CONTROLS:
            db.add(Control(
                control_id=row[0], control_name=row[1], control_description=row[2],
                mapped_risk_id=row[3], control_type=row[4], implementation_status=row[5],
                effectiveness=row[6], evidence=row[7], gap_description=row[8],
                risk_level_after_control=row[9], iso_clause=row[10], nist_function=row[11],
                created_by="system",
            ))
        db.flush()

        print("Seeding audit findings...")
        for row in FINDINGS:
            db.add(AuditFinding(
                finding_id=row[0], risk_id=row[1], control_id=row[2],
                title=row[3], severity=row[4], status=row[5],
                due_date=_dt(row[6]), owner=row[7], description=row[8],
                created_by="system",
            ))
        db.flush()

        print("Seeding users...")
        for uname, pw, role in USERS:
            db.add(User(
                username=uname,
                hashed_password=_hash(pw),
                role=role,
            ))

        db.commit()
        print(f"Seed complete: {len(RISKS)} risks, {len(CONTROLS)} controls, "
              f"{len(FINDINGS)} findings, {len(USERS)} users.")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
