import { useToastStore } from '@/stores/toastStore';

const typeStyles = {
  success: 'bg-green-600',
  error: 'bg-red-600',
  info: 'bg-blue-600',
  warning: 'bg-yellow-500 text-gray-900',
};

const typeIcons = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
  warning: '⚠',
};

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-white text-sm min-w-[280px] max-w-[400px] animate-slide-up ${typeStyles[t.type]}`}
          onClick={() => removeToast(t.id)}
        >
          <span className="font-bold text-base">{typeIcons[t.type]}</span>
          <span className="flex-1">{t.message}</span>
          <button className="ml-2 opacity-70 hover:opacity-100 text-lg leading-none">&times;</button>
        </div>
      ))}
    </div>
  );
}
