import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl, apiService } from '../services/api';
import {
    mockPatients,
    mockHospitals,
    mockDevices,
    mockAccessList,
    seedAuditLogs,
    seedAlarms
} from '../data/mockData';

const RPMContext = createContext(null);

export const RPMProvider = ({ children }) => {
    const navigate = useNavigate();
    const { user, logout, authFetch } = useAuth();
    const { addToast } = useToast();

    const userRole = user?.role || 'patient';
    const userName = user?.name || 'Authorized User';

    // State Declarations
    const [patients, setPatients] = useState([]);
    const [alarms, setAlarms] = useState([]);
    const [auditLogs, setAuditLogs] = useState([]);
    const [devices, setDevices] = useState([]);
    const [adminStats, setAdminStats] = useState({
        totalPatients: 0,
        totalClinicians: 0,
        totalDevices: 0,
        criticalAlarms: 0
    });
    const [doctorsList, setDoctorsList] = useState([]);
    const [viewAllPatients, setViewAllPatients] = useState(false);

    // Admin-specific States
    const [adminUsers, setAdminUsers] = useState([]);
    const [connectionRequests, setConnectionRequests] = useState([]);
    const [doctorSearchQuery, setDoctorSearchQuery] = useState('');
    const [pendingDoctors, setPendingDoctors] = useState([]);
    const [selectedDoctorVerificationDetails, setSelectedDoctorVerificationDetails] = useState(null);
    const [isDoctorVerificationDetailsModalOpen, setIsDoctorVerificationDetailsModalOpen] = useState(false);
    const [isLoadingVerificationDetails, setIsLoadingVerificationDetails] = useState(false);
    const [isDoctorApprovalConfirmOpen, setIsDoctorApprovalConfirmOpen] = useState(false);
    const [isDoctorRejectionConfirmOpen, setIsDoctorRejectionConfirmOpen] = useState(false);
    const [adminDecisionNotes, setAdminDecisionNotes] = useState('');
    const [adminRejectionReason, setAdminRejectionReason] = useState('');
    const [adminDirectorySubTab, setAdminDirectorySubTab] = useState('doctors');

    // Prescription States
    const [prescriptions, setPrescriptions] = useState([]);
    const [isPrescriptionModalOpen, setIsPrescriptionModalOpen] = useState(false);
    const [rxMedicines, setRxMedicines] = useState('');
    const [rxDosage, setRxDosage] = useState('');
    const [rxFrequency, setRxFrequency] = useState('');
    const [rxDuration, setRxDuration] = useState('');
    const [rxInstructions, setRxInstructions] = useState('');
    const [rxDate, setRxDate] = useState(() => new Date().toISOString().split('T')[0]);

    // UI / Global states
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
    const [isNotificationOpen, setIsNotificationOpen] = useState(false);
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const deriveInitialPatientId = () => {
        if (user?.role === 'patient') {
            const devId = user.deviceId || '';
            return devId.replace(/^NP-/, 'P-');
        }
        if (user?.role === 'family') {
            return user.patientId || 'P-102';
        }
        return 'P-102';
    };

    const [selectedPatientId, setSelectedPatientId] = useState(deriveInitialPatientId());
    const [activeAlarmFilter, setActiveAlarmFilter] = useState('all');
    const [clinicalNoteInput, setClinicalNoteInput] = useState('');
    const [caregiverLinkInput, setCaregiverLinkInput] = useState('');
    const [familyLinkInput, setFamilyLinkInput] = useState('');
    const [patientNotesMap, setPatientNotesMap] = useState({});
    const [accessControls, setAccessControls] = useState([]);
    const [ehrSyncTime, setEhrSyncTime] = useState('Checking...');
    const [documentsList, setDocumentsList] = useState([]);
    const [docTitle, setDocTitle] = useState('');
    const [docCategory, setDocCategory] = useState('LAB_REPORT');
    const [docFile, setDocFile] = useState(null);
    const [isUploadingDoc, setIsUploadingDoc] = useState(false);
    const [patientHealthSummary, setPatientHealthSummary] = useState(null);
    const [selectedPendingSummary, setSelectedPendingSummary] = useState(null);

    // Database Notifications states
    const [dbNotifications, setDbNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);

    // Sync state initially
    useEffect(() => {
        setSelectedPatientId(deriveInitialPatientId());
    }, [user]);

    // Utility helpers
    const formatTimeAgo = (timestampStr) => {
        if (!timestampStr) return '';
        try {
            const diffMs = Date.now() - new Date(timestampStr).getTime();
            const diffMins = Math.floor(diffMs / 60000);
            if (diffMins < 1) return 'Just Now';
            if (diffMins < 60) return `${diffMins}m ago`;
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) return `${diffHours}h ago`;
            return new Date(timestampStr).toLocaleDateString();
        } catch {
            return '';
        }
    };

    const fetchNotifications = async () => {
        try {
            const res = await authFetch(getApiUrl('/notifications'));
            if (res.ok) {
                const notifData = await res.json();
                setDbNotifications(notifData);
                const unread = notifData.filter(n => !n.is_read).length;
                setUnreadCount(unread);
            }
        } catch (e) {
            console.error('Error fetching clinical registry notifications:', e);
        }
    };

    const handleMarkNotificationRead = async (notif) => {
        if (notif.is_read) return;
        try {
            const res = await authFetch(getApiUrl(`/notifications/${notif.id}/read`), {
                method: 'PUT'
            });
            if (res.ok) {
                setDbNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
                setUnreadCount(prev => Math.max(0, prev - 1));
            }
        } catch (e) {
            console.error('Failed to mark notification read:', e);
        }
    };

    const handleMarkAllNotificationsRead = async () => {
        try {
            const res = await authFetch(getApiUrl('/notifications/read-all'), {
                method: 'PUT'
            });
            if (res.ok) {
                setDbNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
                setUnreadCount(0);
                addToast('All notifications marked as read.', 'success');
            }
        } catch (e) {
            console.error('Failed to mark all notifications read:', e);
        }
    };

    const fetchSummary = async () => {
        try {
            const pidParam = selectedPatientId || (userRole === 'patient' ? deriveInitialPatientId() : '');
            if (!pidParam) return;
            const res = await authFetch(getApiUrl(`/patients/${pidParam}/summary`));
            if (res.ok) {
                const data = await res.json();
                setPatientHealthSummary(data);
            }
        } catch (e) {
            console.error('Error fetching patient summary:', e);
        }
    };

    // Profile and health data update/delete handlers
    const handleSaveProfile = async (formData) => {
        try {
            const pidParam = selectedPatientId || (userRole === 'patient' ? deriveInitialPatientId() : '');
            const res = await authFetch(getApiUrl(`/patients/${pidParam}/profile`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            if (res.ok) {
                addToast('Profile demographics updated successfully.', 'success');
                fetchSummary();
            }
        } catch (e) {
            console.error('Error saving profile:', e);
        }
    };

    const handleSaveCondition = async (conditionVal) => {
        try {
            const pidParam = selectedPatientId || (userRole === 'patient' ? deriveInitialPatientId() : '');
            const res = await authFetch(getApiUrl('/health-records'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patientId: pidParam, type: 'condition', value: conditionVal })
            });
            if (res.ok) {
                addToast('Condition recorded successfully.', 'success');
                fetchSummary();
            }
        } catch (e) {
            console.error('Error saving condition:', e);
        }
    };

    const handleDeleteCondition = async (id) => {
        try {
            const res = await authFetch(getApiUrl(`/health-records/condition/${id}`), {
                method: 'DELETE'
            });
            if (res.ok) {
                addToast('Condition deleted.', 'info');
                fetchSummary();
            }
        } catch (e) {
            console.error('Error deleting condition:', e);
        }
    };

    const handleSaveAllergy = async (allergyVal) => {
        try {
            const pidParam = selectedPatientId || (userRole === 'patient' ? deriveInitialPatientId() : '');
            const res = await authFetch(getApiUrl('/health-records'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patientId: pidParam, type: 'allergy', value: allergyVal })
            });
            if (res.ok) {
                addToast('Allergy recorded successfully.', 'success');
                fetchSummary();
            }
        } catch (e) {
            console.error('Error saving allergy:', e);
        }
    };

    const handleDeleteAllergy = async (id) => {
        try {
            const res = await authFetch(getApiUrl(`/health-records/allergy/${id}`), {
                method: 'DELETE'
            });
            if (res.ok) {
                addToast('Allergy deleted.', 'info');
                fetchSummary();
            }
        } catch (e) {
            console.error('Error deleting allergy:', e);
        }
    };

    const handleSaveManualVital = async (vitalName, vitalValue) => {
        try {
            const pidParam = selectedPatientId || (userRole === 'patient' ? deriveInitialPatientId() : '');
            const res = await authFetch(getApiUrl('/health-records'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patientId: pidParam, type: 'vital', value: `${vitalName}: ${vitalValue}` })
            });
            if (res.ok) {
                addToast('Manual vital measurement saved.', 'success');
                fetchSummary();
            }
        } catch (e) {
            console.error('Error saving vital:', e);
        }
    };

    const handleDeleteManualVital = async (id) => {
        try {
            const res = await authFetch(getApiUrl(`/health-records/vital/${id}`), {
                method: 'DELETE'
            });
            if (res.ok) {
                addToast('Manual vital deleted.', 'info');
                fetchSummary();
            }
        } catch (e) {
            console.error('Error deleting vital:', e);
        }
    };

    // Main POLLED fetch loop
    const fetchData = async () => {
        if (!user) return;
        try {
            // 1. Fetch active monitoring patients
            let patientsUrl = getApiUrl('/patients');
            if (userRole === 'doctor' && user.npi && !viewAllPatients) {
                patientsUrl += `?doctorNpi=${user.npi}`;
            }
            const resPatients = await authFetch(patientsUrl);
            if (resPatients.ok) {
                const data = await resPatients.json();
                setPatients(data);
            }

            // 2. Fetch recent alerts logs
            const resAlarms = await authFetch(getApiUrl('/alarms'));
            if (resAlarms.ok) {
                const alarmsData = await resAlarms.json();
                setAlarms(alarmsData);
            }

            // 3. Fetch security audit logs
            const resLogs = await authFetch(getApiUrl('/audit-logs'));
            if (resLogs.ok) {
                const logsData = await resLogs.json();
                setAuditLogs(logsData);
            }

            // 4. Fetch admin diagnostics inventory details
            if (userRole === 'admin') {
                const resStats = await authFetch(getApiUrl('/admin/stats'));
                if (resStats.ok) {
                    const statsData = await resStats.json();
                    setAdminStats(statsData);
                }

                const resDevs = await authFetch(getApiUrl('/devices'));
                if (resDevs.ok) {
                    const devsData = await resDevs.json();
                    setDevices(devsData);
                }

                const resUsers = await authFetch(getApiUrl('/admin/users'));
                if (resUsers.ok) {
                    const usersData = await resUsers.json();
                    setAdminUsers(usersData);
                }

                const resPending = await authFetch(getApiUrl('/admin/pending-doctors'));
                if (resPending.ok) {
                    const pendingData = await resPending.json();
                    setPendingDoctors(pendingData);
                }
            }

            // 5. Fetch verified doctors list
            if (userRole === 'patient' || userRole === 'family' || userRole === 'caregiver' || userRole === 'doctor') {
                const resDocs = await authFetch(getApiUrl('/doctors'));
                if (resDocs.ok) {
                    const docsData = await resDocs.json();
                    setDoctorsList(docsData);
                }

                const resControls = await authFetch(getApiUrl('/patients/access-controls'));
                if (resControls.ok) {
                    const controlsData = await resControls.json();
                    setAccessControls(controlsData);
                }
            }

            // 6. Fetch pending correlation requests
            if (userRole === 'doctor' || userRole === 'patient' || userRole === 'family') {
                const resReqs = await authFetch(getApiUrl('/connections/requests'));
                if (resReqs.ok) {
                    const reqsData = await resReqs.json();
                    setConnectionRequests(reqsData);
                }
            }

            // 7. Get documents & prescriptions list
            const pidParam = selectedPatientId || (userRole === 'patient' ? deriveInitialPatientId() : '');
            if (pidParam || userRole === 'patient') {
                const resDocs = await authFetch(getApiUrl(`/documents?patientId=${pidParam || ''}`));
                if (resDocs.ok) {
                    const docsData = await resDocs.json();
                    setDocumentsList(docsData);
                }

                const resRx = await authFetch(getApiUrl(`/prescriptions?patientId=${pidParam || ''}`));
                if (resRx.ok) {
                    const rxData = await resRx.json();
                    setPrescriptions(rxData);
                }
            }

            // 8. Notifications
            fetchNotifications();
        } catch (e) {
            console.error('Error fetching clinical registry database:', e);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 4000);
        return () => clearInterval(interval);
    }, [userRole, user?.token, user?.npi, viewAllPatients, selectedPatientId]);

    const addAuditLog = async (action, target) => {
        try {
            await authFetch(getApiUrl('/audit-logs'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: userName, action, target })
            });
            const resLogs = await authFetch(getApiUrl('/audit-logs'));
            if (resLogs.ok) {
                const logsData = await resLogs.json();
                setAuditLogs(logsData);
            }
        } catch (error) {
            console.error('Failed to commit compliance audit log:', error);
        }
    };

    const handleLogout = () => {
        addAuditLog('User Session Terminated', 'Security Auth Portal');
        logout();
        addToast('Logged out successfully.', 'info');
        navigate('/login');
    };

    // Telemetry simulation triggers
    const triggerTelemetrySimulation = async (vitalsPatch, riskScore, statusState, auditAction) => {
        const selectedPatientObj = patients.find(p => String(p.id) === String(selectedPatientId)) || patients[0];
        if (!selectedPatientObj) return;
        const baseVitals = selectedPatientObj.vitals;
        const payload = {
            patientId: selectedPatientId,
            riskScore,
            statusState,
            auditAction,
            userName,
            vitals: {
                max30102: {
                    heartRate: vitalsPatch.heartRate !== undefined ? vitalsPatch.heartRate : baseVitals.max30102.heartRate,
                    spo2: vitalsPatch.spo2 !== undefined ? vitalsPatch.spo2 : baseVitals.max30102.spo2
                },
                ds18b20: {
                    temperature: vitalsPatch.temperature !== undefined ? vitalsPatch.temperature : baseVitals.ds18b20.temperature
                },
                mpu6050: {
                    accelX: vitalsPatch.accelX !== undefined ? vitalsPatch.accelX : baseVitals.mpu6050.accelX,
                    accelY: vitalsPatch.accelY !== undefined ? vitalsPatch.accelY : baseVitals.mpu6050.accelY,
                    accelZ: vitalsPatch.accelZ !== undefined ? vitalsPatch.accelZ : baseVitals.mpu6050.accelZ,
                    gyroX: vitalsPatch.gyroX !== undefined ? vitalsPatch.gyroX : baseVitals.mpu6050.gyroX,
                    gyroY: vitalsPatch.gyroY !== undefined ? vitalsPatch.gyroY : baseVitals.mpu6050.gyroY,
                    gyroZ: vitalsPatch.gyroZ !== undefined ? vitalsPatch.gyroZ : baseVitals.mpu6050.gyroZ,
                    fallDetected: vitalsPatch.fallDetected !== undefined ? vitalsPatch.fallDetected : baseVitals.mpu6050.fallDetected
                },
                esp32: {
                    connected: vitalsPatch.esp32Connected !== undefined ? vitalsPatch.esp32Connected : baseVitals.esp32.connected,
                    battery: vitalsPatch.esp32Battery !== undefined ? vitalsPatch.esp32Battery : baseVitals.esp32.battery,
                    rssi: vitalsPatch.esp32Rssi !== undefined ? vitalsPatch.esp32Rssi : baseVitals.esp32.rssi
                }
            }
        };

        try {
            const res = await authFetch(getApiUrl('/simulation/trigger'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                let patientsUrl = getApiUrl('/patients');
                if (userRole === 'doctor' && user.npi && !viewAllPatients) {
                    patientsUrl += `?doctorNpi=${user.npi}`;
                }
                const resPatients = await authFetch(patientsUrl);
                if (resPatients.ok) {
                    const data = await resPatients.json();
                    setPatients(data);
                }
            }
        } catch (error) {
            console.error('Failed to trigger telemetry simulation:', error);
        }
    };

    const simulateNormal = () => {
        triggerTelemetrySimulation(
            { heartRate: 72, spo2: 98, temperature: 36.8, fallDetected: false, esp32Connected: true },
            10,
            'Normal',
            'Clinical telemetry normalized'
        );
        addToast('Patient telemetry normalized.', 'success');
    };

    const simulateFall = () => {
        triggerTelemetrySimulation(
            { heartRate: 110, fallDetected: true },
            95,
            'Emergency',
            'MPU6050 Fall Vector Alert Triggered'
        );
        const selectedPatientObj = patients.find(p => String(p.id) === String(selectedPatientId)) || patients[0];
        const pName = selectedPatientObj ? selectedPatientObj.name : selectedPatientId;
        const newAlarm = {
            id: Date.now(),
            type: 'critical',
            desc: `MPU6050: Accel vector spike detected. Fall event registered for ${pName}.`,
            time: 'Just Now',
            patient: pName,
            isCritical: true
        };
        setAlarms(prev => [newAlarm, ...prev]);
        addToast(`EMERGENCY: Fall detected for ${pName}!`, 'error');
    };

    const simulateHypoxia = () => {
        triggerTelemetrySimulation(
            { spo2: 84 },
            80,
            'Critical',
            'MAX30102 Low SpO2 Alarm Triggered'
        );
        const selectedPatientObj = patients.find(p => String(p.id) === String(selectedPatientId)) || patients[0];
        const pName = selectedPatientObj ? selectedPatientObj.name : selectedPatientId;
        const newAlarm = {
            id: Date.now(),
            type: 'critical',
            desc: `MAX30102: SpO2 oxygen saturation dropped to 84% for ${pName}.`,
            time: 'Just Now',
            patient: pName,
            isCritical: true
        };
        setAlarms(prev => [newAlarm, ...prev]);
        addToast(`WARNING: Low oxygen saturation for ${pName}!`, 'error');
    };

    const simulateFever = () => {
        triggerTelemetrySimulation(
            { temperature: 39.1 },
            50,
            'Warning',
            'DS18B20 High Temperature Logged'
        );
        const selectedPatientObj = patients.find(p => String(p.id) === String(selectedPatientId)) || patients[0];
        const pName = selectedPatientObj ? selectedPatientObj.name : selectedPatientId;
        const newAlarm = {
            id: Date.now(),
            type: 'warning',
            desc: `DS18B20: Elevated body temperature (39.1°C) registered for ${pName}.`,
            time: 'Just Now',
            patient: pName,
            isCritical: false
        };
        setAlarms(prev => [newAlarm, ...prev]);
        addToast(`Warning: High temperature for ${pName}.`, 'warning');
    };

    const simulateESP32Disconnect = () => {
        const selectedPatientObj = patients.find(p => String(p.id) === String(selectedPatientId)) || patients[0];
        if (!selectedPatientObj) return;
        triggerTelemetrySimulation(
            { esp32Connected: false },
            selectedPatientObj.risk,
            selectedPatientObj.status,
            'ESP32 Node Disconnect Flagged'
        );
        const pName = selectedPatientObj.name;
        const newAlarm = {
            id: Date.now(),
            type: 'warning',
            desc: `ESP32: Wireless connection lost for ${pName}'s NeuroPatch wearable.`,
            time: 'Just Now',
            patient: pName,
            isCritical: false
        };
        setAlarms(prev => [newAlarm, ...prev]);
        addToast(`Warning: ESP32 node disconnected for ${pName}!`, 'warning');
    };

    const saveClinicalNotes = async () => {
        try {
            const res = await authFetch(getApiUrl(`/patients/${selectedPatientId}/notes`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: clinicalNoteInput, clinicianName: userName })
            });
            if (res.ok) {
                setPatientNotesMap(prev => ({ ...prev, [selectedPatientId]: clinicalNoteInput }));
                addToast('Clinical notes updated.', 'success');
            } else {
                const errorMsg = await res.text();
                addToast(`Failed: ${errorMsg}`, 'error');
            }
        } catch (error) {
            console.error('Failed to sync EHR clinical notes:', error);
            addToast('Connection failed: EHR records not synced.', 'error');
        }
    };

    const handleUpdateDoctor = async (doctorNpi) => {
        try {
            const res = await authFetch(getApiUrl(`/patients/${selectedPatientId}/doctor`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doctorNpi, clinicianName: userName })
            });
            if (res.ok) {
                addToast(doctorNpi ? 'Consulting doctor associated!' : 'De-associated doctor.', 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
            addToast('Doctor association failed.', 'error');
        }
    };

    const handleSendConnectionRequest = async (doctorNpi) => {
        try {
            const res = await authFetch(getApiUrl('/connections/requests'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doctorNpi })
            });
            if (res.ok) {
                addToast('Connection request sent!', 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleCancelConnectionRequest = async (requestId) => {
        try {
            const res = await authFetch(getApiUrl(`/connections/requests/${requestId}`), {
                method: 'DELETE'
            });
            if (res.ok) {
                addToast('Connection request cancelled.', 'info');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleApproveConnection = async (requestId, patientName) => {
        try {
            const res = await authFetch(getApiUrl(`/connections/requests/${requestId}`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'Approved' })
            });
            if (res.ok) {
                addToast(`Approved connection request from ${patientName}.`, 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleDeclineConnection = async (requestId, patientName) => {
        try {
            const res = await authFetch(getApiUrl(`/connections/requests/${requestId}`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'Declined' })
            });
            if (res.ok) {
                addToast(`Declined connection request from ${patientName}.`, 'warning');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const syncExternalEhr = () => {
        setEhrSyncTime('Loading...');
        setTimeout(() => {
            setEhrSyncTime('Just Now');
            addToast('External Health Record Sync completed.', 'success');
            addAuditLog('Initiated External Health Record synchronization (Simulated)', 'EHR Sync Endpoint');
        }, 1000);
    };

    const handleSaveSettings = (e) => {
        if (e && e.preventDefault) e.preventDefault();
        addToast('Global clinical thresholds saved.', 'success');
        addAuditLog('Modified Global Compliance Thresholds', 'Platform Configurations');
    };

    const revokeAccess = async (userId, userNameStr, userRoleStr) => {
        try {
            const res = await authFetch(getApiUrl(`/admin/users/${userId}`), { method: 'DELETE' });
            if (res.ok) {
                addToast(`Successfully revoked access for ${userNameStr} [${userRoleStr.toUpperCase()}].`, 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const approveDoctor = async (doctorId, doctorName) => {
        try {
            const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/approve`), { method: 'PUT' });
            if (res.ok) {
                addToast(`Doctor ${doctorName} has been approved and verified!`, 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const rejectDoctor = async (doctorId, doctorName) => {
        try {
            const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/reject`), { method: 'PUT' });
            if (res.ok) {
                addToast(`Doctor registration for ${doctorName} rejected.`, 'warning');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const verifyAffiliation = async (doctorId, doctorName) => {
        try {
            const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/verify-affiliation`), { method: 'PUT' });
            if (res.ok) {
                addToast(`Hospital affiliation for Dr. ${doctorName} has been verified!`, 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const openDoctorVerificationDetails = async (doctorId) => {
        setIsLoadingVerificationDetails(true);
        setAdminDecisionNotes('');
        setAdminRejectionReason('');
        try {
            const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/details`));
            if (res.ok) {
                const data = await res.json();
                setSelectedDoctorVerificationDetails(data);
                setIsDoctorVerificationDetailsModalOpen(true);
            } else {
                addToast('Failed to load doctor verification details.', 'error');
            }
        } catch (err) {
            console.error('Error fetching doctor details:', err);
        } finally {
            setIsLoadingVerificationDetails(false);
        }
    };

    const handleConfirmApproveDoctor = async () => {
        if (!selectedDoctorVerificationDetails) return;
        const docId = selectedDoctorVerificationDetails.accountDetails.id;
        const docName = selectedDoctorVerificationDetails.accountDetails.fullName;
        if (selectedDoctorVerificationDetails.datasetVerificationDetails.result === 'STATUS_BLOCKED') {
            addToast('Approval Disabled: Doctor has an active disciplinary block record.', 'error');
            return;
        }
        try {
            const res = await authFetch(getApiUrl(`/admin/doctors/${docId}/approve`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: adminDecisionNotes })
            });
            if (res.ok) {
                addToast(`Doctor ${docName} has been approved and verified!`, 'success');
                setIsDoctorApprovalConfirmOpen(false);
                setIsDoctorVerificationDetailsModalOpen(false);
                fetchData();
            } else {
                const errText = await res.text();
                addToast(errText || 'Approval failed.', 'error');
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleConfirmRejectDoctor = async () => {
        if (!selectedDoctorVerificationDetails) return;
        const docId = selectedDoctorVerificationDetails.accountDetails.id;
        const docName = selectedDoctorVerificationDetails.accountDetails.fullName;
        if (!adminRejectionReason.trim()) {
            addToast('Please provide a reason for rejecting doctor registration.', 'warning');
            return;
        }
        try {
            const res = await authFetch(getApiUrl(`/admin/doctors/${docId}/reject`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: adminRejectionReason, notes: adminDecisionNotes })
            });
            if (res.ok) {
                addToast(`Doctor registration for ${docName} rejected.`, 'warning');
                setIsDoctorRejectionConfirmOpen(false);
                setIsDoctorVerificationDetailsModalOpen(false);
                fetchData();
            } else {
                const errText = await res.text();
                addToast(errText || 'Rejection failed.', 'error');
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleCreatePrescription = async (e) => {
        if (e && e.preventDefault) e.preventDefault();
        if (!rxMedicines.trim()) {
            addToast('Please specify medication details.', 'error');
            return;
        }
        const targetPid = selectedPatientId || (patients.length > 0 ? patients[0].id : '');
        if (!targetPid && userRole === 'doctor') {
            addToast('Please select a target patient first.', 'error');
            return;
        }
        try {
            const res = await authFetch(getApiUrl('/prescriptions'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patientId: targetPid,
                    medicines: rxMedicines,
                    dosage: rxDosage,
                    frequency: rxFrequency,
                    duration: rxDuration,
                    instructions: rxInstructions,
                    prescriptionDate: rxDate
                })
            });
            if (res.ok) {
                addToast('Prescription issued successfully and recorded.', 'success');
                setIsPrescriptionModalOpen(false);
                setRxMedicines('');
                setRxDosage('');
                setRxInstructions('');
                fetchData();
            } else {
                const errText = await res.text();
                addToast(errText.replace(/^"|"$/g, '') || 'Failed to issue prescription.', 'error');
            }
        } catch (err) {
            console.error(err);
        }
    };

    const suspendDoctor = async (doctorId, doctorName) => {
        try {
            const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/suspend`), { method: 'PUT' });
            if (res.ok) {
                addToast(`Doctor ${doctorName} has been suspended.`, 'warning');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const approveCaregiverLink = async (linkId, approved, caregiverName) => {
        try {
            let res;
            if (approved) {
                res = await authFetch(getApiUrl(`/caregivers/requests/${linkId}`), {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ approved: true, readOnly: true })
                });
            } else {
                res = await apiService.revokeCaregiverLink(authFetch, linkId);
            }
            if (res.ok) {
                addToast(`Caregiver connection ${approved ? 'approved' : 'revoked'} successfully!`, 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleSendCaregiverLinkRequest = async (e) => {
        if (e && e.preventDefault) e.preventDefault();
        if (!caregiverLinkInput.trim()) {
            addToast('Please enter a valid Access Code.', 'warning');
            return;
        }
        try {
            const res = await authFetch(getApiUrl('/caregivers/requests'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patientId: caregiverLinkInput.trim() })
            });
            if (res.ok) {
                addToast(`Caregiver linkage request dispatched!`, 'success');
                setCaregiverLinkInput('');
            } else {
                const errText = await res.text();
                addToast(errText || 'Failed to send Link Request.', 'error');
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleSendFamilyLinkRequest = async (e) => {
        if (e && e.preventDefault) e.preventDefault();
        if (!familyLinkInput.trim()) {
            addToast('Please enter a valid Patient ID.', 'warning');
            return;
        }
        try {
            const res = await authFetch(getApiUrl('/family/requests'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ patientId: familyLinkInput.trim() })
            });
            if (res.ok) {
                addToast(`Family link request sent!`, 'success');
                setFamilyLinkInput('');
            } else {
                const errText = await res.text();
                addToast(errText || 'Failed to send family link request.', 'error');
            }
        } catch (err) {
            console.error(err);
        }
    };

    const approveFamilyLink = async (linkId, approved, familyName) => {
        try {
            let res;
            if (approved) {
                res = await authFetch(getApiUrl(`/family/requests/${linkId}`), {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ approved: true })
                });
            } else {
                res = await apiService.revokeFamilyLink(authFetch, linkId);
            }
            if (res.ok) {
                addToast(`Family connection ${approved ? 'approved' : 'revoked'} successfully!`, 'success');
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleUploadDocument = async (e) => {
        if (e && e.preventDefault) e.preventDefault();
        if (!docFile) {
            addToast('Please select a file to upload.', 'warning');
            return;
        }
        if (!docTitle.trim()) {
            addToast('Please enter a document title.', 'warning');
            return;
        }
        try {
            setIsUploadingDoc(true);
            const targetPid = selectedPatientId || deriveInitialPatientId();
            const formData = new FormData();
            formData.append('title', docTitle.trim());
            formData.append('documentType', docCategory);
            formData.append('file', docFile);
            if (targetPid) {
                formData.append('patientId', targetPid);
            }
            const res = await authFetch(getApiUrl('/documents'), {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                addToast('Document uploaded successfully!', 'success');
                setDocTitle('');
                setDocFile(null);
                fetchData();
            } else {
                const errText = await res.text();
                addToast(errText || 'Upload failed.', 'error');
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsUploadingDoc(false);
        }
    };

    const selectedPatientObj = patients.find(p => String(p.id) === String(selectedPatientId)) || patients[0] || null;

    return (
        <RPMContext.Provider value={{
            // States
            user, userRole, userName,
            patients, setPatients,
            alarms, setAlarms,
            auditLogs, setAuditLogs,
            devices, setDevices,
            adminStats, setAdminStats,
            doctorsList, setDoctorsList,
            viewAllPatients, setViewAllPatients,
            adminUsers, setAdminUsers,
            connectionRequests, setConnectionRequests,
            doctorSearchQuery, setDoctorSearchQuery,
            pendingDoctors, setPendingDoctors,
            selectedDoctorVerificationDetails, setSelectedDoctorVerificationDetails,
            isDoctorVerificationDetailsModalOpen, setIsDoctorVerificationDetailsModalOpen,
            isLoadingVerificationDetails, setIsLoadingVerificationDetails,
            isDoctorApprovalConfirmOpen, setIsDoctorApprovalConfirmOpen,
            isDoctorRejectionConfirmOpen, setIsDoctorRejectionConfirmOpen,
            adminDecisionNotes, setAdminDecisionNotes,
            adminRejectionReason, setAdminRejectionReason,
            adminDirectorySubTab, setAdminDirectorySubTab,
            prescriptions, setPrescriptions,
            isPrescriptionModalOpen, setIsPrescriptionModalOpen,
            rxMedicines, setRxMedicines,
            rxDosage, setRxDosage,
            rxFrequency, setRxFrequency,
            rxDuration, setRxDuration,
            rxInstructions, setRxInstructions,
            rxDate, setRxDate,
            isSidebarCollapsed, setIsSidebarCollapsed,
            isMobileSidebarOpen, setIsMobileSidebarOpen,
            isNotificationOpen, setIsNotificationOpen,
            isProfileOpen, setIsProfileOpen,
            searchQuery, setSearchQuery,
            selectedPatientId, setSelectedPatientId,
            activeAlarmFilter, setActiveAlarmFilter,
            clinicalNoteInput, setClinicalNoteInput,
            caregiverLinkInput, setCaregiverLinkInput,
            familyLinkInput, setFamilyLinkInput,
            patientNotesMap, setPatientNotesMap,
            accessControls, setAccessControls,
            ehrSyncTime, setEhrSyncTime,
            documentsList, setDocumentsList,
            docTitle, setDocTitle,
            docCategory, setDocCategory,
            docFile, setDocFile,
            isUploadingDoc, setIsUploadingDoc,
            patientHealthSummary, setPatientHealthSummary,
            selectedPendingSummary, setSelectedPendingSummary,
            dbNotifications, setDbNotifications,
            unreadCount, setUnreadCount,
            selectedPatientObj,

            // Functions
            deriveInitialPatientId,
            formatTimeAgo,
            fetchNotifications,
            handleMarkNotificationRead,
            handleMarkAllNotificationsRead,
            fetchSummary,
            handleSaveProfile,
            handleSaveCondition,
            handleDeleteCondition,
            handleSaveAllergy,
            handleDeleteAllergy,
            handleSaveManualVital,
            handleDeleteManualVital,
            fetchData,
            addAuditLog,
            handleLogout,
            triggerTelemetrySimulation,
            simulateNormal,
            simulateFall,
            simulateHypoxia,
            simulateFever,
            simulateESP32Disconnect,
            saveClinicalNotes,
            handleUpdateDoctor,
            handleSendConnectionRequest,
            handleCancelConnectionRequest,
            handleApproveConnection,
            handleDeclineConnection,
            syncExternalEhr,
            handleSaveSettings,
            revokeAccess,
            approveDoctor,
            rejectDoctor,
            verifyAffiliation,
            openDoctorVerificationDetails,
            handleConfirmApproveDoctor,
            handleConfirmRejectDoctor,
            handleCreatePrescription,
            suspendDoctor,
            approveCaregiverLink,
            handleSendCaregiverLinkRequest,
            handleSendFamilyLinkRequest,
            approveFamilyLink,
            handleUploadDocument
        }}>
            {children}
        </RPMContext.Provider>
    );
};

export const useRPM = () => {
    const context = useContext(RPMContext);
    if (!context) {
        throw new Error('useRPM must be used within an RPMProvider');
    }
    return context;
};
