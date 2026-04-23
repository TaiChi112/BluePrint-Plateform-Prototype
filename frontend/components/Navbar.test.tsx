import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import Navbar from './Navbar';

// Mock next-auth
vi.mock('next-auth/react', () => ({
  useSession: vi.fn(() => ({ data: null, status: 'unauthenticated' })),
  signOut: vi.fn(),
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
}));

// Mock next/image with proper typing
vi.mock('next/image', () => ({
  default: (props: React.ImgHTMLAttributes<HTMLImageElement>) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

describe('Navbar', () => {
  const mockOnViewChange = vi.fn();
  const mockOnLoginClick = vi.fn();
  const mockOnLogoutClick = vi.fn();

  const defaultProps = {
    onViewChange: mockOnViewChange,
    user: null,
    onLoginClick: mockOnLoginClick,
    onLogoutClick: mockOnLogoutClick,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders navbar with logo and title', () => {
    render(<Navbar {...defaultProps} />);

    expect(screen.getAllByText('Blueprint')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Hub')[0]).toBeInTheDocument();
  });

  it('renders navigation buttons', () => {
    render(<Navbar {...defaultProps} />);

    expect(screen.getAllByText('Explore')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Post Idea')[0]).toBeInTheDocument();
  });

  it('shows Sign In button when not authenticated', () => {
    render(<Navbar {...defaultProps} />);

    expect(screen.getAllByText('Sign In')[0]).toBeInTheDocument();
  });

  it('calls onViewChange when logo is clicked', () => {
    const { container } = render(<Navbar {...defaultProps} />);

    const logo = container.querySelector('.cursor-pointer');
    if (logo) {
      fireEvent.click(logo);
      expect(mockOnViewChange).toHaveBeenCalledWith('home');
    }
  });
});
