import React from 'react';
import { describe, test, expect, vi, afterEach } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import ProcessDiagramViewer, { parseExcalidrawData } from './ProcessDiagramViewer';

afterEach(() => {
  cleanup();
});

vi.mock('next/dynamic', () => ({
  default: () => {
    return function MockDynamicComponent() {
      return <div data-testid="mock-excalidraw-canvas">Mock Excalidraw Canvas</div>;
    };
  },
}));

describe('parseExcalidrawData', () => {
  test('parses valid input with all fields', () => {
    const input = {
      source: 'mock-mcp-fallback',
      elements: [
        {
          id: 'step-1',
          type: 'rectangle',
          x: 100,
          y: 120,
          width: 240,
          height: 64,
          text: 'Define Requirements',
          backgroundColor: '#dbeafe',
        },
        {
          id: 'arrow-1',
          type: 'arrow',
          startBindingElementId: 'step-1',
          endBindingElementId: 'step-2',
        },
      ],
      appState: { viewBackgroundColor: '#ffffff' },
    };

    const result = parseExcalidrawData(input);

    expect(result).not.toBeNull();
    expect(result?.source).toBe('mock-mcp-fallback');
    expect(result?.elements).toHaveLength(2);
    expect(result?.elements[0].id).toBe('step-1');
    expect(result?.elements[0].type).toBe('rectangle');
    expect(result?.elements[0].backgroundColor).toBe('#dbeafe');
    expect(result?.elements[1].type).toBe('arrow');
    expect(result?.appState).toEqual({ viewBackgroundColor: '#ffffff' });
  });

  test('returns null for missing elements array', () => {
    const input = {
      source: 'test',
      data: 'invalid',
    };

    const result = parseExcalidrawData(input);

    expect(result).toBeNull();
  });

  test('returns null for non-array elements', () => {
    const input = {
      elements: 'not-an-array',
    };

    const result = parseExcalidrawData(input);

    expect(result).toBeNull();
  });

  test('filters out invalid elements (non-objects)', () => {
    const input = {
      elements: [
        { id: 'valid-1', type: 'rectangle' },
        'invalid-string',
        null,
        { id: 'valid-2', type: 'arrow' },
        123,
      ],
    };

    const result = parseExcalidrawData(input);

    expect(result).not.toBeNull();
    expect(result?.elements).toHaveLength(2);
    expect(result?.elements[0].id).toBe('valid-1');
    expect(result?.elements[1].id).toBe('valid-2');
  });

  test('generates fallback IDs for missing id field', () => {
    const input = {
      elements: [
        { type: 'rectangle', x: 100, y: 120 },
        { type: 'arrow' },
        { type: 'text' },
      ],
    };

    const result = parseExcalidrawData(input);

    expect(result).not.toBeNull();
    expect(result?.elements).toHaveLength(3);
    expect(result?.elements[0].id).toBe('element-0');
    expect(result?.elements[1].id).toBe('element-1');
    expect(result?.elements[2].id).toBe('element-2');
  });

  test('coerces invalid types to undefined or defaults', () => {
    const input = {
      elements: [
        {
          id: 123, // invalid: should be string
          type: ['array'], // invalid: should be string
          x: 'not-a-number', // invalid: should be number
          width: true, // invalid: should be number
          text: { obj: 'text' }, // invalid: should be string
        },
      ],
    };

    const result = parseExcalidrawData(input);

    expect(result).not.toBeNull();
    expect(result?.elements).toHaveLength(1);
    expect(result?.elements[0].id).toBe('element-0'); // fallback generated
    expect(result?.elements[0].type).toBe('unknown'); // fallback type
    expect(result?.elements[0].x).toBeUndefined();
    expect(result?.elements[0].width).toBeUndefined();
    expect(result?.elements[0].text).toBeUndefined();
  });

  test('handles empty elements array', () => {
    const input = {
      source: 'test-empty',
      elements: [],
    };

    const result = parseExcalidrawData(input);

    expect(result).not.toBeNull();
    expect(result?.source).toBe('test-empty');
    expect(result?.elements).toHaveLength(0);
  });

  test('handles missing optional fields gracefully', () => {
    const input = {
      elements: [
        {
          id: 'minimal',
          type: 'rectangle',
          // x, y, width, height, text, backgroundColor missing
        },
      ],
    };

    const result = parseExcalidrawData(input);

    expect(result).not.toBeNull();
    expect(result?.elements[0].id).toBe('minimal');
    expect(result?.elements[0].type).toBe('rectangle');
    expect(result?.elements[0].x).toBeUndefined();
    expect(result?.elements[0].y).toBeUndefined();
    expect(result?.elements[0].width).toBeUndefined();
    expect(result?.elements[0].height).toBeUndefined();
    expect(result?.elements[0].text).toBeUndefined();
    expect(result?.elements[0].backgroundColor).toBeUndefined();
  });

  test('preserves source field when present', () => {
    const input = {
      source: 'real-api-v2',
      elements: [{ id: 'test', type: 'rectangle' }],
    };

    const result = parseExcalidrawData(input);

    expect(result?.source).toBe('real-api-v2');
  });

  test('sets source as undefined when missing', () => {
    const input = {
      elements: [{ id: 'test', type: 'rectangle' }],
    };

    const result = parseExcalidrawData(input);

    expect(result?.source).toBeUndefined();
  });

  test('handles appState correctly when present', () => {
    const input = {
      elements: [{ id: 'test', type: 'rectangle' }],
      appState: { zoom: 1.5, scrollX: 100, scrollY: 200 },
    };

    const result = parseExcalidrawData(input);

    expect(result?.appState).toEqual({ zoom: 1.5, scrollX: 100, scrollY: 200 });
  });

  test('sets appState as undefined when missing', () => {
    const input = {
      elements: [{ id: 'test', type: 'rectangle' }],
    };

    const result = parseExcalidrawData(input);

    expect(result?.appState).toBeUndefined();
  });

  test('handles all optional ExcalidrawElement fields', () => {
    const input = {
      elements: [
        {
          id: 'full-element',
          type: 'arrow',
          x: 100,
          y: 200,
          width: 300,
          height: 50,
          text: 'Arrow text',
          backgroundColor: '#ffffff',
          startBindingElementId: 'start-id',
          endBindingElementId: 'end-id',
        },
      ],
    };

    const result = parseExcalidrawData(input);

    expect(result).not.toBeNull();
    const element = result?.elements[0];
    expect(element?.id).toBe('full-element');
    expect(element?.type).toBe('arrow');
    expect(element?.x).toBe(100);
    expect(element?.y).toBe(200);
    expect(element?.width).toBe(300);
    expect(element?.height).toBe(50);
    expect(element?.text).toBe('Arrow text');
    expect(element?.backgroundColor).toBe('#ffffff');
    expect(element?.startBindingElementId).toBe('start-id');
    expect(element?.endBindingElementId).toBe('end-id');
  });
});

describe('ProcessDiagramViewer renderer selection', () => {
  test('renders mock SVG renderer when source is mock-mcp-fallback', () => {
    const mockData = {
      source: 'mock-mcp-fallback',
      elements: [
        { id: 'step-1', type: 'rectangle', x: 100, y: 100, width: 200, height: 60, text: 'Step 1' },
      ],
    };

    render(<ProcessDiagramViewer excalidrawJson={mockData} />);

    expect(screen.getByText('Process Flow Diagram')).toBeInTheDocument();
    expect(screen.getByText(/Mock Visualization \(SVG\)/)).toBeInTheDocument();
  });

  test('renders real interactive renderer when source is not mock', () => {
    const realData = {
      source: 'real-api-v1',
      elements: [
        { id: 'step-1', type: 'rectangle', x: 100, y: 100, width: 200, height: 60, text: 'Step 1' },
      ],
    };

    render(<ProcessDiagramViewer excalidrawJson={realData} />);

    expect(screen.getByText('Process Flow Diagram')).toBeInTheDocument();
    expect(screen.getByText(/Interactive Excalidraw/)).toBeInTheDocument();
  });

  test('forces mock renderer when forceMockDisplay is true', () => {
    const realData = {
      source: 'real-api-v1',
      elements: [
        { id: 'step-1', type: 'rectangle', x: 100, y: 100, width: 200, height: 60, text: 'Step 1' },
      ],
    };

    render(<ProcessDiagramViewer excalidrawJson={realData} forceMockDisplay={true} />);

    expect(screen.getByText(/Mock Visualization \(SVG\)/)).toBeInTheDocument();
    expect(screen.queryByText(/Interactive Excalidraw/)).not.toBeInTheDocument();
  });
});
