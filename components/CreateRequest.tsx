"use client";
import {
  AlertCircle,
  BookOpen,
  Box,
  CheckCircle,
  Lock,
  Shield,
  Target,
  Trash2,
  Users,
  X,
  Zap,
} from 'lucide-react';
import { useState } from 'react';
import type { CreateRequestFormData } from '../types';
import SectionHeader from './SectionHeader';

const CreateRequest = ({
  onCancel,
  onSubmit,
}: {
  onCancel: () => void;
  onSubmit: (data: CreateRequestFormData) => void;
}) => {
  const [formData, setFormData] = useState<CreateRequestFormData>({
    title: '',
    version: '0.1',
    problem: '',
    goal: '',
    inScope: [''],
    outScope: [''],
    users: [''],
    systemActors: [''],
    features: [''],
    userStories: [''],
    performance: '',
    security: '',
    reliability: '',
    techConstraints: [''],
    bizConstraints: [''],
    assumptions: [''],
    dependencies: [''],
    definitionOfDone: [''],
  });

  const [activeSection, setActiveSection] = useState(1);

  const handleArrayChange = (
    field: keyof typeof formData,
    idx: number,
    value: string
  ) => {
    const arr = [...(formData[field] as string[])];
    arr[idx] = value;
    setFormData({ ...formData, [field]: arr });
  };

  const addArrayItem = (field: keyof typeof formData) => {
    setFormData({ ...formData, [field]: [...(formData[field] as string[]), ''] });
  };

  const removeArrayItem = (field: keyof typeof formData, idx: number) => {
    const arr = [...(formData[field] as string[])];
    arr.splice(idx, 1);
    setFormData({ ...formData, [field]: arr });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.problem) {
      alert('Please fill in at least the Project Name and Problem Statement.');
      return;
    }
    onSubmit(formData);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 animate-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-900">
          Create New Requirement
        </h1>
        <button onClick={onCancel} className="text-slate-500 hover:text-slate-800">
          <X size={24} />
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col md:flex-row">
        <div className="w-full md:w-1/3 bg-slate-50 border-r border-slate-200">
          <SectionHeader
            num={1}
            title="Project Info"
            icon={<BookOpen size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={2}
            title="Problem & Goal"
            icon={<AlertCircle size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={3}
            title="Scope"
            icon={<Target size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={4}
            title="Stakeholders"
            icon={<Users size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={5}
            title="Functional Reqs"
            icon={<Zap size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={6}
            title="Non-Functional"
            icon={<Shield size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={7}
            title="Constraints"
            icon={<Lock size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={8}
            title="Assumptions"
            icon={<Box size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
          <SectionHeader
            num={9}
            title="Acceptance"
            icon={<CheckCircle size={16} />}
            activeSection={activeSection}
            setActiveSection={setActiveSection}
          />
        </div>

        <div className="w-full md:w-2/3 p-6 max-h-150 overflow-y-auto">
          <form onSubmit={handleSubmit} className="space-y-6">
            {activeSection === 1 && (
              <div className="space-y-4 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  1. Project Information
                </h3>
                <div>
                  <label className="label">Project Name *</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    placeholder="e.g. Smart Queue"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="label">Version</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.version}
                    onChange={(e) =>
                      setFormData({ ...formData, version: e.target.value })
                    }
                  />
                </div>
              </div>
            )}

            {activeSection === 2 && (
              <div className="space-y-4 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  2. Problem Statement
                </h3>
                <div>
                  <label className="label">Current Problem *</label>
                  <textarea
                    className="textarea h-32"
                    value={formData.problem}
                    onChange={(e) =>
                      setFormData({ ...formData, problem: e.target.value })
                    }
                    placeholder="What is the pain point?"
                  />
                </div>
                <div>
                  <label className="label">Business Goal</label>
                  <textarea
                    className="textarea"
                    value={formData.goal}
                    onChange={(e) =>
                      setFormData({ ...formData, goal: e.target.value })
                    }
                    placeholder="What is the objective?"
                  />
                </div>
              </div>
            )}

            {activeSection === 3 && (
              <div className="space-y-6 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  3. Project Scope
                </h3>
                <div>
                  <label className="label">In-Scope (What we will do)</label>
                  {formData.inScope.map((item, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        className="input"
                        value={item}
                        onChange={(e) =>
                          handleArrayChange('inScope', i, e.target.value)
                        }
                      />
                      <button
                        type="button"
                        onClick={() => removeArrayItem('inScope', i)}
                      >
                        <Trash2 size={16} className="text-slate-400" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('inScope')}
                    className="text-blue-600 text-sm font-medium"
                  >
                    + Add Item
                  </button>
                </div>
                <div>
                  <label className="label">Out-of-Scope (What we won`t do)</label>
                  {formData.outScope.map((item, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        className="input"
                        value={item}
                        onChange={(e) =>
                          handleArrayChange('outScope', i, e.target.value)
                        }
                      />
                      <button
                        type="button"
                        onClick={() => removeArrayItem('outScope', i)}
                      >
                        <Trash2 size={16} className="text-slate-400" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('outScope')}
                    className="text-blue-600 text-sm font-medium"
                  >
                    + Add Item
                  </button>
                </div>
              </div>
            )}

            {activeSection === 4 && (
              <div className="space-y-6 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  4. Stakeholders
                </h3>
                <div>
                  <label className="label">User Personas</label>
                  {formData.users.map((item, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        className="input"
                        value={item}
                        onChange={(e) =>
                          handleArrayChange('users', i, e.target.value)
                        }
                        placeholder="e.g. Admin, Customer"
                      />
                      <button
                        type="button"
                        onClick={() => removeArrayItem('users', i)}
                      >
                        <Trash2 size={16} className="text-slate-400" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('users')}
                    className="text-blue-600 text-sm font-medium"
                  >
                    + Add Persona
                  </button>
                </div>
              </div>
            )}

            {activeSection === 5 && (
              <div className="space-y-6 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  5. Functional Requirements
                </h3>
                <div>
                  <label className="label">Features List</label>
                  {formData.features.map((item, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        className="input"
                        value={item}
                        onChange={(e) =>
                          handleArrayChange('features', i, e.target.value)
                        }
                        placeholder="e.g. User Login"
                      />
                      <button
                        type="button"
                        onClick={() => removeArrayItem('features', i)}
                      >
                        <Trash2 size={16} className="text-slate-400" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('features')}
                    className="text-blue-600 text-sm font-medium"
                  >
                    + Add Feature
                  </button>
                </div>
              </div>
            )}

            {activeSection === 6 && (
              <div className="space-y-4 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  6. Non-Functional Requirements
                </h3>
                <div>
                  <label className="label">Performance</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.performance}
                    onChange={(e) =>
                      setFormData({ ...formData, performance: e.target.value })
                    }
                    placeholder="e.g. < 1s latency"
                  />
                </div>
                <div>
                  <label className="label">Security</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.security}
                    onChange={(e) =>
                      setFormData({ ...formData, security: e.target.value })
                    }
                    placeholder="e.g. AES-256 Encryption"
                  />
                </div>
                <div>
                  <label className="label">Reliability</label>
                  <input
                    type="text"
                    className="input"
                    value={formData.reliability}
                    onChange={(e) =>
                      setFormData({ ...formData, reliability: e.target.value })
                    }
                    placeholder="e.g. 99.9% Uptime"
                  />
                </div>
              </div>
            )}

            {activeSection === 7 && (
              <div className="space-y-6 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  7. Constraints
                </h3>
                <div>
                  <label className="label">Technical Constraints</label>
                  {formData.techConstraints.map((item, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        className="input"
                        value={item}
                        onChange={(e) =>
                          handleArrayChange('techConstraints', i, e.target.value)
                        }
                        placeholder="e.g. Must use React"
                      />
                      <button
                        type="button"
                        onClick={() => removeArrayItem('techConstraints', i)}
                      >
                        <Trash2 size={16} className="text-slate-400" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('techConstraints')}
                    className="text-blue-600 text-sm font-medium"
                  >
                    + Add Item
                  </button>
                </div>
              </div>
            )}

            {activeSection === 8 && (
              <div className="space-y-6 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  8. Assumptions
                </h3>
                <div>
                  <label className="label">Assumptions</label>
                  {formData.assumptions.map((item, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        className="input"
                        value={item}
                        onChange={(e) =>
                          handleArrayChange('assumptions', i, e.target.value)
                        }
                        placeholder="e.g. Users have internet"
                      />
                      <button
                        type="button"
                        onClick={() => removeArrayItem('assumptions', i)}
                      >
                        <Trash2 size={16} className="text-slate-400" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('assumptions')}
                    className="text-blue-600 text-sm font-medium"
                  >
                    + Add Item
                  </button>
                </div>
              </div>
            )}

            {activeSection === 9 && (
              <div className="space-y-6 animate-in fade-in">
                <h3 className="font-bold text-lg text-slate-800 mb-4">
                  9. Acceptance Criteria
                </h3>
                <div>
                  <label className="label">Definition of Done</label>
                  {formData.definitionOfDone.map((item, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        className="input"
                        value={item}
                        onChange={(e) =>
                          handleArrayChange('definitionOfDone', i, e.target.value)
                        }
                        placeholder="e.g. All tests passed"
                      />
                      <button
                        type="button"
                        onClick={() => removeArrayItem('definitionOfDone', i)}
                      >
                        <Trash2 size={16} className="text-slate-400" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => addArrayItem('definitionOfDone')}
                    className="text-blue-600 text-sm font-medium"
                  >
                    + Add Criteria
                  </button>
                </div>
              </div>
            )}

            <div className="flex justify-between mt-8 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActiveSection(Math.max(1, activeSection - 1))}
                className={`px-4 py-2 rounded text-slate-600 font-medium ${
                  activeSection === 1 ? 'invisible' : ''
                }`}
              >
                Previous
              </button>

              {activeSection < 9 ? (
                <button
                  type="button"
                  onClick={() =>
                    setActiveSection(Math.min(9, activeSection + 1))
                  }
                  className="px-6 py-2 bg-blue-600 text-white rounded font-bold hover:bg-blue-700"
                >
                  Next Step
                </button>
              ) : (
                <button
                  type="submit"
                  className="px-6 py-2 bg-green-600 text-white rounded font-bold hover:bg-green-700 shadow-lg"
                >
                  Create Blueprint
                </button>
              )}
            </div>
          </form>
        </div>
      </div>

      <style>{`
            .label { display: block; font-size: 0.875rem; font-weight: 600; color: #334155; margin-bottom: 0.5rem; }
            .input { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; outline: none; transition: all; font-size: 0.875rem; }
            .input:focus { border-color: #3b82f6; ring: 2px solid #3b82f6; }
            .textarea { width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; outline: none; transition: all; font-size: 0.875rem; min-height: 80px; }
            .textarea:focus { border-color: #3b82f6; }
        `}</style>
    </div>
  );
};

export default CreateRequest;
