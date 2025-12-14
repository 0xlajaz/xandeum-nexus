const { useState, useEffect, useMemo } = React;

// --- ICONS & COMPONENTS ---
const DownloadIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
);

const CopyIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
);

const MetricCard = ({ label, value, sub, icon }) => (
    <div className="glass p-5 rounded-xl border-l-2 border-x-primary relative overflow-hidden group hover:border-l-4 transition-all hover:bg-x-panel/80">
        <div className="flex justify-between items-start z-10 relative">
            <div>
                <p className="text-xs text-x-dim uppercase tracking-wider font-bold mb-1">{label}</p>
                <h3 className="text-3xl font-bold text-white neon-text">{value}</h3>
                <p className="text-xs text-x-primary mt-1 font-mono">{sub}</p>
            </div>
            <div className="text-x-primary opacity-50 group-hover:opacity-100 transition-opacity transform group-hover:scale-110 duration-300">
                {icon}
            </div>
        </div>
    </div>
);

const ProgressBar = ({ value, max = 100, color = 'bg-x-primary' }) => (
    <div className="w-full bg-x-border rounded-full h-1.5 mt-2 overflow-hidden">
        <div className={`${color} h-1.5 rounded-full transition-all duration-1000 ease-out`} style={{width: `${Math.min((value/max)*100, 100)}%`}}></div>
    </div>
);

const NodeRow = ({ node }) => {
    const [copied, setCopied] = useState(false);
    const isV7 = node.version.includes('0.7') || node.version.includes('0.8');

    // --- SCORE VARIABLES ---
    const breakdown = node.score_breakdown || {};
    const vScore = breakdown['v0.7_compliance'] || 0;
    const uScore = breakdown.uptime_reliability || 0;
    const sScore = breakdown.storage_weight || 0;
    const pScore = breakdown.paging_efficiency || 0;

    // --- COLOR LOGIC ---
    let statusColor = 'bg-x-danger shadow-[0_0_8px_rgba(255,51,102,0.5)]'; 
    let scoreColor = 'text-x-danger';
    let warningReason = "";

    if (node.health_score > 80) {
        statusColor = 'bg-x-primary shadow-[0_0_8px_#00FFA3]';
        scoreColor = 'text-white';
    } else if (node.health_score >= 60) {
        statusColor = 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.5)]'; 
        scoreColor = 'text-yellow-500';
    }

    if (node.health_score < 60) {
        if (node.uptime_sec < 86400) warningReason = "CRITICAL: Low Uptime (< 24h)";
        else if (!isV7) warningReason = "WARNING: Outdated Version";
        else warningReason = "Check Connection";
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(node.pubkey);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <tr className="border-b border-x-border hover:bg-x-primary/5 transition-colors text-sm group relative">
            <td className="py-4 pl-4">
                <div className="flex items-center gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${statusColor}`}></div>
                    
                    <div 
                        onClick={handleCopy}
                        className="flex items-center gap-2 cursor-pointer group/copy relative px-2 py-1 rounded hover:bg-white/5 transition-all"
                        title="Click to Copy Full ID"
                    >
                        <span className="font-mono text-gray-300 group-hover/copy:text-white transition-colors">
                            {node.short_id}
                        </span>
                        <span className={`text-x-primary transition-all duration-300 ${copied ? 'opacity-100 scale-100' : 'opacity-0 scale-0 group-hover/copy:opacity-50'}`}>
                            {copied ? <span className="text-[10px] font-bold tracking-wider">COPIED!</span> : <CopyIcon />}
                        </span>
                    </div>
                </div>
                {node.health_score < 60 && (
                    <div className="text-[10px] text-x-danger font-mono mt-1 pl-6 uppercase tracking-wide animate-pulse">
                        ⚠️ {warningReason}
                    </div>
                )}
            </td>
            <td className="py-4">
                <span className={`px-2 py-0.5 rounded text-xs font-mono border ${isV7 ? 'border-x-primary/30 text-x-primary bg-x-primary/10' : 'border-x-danger/50 text-x-danger bg-x-danger/10'}`}>
                    {node.version}
                </span>
            </td>
            <td className="py-4 font-mono text-gray-400">
                {(node.uptime_sec / 86400).toFixed(1)}d
            </td>
            <td className="py-4">
                <div className="flex flex-col">
                    <span className="text-white font-medium">{node.storage_gb} GB</span>
                    <span className="text-[10px] text-gray-500">{(node.storage_gb * 1024).toFixed(0)} MB Cached</span>
                </div>
            </td>
            <td className="py-4">
                <div className="w-24">
                    <div className="flex justify-between text-xs mb-1">
                        <span className={node.paging_metrics.hit_rate > 0.9 ? "text-x-primary" : "text-gray-400"}>
                            {(node.paging_metrics.hit_rate * 100).toFixed(0)}%
                        </span>
                    </div>
                    <ProgressBar value={node.paging_metrics.hit_rate * 100} color={node.paging_metrics.hit_rate > 0.9 ? "bg-x-accent" : "bg-x-dim"} />
                </div>
            </td>
            
            <td className="py-4 pr-4 text-right relative">
                <div className="group/score inline-block cursor-help relative">
                    <span className={`text-lg font-bold ${scoreColor}`}>
                        {node.health_score}
                    </span>
                    
                    <div className="absolute right-0 top-full mt-2 w-56 bg-[#0F1219] border border-x-border p-4 rounded-lg shadow-2xl opacity-0 group-hover/score:opacity-100 pointer-events-none transition-all duration-200 z-[100] translate-y-[-10px] group-hover/score:translate-y-0">
                        <div className="text-[10px] font-bold text-gray-400 mb-3 border-b border-white/10 pb-2 tracking-widest uppercase flex justify-between">
                            <span>Breakdown</span>
                        </div>
                        
                        <div className="space-y-2 font-mono text-xs text-left">
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500 flex flex-col leading-none">
                                    Ver <span className="text-[8px] opacity-50 mt-0.5">Target: v0.7+</span>
                                </span>
                                <span className={vScore === 40 ? "text-x-primary" : "text-x-danger"}>+{vScore}</span>
                            </div>

                            <div className="flex justify-between items-center">
                                <span className="text-gray-500 flex flex-col leading-none">
                                    Up <span className="text-[8px] opacity-50 mt-0.5">vs Network Max</span>
                                </span>
                                <span className={uScore > 20 ? "text-white" : "text-x-danger"}>+{uScore}</span>
                            </div>

                            <div className="flex justify-between items-center">
                                <span className="text-gray-500 flex flex-col leading-none">
                                    Sto <span className="text-[8px] opacity-50 mt-0.5">Target: &gt;100MB</span>
                                </span>
                                <span className="text-white">+{sScore}</span>
                            </div>

                            <div className="flex justify-between items-center">
                                <span className="text-gray-500 flex flex-col leading-none">
                                    Page <span className="text-[8px] opacity-50 mt-0.5">Hit Rate</span>
                                </span>
                                <span className="text-x-accent">+{pScore}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </td>
        </tr>
    );
};

const App = () => {
    const [data, setData] = useState(null);
    const [history, setHistory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [filter, setFilter] = useState("all"); 
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 8; 

    const fetchData = async () => {
        try {
            const [telemRes, histRes] = await Promise.all([
                fetch('/api/telemetry'),
                fetch('/api/history/trend')
            ]);
            
            if (!telemRes.ok) throw new Error('API Error');
            
            const telemData = await telemRes.json();
            const histData = await histRes.json();
            
            setData(telemData);
            setHistory(histData);
            setLoading(false);
            
            if (histData.timestamps && document.getElementById('mainChart')) {
                updateChart(histData);
            }
        } catch (e) {
            console.error(e);
            if(loading) setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); 
        return () => clearInterval(interval);
    }, []);

    useEffect(() => { setCurrentPage(1); }, [searchTerm, filter]);

    const updateChart = (histData) => {
        const ctx = document.getElementById('mainChart').getContext('2d');
        if (window.myChart) window.myChart.destroy();
        
        const gradientGreen = ctx.createLinearGradient(0, 0, 0, 400);
        gradientGreen.addColorStop(0, 'rgba(0, 255, 163, 0.2)');
        gradientGreen.addColorStop(1, 'rgba(0, 255, 163, 0)');

        window.myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: histData.timestamps.map(t => new Date(t * 1000).toLocaleTimeString()),
                datasets: [{
                    label: 'Network Health',
                    data: histData.health,
                    borderColor: '#00FFA3',
                    backgroundColor: gradientGreen,
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Paging Efficiency',
                    data: histData.paging_efficiency.map(v => v * 100),
                    borderColor: '#7000FF',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: { 
                    legend: { position: 'top', align: 'end', labels: { color: '#6B7280', font: { size: 10, family: 'JetBrains Mono' }, boxWidth: 10 } },
                    tooltip: { backgroundColor: '#151A23', titleColor: '#fff', bodyColor: '#9CA3AF', borderColor: '#1E2330', borderWidth: 1 }
                },
                scales: {
                    y: { grid: { color: '#1E2330' }, ticks: { color: '#4B5563', font: { size: 10 } } },
                    x: { display: false }
                }
            }
        });
    };

    const handleExport = () => {
        if (!data || !data.nodes) return;
        const csvContent = "data:text/csv;charset=utf-8," 
            + "NodeID,IP,Version,Uptime(sec),Storage(GB),HitRate,HealthScore\n"
            + data.nodes.map(n => 
                `${n.pubkey},${n.ip},${n.version},${n.uptime_sec},${n.storage_gb},${n.paging_metrics.hit_rate},${n.health_score}`
            ).join("\n");
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "xandeum_network_analytics.csv");
        document.body.appendChild(link);
        link.click();
    };

    const filteredNodes = useMemo(() => {
        if (!data) return [];
        return data.nodes.filter(n => {
            const matchesSearch = n.pubkey.toLowerCase().includes(searchTerm.toLowerCase());
            if (filter === 'v0.7') return matchesSearch && n.version.includes('0.7');
            if (filter === 'issues') return matchesSearch && n.health_score < 60;
            return matchesSearch;
        });
    }, [data, searchTerm, filter]);

    const totalPages = Math.ceil(filteredNodes.length / itemsPerPage);
    const paginatedNodes = filteredNodes.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

    if (loading && !data) return (
        <div className="h-screen flex items-center justify-center flex-col gap-4">
            <div className="w-16 h-16 border-4 border-x-border border-t-x-primary rounded-full animate-spin"></div>
            <div className="text-x-primary font-mono text-sm animate-pulse tracking-widest">INITIALIZING SYSTEM...</div>
        </div>
    );

    if (!data) return <div className="h-screen flex items-center justify-center text-red-500 font-mono">CONNECTION LOST. RECONNECTING...</div>;

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-x-border pb-6 gap-4">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-3 h-3 bg-x-primary rounded-full animate-pulse-fast shadow-[0_0_10px_#00FFA3]"></div>
                        <h1 className="text-4xl font-black text-white tracking-tighter">XANDEUM<span className="text-x-primary">NEXUS</span></h1>
                    </div>
                    <p className="text-gray-500 font-mono text-xs md:text-sm tracking-wide">PROFESSIONAL ANALYTICS // <span className="text-x-primary">SYSTEM ONLINE</span></p>
                </div>
                <div className="text-right hidden md:block">
                    <div className="text-2xl font-mono text-white font-bold">{data.network.total_nodes} <span className="text-sm text-gray-500 font-normal">NODES ACTIVE</span></div>
                    <div className="text-xs text-x-dim font-mono">GOSSIP LATENCY: 12ms</div>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard 
                    label="Total Storage" 
                    value={data.network.total_storage_gb.toFixed(2)} 
                    sub="GIGABYTES POOLED"
                    icon={<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>}
                />
                <MetricCard 
                    label="Paging Efficiency" 
                    value={(data.network.avg_paging_efficiency * 100).toFixed(1) + "%"} 
                    sub="AVG HIT RATE"
                    icon={<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>}
                />
                    <MetricCard 
                    label="Protocol Adoption" 
                    value={((data.network.v7_adoption / Math.max(data.network.total_nodes, 1)) * 100).toFixed(0) + "%"} 
                    sub="LATEST VERSION"
                    icon={<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>}
                />
                    <MetricCard 
                    label="Network Health" 
                    value={data.network.avg_health.toFixed(0)} 
                    sub="GLOBAL SCORE"
                    icon={<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg>}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Chart */}
                <div className="lg:col-span-2 glass p-6 rounded-xl border border-white/5">
                    <h3 className="text-white font-bold mb-6 flex items-center gap-2 text-sm tracking-wider">
                        <span className="w-2 h-2 bg-x-primary rounded-full"></span>
                        REAL-TIME NETWORK PERFORMANCE
                    </h3>
                    <div className="h-64 w-full">
                        <canvas id="mainChart"></canvas>
                    </div>
                </div>

                {/* Gossip Visualizer (Simplified) */}
                <div className="glass p-6 rounded-xl border border-white/5 flex flex-col justify-between">
                    <div>
                        <h3 className="text-white font-bold mb-4 text-sm tracking-wider">GOSSIP PROTOCOL STATUS</h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                                <span className="text-gray-400">Update Frequency</span>
                                <span className="text-x-primary font-mono">400ms</span>
                            </div>
                            <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                                <span className="text-gray-400">Packet Size</span>
                                <span className="text-white font-mono">2.4kb</span>
                            </div>
                            <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                                <span className="text-gray-400">Active Entrypoints</span>
                                <span className="text-white font-mono">6/8</span>
                            </div>
                        </div>
                    </div>
                    <div className="mt-6">
                        <div className="text-[10px] text-gray-500 mb-2 uppercase">Live Latency Map</div>
                        <div className="flex gap-1 h-16 items-end bg-black/20 p-2 rounded-lg">
                            {[...Array(15)].map((_, i) => (
                                <div key={i} className="flex-1 bg-x-accent rounded-sm opacity-60 animate-pulse" 
                                        style={{
                                            height: `${Math.random() * 80 + 20}%`,
                                            animationDelay: `${i * 0.1}s`
                                        }}>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="glass rounded-xl overflow-hidden border border-white/5 mb-20 flex flex-col h-[800px]">
                <div className="p-4 border-b border-x-border flex flex-col md:flex-row justify-between items-center gap-4 bg-x-panel/50 shrink-0">
                    <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
                        <button 
                            onClick={() => setFilter('all')} 
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap border ${filter === 'all' ? 'bg-x-primary text-black border-x-primary shadow-[0_0_10px_rgba(0,255,163,0.3)]' : 'bg-white/5 text-gray-400 border-transparent hover:border-white/20 hover:text-white'}`}
                        >
                            ALL NODES ({data ? data.nodes.length : 0})
                        </button>
                        
                        <button 
                            onClick={() => setFilter('v0.7')} 
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap border ${filter === 'v0.7' ? 'bg-x-primary/20 text-x-primary border-x-primary' : 'bg-white/5 text-gray-400 border-transparent hover:border-white/20 hover:text-white'}`}
                        >
                            VERIFIED v0.7
                        </button>
                        
                        <button 
                            onClick={() => setFilter('issues')} 
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap border flex items-center gap-2 ${filter === 'issues' ? 'bg-x-danger text-white border-x-danger shadow-[0_0_10px_rgba(255,51,102,0.4)]' : 'bg-white/5 text-gray-400 border-transparent hover:border-x-danger/50 hover:text-x-danger'}`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                            SHOW ISSUES
                        </button>
                    </div>
                    
                    <div className="flex gap-3 w-full md:w-auto">
                        <div className="relative flex-grow">
                            <input 
                                type="text" 
                                placeholder="SEARCH ID..." 
                                className="w-full bg-black/40 text-xs px-4 py-2 rounded-lg border border-x-border focus:border-x-primary outline-none text-white transition-all placeholder-gray-600"
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <button onClick={handleExport} className="px-4 py-2 bg-x-accent/10 border border-x-accent/50 hover:bg-x-accent/20 text-x-accent rounded-lg text-xs font-bold transition-all flex items-center gap-2">
                            <DownloadIcon /> CSV
                        </button>
                    </div>
                </div>
                
                <div className="overflow-auto custom-scroll flex-grow"> 
                    <table className="w-full text-left border-collapse relative">
                        <thead className="bg-[#0F1219] sticky top-0 z-20 text-[10px] uppercase text-gray-500 font-bold tracking-wider shadow-lg">
                            <tr>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">Node Identity</th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">Client Ver</th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">Uptime</th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">Capacity</th>
                                <th className="px-4 py-3 border-b border-white/10 bg-[#0F1219]">Performance</th>
                                <th className="px-4 py-3 text-right border-b border-white/10 bg-[#0F1219]">Score</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {filteredNodes.map(node => (
                                <NodeRow key={node.pubkey} node={node} />
                            ))}
                            
                            {filteredNodes.length === 0 && (
                                <tr><td colSpan="6" className="p-12 text-center text-gray-500 font-mono text-sm">NO NODES MATCHING CRITERIA</td></tr>
                            )}
                            
                            {filteredNodes.length > 0 && (
                                <tr><td colSpan="6" className="p-4 text-center text-gray-600 font-mono text-[10px] uppercase tracking-widest opacity-50">End of Network List</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);