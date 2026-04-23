import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import ArtifactViewer from './ArtifactViewer';
import type { Artifact } from '../types';

// Mock MermaidDiagram component
vi.mock('./MermaidDiagram', () => ({
  default: ({ code }: { code: string }) => <div data-testid="mermaid-diagram">{code}</div>,
}));

// Mock RequirementViewer component
vi.mock('./RequirementViewer', () => ({
  default: () => <div data-testid="requirement-viewer">Requirement Viewer</div>,
}));

describe('ArtifactViewer', () => {
  const mockArtifact: Artifact = {
    id: 'artifact-1',
    type: 'requirement',
    title: 'Requirements',
    content: 'Test content',
    dataSpec: {
      project_name: 'Test Project',
      problem_statement: 'This is a test problem statement',
      solution_overview: 'This is a test solution overview',
      functional_requirements: ['Req 1', 'Req 2', 'Req 3'],
      non_functional_requirements: ['NFR 1', 'NFR 2'],
      tech_stack_recommendation: ['React', 'Node.js', 'PostgreSQL'],
      status: 'Draft',
      _saved_at: '2026-03-03T10:00:00Z',
    },
  };

  const mockOnAction = vi.fn();
  const mockOnUpdateStructuredSection = vi.fn();

  const defaultProps = {
    artifact: mockArtifact,
    isOwner: false,
    onAction: mockOnAction,
    onUpdateStructuredSection: mockOnUpdateStructuredSection,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders project name from dataSpec', () => {
    const { getAllByText } = render(<ArtifactViewer {...defaultProps} />);

    expect(getAllByText('Test Project')[0]).toBeInTheDocument();
  });

  it('renders project status badge', () => {
    render(<ArtifactViewer {...defaultProps} />);

    expect(screen.getAllByText('Draft')[0]).toBeInTheDocument();
  });

  it('renders problem statement section', () => {
    render(<ArtifactViewer {...defaultProps} />);

    expect(screen.getAllByText('Problem Statement')[0]).toBeInTheDocument();
    expect(screen.getAllByText('This is a test problem statement')[0]).toBeInTheDocument();
  });

  it('renders solution overview section', () => {
    render(<ArtifactViewer {...defaultProps} />);

    expect(screen.getAllByText('Solution Overview')[0]).toBeInTheDocument();
  });

  it('renders saved timestamp when available', () => {
    render(<ArtifactViewer {...defaultProps} />);

    // Should show "Saved: " followed by formatted date
    expect(screen.getAllByText(/Saved:/)[0]).toBeInTheDocument();
  });

  it('handles missing saved_at timestamp', () => {
    const artifactWithoutTimestamp: Artifact = {
      ...mockArtifact,
      dataSpec: {
        ...mockArtifact.dataSpec!,
        _saved_at: '',
      },
    };

    const { getAllByText } = render(<ArtifactViewer {...{ ...defaultProps, artifact: artifactWithoutTimestamp }} />);

    // Should not crash and should render project name
    expect(getAllByText('Test Project')[0]).toBeInTheDocument();
  });
});
