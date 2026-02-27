"use client";
import { ChevronDown, Edit3 } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { RequirementSection } from '../types';
import SectionEditorModal from './SectionEditorModal';

const RequirementViewer = ({
  sections,
  isOwner,
  onUpdateSection,
}: {
  sections: RequirementSection[];
  isOwner: boolean;
  onUpdateSection: (section: RequirementSection) => void;
}) => {
  const [localSections, setLocalSections] = useState(sections);
  const [editingSection, setEditingSection] = useState<RequirementSection | null>(
    null
  );

  useEffect(() => {
    setLocalSections(sections);
  }, [sections]);

  const toggleSection = (id: string) => {
    setLocalSections((prev) =>
      prev.map((s) => (s.id === id ? { ...s, isExpanded: !s.isExpanded } : s))
    );
  };

  const handleEditClick = (section: RequirementSection, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSection(section);
  };

  return (
    <div className="space-y-4">
      {localSections.map((section) => (
        <div
          key={section.id}
          className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm hover:border-blue-200 transition"
        >
          <div
            className={`flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition ${
              section.isExpanded ? 'border-b border-slate-100' : ''
            }`}
            onClick={() => toggleSection(section.id)}
          >
            <div className="flex items-center space-x-3 font-bold text-slate-800">
              <div
                className={`text-slate-400 transition-transform duration-200 ${
                  section.isExpanded ? 'rotate-0' : '-rotate-90'
                }`}
              >
                <ChevronDown size={18} />
              </div>
              <span className="text-blue-600">{section.icon}</span>
              <span>{section.title}</span>
            </div>
            {isOwner && (
              <button
                onClick={(e) => handleEditClick(section, e)}
                className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-slate-500 bg-slate-100 hover:text-blue-600 hover:bg-blue-50 rounded-full transition"
                title="Edit this section"
              >
                <Edit3 size={14} />
                <span className="hidden sm:inline">Edit</span>
              </button>
            )}
          </div>

          {section.isExpanded && (
            <div className="p-5 bg-slate-50/50 space-y-4 animate-in slide-in-from-top-1 duration-200">
              {section.fields.map((field) => (
                <div
                  key={field.id}
                  className="grid grid-cols-1 md:grid-cols-4 gap-2 md:gap-4 border-b border-slate-100 last:border-0 pb-3 last:pb-0"
                >
                  <div className="text-sm font-semibold text-slate-600 md:text-right pt-1">
                    {field.label}
                  </div>
                  <div className="md:col-span-3 text-sm text-slate-800">
                    {Array.isArray(field.value) ? (
                      field.value.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 pl-2">
                          {field.value.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-slate-400 italic">Not specified</span>
                      )
                    ) : field.value ? (
                      <p className="whitespace-pre-wrap">{field.value}</p>
                    ) : (
                      <span className="text-slate-400 italic">Not specified</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}

      {editingSection && (
        <SectionEditorModal
          isOpen={true}
          onClose={() => setEditingSection(null)}
          section={editingSection}
          onSubmit={(updated) => {
            onUpdateSection(updated);
            setEditingSection(null);
          }}
        />
      )}
    </div>
  );
};

export default RequirementViewer;
