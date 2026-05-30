/**
 * PaperNest sidebar navigation. Branding components ada di
 * `./PaperNestLogo` — re-export di sini untuk backward compat dengan
 * import-an lama: `import { PaperNestIcon } from "@/components/SideNav"`.
 */
import { X } from "lucide-react"
import { useAuthStore } from "@/stores/authStore"
import {
  PaperNestIcon,
  PaperNestLogoFull,
  PaperLensLogo,
} from "./PaperNestLogo"

export { PaperNestIcon, PaperNestLogoFull, PaperLensLogo }

/**
 * Slim left sidebar navigation — OpenAlex-style
 * Fixed position, contains: logo, new-search button, and bottom login icon.
 */
export function SideNav({ 
  onLogoClick, 
  onSearchClick,
  onLoginClick 
}: { 
  onLogoClick?: () => void; 
  onSearchClick?: () => void;
  onLoginClick?: () => void;
}) {
  const { isAuthenticated, user, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
    window.location.href = '/' // Redirect to home after logout
  }

  return (
    <nav className="fixed left-0 top-0 z-50 hidden md:flex h-screen w-16 flex-col items-center border-r border-border bg-background py-4">
      {/* Logo */}
      <button
        onClick={onLogoClick}
        className="flex h-8 w-8 items-center justify-center transition-opacity hover:opacity-60"
        aria-label="PaperNest Home"
      >
        <PaperNestIcon className="h-7 w-7" />
      </button>

      {/* New search */}
      <button
        onClick={onSearchClick}
        className="mt-4 flex h-7 w-7 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        aria-label="New search"
        title="New search"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="h-4 w-4">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </button>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Login / Logout icon */}
      {isAuthenticated ? (
        <button
          onClick={handleLogout}
          className="mb-2 flex h-7 w-7 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          aria-label="Logout"
          title={`Logout (${user?.email})`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </button>
      ) : (
        <button
          onClick={onLoginClick}
          className="mb-2 flex h-7 w-7 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          aria-label="Sign in"
          title="Sign in"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
            <polyline points="10 17 15 12 10 7" />
            <line x1="15" y1="12" x2="3" y2="12" />
          </svg>
        </button>
      )}
    </nav>
  )
}

/**
 * Mobile navigation overlay
 */
export function MobileNav({ 
  isOpen, 
  onClose, 
  onLogoClick, 
  onSearchClick,
  onLoginClick
}: { 
  isOpen: boolean; 
  onClose: () => void;
  onLogoClick?: () => void;
  onSearchClick?: () => void;
  onLoginClick?: () => void;
}) {
  const { isAuthenticated, user, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
    onClose()
    window.location.href = '/'
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex md:hidden">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />
      
      {/* Menu content */}
      <div className="relative flex h-full w-64 flex-col bg-background border-r border-border p-6 shadow-xl animate-in slide-in-from-left duration-200">
        <div className="flex items-center justify-between mb-8">
          <PaperNestLogoFull className="h-7" />
          <button onClick={onClose} className="p-1 rounded-md hover:bg-accent text-muted-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-col gap-4">
          <button 
            onClick={() => { onLogoClick?.(); onClose(); }}
            className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-accent text-[15px] font-medium"
          >
            <PaperNestIcon className="h-5 w-5" />
            Home
          </button>
          <button 
            onClick={() => { onSearchClick?.(); onClose(); }}
            className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-accent text-[15px] font-medium"
          >
            <div className="flex h-5 w-5 items-center justify-center rounded border border-current">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-3 w-3">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </div>
            New Search
          </button>
        </nav>

        <div className="mt-auto pt-6 border-t border-border">
          {isAuthenticated ? (
            <div className="space-y-3">
              <div className="px-4 py-2 text-sm text-muted-foreground">
                {user?.email}
              </div>
              <button 
                onClick={handleLogout}
                className="flex w-full items-center gap-3 px-4 py-3 rounded-lg hover:bg-accent text-[15px] font-medium text-destructive"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Logout
              </button>
            </div>
          ) : (
            <button 
              onClick={() => { onLoginClick?.(); onClose(); }}
              className="flex w-full items-center gap-3 px-4 py-3 rounded-lg hover:bg-accent text-[15px] font-medium text-muted-foreground"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                <polyline points="10 17 15 12 10 7" />
                <line x1="15" y1="12" x2="3" y2="12" />
              </svg>
              Sign in
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

