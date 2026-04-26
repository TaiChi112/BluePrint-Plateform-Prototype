"use client";
import {
  BookOpen,
  CheckSquare,
  ChevronDown,
  Database,
  Edit3,
  ExternalLink,
  FileText,
  AlertCircle,
  Lightbulb,
  Zap,
  Shield,
  Code2,
} from 'lucide-react';
import { useState } from 'react';
import type { Artifact, RequirementSection } from '../types';
import MermaidDiagram from './MermaidDiagram';
import RequirementViewer from './RequirementViewer';

const ArtifactViewer = ({
  artifact,
  isOwner,
  onAction,
  onUpdateStructuredSection,
}: {
  artifact: Artifact;
  isOwner: boolean;
  onAction: (artifact: Artifact, mode: 'edit' | 'suggest') => void;
  onUpdateStructuredSection?: (updatedSection: RequirementSection) => void;
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  // State for collapsible sections in JSON spec
  const [expandedSections, setExpandedSections] = useState({
    problem: true,
    solution: true,
    functional: false,
    nonFunctional: false,
    techStack: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Handle JSON Spec format
  if (artifact.dataSpec) {
    return (
      <div className="space-y-4">
        {/* Project Name Header */}
            <div className="bg-linear-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-2">
            <div className="bg-blue-500 p-2 rounded-lg">
              <BookOpen className="text-white" size={24} />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">{artifact.dataSpec.project_name}</h2>
          </div>
          <div className="flex items-center space-x-2 mt-3">
            <span className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-semibold">
              {artifact.dataSpec.status}
            </span>
            {artifact.dataSpec._saved_at && (
              <span className="text-xs text-slate-500">
                Saved: {new Date(artifact.dataSpec._saved_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Problem Statement */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition overflow-hidden">
          <div 
            className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition"
            onClick={() => toggleSection('problem')}
          >
            <div className="flex items-center space-x-2">
              <AlertCircle className="text-red-500" size={20} />
              <h3 className="font-bold text-lg text-slate-800">Problem Statement</h3>
            </div>
            <ChevronDown 
              size={20} 
              className={`text-slate-400 transition-transform duration-200 ${expandedSections.problem ? 'rotate-0' : '-rotate-90'}`}
            />
          </div>
          {expandedSections.problem && (
            <div className="px-6 pb-6 animate-in slide-in-from-top-2 duration-200">
              <p className="text-slate-600 leading-relaxed">{artifact.dataSpec.problem_statement}</p>
            </div>
          )}
        </div>

        {/* Solution Overview */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition overflow-hidden">
          <div 
            className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition"
            onClick={() => toggleSection('solution')}
          >
            <div className="flex items-center space-x-2">
              <Lightbulb className="text-yellow-500" size={20} />
              <h3 className="font-bold text-lg text-slate-800">Solution Overview</h3>
            </div>
            <ChevronDown 
              size={20} 
              className={`text-slate-400 transition-transform duration-200 ${expandedSections.solution ? 'rotate-0' : '-rotate-90'}`}
            />
          </div>
          {expandedSections.solution && (
            <div className="px-6 pb-6 animate-in slide-in-from-top-2 duration-200">
              <p className="text-slate-600 leading-relaxed">{artifact.dataSpec.solution_overview}</p>
            </div>
          )}
        </div>

        {/* Functional Requirements */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition overflow-hidden">
          <div 
            className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition"
            onClick={() => toggleSection('functional')}
          >
            <div className="flex items-center space-x-2">
              <Zap className="text-green-500" size={20} />
              <h3 className="font-bold text-lg text-slate-800">Functional Requirements</h3>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">
                {artifact.dataSpec.functional_requirements.length}
              </span>
            </div>
            <ChevronDown 
              size={20} 
              className={`text-slate-400 transition-transform duration-200 ${expandedSections.functional ? 'rotate-0' : '-rotate-90'}`}
            />
          </div>
          {expandedSections.functional && (
            <div className="px-6 pb-6 animate-in slide-in-from-top-2 duration-200">
              <ul className="space-y-2">
                {artifact.dataSpec.functional_requirements.map((item, i) => (
                  <li key={i} className="text-slate-600 flex gap-3">
                    <span className="text-green-500 font-bold mt-1">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Non-Functional Requirements */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition overflow-hidden">
          <div 
            className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition"
            onClick={() => toggleSection('nonFunctional')}
          >
            <div className="flex items-center space-x-2">
              <Shield className="text-purple-500" size={20} />
              <h3 className="font-bold text-lg text-slate-800">Non-Functional Requirements</h3>
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-semibold">
                {artifact.dataSpec.non_functional_requirements.length}
              </span>
            </div>
            <ChevronDown 
              size={20} 
              className={`text-slate-400 transition-transform duration-200 ${expandedSections.nonFunctional ? 'rotate-0' : '-rotate-90'}`}
            />
          </div>
          {expandedSections.nonFunctional && (
            <div className="px-6 pb-6 animate-in slide-in-from-top-2 duration-200">
              <ul className="space-y-2">
                {artifact.dataSpec.non_functional_requirements.map((item, i) => (
                  <li key={i} className="text-slate-600 flex gap-3">
                    <span className="text-purple-500 font-bold mt-1">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Tech Stack Recommendation */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition overflow-hidden">
          <div 
            className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition"
            onClick={() => toggleSection('techStack')}
          >
            <div className="flex items-center space-x-2">
              <Code2 className="text-blue-500" size={20} />
              <h3 className="font-bold text-lg text-slate-800">Tech Stack Recommendation</h3>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-semibold">
                {artifact.dataSpec.tech_stack_recommendation.length}
              </span>
            </div>
            <ChevronDown 
              size={20} 
              className={`text-slate-400 transition-transform duration-200 ${expandedSections.techStack ? 'rotate-0' : '-rotate-90'}`}
            />
          </div>
          {expandedSections.techStack && (
            <div className="px-6 pb-6 animate-in slide-in-from-top-2 duration-200">
              <div className="flex flex-wrap gap-2">
                {artifact.dataSpec.tech_stack_recommendation.map((tech, i) => (
                  <span
                    key={i}
                    className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium border border-blue-200 hover:bg-blue-100 transition"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (artifact.contentFormat === 'structured' && artifact.structuredContent) {
    return (
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-4 border-b border-slate-200 pb-2">
          <div className="bg-orange-100 p-2 rounded-lg">
            <FileText className="text-orange-600" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {artifact.title}
            </h2>
            <p className="text-xs text-slate-500">
              Comprehensive Software Requirements Specification
            </p>
          </div>
        </div>
        <RequirementViewer
          sections={artifact.structuredContent}
          isOwner={isOwner}
          onUpdateSection={(updated) =>
            onUpdateStructuredSection && onUpdateStructuredSection(updated)
          }
        />
      </div>
    );
  }

  const getIcon = () => {
    switch (artifact.type) {
      case 'requirement':
        return <FileText className="text-orange-500" />;
      case 'diagram':
        return <Database className="text-purple-500" />;
      case 'testing':
        return <CheckSquare className="text-green-500" />;
      default:
        return <BookOpen />;
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg mb-4 overflow-hidden shadow-sm hover:border-blue-200 transition">
      <div
        className={`flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition ${
          isExpanded ? 'border-b border-slate-100' : ''
        }`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3 select-none">
          <div
            className={`text-slate-400 transition-transform duration-200 ${
              isExpanded ? 'rotate-0' : '-rotate-90'
            }`}
          >
            <ChevronDown size={20} />
          </div>
          {getIcon()}
          <h4 className="font-bold text-slate-800">{artifact.title}</h4>
          <span className="text-[10px] uppercase tracking-wider font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {artifact.type}
          </span>
        </div>

        <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
          {isOwner && artifact.contentFormat !== 'structured' && (
            <button
              onClick={() => onAction(artifact, 'edit')}
              className="p-2 text-slate-400 hover:text-green-600 rounded-full hover:bg-green-50 transition"
            >
              <Edit3 size={16} />
            </button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="p-5 bg-white animate-in slide-in-from-top-2 duration-200">
          {artifact.externalLinks && (
            <div className="flex flex-wrap gap-2 mb-4">
              {artifact.externalLinks.map((link, idx) => (
                <a
                  key={idx}
                  href={link.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center space-x-2 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-100 px-3 py-1.5 rounded-full hover:bg-blue-100 transition"
                >
                  <ExternalLink size={12} />
                  <span>{link.title}</span>
                </a>
              ))}
            </div>
          )}
          {artifact.contentFormat === 'mermaid' ? (
            <div className="relative">
              <MermaidDiagram code={artifact.content} />
            </div>
          ) : (
            <div className="prose prose-sm text-slate-600 whitespace-pre-line">
              {artifact.content}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ArtifactViewer;
