"use client";
import type React from 'react';

const SectionHeader = ({
  num,
  title,
  icon,
  activeSection,
  setActiveSection,
}: {
  num: number;
  title: string;
  icon: React.ReactNode;
  activeSection: number;
  setActiveSection: (num: number) => void;
}) => (
  <div
    onClick={() => setActiveSection(num)}
    className={`flex items-center justify-between p-4 cursor-pointer transition ${
      activeSection === num
        ? 'bg-blue-50 border-l-4 border-blue-500'
        : 'bg-white hover:bg-slate-50 border-l-4 border-transparent'
    }`}
  >
    <div className="flex items-center space-x-3">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
          activeSection === num
            ? 'bg-blue-600 text-white'
            : 'bg-slate-200 text-slate-600'
        }`}
      >
        {num}
      </div>
      <div className="flex flex-col">
        <span
          className={`text-sm font-bold ${
            activeSection === num ? 'text-blue-800' : 'text-slate-700'
          }`}
        >
          {title}
        </span>
      </div>
    </div>
    <div className="text-slate-400">{icon}</div>
  </div>
);

export default SectionHeader;
