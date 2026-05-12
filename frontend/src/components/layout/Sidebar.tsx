import {NavLink} from 'react-router-dom'
import {LayoutDashboard, Settings, Workflow} from 'lucide-react'

export function Sidebar() {
  return (
    <nav className="w-64 bg-surface-container flex flex-col h-full border-r border-outline-variant/20">
      <div className="p-6">
        <h1 className="font-headline text-2xl text-on-surface tracking-tight uppercase">BlockBT</h1>
      </div>

      <div className="flex-1 px-4 space-y-2 mt-4">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container-high transition-colors text-left group cursor-not-allowed opacity-50">
          <LayoutDashboard className="w-5 h-5 group-hover:text-on-surface transition-colors" />
          <span className="font-label text-sm font-medium group-hover:text-on-surface transition-colors">Dashboard (Soon)</span>
        </button>

        <NavLink 
            to="/" 
            className={({ isActive }) => 
                `w-full flex items-center gap-3 px-4 py-3 text-left relative transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'}`
            }
        >
          {({ isActive }) => (
            <>
              {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_10px_rgba(129,236,255,0.5)]"></div>}
              <Workflow className="w-5 h-5" />
              <span className="font-label text-sm font-medium">Visual Builder</span>
            </>
          )}
        </NavLink>

        <NavLink 
            to="/settings" 
            className={({ isActive }) => 
                `w-full flex items-center gap-3 px-4 py-3 text-left relative transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'}`
            }
        >
          {({ isActive }) => (
            <>
              {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_10px_rgba(129,236,255,0.5)]"></div>}
              <Settings className="w-5 h-5" />
              <span className="font-label text-sm font-medium">Settings</span>
            </>
          )}
        </NavLink>

      </div>

      <div className="p-6 mt-auto">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-surface-container-highest flex items-center justify-center border border-outline-variant/30">
            <span className="font-headline text-on-surface font-bold text-xs">BT</span>
          </div>
          <div>
            <p className="font-label text-xs font-medium text-on-surface">BlockBT Local</p>
            <p className="font-label text-[10px] text-on-surface-variant">Air-Gapped</p>
          </div>
        </div>
      </div>
    </nav>
  )
}
