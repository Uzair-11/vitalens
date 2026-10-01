# VitaLens Payments & Notifications: Regulatory & Technical Compliance Reference

> [!CAUTION]
> **CRITICAL COMPLIANCE & LEGAL DISCLAIMER**:
> The payment provider (`RazorpaySandboxProvider`) implemented in this phase is a **fully local, self-contained protocol simulation (mock)**. It **does NOT make external network calls to `api.razorpay.com`** or use live Razorpay sandbox credentials. Payments introduce serious legal and regulatory obligations under Indian law and international payment security frameworks. **No real money should be moved and no production credentials should be configured until an independent legal, banking, and compliance review is conducted.**

---

## 1. Regulatory Surface & Compliance Frameworks

### 1.1 Reserve Bank of India (RBI) Payment Aggregator (PA) Guidelines
Under the RBI Framework for Regulation of Payment Aggregators and Payment Gateways:
- **Merchant Onboarding & KYC**: Platform entities facilitating doctor-patient transactions must complete merchant due diligence (PAN, GSTIN, medical council registrations).
- **Settlement & Escrow Mechanisms**: Consultation fees collected from patients cannot be comingled with operational platform funds; funds must flow through an RBI-authorized PA Escrow/Nodal account with defined settlement timeframes (T+1 or T+2 to doctors).
- **Customer Grievance Redressal**: Mandatory 2-tier dispute and refund resolution protocol for failed consultations or cancellations.
- **Data Storage Restrictions**: No customer card data (PAN, CVV, PIN) or net banking credentials may be stored on VitaLens servers.

### 1.2 PCI-DSS (Payment Card Industry Data Security Standard) Scope
- **Out of Scope Strategy (SAQ-A)**: VitaLens delegates all direct cardholder data entry to Razorpay's PCI-DSS Level 1 compliant hosted checkout SDKs. VitaLens backend servers handle only tokenized identifiers (`order_id`, `payment_id`, HMAC signatures), keeping the core application in the minimal SAQ-A compliance scope.
- **Server-Side Signature Verification**: Client-reported payment success is never trusted. All state transitions to `PAID` require cryptographic HMAC-SHA256 verification using the gateway's private secret.

### 1.3 Digital Personal Data Protection Act (DPDP 2023) Alignment
- **Separation of Concerns**: Clinical health records (`medical_reports`, `biomarkers`) are logically separated from financial transaction logs (`appointments.payment_id`, `audit_logs`).
- **Consent-Gated Communications**: Financial transaction receipts and system notifications are filtered through the user's `NOTIFICATIONS` consent record. Revoking notification consent suppresses marketing/informative messages while retaining essential transactional security audit logs.

---

## 2. Technical Architecture & State Machines

### 2.1 Feature Flag Governance (`PAYMENTS_ENABLED`)
- When `PAYMENTS_ENABLED=false` (default dev/test): Appointment booking completes directly with `status="CONFIRMED"` and `payment_status="PAID"`.
- When `PAYMENTS_ENABLED=true`: Appointment booking creates the appointment in `status="PENDING_PAYMENT"` and `payment_status="PENDING"`. The appointment is not confirmed until server-side signature verification succeeds.

### 2.2 Payment State Machine
```
[Slot Selected]
       │
       ▼
[Appointment Created: PENDING_PAYMENT]
       │
       ├─► POST /appointments/{id}/payment/initiate ──► [Local Order Created (order_xxx)]
       │                                                         │
       │                                                         ▼
       │                                                [User Pays in Checkout]
       │                                                         │
       ├─► POST /appointments/{id}/payment/verify                │
       │        ├── Invalid / Tampered Signature ────────► [payment_status: FAILED]
       │        └── Valid HMAC-SHA256 Signature  ────────► [payment_status: PAID, status: CONFIRMED]
       │                                                                 │
       │                                                                 ▼
       │                                                    [Trigger Confirmed Notification]
       │
       └── Timeout / Cancelled (>15 min uncompleted) ────► [Slot Released, status: CANCELLED]
```

### 2.3 Slot Locking & Expiry Policy
- When an appointment is created in `PENDING_PAYMENT`, the doctor's calendar slot is soft-locked to prevent double-booking.
- If payment is not completed within **15 minutes**, or if payment fails, the slot is automatically released back to doctor availability upon cancellation or lazy evaluation.

---

## 3. Local Mock vs. Real Razorpay Sandbox Disclosure

### 3.1 What is Implemented (`RazorpaySandboxProvider`)
- **Self-Contained Local Simulation**: Generates formatted `order_<uuid>` IDs in-memory and executes HMAC-SHA256 signature verification matching Razorpay's cryptographic verification specification: `hmac.new(secret, f"{order_id}|{payment_id}", sha256)`.
- **Zero External Network Dependencies**: Does not issue outbound HTTP requests to `https://api.razorpay.com`. This allows complete deterministic offline testing of the appointment state machine and payment verification gating.

### 3.2 What is Required for Real Sandbox / Production Connection
1. **Outbound API Integration**: Replace/extend `create_order` to invoke `POST https://api.razorpay.com/v1/orders` with HTTP Basic Auth (`RAZORPAY_KEY_ID:RAZORPAY_KEY_SECRET`).
2. **Real Razorpay Test API Keys**: Register on the Razorpay Dashboard to obtain `rzp_test_...` key and secret.
3. **Webhook Handler**: Register `POST /api/v1/payments/webhook` with Razorpay Webhook signature verification (`X-Razorpay-Signature`) to handle asynchronous payment captures and refunds.

---

## 4. Notification Engine Architecture

### 4.1 Interface & Multi-Provider Design (`app/core/notifications.py`)
- `NotificationService`: Core dispatcher responsible for consent checking, template rendering, and log persistence.
- `SandboxNotificationProvider`: Default local provider writing structured JSON logs with zero third-party dependencies.
- `ExpoPushNotificationProvider`: Documented & stubbed push notification adapter ready for Expo push tokens.

### 4.2 Queryable Audit Trail (`notification_logs`)
Every notification attempt creates a queryable database record:
- `user_id`: Target recipient user FK.
- `event_type`: `APPOINTMENT_CONFIRMED`, `APPOINTMENT_CANCELLED`, `REPORT_ANALYSIS_COMPLETE`.
- `status`: `SENT`, `FAILED`, or `SKIPPED_NO_CONSENT`.
- `created_at`: UTC timestamp.

---

## 5. Operational Status & Verification Matrix

| Component | Operational Status | Verification Method | Notes / Gap Disclosure |
|---|---|---|---|
| **Razorpay Order Creation Flow** | Local Simulation | Automated test suite (`test_phase7_payment_initiation_and_valid_signature_verification`) | **Self-contained mock** generating `order_<uuid>`. No external network calls to `api.razorpay.com`. |
| **HMAC-SHA256 Signature Verification** | Locally Verified | Cryptographic comparison against tampered signatures (`test_phase7_tampered_signature_rejection`) | Uses constant-time `hmac.compare_digest` with local secret. Follows Razorpay specification. |
| **Payment-Gated Appointment Booking** | Locally Verified | Env-flag test suite (`test_phase7_appointment_booking_payment_gating`) | Verified with `PAYMENTS_ENABLED=true`. |
| **Consent-Gated Notifications** | Locally Verified | Consent toggle test suite (`test_phase7_notification_consent_gating`) | Gated on `NOTIFICATIONS` DPDP consent record. |
| **Queryable Notification Logs** | Locally Verified | Database assertion on `notification_logs` table | Indexed by `user_id`, `event_type`, and `status`. |
| **Real Razorpay API Connection** | Documented Gap | Not Exercised | Requires live/test credentials from Razorpay dashboard and outbound HTTP calls to `api.razorpay.com`. |
| **Production Settlement & Escrow** | Documented Gap | Regulatory review required | Requires RBI-compliant merchant aggregator agreement, GST invoicing integration, and escrow bank linkage. |
| **Expo Mobile Push Delivery** | Documented Gap | Stubbed in `ExpoPushNotificationProvider` | Requires Expo Application Project ID and APNs/FCM credentials. |
