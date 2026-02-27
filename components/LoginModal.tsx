"use client";
import { Github, Mail, User, X } from 'lucide-react';

const LoginModal = ({
  isOpen,
  onClose,
  onLogin,
}: {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (provider: 'google' | 'github') => void;
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 z-100 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-8 relative transform transition-all scale-100">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition"
        >
          <X size={20} />
        </button>

        <div className="text-center mb-8">
          <div className="bg-blue-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-600 ring-4 ring-blue-50">
            <User size={32} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Welcome Back</h2>
          <p className="text-slate-500 mt-2 text-sm">
            Sign in to share your ideas or contribute code
          </p>
        </div>

        <div className="space-y-3">
          <button
            onClick={() => onLogin('google')}
            className="w-full flex items-center justify-center space-x-3 p-3 border border-slate-200 rounded-xl hover:bg-slate-50 hover:border-slate-300 transition font-medium text-slate-700 bg-white"
          >
            <Mail size={20} className="text-red-500" />
            <span>Continue with Google</span>
          </button>
          <button
            onClick={() => onLogin('github')}
            className="w-full flex items-center justify-center space-x-3 p-3 bg-[#24292e] text-white rounded-xl hover:bg-[#2f363d] transition font-medium shadow-md"
          >
            <Github size={20} />
            <span>Continue with GitHub</span>
          </button>
        </div>

        <p className="text-xs text-center text-slate-400 mt-6">
          Note: Logs in as `Blueprint_Core_Team` to test editing.
        </p>
      </div>
    </div>
  );
};

export default LoginModal;
