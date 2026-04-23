import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProjectCard from './ProjectCard';
import type { Project } from '../types';

describe('ProjectCard', () => {
  const mockProject: Project = {
    id: 'test-1',
    title: 'Test Project',
    summary: 'This is a test project summary',
    author: 'John Doe',
    isPublished: true,
    createdAt: '2026-03-01',
    tags: ['React', 'TypeScript', 'Testing', 'Vitest', 'Frontend'],
    versions: [
      {
        versionNumber: '1.0.0',
        label: 'Initial',
        description: 'Initial release',
        artifacts: [
          {
            id: 'artifact-1',
            type: 'requirement',
            title: 'Requirements',
            content: 'Test content',
          },
        ],
      },
      {
        versionNumber: '1.1.0',
        label: 'Update',
        description: 'Updated release',
        artifacts: [
          {
            id: 'artifact-2',
            type: 'requirement',
            title: 'Requirements v2',
            content: 'Test content v2',
          },
        ],
      },
    ],
  };

  const mockOnClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders project title', () => {
    render(<ProjectCard project={mockProject} onClick={mockOnClick} />);

    const titleElements = screen.getAllByText('Test Project');
    expect(titleElements[0]).toBeInTheDocument();
  });

  it('renders project summary', () => {
    render(<ProjectCard project={mockProject} onClick={mockOnClick} />);

    expect(screen.getAllByText('This is a test project summary')[0]).toBeInTheDocument();
  });

  it('renders project author', () => {
    render(<ProjectCard project={mockProject} onClick={mockOnClick} />);

    const authorElements = screen.getAllByText(/By John Doe/i);
    expect(authorElements[0]).toBeInTheDocument();
  });

  it('renders version count', () => {
    render(<ProjectCard project={mockProject} onClick={mockOnClick} />);

    const versionElements = screen.getAllByText('2');
    expect(versionElements[0]).toBeInTheDocument();
  });

  it('renders first 4 tags', () => {
    render(<ProjectCard project={mockProject} onClick={mockOnClick} />);

    expect(screen.getAllByText('React')[0]).toBeInTheDocument();
    expect(screen.getAllByText('TypeScript')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Testing')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Vitest')[0]).toBeInTheDocument();
  });

  it('shows +N badge when more than 4 tags', () => {
    render(<ProjectCard project={mockProject} onClick={mockOnClick} />);

    const plusElements = screen.getAllByText('+1');
    expect(plusElements[0]).toBeInTheDocument();
  });

  it('renders View Blueprint action', () => {
    render(<ProjectCard project={mockProject} onClick={mockOnClick} />);

    const viewActions = screen.getAllByText('View Blueprint');
    expect(viewActions.length).toBeGreaterThan(0);
  });
});
