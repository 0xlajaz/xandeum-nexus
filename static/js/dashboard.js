const { useState, useEffect, useMemo, useCallback, useRef } = React;

// ==========================================
// 🎨 ICON COMPONENTS - Professional SVG Icons
// ==========================================

const DownloadIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
    </svg>
);

const CopyIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
);

const BellIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
    </svg>
);

const CheckIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
);

const SearchIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
    </svg>
);

const RefreshIcon = ({ spinning }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={spinning ? 'animate-spin' : ''}>
        <polyline points="23 4 23 10 17 10"></polyline>
        <polyline points="1 20 1 14 7 14"></polyline>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
    </svg>
);

const AlertIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
    </svg>
);

// ==========================================
// 🎯 UTILITY FUNCTIONS
// ==========================================

/**
 * Format uptime seconds into human-readable duration
 * @param {number} seconds - Uptime in seconds
 * @returns {string} Formatted duration
 */
const formatUptime = (seconds) => {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    }
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    return `${days}d ${hours}h`;
};

/**
 * Format storage with appropriate units
 * @param {number} gb - Size in GB
 * @returns {string} Formatted storage string
 */
const formatStorage = (gb) => {
    if (gb < 0.001) return `${(gb * 1024 * 1024).toFixed(0)} KB`;
    if (gb < 1) return `${(gb * 1024).toFixed(0)} MB`;
    return `${gb.toFixed(2)} GB`;
};

/**
 * Get health status color and emoji based on score
 * @param {number} score - Health score (0-100)
 * @returns {object} Color class and emoji
 */
const getHealthStatus = (score) => {
    if (score >= 90) return { 
        color: 'bg-x-primary shadow-[0_0_8px_#00FFA3]', 
        textColor: 'text-white', 
        emoji: '🟢',
        label: 'EXCELLENT'
    };
    if (score >= 75) return { 
        color: 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.5)]', 
        textColor: 'text-yellow-500', 
        emoji: '🟡',
        label: 'GOOD'
    };
    if (score >= 50) return { 
        color: 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]', 
        textColor: 'text-orange-500', 
        emoji: '🟠',
        label: 'FAIR'
    };
    return { 
        color: 'bg-x-danger shadow-[0_0_8px_rgba(255,51,102,0.5)]', 
        textColor: 'text-x-danger', 
        emoji: '🔴',
        label: 'POOR'
    };
};

/**
 * Debounce function for search input
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// ==========================================
// 📊 METRIC CARD COMPONENT
// ==========================================

const MetricCard = ({ label, value, sub, icon }) => (
    <div className="glass p-5 rounded-xl border-l-2 border-x-primary relative overflow-hidden group hover:border-l-4 transition-all duration-300 hover:bg-x-panel/80 hover:scale-[1.02]">
        <div className="flex justify-between items-start z-10 relative">
            <div>
                <p className="text-xs text-x-dim uppercase tracking-wider font-bold mb-1">{label}</p>
                <h3 className="text-3xl font-bold text-white neon-text transition-all duration-300">{value}</h3>
                <p className="text-xs text-x-primary mt-1 font-mono">{sub}</p>
            </div>
            <div className="text-x-primary opacity-50 group-hover:opacity-100 transition-all duration-300 transform group-hover:scale-110 group-hover:rotate-12">
                {icon}
            </div>
        </div>
        {/* Subtle gradient overlay on hover */}
        <div className="absolute inset-0 bg-gradient-to-br from-x-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
    </div>
);

// ==========================================
// 📶 NEW COMPONENT: Signal Strength (Insight 2)
// ==========================================
const SignalIndicator = ({ strength, max = 9 }) => {
    // Calculate percentage (1 to 9 seeds)
    const percent = (strength / max) * 100;
    
    let color = "bg-x-danger";
    if (percent > 60) color = "bg-x-primary";
    else if (percent > 30) color = "bg-yellow-500";

    return (
        <div className="flex flex-col gap-0.5 group/signal relative cursor-help">
            <div className="flex items-end gap-0.5 h-3">
                {[...Array(4)].map((_, i) => (
                    <div 
                        key={i} 
                        className={`w-1 rounded-sm ${i / 4 < percent / 100 ? color : 'bg-gray-700'}`}
                        style={{ height: `${(i + 1) * 25}%` }}
                    ></div>
                ))}
            </div>
            {/* Tooltip */}
            <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover/signal:block bg-black border border-white/20 text-[10px] px-2 py-1 rounded whitespace-nowrap z-50">
                Seen by {strength} Seed Nodes
            </div>
        </div>
    );
};

// ==========================================
// 🗺️ NEW COMPONENT: Network Topology Map
// ==========================================
const TopologyMap = ({ geoData }) => {
    // Sort countries by node count
    const sorted = Object.entries(geoData || {})
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5); // Top 5 only

    const maxCount = sorted.length > 0 ? sorted[0][1] : 1;

    return (
        <div className="glass p-6 rounded-xl border border-white/5 hover:border-white/10 transition-all duration-300 flex flex-col justify-between">
            <h3 className="text-white font-bold mb-4 text-sm tracking-wider flex items-center gap-2">
                <span className="text-lg">🌍</span>
                GLOBAL NODE DISTRIBUTION
            </h3>
            
            <div className="flex-grow flex flex-col justify-center gap-4">
                {sorted.length > 0 ? sorted.map(([key, count], idx) => {
                    // Logic: Split "US|New York" -> Code="US", Label="New York"
                    // Fallback: If no pipe, assume key is country code (e.g. "US")
                    const parts = key.split('|');
                    const code = parts[0];
                    const label = parts.length > 1 ? parts[1] : (code === '??' ? 'Unknown Region' : code);

                    return (
                        <div key={key} className="relative group">
                            <div className="flex justify-between text-xs mb-1 font-mono text-gray-400">
                                <span className="flex items-center gap-2">
                                    <CountryFlag code={code} name={label} />
                                    <span className="truncate max-w-[120px]" title={label}>
                                        {label}
                                    </span>
                                </span>
                                <span className="text-white font-bold">{count} Nodes</span>
                            </div>
                            {/* Bar Chart */}
                            <div className="w-full bg-black/50 rounded-full h-2 overflow-hidden">
                                <div 
                                    className={`h-full rounded-full ${idx === 0 ? 'bg-x-primary' : 'bg-x-accent'} opacity-80 group-hover:opacity-100 transition-all duration-1000`}
                                    style={{ width: `${(count / maxCount) * 100}%` }}
                                ></div>
                            </div>
                        </div>
                    );
                }) : (
                    <div className="text-center text-gray-600 font-mono text-xs py-10">
                        Gathering Location Data...
                    </div>
                )}
            </div>
            
            <div className="mt-4 pt-4 border-t border-white/5 text-[10px] text-gray-500 font-mono flex justify-between">
                <span>Top Region Dominance</span>
                <span className="text-x-primary">
                    {sorted.length > 0 ? Math.round((sorted[0][1] / Math.max(1, Object.values(geoData).reduce((a,b)=>a+b,0))) * 100) : 0}%
                </span>
            </div>
        </div>
    );
};

// ==========================================
// 🌍 NEW COMPONENT: Country Flag (Insight 3)
// ==========================================
const CountryFlag = ({ code, name }) => {
    if (!code || code === '??') return <span className="text-gray-600">🌐</span>;
    
    // Convert ISO code to Emoji Flag
    const flag = code
        .toUpperCase()
        .replace(/./g, char => String.fromCodePoint(char.charCodeAt(0) + 127397));
        
    return (
        <span className="cursor-help text-lg" title={name || code}>
            {flag}
        </span>
    );
};

// ==========================================
// 📈 PROGRESS BAR COMPONENT
// ==========================================

const ProgressBar = ({ value, max = 100, color = 'bg-x-primary' }) => (
    <div className="w-full bg-x-border rounded-full h-1.5 mt-2 overflow-hidden">
        <div 
            className={`${color} h-1.5 rounded-full transition-all duration-1000 ease-out`} 
            style={{ width: `${Math.min((value / max) * 100, 100)}%` }}
        ></div>
    </div>
);

const NodeRow = React.memo(({ node }) => {
    const [copied, setCopied] = useState(false);
    
    // Version validation
    const isSafeVersion = node.version.includes('0.8') || node.version.includes('0.9');
    #CHANGE THE BOT USERNAME!
    const BOT_USERNAME = ".........";

    // Score breakdown with defaults
    const breakdown = node.score_breakdown || {};
    const vScore = breakdown['v0.7_compliance'] || 0;
    const uScore = breakdown.uptime_reliability || 0;
    const sScore = breakdown.storage_weight || 0;
    const pScore = breakdown.paging_efficiency || 0;

    const locationStr = node.geo?.city 
        ? `${node.geo.city}, ${node.geo.country}` 
        : (node.geo?.country || 'Unknown Region');

    // Health status
    const healthStatus = getHealthStatus(node.health_score);

    // Warning detection logic
    let warningReason = "";
    if (node.health_score < 60) {
        const warnings = [];
        if (node.uptime_sec < 86400) warnings.push("Low Uptime");
        if (!isSafeVersion) warnings.push("Outdated Ver");
        if (node.storage_gb < 0.1) warnings.push("Low Storage");
        if (warnings.length === 0) warnings.push("Check Connection");
        warningReason = warnings.join(" • ");
    }

    // Copy handler with feedback
    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(node.pubkey)
            .then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            })
            .catch(err => console.error('Copy failed:', err));
    }, [node.pubkey]);

    return (
        <tr className="border-b border-x-border hover:bg-x-primary/5 transition-all duration-200 text-sm group relative">
            {/* Node Identity Column */}
            <td className="py-4 pl-4 align-middle">
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-3">
                        {/* Status Indicator */}
                        <div className={`w-2.5 h-2.5 rounded-full ${healthStatus.color} animate-pulse shrink-0`}></div>
                        
                        {/* Copyable Node ID */}
                        <div 
                            onClick={handleCopy}
                            className="flex items-center gap-2 cursor-pointer group/copy relative px-2 py-1 rounded hover:bg-white/5 transition-all duration-200"
                            title={`Click to copy: ${node.pubkey}`}
                        >
                            <span className="font-mono text-[10px] break-all text-gray-300 group-hover/copy:text-white transition-colors">
                                {node.pubkey}
                            </span>
                            <span className={`text-x-primary transition-all duration-300 ${copied ? 'opacity-100 scale-100' : 'opacity-0 scale-0 group-hover/copy:opacity-50'}`}>
                                {copied ? (
                                    <span className="text-[10px] font-bold tracking-wider flex items-center gap-1">
                                        <CheckIcon />
                                    </span>
                                ) : <CopyIcon />}
                            </span>
                        </div>

                        {/* Alert Warning sebagai Tooltip Bawah */}
                        {node.health_score < 60 && (
                            <div className="relative group/alert">
                                <div className="text-x-danger cursor-help animate-pulse p-1 hover:bg-x-danger/10 rounded">
                                    <AlertIcon />
                                </div>
                                {/* Tooltip Container */}
                                <div className="absolute top-full left-0 mt-2 w-48 bg-[#0F1219] border border-x-danger/50 p-3 rounded-lg shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)] opacity-0 group-hover/alert:opacity-100 pointer-events-none transition-all duration-200 z-[60] translate-y-[-5px] group-hover/alert:translate-y-0">
                                    <div className="text-[10px] font-bold text-x-danger uppercase mb-1 tracking-wider border-b border-x-danger/20 pb-1">
                                        Attention Required
                                    </div>
                                    <div className="text-xs text-gray-300 font-mono leading-relaxed">
                                        {warningReason}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Telegram Bot Monitor Link */}
                        {/* PERBAIKAN 1: Menghapus 'ml-auto', diganti 'ml-2' agar tidak terlalu jauh */}
                        <a 
                            href={`https://t.me/${BOT_USERNAME}?start=${encodeURIComponent(node.pubkey)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ml-2 p-1.5 rounded-full bg-x-panel border border-white/5 hover:border-x-primary hover:text-x-primary text-gray-500 transition-all duration-200 shadow-sm group/bell relative"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <BellIcon />
                            {/* Tooltip for Bot */}
                            <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 text-[10px] bg-black border border-x-primary text-x-primary rounded opacity-0 group-hover/bell:opacity-100 pointer-events-none whitespace-nowrap transition-opacity duration-200 z-50">
                                📊 Monitor Node
                            </span>
                        </a>
                    </div>
                    
                    {/* Geo Location Info */}
                    <div className="flex items-center gap-2 pl-6 mt-0.5 text-[10px] text-gray-500 font-mono opacity-70">
                        <CountryFlag code={node.geo?.countryCode} name={node.geo?.country} />
                        <span>{node.ip}</span>
                        <span className="text-gray-700 mx-1">•</span>
                        <span className="truncate max-w-[150px]" title={locationStr}>
                            {locationStr}
                        </span>
                    </div>
                </div>
            </td>
            
            {/* Version Column */}
            <td className="py-4 align-middle">
                {/* PERBAIKAN 2: Membatasi lebar (max-w) dan truncate agar versi panjang terpotong rapi */}
                <div className="max-w-[140px]" title={node.version}>
                    <span className={`px-2.5 py-1 rounded text-xs font-mono border transition-all duration-200 block w-full truncate ${isSafeVersion ? 'border-x-primary/30 text-x-primary bg-x-primary/10' : 'border-x-danger/50 text-x-danger bg-x-danger/10 animate-pulse'}`}>
                        {node.version}
                    </span>
                </div>
            </td>
            
            {/* Reputation Credits Column */}
            <td className="py-4 align-middle">
                <div className="flex items-center gap-2">
                    <span className="font-mono text-x-primary/90 font-bold text-sm">
                        {node.reputation_credits ? node.reputation_credits.toLocaleString() : "0"}
                    </span>
                    {node.reputation_credits > 1000 && (
                        <span className="text-[9px] bg-x-accent/20 text-x-accent px-1.5 py-0.5 rounded border border-x-accent/20 font-bold tracking-wider">
                            TOP
                        </span>
                    )}
                </div>
            </td>
            
            {/* Storage Capacity Column */}
            <td className="py-4 align-middle">
                <div className="flex flex-col gap-0.5">
                    <span className="text-white font-medium text-sm">{formatStorage(node.storage_gb)}</span>
                    <span className="text-[10px] text-gray-500 font-mono">
                        {node.storage_used ? `${formatStorage(node.storage_used / (1024**3))} Used` : 'Committed'}
                    </span>
                </div>
            </td>
            
            {/* Performance (Paging) Column */}
            <td className="py-4 align-middle">
                <div className="w-28">
                    <div className="flex justify-between text-xs mb-1.5">
                        <span className={node.paging_metrics.hit_rate > 0.9 ? "text-x-primary font-bold" : "text-gray-400"}>
                            {(node.paging_metrics.hit_rate * 100).toFixed(1)}%
                        </span>
                        <span className="text-gray-600 text-[10px]">
                            {node.paging_metrics.hit_rate > 0.95 ? '⚡ Optimal' : ''}
                        </span>
                    </div>
                    <ProgressBar 
                        value={node.paging_metrics.hit_rate * 100} 
                        color={node.paging_metrics.hit_rate > 0.9 ? "bg-x-accent" : "bg-x-dim"} 
                    />
                </div>
            </td>
            
            {/* Health Score Column */}
            <td className="py-4 pr-4 text-right align-middle relative">
                <div className="group/score inline-block cursor-help relative">
                    <div className="flex items-center justify-end gap-3">
                        <span className="text-xs text-gray-600 font-mono opacity-50">{healthStatus.emoji}</span>
                        <span className={`text-xl font-bold ${healthStatus.textColor} transition-all duration-300 group-hover/score:scale-110 drop-shadow-lg`}>
                            {node.health_score}
                        </span>
                    </div>
                    
                    {/* Enhanced Score Breakdown Tooltip */}
                    <div className="absolute right-0 top-full mt-3 w-80 bg-[#0F1219] border border-x-border p-5 rounded-xl shadow-[0_20px_50px_-10px_rgba(0,0,0,0.8)] opacity-0 group-hover/score:opacity-100 pointer-events-none transition-all duration-200 z-[100] translate-y-[-10px] group-hover/score:translate-y-0 backdrop-blur-xl ring-1 ring-white/10">
                        <div className="flex justify-between items-center mb-4 border-b border-white/10 pb-3">
                            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">
                                Health Diagnosis
                            </span>
                            <span className={`${healthStatus.textColor} font-mono text-xs px-2 py-0.5 rounded bg-white/5 border border-white/5`}>
                                {healthStatus.label}
                            </span>
                        </div>
                        
                        <div className="space-y-4 font-mono text-sm text-left">
                            {/* Version Score */}
                            <div className="flex justify-between items-center group/item">
                                <div className="flex flex-col">
                                    <span className="text-gray-400 group-hover/item:text-white transition-colors">Client Version</span>
                                    <span className="text-[10px] text-gray-600">Compliance check (v0.8+)</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={vScore === 40 ? "text-x-primary font-bold" : "text-x-danger"}>
                                        {vScore}/40
                                    </span>
                                    {vScore === 40 && <CheckIcon />}
                                </div>
                            </div>
                            
                            {/* Uptime Score */}
                            <div className="flex justify-between items-center group/item">
                                <div className="flex flex-col">
                                    <span className="text-gray-400 group-hover/item:text-white transition-colors">Uptime Stability</span>
                                    <span className="text-[10px] text-gray-600">{formatUptime(node.uptime_sec)} active</span>
                                </div>
                                <span className={uScore > 20 ? "text-white font-bold" : "text-yellow-500"}>
                                    {uScore}/30
                                </span>
                            </div>
                            
                            {/* Storage Score */}
                            <div className="flex justify-between items-center group/item">
                                <div className="flex flex-col">
                                    <span className="text-gray-400 group-hover/item:text-white transition-colors">Storage Pool</span>
                                    <span className="text-[10px] text-gray-600">Target: ≥100MB</span>
                                </div>
                                <span className={sScore >= 15 ? "text-white font-bold" : "text-orange-500"}>
                                    {sScore}/20
                                </span>
                            </div>
                            
                            {/* Paging Score */}
                            <div className="flex justify-between items-center group/item">
                                <div className="flex flex-col">
                                    <span className="text-gray-400 group-hover/item:text-white transition-colors">Paging Efficiency</span>
                                    <span className="text-[10px] text-gray-600">Memory hit rate</span>
                                </div>
                                <span className="text-x-accent font-bold">
                                    {pScore}/10
                                </span>
                            </div>
                        </div>
                        
                        {/* Latency Info */}
                        {node.latency_ms && (
                            <div className="mt-4 pt-3 border-t border-white/10 flex justify-between items-center bg-black/20 p-2 rounded">
                                <span className="text-[10px] text-gray-500 uppercase tracking-wider">Network Latency</span>
                                <span className="text-x-primary font-mono text-xs font-bold">{node.latency_ms.toFixed(0)}ms</span>
                            </div>
                        )}
                    </div>
                </div>
            </td>
        </tr>
    );
});

// Add display name for React DevTools
NodeRow.displayName = 'NodeRow';

// ==========================================
// 🎮 MAIN APP COMPONENT
// ==========================================

const App = () => {
    // ========== STATE MANAGEMENT ==========
    const [data, setData] = useState(null);
    const [history, setHistory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [filter, setFilter] = useState("all");
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [lastUpdate, setLastUpdate] = useState(null);
    
    // Refs for cleanup and chart
    const intervalRef = useRef(null);
    const chartRef = useRef(null);

    // ========== DATA FETCHING ==========
    
    /**
     * Fetch telemetry and historical data from API
     * Includes error handling and loading states
     */
    const fetchData = useCallback(async (isManualRefresh = false) => {
        if (isManualRefresh) setIsRefreshing(true);
        
        try {
            const [telemRes, histRes] = await Promise.all([
                fetch('/api/telemetry'),
                fetch('/api/history/trend')
            ]);
            
            if (!telemRes.ok) {
                throw new Error(`API Error: ${telemRes.status} ${telemRes.statusText}`);
            }
            
            const telemData = await telemRes.json();
            const histData = await histRes.json();
            
            // Validate data structure
            if (!telemData || !telemData.nodes || !Array.isArray(telemData.nodes)) {
                throw new Error('Invalid data structure received from API');
            }
            
            setData(telemData);
            setHistory(histData);
            setError(null);
            setLoading(false);
            setLastUpdate(new Date());
            
            // Update chart if data is available
            if (histData.timestamps && histData.timestamps.length > 0) {
                updateChart(histData);
            }
        } catch (err) {
            console.error('Fetch error:', err);
            setError(err.message);
            if (loading) setLoading(false);
        } finally {
            if (isManualRefresh) {
                // Keep spinner visible for at least 500ms for UX feedback
                setTimeout(() => setIsRefreshing(false), 500);
            }
        }
    }, [loading]);

    // Manual refresh handler
    const handleManualRefresh = useCallback(() => {
        fetchData(true);
    }, [fetchData]);

    // ========== EFFECTS ==========
    
    // Initial data fetch and interval setup
    useEffect(() => {
        fetchData();
        intervalRef.current = setInterval(() => fetchData(), 5000);
        
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
            if (chartRef.current) {
                chartRef.current.destroy();
                chartRef.current = null;
            }
        };
    }, [fetchData]);

    // Debounced search effect
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedSearch(searchTerm);
        }, 300);

        return () => clearTimeout(handler);
    }, [searchTerm]);

    // ========== CHART MANAGEMENT ==========
    
    /**
     * Update Chart.js visualization with historical data
     * @param {Object} histData - Historical network data
     */
    const updateChart = useCallback((histData) => {
        const canvas = document.getElementById('mainChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (chartRef.current) {
            chartRef.current.destroy();
            chartRef.current = null;
        }
        
        // Create gradients
        const gradientGreen = ctx.createLinearGradient(0, 0, 0, 400);
        gradientGreen.addColorStop(0, 'rgba(0, 255, 163, 0.2)');
        gradientGreen.addColorStop(1, 'rgba(0, 255, 163, 0)');

        const gradientPurple = ctx.createLinearGradient(0, 0, 0, 400);
        gradientPurple.addColorStop(0, 'rgba(112, 0, 255, 0.1)');
        gradientPurple.addColorStop(1, 'rgba(112, 0, 255, 0)');

        chartRef.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: histData.timestamps.map(t => {
                    const date = new Date(t * 1000);
                    return date.toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit'
                    });
                }),
                datasets: [
                    {
                        label: 'Network Health',
                        data: histData.health,
                        borderColor: '#00FFA3',
                        backgroundColor: gradientGreen,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: '#00FFA3',
                        pointBorderColor: '#0F1219',
                        pointBorderWidth: 2,
                        pointHoverRadius: 5,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Paging Efficiency',
                        data: histData.paging_efficiency.map(v => v * 100),
                        borderColor: '#7000FF',
                        backgroundColor: gradientPurple,
                        borderWidth: 2,
                        pointRadius: 2,
                        pointBackgroundColor: '#7000FF',
                        pointBorderColor: '#0F1219',
                        pointBorderWidth: 2,
                        pointHoverRadius: 4,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: '#9CA3AF',
                            font: {
                                size: 11,
                                family: 'JetBrains Mono',
                                weight: '500'
                            },
                            boxWidth: 12,
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 18, 25, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#9CA3AF',
                        borderColor: '#1E2330',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += context.parsed.y.toFixed(1);
                                if (context.datasetIndex === 1) {
                                    label += '%';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: '#1E2330',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 10,
                                family: 'JetBrains Mono'
                            },
                            padding: 8
                        },
                        beginAtZero: true
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#6B7280',
                            font: {
                                size: 9,
                                family: 'JetBrains Mono'
                            },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 8
                        }
                    }
                }
            }
        });
    }, []);

    // ========== CSV EXPORT ==========
    
    /**
     * Export current node data to CSV file
     * Includes proper escaping and formatting
     */
    const handleExport = useCallback(() => {
        if (!data || !data.nodes || data.nodes.length === 0) {
            alert('No data available to export');
            return;
        }

        const escapeCsv = (str) => {
            if (typeof str !== 'string') return str;
            // Prevent Excel Formula Injection
            if (/^[=+\-@]/.test(str)) {
                str = "'" + str;
            }
            // Escape double quotes
            return `"${str.replace(/"/g, '""')}"`;
        };

        const headers = 'NodeID,IP,Version,Uptime(sec),Uptime(formatted),Credits,Storage(GB),HitRate(%),HealthScore,Status\n';
        const rows = data.nodes.map(n => {
            const status = getHealthStatus(n.health_score);
            return [
                escapeCsv(n.pubkey),
                escapeCsv(n.ip),
                escapeCsv(n.version),
                n.uptime_sec,
                escapeCsv(formatUptime(n.uptime_sec)),
                n.reputation_credits || 0,
                n.storage_gb.toFixed(4),
                (n.paging_metrics.hit_rate * 100).toFixed(2),
                n.health_score,
                status.label
            ].join(',');
        }).join('\n');

        const csvContent = 'data:text/csv;charset=utf-8,' + headers + rows;
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `xandeum_network_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, [data]);

    // ========== NODE FILTERING ==========
    
    /**
     * Filter and search nodes based on user input
     * Memoized for performance
     */
    const filteredNodes = useMemo(() => {
        if (!data || !data.nodes) return [];
        
        return data.nodes.filter(node => {
            // Search filter
            const term = debouncedSearch.toLowerCase();
            const matchesSearch = node.pubkey.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
                                node.ip.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
                                node.version.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
                                (node.geo?.city || '').toLowerCase().includes(term) ||
                                (node.geo?.country || '').toLowerCase().includes(term);
            if (!matchesSearch) return false;
            
            // Category filter
            if (filter === 'v0.8') {
                return node.version.includes('0.8') || node.version.includes('0.9');
            }
            
            if (filter === 'issues') {
                return node.health_score < 60;
            }
            
            return true;
        });
    }, [data, debouncedSearch, filter]);

    // ========== RENDER STATES ==========
    
    // Initial loading state
    if (loading && !data) {
        return (
            <div className="h-screen flex items-center justify-center flex-col gap-4">
                <div className="w-16 h-16 border-4 border-x-border border-t-x-primary rounded-full animate-spin"></div>
                <div className="text-x-primary font-mono text-sm animate-pulse tracking-widest">INITIALIZING NEXUS...</div>
                <div className="text-gray-600 font-mono text-xs">Connecting to Xandeum Network</div>
            </div>
        );
    }

    // Error state with retry option
    if (error && !data) {
        return (
            <div className="h-screen flex items-center justify-center flex-col gap-4">
                <div className="text-x-danger text-4xl mb-4">⚠️</div>
                <div className="text-x-danger font-mono text-sm font-bold">CONNECTION ERROR</div>
                <div className="text-gray-500 font-mono text-xs max-w-md text-center">{error}</div>
                <button 
                    onClick={() => { setError(null); setLoading(true); fetchData(); }}
                    className="mt-4 px-6 py-2 bg-x-primary text-black font-bold rounded-lg hover:bg-x-primary/80 transition-all"
                >
                    RETRY CONNECTION
                </button>
            </div>
        );
    }

    // No data fallback (shouldn't happen but defensive)
    if (!data) {
        return (
            <div className="h-screen flex items-center justify-center text-gray-500 font-mono">
                <div className="text-center">
                    <div className="text-4xl mb-4">📡</div>
                    <div>No data available. Please refresh.</div>
                </div>
            </div>
        );
    }

    // ========== MAIN RENDER ==========
    
    return (
        <div className="w-full mx-auto p-3 md:p-6 lg:p-8 space-y-8 pb-20">
            {/* ===== HEADER SECTION ===== */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-x-border pb-6 gap-4">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-3 h-3 bg-x-primary rounded-full animate-pulse-fast shadow-[0_0_10px_#00FFA3]"></div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">
                            XANDEUM<span className="text-x-primary">NEXUS</span>
                        </h1>
                    </div>
                    <p className="text-gray-500 font-mono text-xs md:text-sm tracking-wide">
                        PROFESSIONAL ANALYTICS // 
                        <span className="text-x-primary ml-2">SYSTEM ONLINE</span>
                    </p>
                    {lastUpdate && (
                        <p className="text-gray-600 font-mono text-[10px] mt-1">
                            Last updated: {lastUpdate.toLocaleTimeString()}
                        </p>
                    )}
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={handleManualRefresh}
                        disabled={isRefreshing}
                        className="flex items-center gap-2 px-3 py-2 bg-x-panel border border-x-border hover:border-x-primary text-gray-400 hover:text-x-primary rounded-lg text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Refresh data"
                    >
                        <RefreshIcon spinning={isRefreshing} />
                        <span className="hidden md:inline">REFRESH</span>
                    </button>
                    <div className="text-right">
                        <div className="text-2xl font-mono text-white font-bold">
                            {data.network.total_nodes}
                            <span className="text-sm text-gray-500 font-normal ml-2">NODES</span>
                        </div>
                        <div className="text-xs text-x-dim font-mono">
                            LIVE MONITORING
                        </div>
                    </div>
                </div>
            </div>

            {/* ===== KPI METRIC CARDS ===== */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <MetricCard 
                    label="Total Storage" 
                    value={data.network.total_storage_gb.toFixed(2)} 
                    sub="GIGABYTES POOLED"
                    icon={
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                        </svg>
                    }
                />
                <MetricCard 
                    label="Network Redundancy" 
                    value={data.network.avg_visibility ? data.network.avg_visibility.toFixed(1) : "0.0"} 
                    sub="AVG WITNESS COUNT"
                    icon={
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                        </svg>
                    }
                />
                <MetricCard 
                    label="Paging Efficiency" 
                    value={(data.network.avg_paging_efficiency * 100).toFixed(1) + "%"} 
                    sub="AVG HIT RATE"
                    icon={
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    }
                />
                <MetricCard 
                    label="Protocol Adoption" 
                    value={((data.network.v7_adoption / Math.max(data.network.total_nodes, 1)) * 100).toFixed(0) + "%"} 
                    sub="LATEST VERSION"
                    icon={
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    }
                />
                <MetricCard 
                    label="Network Health" 
                    value={data.network.avg_health.toFixed(0)} 
                    sub="GLOBAL SCORE"
                    icon={
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                        </svg>
                    }
                />
            </div>

            {/* ===== CHARTS & VISUALIZATION ===== */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Main Performance Chart */}
                <div className="lg:col-span-2 glass p-6 rounded-xl border border-white/5 hover:border-white/10 transition-all duration-300">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-white font-bold flex items-center gap-2 text-sm tracking-wider">
                            <span className="w-2 h-2 bg-x-primary rounded-full animate-pulse"></span>
                            REAL-TIME NETWORK PERFORMANCE
                        </h3>
                        {history && history.timestamps && (
                            <span className="text-[10px] text-gray-600 font-mono">
                                {history.timestamps.length} data points
                            </span>
                        )}
                    </div>
                    <div className="h-64 w-full">
                        <canvas id="mainChart"></canvas>
                    </div>
                </div>
                <div className="h-full">
            <TopologyMap geoData={data.network.geo_distribution} />
                </div>
                {/* Gossip Protocol Status Panel */}
                <div className="glass p-6 rounded-xl border border-white/5 hover:border-white/10 transition-all duration-300 flex flex-col justify-between">
                    <div>
                        <h3 className="text-white font-bold mb-4 text-sm tracking-wider flex items-center gap-2">
                            <span className="w-2 h-2 bg-x-accent rounded-full animate-pulse"></span>
                            GOSSIP PROTOCOL STATUS
                        </h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                                <span className="text-gray-400">Update Frequency</span>
                                <span className="text-x-primary font-mono font-bold">~5s</span>
                            </div>
                            <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                                <span className="text-gray-400">Network Nodes</span>
                                <span className="text-white font-mono font-bold">{data.network.total_nodes}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                                <span className="text-gray-400">Avg Response</span>
                                <span className="text-white font-mono font-bold">
                                    {data.nodes.length > 0 
                                        ? Math.round(data.nodes.reduce((acc, n) => acc + (n.latency_ms || 0), 0) / data.nodes.length)
                                        : 0}ms
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="mt-6">
                        <div className="text-[10px] text-gray-500 mb-2 uppercase tracking-wider">Live Network Activity</div>
                        <div className="flex gap-1 h-16 items-end bg-black/20 p-2 rounded-lg">
                            {[...Array(15)].map((_, i) => (
                                <div 
                                    key={i} 
                                    className="flex-1 bg-gradient-to-t from-x-accent to-x-primary rounded-sm opacity-60 animate-pulse transition-all duration-300" 
                                    style={{
                                        height: `${Math.random() * 80 + 20}%`,
                                        animationDelay: `${i * 0.1}s`
                                    }}
                                ></div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* ===== NODE TABLE ===== */}
            <div className="glass rounded-xl overflow-hidden border border-white/5 mb-20 flex flex-col h-[800px] hover:border-white/10 transition-all duration-300">
                {/* Table Controls */}
                <div className="p-4 border-b border-x-border flex flex-col md:flex-row justify-between items-center gap-4 bg-x-panel/50 shrink-0">
                    {/* Filter Buttons */}
                    <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
                        <button 
                            onClick={() => setFilter('all')} 
                            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap border flex items-center gap-2 ${
                                filter === 'all' 
                                    ? 'bg-x-primary text-black border-x-primary shadow-[0_0_10px_rgba(0,255,163,0.3)]' 
                                    : 'bg-white/5 text-gray-400 border-transparent hover:border-white/20 hover:text-white'
                            }`}
                        >
                            <span>ALL NODES</span>
                            <span className="bg-black/30 px-2 py-0.5 rounded-full text-[10px]">
                                {data.nodes.length}
                            </span>
                        </button>
                        
                        <button 
                            onClick={() => setFilter('v0.8')}
                            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap border flex items-center gap-2 ${
                                filter === 'v0.8' 
                                    ? 'bg-x-primary/20 text-x-primary border-x-primary' 
                                    : 'bg-white/5 text-gray-400 border-transparent hover:border-white/20 hover:text-white'
                            }`}
                        >
                            <CheckIcon />
                            <span>VERIFIED v0.8+</span>
                        </button>
                        
                        <button 
                            onClick={() => setFilter('issues')} 
                            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap border flex items-center gap-2 ${
                                filter === 'issues' 
                                    ? 'bg-x-danger text-white border-x-danger shadow-[0_0_10px_rgba(255,51,102,0.4)]' 
                                    : 'bg-white/5 text-gray-400 border-transparent hover:border-x-danger/50 hover:text-x-danger'
                            }`}
                        >
                            <AlertIcon />
                            <span>ISSUES</span>
                            {data.nodes.filter(n => n.health_score < 60).length > 0 && (
                                <span className="bg-x-danger/30 px-2 py-0.5 rounded-full text-[10px]">
                                    {data.nodes.filter(n => n.health_score < 60).length}
                                </span>
                            )}
                        </button>
                    </div>
                    
                    {/* Search and Export */}
                    <div className="flex gap-3 w-full md:w-auto">
                        <div className="relative flex-grow">
                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600">
                                <SearchIcon />
                            </div>
                            <input 
                                type="text" 
                                placeholder="SEARCH NODE ID, IP, CITY..." 
                                className="w-full bg-black/40 text-xs pl-10 pr-4 py-2 rounded-lg border border-x-border focus:border-x-primary outline-none text-white transition-all placeholder-gray-600"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                            {searchTerm && (
                                <button
                                    onClick={() => setSearchTerm('')}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-white transition-colors"
                                >
                                    ×
                                </button>
                            )}
                        </div>
                        <button 
                            onClick={handleExport}
                            disabled={!data || !data.nodes || data.nodes.length === 0}
                            className="px-4 py-2 bg-x-accent/10 border border-x-accent/50 hover:bg-x-accent/20 text-x-accent rounded-lg text-xs font-bold transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Export to CSV"
                        >
                            <DownloadIcon />
                            <span className="hidden sm:inline">CSV</span>
                        </button>
                    </div>
                </div>
                
                {/* Results Info Bar */}
                {debouncedSearch && (
                    <div className="px-4 py-2 bg-x-panel/30 border-b border-x-border text-xs text-gray-400 font-mono">
                        <span className="text-x-primary">{filteredNodes.length}</span> result{filteredNodes.length !== 1 ? 's' : ''} for "{debouncedSearch}"
                        {filteredNodes.length === 0 && (
                            <span className="ml-2 text-gray-600">- Try a different search term</span>
                        )}
                    </div>
                )}
                
                {/* Table Container */}
                <div className="overflow-auto custom-scroll flex-grow"> 
                    <table className="w-full text-left border-collapse relative">
                        <thead className="bg-[#0F1219] sticky top-0 z-20 text-[10px] uppercase text-gray-500 font-bold tracking-wider shadow-lg">
                            <tr>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">
                                    Node Identity
                                </th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">
                                    Client Ver
                                </th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219] text-x-primary">
                                    Credits
                                </th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">
                                    Capacity
                                </th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">
                                    Performance
                                </th>
                                <th className="px-4 py-3 text-right border-b border-white/10 bg-[#0F1219]">
                                    Score
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {filteredNodes.length > 0 ? (
                                <>
                                    {filteredNodes.map(node => (
                                        <NodeRow key={node.pubkey} node={node} />
                                    ))}
                                    <tr>
                                        <td colSpan="6" className="p-4 text-center text-gray-600 font-mono text-[10px] uppercase tracking-widest opacity-50">
                                            — End of Network List ({filteredNodes.length} node{filteredNodes.length !== 1 ? 's' : ''}) —
                                        </td>
                                    </tr>
                                </>
                            ) : (
                                <tr>
                                    <td colSpan="6" className="p-12 text-center">
                                        <div className="flex flex-col items-center gap-4 text-gray-500">
                                            <div className="text-4xl opacity-50">🔍</div>
                                            <div className="font-mono text-sm font-bold">NO NODES FOUND</div>
                                            <div className="text-xs text-gray-600">
                                                {debouncedSearch 
                                                    ? `No matches for "${debouncedSearch}". Try a different search.`
                                                    : filter === 'issues' 
                                                        ? 'No nodes with health issues detected. All systems nominal!'
                                                        : 'No nodes match the current filter.'}
                                            </div>
                                            {(debouncedSearch || filter !== 'all') && (
                                                <button
                                                    onClick={() => {
                                                        setSearchTerm('');
                                                        setFilter('all');
                                                    }}
                                                    className="mt-2 px-4 py-2 bg-x-primary/10 border border-x-primary/30 hover:bg-x-primary/20 text-x-primary rounded-lg text-xs font-bold transition-all"
                                                >
                                                    CLEAR FILTERS
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Footer Attribution */}
            <div className="text-center text-gray-600 font-mono text-[10px] py-8 border-t border-x-border">
                <div className="flex items-center justify-center gap-2 mb-2">
                    <span className="w-1.5 h-1.5 bg-x-primary rounded-full animate-pulse"></span>
                    <span>XANDEUM NEXUS INTELLIGENCE</span>
                </div>
                <div className="text-gray-700">
                    Powered by Xandeum Network • Real-time Gossip Protocol • v1.1.0-SENTINEL
                </div>
            </div>
        </div>
    );
};

// ==========================================
// 🚀 INITIALIZE APPLICATION
// ==========================================

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
