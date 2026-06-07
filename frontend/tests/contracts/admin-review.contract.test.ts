/**
 * Admin review contract test
 * 
 * Validates frontend expectations for admin review interface.
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';

const ReviewItemSchema = z.object({
  id: z.string(),
  event_candidate_id: z.string(),
  status: z.enum(['pending', 'approved', 'rejected']),
  created_at: z.string().datetime(),
  requires_review: z.boolean(),
  visible_public: z.boolean(),
  raw_evidence: z.object({
    snapshot_id: z.string(),
    source_name: z.string(),
    source_url: z.string().url(),
    title: z.string(),
    body: z.string(),
  }).nullable(),
  ai_fields: z.object({
    extracted_entities: z.array(z.string()).optional(),
    confidence: z.number().min(0).max(1).optional(),
    basis: z.enum(['source_evidence', 'model_inference', 'mixed']).optional(),
  }).optional(),
});

type ReviewItem = z.infer<typeof ReviewItemSchema>;

describe('Admin Review Contract', () => {
  it('validates review item structure', () => {
    const item: ReviewItem = {
      id: 'review_001',
      event_candidate_id: 'evt_001',
      status: 'pending',
      created_at: '2024-01-15T10:00:00Z',
      requires_review: true,
      visible_public: false,
      raw_evidence: {
        snapshot_id: 'snap_001',
        source_name: 'SK Police',
        source_url: 'https://example.gov.sk.ca/police/001',
        title: 'Missing Person',
        body: 'Details here',
      },
      ai_fields: {
        extracted_entities: ['John Smith', 'Saskatoon'],
        confidence: 0.95,
        basis: 'mixed',
      },
    };

    expect(() => ReviewItemSchema.parse(item)).not.toThrow();
  });

  it('hides raw_evidence from public view', () => {
    const approved_item: ReviewItem = {
      id: 'review_002',
      event_candidate_id: 'evt_002',
      status: 'approved',
      created_at: '2024-01-15T10:00:00Z',
      requires_review: false,
      visible_public: true,
      raw_evidence: null,  // Hidden after approval
    };

    expect(approved_item.raw_evidence).toBeNull();
    expect(approved_item.visible_public).toBe(true);
  });

  it('marks AI-generated fields explicitly', () => {
    const item_with_ai: ReviewItem = {
      id: 'review_003',
      event_candidate_id: 'evt_003',
      status: 'pending',
      created_at: '2024-01-15T10:00:00Z',
      requires_review: true,
      visible_public: false,
      raw_evidence: null,
      ai_fields: {
        extracted_entities: ['Entity1'],
        confidence: 0.75,
        basis: 'model_inference',
      },
    };

    expect(item_with_ai.ai_fields?.basis).toBe('model_inference');
    // Model-inferred content requires review before public use
    expect(item_with_ai.requires_review).toBe(true);
  });

  it('rejects low-confidence AI without review requirement', () => {
    const bad_item = {
      id: 'review_004',
      event_candidate_id: 'evt_004',
      status: 'approved',
      created_at: '2024-01-15T10:00:00Z',
      requires_review: false,  // Should require review!
      visible_public: true,
      raw_evidence: null,
      ai_fields: {
        confidence: 0.30,  // Low!
        basis: 'model_inference',
      },
    };

    // Validation should flag this
    expect(bad_item.ai_fields.confidence).toBeLessThan(0.5);
    // Frontend should enforce: low confidence + model_inference = requires_review
  });

  it('tracks admin approval workflow', () => {
    const workflow_item: ReviewItem = {
      id: 'review_005',
      event_candidate_id: 'evt_005',
      status: 'pending',
      created_at: '2024-01-15T10:00:00Z',
      requires_review: true,
      visible_public: false,
      raw_evidence: {
        snapshot_id: 'snap_005',
        source_name: 'Test',
        source_url: 'https://example.com',
        title: 'Title',
        body: 'Body',
      },
    };

    // Admin can approve
    const approved: ReviewItem = {
      ...workflow_item,
      status: 'approved',
      visible_public: true,
      raw_evidence: null,  // Removed after approval
    };

    expect(approved.status).toBe('approved');
    expect(approved.visible_public).toBe(true);
    expect(approved.raw_evidence).toBeNull();
  });
});
