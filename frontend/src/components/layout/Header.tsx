import { useAuthStore } from '@/stores/authStore';
import { useAppStore } from '@/stores/appStore';

export function Header() {
  const { user, logout } = useAuthStore();
  const { toggleSidebar, sidebarOpen } = useAppStore();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 sticky top-0 z-30">
      {/* Left */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>
        <span className="text-sm text-gray-500">
          {sidebarOpen ? '' : '智家管家AI'}
        </span>
      </div>

      {/* Right */}
      <div className="flex items-center gap-4">
        {/* Notification placeholder */}
        <button className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-400 relative">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
          </svg>
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* User menu */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div className="hidden sm:block text-sm">
            <p className="font-medium text-gray-900">{user?.name || '用户'}</p>
            <p className="text-xs text-gray-500">{user?.role === 'admin' ? '管理员' : user?.role || ''}</p>
          </div>
          <button
            onClick={logout}
            className="ml-2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-red-500"
            title="退出登录"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
