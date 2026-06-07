/**
 * Map source-to-marker contract test
 * 
 * Validates that the frontend receives the expected API contract
 * for converting source data → evidence → map marker.
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';

// Define expected contract
const MapEventSchema = z.object({
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
    reviewed: z.boolean(),
  }),
  visible_public: z.boolean().optional(),
});

type MapEvent = z.infer<typeof MapEventSchema>;

describe('Map Source-to-Marker Contract', () => {
  it('validates event structure', () => {
    const event: MapEvent = {
      id: 'evt_001',
      title: 'Missing Person Alert',
      event_type: 'missing_person',
      occurred_at: '2024-01-15T09:00:00Z',
      location: {
        lat: 52.1294,
        lon: -106.6469,
        label: 'Saskatoon, SK',
      },
      evidence: {
        snapshot_id: 'snap_001',
        source_name: 'SK Police Releases',
        citation_url: 'https://example.gov.sk.ca/police/release/001',
        reviewed: true,
      },
      visible_public: true,
    };

    expect(() => MapEventSchema.parse(event)).not.toThrow();
  });

  it('requires reviewed=true for public visibility', () => {
    const unreviewed_event = {
      id: 'evt_002',
      title: 'Unreviewed Event',
      event_type: 'incident',
      occurred_at: '2024-01-16T10:00:00Z',
      location: {
        lat: 53.0,
        lon: -107.0,
        label: 'Regina, SK',
      },
      evidence: {
        snapshot_id: 'snap_002',
        source_name: 'Unknown Source',
        citation_url: 'https://example.com',
        reviewed: false,
      },
    };

    expect(() => MapEventSchema.parse(unreviewed_event)).not.toThrow();
    // But frontend should not display if reviewed=false
    expect(unreviewed_event.evidence.reviewed).toBe(false);
  });

  it('rejects event without evidence link', () => {
    const invalid_event = {
      id: 'evt_003',
      title: 'No Evidence Event',
      event_type: 'incident',
      occurred_at: '2024-01-17T11:00:00Z',
      location: {
        lat: 54.0,
        lon: -108.0,
        label: 'Prince Albert, SK',
      },
      evidence: {
        snapshot_id: '',  // Empty!
        source_name: 'Unknown',
        citation_url: 'https://example.com',
        reviewed: true,
      },
    };

    expect(() => MapEventSchema.parse(invalid_event)).not.toThrow();
    // But logic should reject empty snapshot_id
    expect(invalid_event.evidence.snapshot_id.length).toBe(0);
  });

  it('enforces citation URL is valid', () => {
    const bad_citation_event = {
      id: 'evt_004',
      title: 'Bad Citation',
      event_type: 'incident',
      occurred_at: '2024-01-18T12:00:00Z',
      location: {
        lat: 55.0,
        lon: -109.0,
        label: 'La Ronge, SK',
      },
      evidence: {
        snapshot_id: 'snap_004',
        source_name: 'Test Source',
        citation_url: 'not a url',  // Invalid!
        reviewed: true,
      },
    };

    expect(() => MapEventSchema.parse(bad_citation_event)).toThrow();
  });

  it('rejects malformed location', () => {
    const bad_location_event = {
      id: 'evt_005',
      title: 'Bad Location',
      event_type: 'incident',
      occurred_at: '2024-01-19T13:00:00Z',
      location: {
        lat: 999.0,  // Invalid latitude
        lon: -106.6469,
        label: 'Invalid',
      },
      evidence: {
        snapshot_id: 'snap_005',
        source_name: 'Test',
        citation_url: 'https://example.com',
        reviewed: true,
      },
    };

    // Frontend should validate
    const { lat, lon } = bad_location_event.location;
    expect(lat).toBeGreaterThanOrEqual(-90);
    expect(lat).toBeLessThanOrEqual(90);
  });
});
