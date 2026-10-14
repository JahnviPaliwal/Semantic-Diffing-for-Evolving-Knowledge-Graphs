import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import React from 'react';
import { EmptyState } from '../components/EmptyState';
import { TimelineVisualizer } from '../components/TimelineVisualizer';
import { ChangesTable } from '../components/ChangesTable';
import { DiffItem, Version } from '../api/types';
import { ApiKeyProvider, useApiKey } from '../context/ApiKeyContext';
import { getSessionGroqApiKey } from '../api/client';

describe('Frontend Component Tests', () => {
  it('renders EmptyState with custom title and action', () => {
    let clicked = false;
    render(
      <EmptyState
        title="No Test Items"
        description="Please add items to test this view."
        action={
          <button onClick={() => { clicked = true; }}>
            Create Item
          </button>
        }
      />
    );

    expect(screen.getByText('No Test Items')).toBeInTheDocument();
    expect(screen.getByText('Please add items to test this view.')).toBeInTheDocument();
    const btn = screen.getByText('Create Item');
    btn.click();
    expect(clicked).toBe(true);
  });

  it('renders TimelineVisualizer with version list', () => {
    const mockVersions: Version[] = [
      {
        id: 1,
        project_id: 1,
        version_num: 1,
        version_label: 'v1',
        filename: 'report_v1.txt',
        doc_hash: 'hash1',
        status: 'ready',
        node_count: 5,
        edge_count: 3,
        created_at: new Date().toISOString(),
      },
      {
        id: 2,
        project_id: 1,
        version_num: 2,
        version_label: 'v2',
        filename: 'report_v2.txt',
        doc_hash: 'hash2',
        status: 'ready',
        node_count: 7,
        edge_count: 4,
        created_at: new Date().toISOString(),
      },
    ];

    render(
      <TimelineVisualizer
        versions={mockVersions}
        selectedPair={['1', '2']}
      />
    );

    expect(screen.getByText('Knowledge Graph Evolution Timeline')).toBeInTheDocument();
    expect(screen.getByText('report_v1.txt')).toBeInTheDocument();
    expect(screen.getByText('report_v2.txt')).toBeInTheDocument();
  });

  it('renders ChangesTable with filter controls and items', () => {
    const mockItems: DiffItem[] = [
      {
        element_type: 'node',
        change_type: 'ADDED',
        canonical_name: 'NovaPay',
        severity: 'HIGH',
        confidence: 0.95,
        source_quote: 'Acme introduced NovaPay for mobile checkout.',
        chunk_reference: 'chunk-1',
      },
      {
        element_type: 'node',
        change_type: 'RENAMED',
        canonical_name: 'OmniAI Corp',
        previous_name: 'OmniTech',
        severity: 'CRITICAL',
        confidence: 0.98,
        source_quote: 'OmniTech was rebranded as OmniAI Corp.',
        chunk_reference: 'chunk-2',
      },
    ];

    render(
      <ChangesTable
        items={mockItems}
        onSelectItem={() => {}}
      />
    );

    expect(screen.getByText('NovaPay')).toBeInTheDocument();
    expect(screen.getByText('OmniAI Corp')).toBeInTheDocument();
    expect(screen.getAllByText('CRITICAL').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('HIGH').length).toBeGreaterThanOrEqual(1);
  });

  it('manages Groq API Key purely in volatile memory', () => {
    const TestComponent = () => {
      const { apiKey, hasApiKey, setApiKey, clearApiKey } = useApiKey();
      return (
        <div>
          <span data-testid="status">{hasApiKey ? 'active' : 'inactive'}</span>
          <span data-testid="key">{apiKey}</span>
          <button onClick={() => setApiKey('gsk_test123456')}>Set</button>
          <button onClick={() => clearApiKey()}>Clear</button>
        </div>
      );
    };

    render(
      <ApiKeyProvider>
        <TestComponent />
      </ApiKeyProvider>
    );

    // Initial state: empty (wipe on reload behavior)
    expect(screen.getByTestId('status').textContent).toBe('inactive');
    expect(screen.getByTestId('key').textContent).toBe('');
    expect(getSessionGroqApiKey()).toBe('');

    // Set key
    act(() => {
      fireEvent.click(screen.getByText('Set'));
    });
    expect(screen.getByTestId('status').textContent).toBe('active');
    expect(screen.getByTestId('key').textContent).toBe('gsk_test123456');
    expect(getSessionGroqApiKey()).toBe('gsk_test123456');

    // Clear key
    act(() => {
      fireEvent.click(screen.getByText('Clear'));
    });
    expect(screen.getByTestId('status').textContent).toBe('inactive');
    expect(screen.getByTestId('key').textContent).toBe('');
    expect(getSessionGroqApiKey()).toBe('');
  });
});
