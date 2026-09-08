import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { 
  Cpu, 
  Search, 
  RefreshCw, 
  ShieldCheck, 
  Radio, 
  Activity, 
  UserCheck, 
  Clock, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export const DevicesPage = () => {
  const { user, authFetch } = useAuth();
  const { addToast } = useToast();
  const [devices, setDevices] = useState([]);
  const [stats, setStats] = useState({ totalDevices: 0, assignedDevices: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  const fetchDevices = async () => {
    try {
      setIsLoading(true);
      const [devRes, statsRes] = await Promise.all([
        authFetch(getApiUrl('/admin/devices')),
        authFetch(getApiUrl('/admin/stats'))
      ]);

      if (devRes.ok) {
        const data = await devRes.json();
        setDevices(Array.isArray(data) ? data : []);
      }
      if (statsRes.ok) {
        const sData = await statsRes.json();
        setStats(sData);
      }
    } catch (e) {
      console.error('Error fetching devices:', e);
      addToast('Failed to load registered device telemetry.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const filteredDevices = devices.filter((d) => {
    const query = searchQuery.toLowerCase();
    const matchesQuery = 
      (d.serial || '').toLowerCase().includes(query) ||
      (d.mac || '').toLowerCase().includes(query) ||
      (d.assignedPatientName || '').toLowerCase().includes(query) ||
      (d.assignedPatientId || '').toLowerCase().includes(query) ||
      (d.type || '').toLowerCase().includes(query);

    if (filterType === 'WEARABLE') return matchesQuery && d.type?.includes('Wearable');
    if (filterType === 'SYNTHETIC') return matchesQuery && d.type?.includes('Synthetic');
    if (filterType === 'ASSIGNED') return matchesQuery && d.assignedPatientId;
    if (filterType === 'UNASSIGNED') return matchesQuery && !d.assignedPatientId;
    return matchesQuery;
  });

  return (
    <div className="space-y-6 text-left max-w-6xl mx-auto font-sans select-none">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-850 p-6 shadow-sm flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-left">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <Cpu className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-black text-slate-950 dark:text-slate-50 tracking-tight">
              Hardware & IoT Device Management
            </h1>
          </div>
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mt-1">
            Registered biomedical wearable sensors, telemetry streaming nodes, and patient device assignments.
          </p>
        </div>
        <button
          onClick={fetchDevices}
          className="flex items-center gap-2 px-3.5 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors border-none cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Fleet</span>
        </button>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Total Registered Fleet</span>
            <Cpu className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-1">
            {stats.totalDevices || devices.length}
          </p>
          <span className="text-[10px] text-slate-400 font-semibold">Nodes in Database</span>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Assigned to Patients</span>
            <UserCheck className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-black text-blue-600 dark:text-blue-400 mt-1">
            {stats.assignedDevices || devices.filter(d => d.assignedPatientId).length}
          </p>
          <span className="text-[10px] text-emerald-600 font-semibold">Active telemetry bindings</span>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Wearable Biosensors</span>
            <Activity className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-2xl font-black text-purple-600 dark:text-purple-400 mt-1">
            {devices.filter(d => d.type?.includes('Wearable')).length}
          </p>
          <span className="text-[10px] text-slate-400 font-semibold">MAX30102 / MPU6050</span>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Synthetic Generators</span>
            <Radio className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">
            {devices.filter(d => d.type?.includes('Synthetic')).length}
          </p>
          <span className="text-[10px] text-slate-400 font-semibold">Simulated Telemetry Feeds</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by serial, MAC, patient..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap gap-2 self-start md:self-auto">
          {['ALL', 'WEARABLE', 'SYNTHETIC', 'ASSIGNED', 'UNASSIGNED'].map((f) => (
            <button
              key={f}
              onClick={() => setFilterType(f)}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-black uppercase tracking-wider transition-colors border-none cursor-pointer ${
                filterType === f
                  ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Devices List Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
          <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
            Registered Devices ({filteredDevices.length})
          </span>
          <span className="text-[10px] font-bold text-slate-400 uppercase">
            Live Database Sync
          </span>
        </div>

        {filteredDevices.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <Cpu className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto" />
            <h4 className="text-sm font-black text-slate-700 dark:text-slate-300">No Devices Found</h4>
            <p className="text-xs text-slate-400 font-semibold">
              No matching hardware devices or synthetic generators registered.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 text-[10px] font-black uppercase text-slate-400 tracking-wider">
                  <th className="py-3 px-4">Device Serial</th>
                  <th className="py-3 px-4">MAC Address</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Assigned Patient</th>
                  <th className="py-3 px-4">Assignment Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-300">
                {filteredDevices.map((d, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900 dark:text-slate-100">
                      {d.serial}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                      {d.mac}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                        d.type?.includes('Wearable')
                          ? 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300 border border-purple-200/50'
                          : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border border-amber-200/50'
                      }`}>
                        {d.type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                        d.status === 'Active' || d.status === 'Assigned'
                          ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                          : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                      }`}>
                        {d.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {d.assignedPatientId ? (
                        <div>
                          <span className="font-bold text-slate-900 dark:text-slate-100 block">
                            {d.assignedPatientName}
                          </span>
                          <span className="text-[10px] font-mono text-blue-600 dark:text-blue-400 font-semibold">
                            ID: {d.assignedPatientId}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic text-[11px]">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-[11px] text-slate-500">
                      {d.assignedAt ? new Date(d.assignedAt).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DevicesPage;
