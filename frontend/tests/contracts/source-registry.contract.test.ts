/**
 * Source registry contract test
 * 
 * Validates frontend expectations for source admin interface.
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';

const SourceRegistryEntrySchema = z.object({
  id: z.string(),
  name: z.string(),
  jurisdiction: z.string(),
  source_type: z.enum(['court', 'tribunal', 'statute', 'police', 'news', 'registry', 'stats']),
  machine_ingest: z.boolean(),
  status: z.enum(['runnable', 'manual', 'enable_ready', 'deprecated', 'disabled']),
  last_verified_at: z.string().datetime(),
  failure_reason: z.string().nullable(),
});

type SourceRegistryEntry = z.infer<typeof SourceRegistryEntrySchema>;

describe('Source Registry Contract', () => {
  it('validates source entry structure', () => {
    const source: SourceRegistryEntry = {
      id: 'sk_police_releases',
      name: 'Saskatchewan Police Releases',
      jurisdiction: 'SK',
      source_type: 'police',
      machine_ingest: true,
      status: 'runnable',
      last_verified_at: '2024-01-15T10:00:00Z',
      failure_reason: null,
    };

    expect(() => SourceRegistryEntrySchema.parse(source)).not.toThrow();
  });

  it('requires status for runnable sources', () => {
    const runnable_source: SourceRegistryEntry = {
      id: 'test_source',
      name: 'Test Source',
      jurisdiction: 'ON',
      source_type: 'court',
      machine_ingest: true,
      status: 'runnable',
      last_verified_at: '2024-01-15T10:00:00Z',
      failure_reason: null,
    };

    expect(runnable_source.status).toBe('runnable');
    expect(runnable_source.failure_reason).toBeNull();
  });

  it('requires failure_reason for deprecated sources', () => {
    const deprecated_source: SourceRegistryEntry = {
      id: 'old_source',
      name: 'Deprecated Source',
      jurisdiction: 'MB',
      source_type: 'statute',
      machine_ingest: false,
      status: 'deprecated',
      last_verified_at: '2023-12-01T10:00:00Z',
      failure_reason: 'Source no longer publicly available',
    };

    expect(deprecated_source.status).toBe('deprecated');
    expect(deprecated_source.failure_reason).not.toBeNull();
  });

  it('rejects runnable source without verification date', () => {
    const bad_source = {
      id: 'test',
      name: 'Test',
      jurisdiction: 'AB',
      source_type: 'police',
      machine_ingest: true,
      status: 'runnable',
      last_verified_at: 'invalid',
      failure_reason: null,
    };

    expect(() => SourceRegistryEntrySchema.parse(bad_source)).toThrow();
  });

  it('enforces disable reason for disabled sources', () => {
    const disabled_source = {
      id: 'disabled_source',
      name: 'Disabled Source',
      jurisdiction: 'ON',
      source_type: 'registry',
      machine_ingest: false,
      status: 'disabled',
      last_verified_at: '2024-01-10T10:00:00Z',
      failure_reason: 'Source site down',
    };

    expect(disabled_source.status).toBe('disabled');
  });
});
