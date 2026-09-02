import React, { useState, useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

// --- MOCK DATA ---
const MOCK_EVENTS = [
  { entity_type: 'payment', entity_id: 'pay_H9zL2x', root_cause: 'bank_decline', diagnosis_confidence: 0.94, action: 'send_payment_link', compliance_result: 'allow', channel: 'whatsapp', outcome: 'recovered', amount: 1499, recovered_at: '2026-09-02T14:32:00Z' },
  { entity_type: 'subscription', entity_id: 'sub_G8aM1q', root_cause: 'insufficient_funds', diagnosis_confidence: 0.88, action: 'schedule_retry', compliance_result: 'allow', channel: 'system', outcome: 'pending', amount: 499, recovered_at: null },
  { entity_type: 'payment', entity_id: 'pay_F7xK0p', root_cause: 'card_expired', diagnosis_confidence: 0.99, action: 'prompt_card_update', compliance_result: 'block: max_contacts_reached', channel: 'email', outcome: 'held', amount: 8900, recovered_at: null },
  { entity_type: 'invoice', entity_id: 'inv_J2bN4w', root_cause: 'gateway_timeout', diagnosis_confidence: 0.76, action: 'silent_retry', compliance_result: 'allow', channel: 'system', outcome: 'recovered', amount: 25000, recovered_at: '2026-09-02T14:15:22Z' },
  { entity_type: 'payment', entity_id: 'pay_M5vC9s', root_cause: 'fraud_suspicion', diagnosis_confidence: 0.65, action: 'escalate_to_human', compliance_result: 'allow', channel: 'dashboard', outcome: 'pending', amount: 45000, recovered_at: null },
];

const PROMISES_TO_PAY = [
  { id: 'usr_T92', amount: 12500, date: '2026-09-04' },
  { id: 'usr_X14', amount: 3499, date: '2026-09-05' },
];

const PIPELINE_NODES = ['Diagnosis', 'Strategy', 'Compliance Gate', 'Execution', 'Escalation'];

// --- COMPONENTS ---

const RippleIntro = ({ children }: { children: React.ReactNode }) => {
  const prefersReducedMotion = useReducedMotion();
  const [animating, setAnimating] = useState(!prefersReducedMotion);

  useEffect(() => {
    if (!prefersReducedMotion) {
      const t = setTimeout(() => setAnimating(false), 2500);
      return () => clearTimeout(t);
    }
  }, [prefersReducedMotion]);

  if (!animating) return <>{children}</>;

  return (
    <div className="relative min-h-screen">
      <svg width="0" height="0" className="absolute pointer-events-none">
        <filter id="liquid-distortion">
          <feTurbulence type="fractalNoise" baseFrequency="0.01 0.05" numOctaves="1" result="noise">
            <animate attributeName="baseFrequency" values="0.08 0.15; 0 0" dur="2.4s" calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1" fill="freeze" />
          </feTurbulence>
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="30" xChannelSelector="R" yChannelSelector="G">
            <animate attributeName="scale" values="60; 0" dur="2.4s" calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1" fill="freeze" />
          </feDisplacementMap>
        </filter>
      </svg>
      <div style={{ filter: 'url(#liquid-distortion)' }} className="h-full">
        {children}
      </div>
    </div>
  );
};

const LiquidGauge = ({ percentage }: { percentage: number }) => {
  const prefersReducedMotion = useReducedMotion();
  
  return (
    <div className="relative w-16 h-16 rounded-full border-2 border-neutral-800 overflow-hidden bg-neutral-900 flex items-center justify-center shrink-0">
      <motion.div 
        className="absolute bottom-0 left-0 right-0 bg-agent opacity-80"
        initial={{ height: '0%' }}
        animate={{ height: `${percentage}%` }}
        transition={{ duration: prefersReducedMotion ? 0 : 2.5, ease: "easeOut" }}
      >
        <svg viewBox="0 0 100 20" className="absolute -top-4 w-[200%] h-4 animate-wave fill-agent opacity-80" style={{ marginLeft: '-50%' }}>
          {/* Simple wave path */}
          <path d="M0,10 C25,20 25,0 50,10 C75,20 75,0 100,10 L100,20 L0,20 Z" />
        </svg>
      </motion.div>
      <span className="relative z-10 font-mono text-sm text-white font-medium">{percentage}%</span>
      <style>{`
        @keyframes wave {
          0% { transform: translateX(0); }
          100% { transform: translateX(50%); }
        }
        .animate-wave {
          animation: wave 3s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default function App() {
  const [activeNodeIndex, setActiveNodeIndex] = useState(0);
  const [metrics, setMetrics] = useState({
    at_risk: 892400,
    recovered: 142390,
    recovery_rate: 15.9,
    processed: 1204
  });
  const [events, setEvents] = useState(MOCK_EVENTS);

  // Poll backend APIs
  useEffect(() => {
    const fetchData = async () => {
      try {
        const metRes = await fetch("http://localhost:8000/api/metrics");
        if (metRes.ok) {
          const data = await metRes.json();
          setMetrics(data);
        }
        
        const evtRes = await fetch("http://localhost:8000/api/events");
        if (evtRes.ok) {
          const newEvents = await evtRes.json();
          // We keep a rolling window of events
          setEvents(prev => [...newEvents, ...prev].slice(0, 6));
        }
      } catch (e) {
        // Fallback to mock data if backend isn't reachable
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Simulate active node pulsing
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveNodeIndex(prev => (prev + 1) % PIPELINE_NODES.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <RippleIntro>
      <div className="min-h-screen bg-base p-6 md:p-12 text-neutral-400">
        
        {/* Header */}
        <header className="mb-12 flex justify-between items-end">
          <div>
            <h1 className="font-sans text-3xl font-bold text-white tracking-tight">Autonomous Revenue Sentinel</h1>
            <p className="font-mono text-xs mt-2 text-neutral-400">System status: Active monitoring</p>
          </div>
        </header>

        {/* Pipeline Node Graph */}
        <section className="mb-12 border-b border-neutral-800 pb-8">
          <div className="flex items-center gap-4 overflow-x-auto">
            {PIPELINE_NODES.map((node, i) => (
              <React.Fragment key={node}>
                <div className={`font-mono text-xs px-3 py-1.5 rounded-sm border transition-colors duration-500 whitespace-nowrap
                  ${i === activeNodeIndex ? 'border-agent text-agent bg-agent/10' : 'border-neutral-800 text-neutral-500 bg-neutral-900'}
                `}>
                  {node}
                </div>
                {i < PIPELINE_NODES.length - 1 && (
                  <div className={`h-px w-8 transition-colors duration-500 ${i === activeNodeIndex ? 'bg-agent' : 'bg-neutral-800'}`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </section>

        {/* Hero Metrics */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="p-5 border border-neutral-800 bg-neutral-900 flex flex-col justify-between">
            <span className="font-sans text-sm text-neutral-500 mb-4 block">Revenue at risk</span>
            <span className="font-mono text-2xl text-white">₹{metrics.at_risk.toLocaleString()}</span>
          </div>
          <div className="p-5 border border-neutral-800 bg-neutral-900 flex flex-col justify-between">
            <span className="font-sans text-sm text-neutral-500 mb-4 block">Successfully recovered</span>
            <span className="font-mono text-3xl text-money">₹{metrics.recovered.toLocaleString()}</span>
          </div>
          <div className="p-5 border border-neutral-800 bg-neutral-900 flex items-center justify-between">
            <div>
              <span className="font-sans text-sm text-neutral-500 mb-4 block">Recovery rate</span>
              <span className="font-mono text-xl text-white">{metrics.recovery_rate.toFixed(1)}%</span>
            </div>
            <LiquidGauge percentage={Math.round(metrics.recovery_rate)} />
          </div>
          <div className="p-5 border border-neutral-800 bg-neutral-900 flex flex-col justify-between">
            <span className="font-sans text-sm text-neutral-500 mb-4 block">Transactions processed</span>
            <span className="font-mono text-2xl text-white">{metrics.processed.toLocaleString()}</span>
          </div>
        </section>

        {/* Lower Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Feed */}
          <section className="lg:col-span-2">
            <h2 className="font-sans text-lg text-white mb-4">Live Event Feed</h2>
            <div className="border border-neutral-800 bg-neutral-900">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-neutral-800">
                    <th className="font-mono text-xs text-neutral-500 font-normal p-4">Entity</th>
                    <th className="font-mono text-xs text-neutral-500 font-normal p-4">Root Cause</th>
                    <th className="font-mono text-xs text-neutral-500 font-normal p-4">Action Taken</th>
                    <th className="font-mono text-xs text-neutral-500 font-normal p-4 text-right">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((evt, i) => (
                    <tr key={i} className="border-b border-neutral-800/50 last:border-0 hover:bg-neutral-800/20 transition-colors">
                      <td className="p-4 font-mono text-xs text-white">
                        {evt.entity_id}
                        <div className="text-neutral-500 mt-1 opacity-70">{evt.entity_type}</div>
                      </td>
                      <td className="p-4 font-mono text-xs text-neutral-300">
                        {evt.root_cause}
                        <div className="text-agent mt-1 opacity-80">conf: {evt.diagnosis_confidence.toFixed(2)}</div>
                      </td>
                      <td className="p-4 font-mono text-xs">
                        {evt.compliance_result.startsWith('block') ? (
                          <span className="text-neutral-500">held: {evt.compliance_result.split(': ')[1]}</span>
                        ) : (
                          <span className="text-white">{evt.action}</span>
                        )}
                        <div className="text-neutral-500 mt-1 opacity-70">via {evt.channel}</div>
                      </td>
                      <td className="p-4 font-mono text-xs text-right">
                        <span className={evt.outcome === 'recovered' ? 'text-money' : 'text-neutral-400'}>
                          ₹{evt.amount.toLocaleString()}
                        </span>
                        <div className="text-neutral-500 mt-1 opacity-70">
                          {evt.outcome}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Sidebar */}
          <aside className="space-y-8">
            <section>
              <h2 className="font-sans text-lg text-white mb-4">Promises to Pay</h2>
              <div className="border border-neutral-800 bg-neutral-900 p-4 space-y-3">
                {PROMISES_TO_PAY.map((ptp, i) => (
                  <div key={i} className="flex justify-between items-center font-mono text-xs">
                    <span className="text-white">{ptp.id}</span>
                    <span className="text-neutral-400">{ptp.date}</span>
                    <span className="text-money">₹{ptp.amount.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </section>

            <section>
              <h2 className="font-sans text-lg text-white mb-4">Diagnostics</h2>
              <div className="border border-neutral-800 bg-neutral-900 p-4 space-y-4">
                <div>
                  <div className="flex justify-between font-mono text-xs mb-2">
                    <span className="text-neutral-300">bank_decline</span>
                    <span className="text-neutral-500">42%</span>
                  </div>
                  <div className="w-full bg-neutral-800 h-1">
                    <div className="bg-agent h-1" style={{ width: '42%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between font-mono text-xs mb-2">
                    <span className="text-neutral-300">insufficient_funds</span>
                    <span className="text-neutral-500">28%</span>
                  </div>
                  <div className="w-full bg-neutral-800 h-1">
                    <div className="bg-agent h-1" style={{ width: '28%' }}></div>
                  </div>
                </div>
              </div>
            </section>
          </aside>

        </div>
      </div>
    </RippleIntro>
  );
}
