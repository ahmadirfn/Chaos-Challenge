import { useEffect, useState } from 'react'
import {
  Activity, ArrowUpRight, AudioLines, Bolt, Check, ChevronDown,
  CircleHelp, Clock3, Gamepad2, History, LayoutDashboard, Menu,
  Radio, Settings2, ShieldCheck, Sparkles, Twitch, Users, Wifi, WifiOff,
  X,
} from 'lucide-react'
import { getHealth, type HealthResponse } from './services/api'

type HealthState = { data: HealthResponse | null; error: string | null; loading: boolean }

const steps = [
  { name: 'Project foundation', detail: 'Dashboard, API and local database', complete: true },
  { name: 'Chaos engine', detail: 'Rounds, voting and challenge memory', complete: true },
  { name: 'Local AI + Twitch', detail: 'Ollama generation and live chat', complete: false },
  { name: 'Live stream experience', detail: 'Controls, overlay and demo mode', complete: false },
]

function App() {
  const [health, setHealth] = useState<HealthState>({ data: null, error: null, loading: true })
  const [mobileMenu, setMobileMenu] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    async function refresh() {
      try {
        const data = await getHealth(controller.signal)
        setHealth({ data, error: null, loading: false })
      } catch (error) {
        if (!controller.signal.aborted) {
          setHealth({ data: null, error: error instanceof Error ? error.message : 'Connection failed', loading: false })
        }
      }
    }
    void refresh()
    const timer = window.setInterval(() => void refresh(), 10000)
    return () => { controller.abort(); window.clearInterval(timer) }
  }, [])

  const online = health.data?.status === 'ok'

  return (
    <div className="app-shell min-h-screen text-slate-100">
      <aside className={`sidebar ${mobileMenu ? 'sidebar-open' : ''}`}>
        <div className="flex items-center justify-between px-6 pt-7 pb-8">
          <div className="flex items-center gap-3">
            <div className="brand-mark"><Bolt size={23} fill="currentColor" strokeWidth={2.5} /></div>
            <div><div className="font-black tracking-tight leading-none text-[17px]">CHAOS<span className="text-violet-400">.</span></div><div className="text-[10px] font-bold tracking-[0.25em] text-slate-500 mt-1">DIRECTOR</div></div>
          </div>
          <button className="lg:hidden text-slate-400" aria-label="Close menu" onClick={() => setMobileMenu(false)}><X size={20} /></button>
        </div>
        <div className="px-4">
          <div className="nav-caption">WORKSPACE</div>
          <div className="nav-item nav-active"><LayoutDashboard size={18} /> Dashboard <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400" /></div>
          <div className="nav-item nav-disabled"><History size={18} /> Chaos history <span className="soon">SOON</span></div>
          <div className="nav-item nav-disabled"><Activity size={18} /> Activity feed <span className="soon">SOON</span></div>
          <div className="nav-caption mt-9">STREAM TOOLS</div>
          <div className="nav-item nav-disabled"><Radio size={18} /> OBS overlay <span className="soon">SOON</span></div>
          <div className="nav-item nav-disabled"><Settings2 size={18} /> Settings <span className="soon">SOON</span></div>
        </div>
        <div className="mt-auto px-4 pb-6">
          <div className="sidebar-help"><CircleHelp size={18} className="text-violet-300" /><div><div className="text-sm font-semibold">Phase 2 core engine</div><div className="text-xs text-slate-400 mt-1">Rounds and voting are available through the local API.</div></div></div>
          <div className="flex items-center gap-2 px-2 pt-5 text-xs text-slate-500"><ShieldCheck size={15} /> Local-first development</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="flex items-center gap-3"><button className="lg:hidden text-slate-400" aria-label="Open menu" onClick={() => setMobileMenu(true)}><Menu size={22} /></button><span className="text-slate-500">Workspace</span><span className="text-slate-700">/</span><span className="font-semibold text-slate-200">Dashboard</span></div>
          <div className="flex items-center gap-3"><span className="hidden sm:inline text-xs text-slate-500">LOCAL DEVELOPMENT</span><div className={`top-status ${online ? 'top-status-online' : ''}`}><span className={`status-dot ${online ? 'bg-emerald-400' : 'bg-amber-400'}`} />{health.loading ? 'Checking API' : online ? 'System online' : 'API offline'}</div></div>
        </header>

        <div className="content-wrap">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-5 mb-8">
            <div><div className="eyebrow"><Sparkles size={14} /> YOUR STREAM COMMAND CENTER</div><h1 className="page-title">Run the show<span className="text-violet-400">.</span></h1><p className="text-slate-400 mt-2 max-w-xl">Turn audience energy into unforgettable stream moments.</p></div>
            <div className="phase-tag"><span className="h-2 w-2 rounded-full bg-cyan-400" /> PHASE 02 <span className="text-slate-600">/</span> CORE ENGINE</div>
          </div>

          <section className="hero-card mb-6" aria-label="Welcome">
            <div className="hero-orb hero-orb-one" /><div className="hero-orb hero-orb-two" />
            <div className="relative z-10 max-w-2xl"><div className="hero-kicker"><AudioLines size={17} /> THE NEXT GENERATION OF INTERACTIVE STREAMING</div><h2 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight mt-4">Your stream. Their choices.<br /><span className="hero-gradient">AI-powered chaos.</span></h2><p className="mt-4 text-sm sm:text-base text-slate-300 max-w-lg leading-relaxed">The core engine now runs rounds, voting and challenge memory through the API. AI, Twitch chat and OBS are coming next.</p><div className="flex flex-wrap gap-3 mt-7"><span className="hero-pill"><Check size={15} /> Persistent rounds</span><span className="hero-pill"><Check size={15} /> Vote tracking</span><span className="hero-pill"><Check size={15} /> No credentials needed</span></div></div>
            <div className="hero-emblem"><Bolt size={84} fill="currentColor" strokeWidth={1.5} /></div>
          </section>

          <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
            <div className="space-y-5">
              <section className="panel p-6 sm:p-7">
                <div className="section-heading"><div><div className="section-icon"><Gamepad2 size={20} /></div><h2>Stream configuration</h2><p>Shape the kind of chaos your audience creates.</p></div><span className="section-badge">UI CONTROLS IN PHASE 5</span></div>
                <div className="grid sm:grid-cols-2 gap-4 mt-7">
                  <div><label className="field-label">STREAM MODE</label><div className="select-preview"><Gamepad2 size={18} className="text-violet-400" /><span>Gaming</span><ChevronDown size={16} className="ml-auto text-slate-500" /></div></div>
                  <div><label className="field-label">CHAOS INTENSITY</label><div className="select-preview"><Bolt size={18} className="text-cyan-400" /><span>Balanced</span><ChevronDown size={16} className="ml-auto text-slate-500" /></div></div>
                  <div><label className="field-label">VOTING DURATION</label><div className="select-preview"><Clock3 size={18} className="text-violet-400" /><span>60 seconds</span><ChevronDown size={16} className="ml-auto text-slate-500" /></div></div>
                  <div><label className="field-label">AUDIENCE</label><div className="select-preview"><Users size={18} className="text-cyan-400" /><span>Twitch chat</span><ChevronDown size={16} className="ml-auto text-slate-500" /></div></div>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-7 pt-6 border-t border-white/[.07]"><div className="text-sm text-slate-500">Use the API docs for Phase 2 controls. Dashboard controls arrive in Phase 5.</div><button className="primary-button" disabled><Sparkles size={17} /> Generate challenges <ArrowUpRight size={16} /></button></div>
              </section>
              <section className="panel p-6 sm:p-7"><div className="flex items-center justify-between"><div><h2 className="font-bold text-lg">Challenge arena</h2><p className="text-sm text-slate-500 mt-1">Challenge cards will appear here in Phase 5.</p></div><span className="mini-badge">API READY</span></div><div className="empty-state mt-6"><div className="empty-icon"><Sparkles size={27} /></div><div className="font-semibold mt-4">The engine is ready</div><p className="text-sm text-slate-500 mt-1">Try a full round in the local API docs at /docs.</p></div></section>
            </div>

            <div className="space-y-5">
              <section className="panel p-6"><div className="flex items-center justify-between"><h2 className="font-bold text-lg">System status</h2><Activity size={18} className="text-slate-500" /></div><div className="status-row mt-6"><div className="status-icon"><Wifi size={17} /></div><div><div className="font-medium text-sm">Backend API</div><div className="text-xs text-slate-500 mt-0.5">127.0.0.1:8000</div></div><span className={`ml-auto status-label ${online ? 'text-emerald-300' : 'text-amber-300'}`}>{health.loading ? 'CHECKING' : online ? 'ONLINE' : 'OFFLINE'}</span></div><div className="status-row"><div className="status-icon"><ShieldCheck size={17} /></div><div><div className="font-medium text-sm">SQLite database</div><div className="text-xs text-slate-500 mt-0.5">Local data storage</div></div><span className={`ml-auto status-label ${online ? 'text-emerald-300' : 'text-amber-300'}`}>{online ? 'READY' : 'UNKNOWN'}</span></div><div className="status-row"><div className="status-icon"><Twitch size={17} /></div><div><div className="font-medium text-sm">Twitch channel</div><div className="text-xs text-slate-500 mt-0.5">Integration in Phase 4</div></div><span className="ml-auto status-label text-slate-500">NOT SET UP</span></div>{health.error && <div role="alert" className="error-box"><WifiOff size={16} /> {health.error}. Start the backend with the README command.</div>}</section>
              <section className="panel p-6"><div className="flex items-center justify-between"><h2 className="font-bold text-lg">Build progress</h2><span className="text-xs font-semibold text-violet-300">2 OF 4</span></div><div className="progress-track mt-5"><div className="progress-fill" /></div><div className="mt-6 space-y-5">{steps.map((step, index) => <div className="flex items-start gap-3" key={step.name}><div className={`step-number ${step.complete ? 'step-complete' : ''}`}>{step.complete ? <Check size={15} /> : `0${index + 1}`}</div><div><div className={`text-sm font-semibold ${step.complete ? 'text-slate-100' : 'text-slate-400'}`}>{step.name}</div><p className="text-xs text-slate-500 mt-1">{step.detail}</p></div></div>)}</div></section>
              <div className="tip-card"><div className="flex items-center gap-2 text-cyan-300 font-semibold text-sm"><Sparkles size={16} /> BUILT FOR THE MOMENT</div><p className="text-sm text-slate-400 mt-2 leading-relaxed">Every great stream starts somewhere. Your control room is ready for its first challenge.</p></div>
            </div>
          </div>
          <footer className="text-center text-xs text-slate-600 py-10">CHAOS DIRECTOR <span className="mx-2">•</span> Your Stream. Their Choices. AI-Powered Chaos.</footer>
        </div>
      </main>
    </div>
  )
}

export default App

