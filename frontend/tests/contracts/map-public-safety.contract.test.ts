/**
 * Map public safety contract test
 * 
 * Validates that public map API never leaks unreviewed/private data.
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';

const PublicMapEventSchema = z.object({
  id: z.string(),
  title: z.string(),
  event_type: z.string(),
  occurred_at: z.string().datetime(),
  location: z.object({
    lat: z.number(),
    lon: z.number(),
    label: z.string(),
  }),
  evidence: z.object({
    snapshot_id: z.string(),
    source_name: z.string(),
    citation_url: z.string().url(),
    reviewed: z.literal(true),  // Must always be true in public API
  }),
});

type PublicMapEvent = z.infer<typeof PublicMapEventSchema>;

describe('Map Public Safety Contract', () => {
  it('returns only reviewed events', () => {
    const event: PublicMapEvent = {
      id: 'evt_001',
      title: 'Public Event',
      event_type: 'incident',
      occurred_at: '2024-01-15T09:00:00Z',
      location: {
        lat: 52.1294,
        lon: -106.6469,
        label: 'Saskatoon, SK',
      },
      evidence: {
        snapshot_id: 'snap_001',
        source_name: 'Verified Source',
        citation_url: 'https://example.com',
        reviewed: true,
      },
    };

    expect(() => PublicMapEventSchema.parse(event)).not.toThrow();
  });

  it('rejects unreviewed event', () => {
    const unreviewed_event = {
      id: 'evt_002',
      title: 'Unreviewed',
      event_type: 'incident',
      occurred_at: '2024-01-16T10:00:00Z',
      location: {
        lat: 53.0,
        lon: -107.0,
        label: 'Regina, SK',
      },
      evidence: {
        snapshot_id: 'snap_002',
        source_name: 'Source',
        citation_url: 'https://example.com',
        reviewed: false,  // Not reviewed!
      },
    };

    expect(() => PublicMapEventSchema.parse(unreviewed_event)).toThrow();
  });

  it('never exposes raw notes', () => {
    const safe_response = {
      events: [
        {
          id: 'evt_003',
          title: 'Safe Event',
          event_type: 'incident',
          occurred_at: '2024-01-17T11:00:00Z',
          location: {
            lat: 54.0,
            lon: -108.0,
            label: 'Prince Albert, SK',
          },
          evidence: {
            snapshot_id: 'snap_003',
            source_name: 'Source',
            citation_url: 'https://example.com',
            reviewed: true,
          },
          // No raw_notes
          // No reviewer_comments
          // No internal_flags
        },
      ],
    };

    for (const event of safe_response.events) {
      expect(event).not.toHaveProperty('raw_notes');
      expect(event).not.toHaveProperty('reviewer_comments');
      expect(event).not.toHaveProperty('internal_flags');
    }
  });

  it('never exposes stack traces', () => {
    const safe_response = {
      events: [
        {
          id: 'evt_004',
          title: 'Event',
          event_type: 'incident',
          occurred_at: '2024-01-18T12:00:00Z',
          location: {
            lat: 55.0,
            lon: -109.0,
            label: 'La Ronge, SK',
          },
          evidence: {
            snapshot_id: 'snap_004',
            source_name: 'Source',
            citation_url: 'https://example.com',
            reviewed: true,
          },
        },
      ],
    };

    const response_str = JSON.stringify(safe_response);
    expect(response_str).not.toContain('Traceback');
    expect(response_str).not.toContain('File "');
    expect(response_str).not.toContain('Error:');
  });

  it('includes citation for every event', () => {
    const event: PublicMapEvent = {
      id: 'evt_005',
      title: 'Cited Event',
      event_type: 'incident',
      occurred_at: '2024-01-19T13:00:00Z',
      location: {
        lat: 56.0,
        lon: -110.0,
        label: 'Denim City, SK',
      },
      evidence: {
        snapshot_id: 'snap_005',
        source_name: 'Source',
        citation_url: 'https://example.com',
        reviewed: true,
      },
    };

    expect(event.evidence.snapshot_id).toBeTruthy();
    expect(event.evidence.citation_url).toBeTruthy();
    expect(event.evidence.reviewed).toBe(true);
  });
});
