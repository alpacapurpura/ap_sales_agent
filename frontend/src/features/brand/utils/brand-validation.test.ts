import { describe, it, expect } from 'vitest';
import {
  validateIdentity,
  validateStrategy,
  validateStory,
  validateVisuals,
  validateTeam,
  validateContact,
  validateAuthority,
} from './brand-validation';

describe('Brand Validation Utils', () => {

  describe('validateIdentity', () => {
    it('should handle undefined identity', () => {
      const result = validateIdentity(undefined as any);
      expect(result.status).toBe('empty');
      expect(result.score).toBe(0);
      expect(result.missingFields).toContain('Datos de Identidad');
    });

    it('should identify missing fields', () => {
      const identity = { brand_name: 'Test Brand' } as any;
      const result = validateIdentity(identity);
      expect(result.status).toBe('partial');
      expect(result.missingFields).toContain('Sitio Web');
      expect(result.missingFields).toContain('Industria');
      expect(result.missingFields).toContain('Logo');
      expect(result.score).toBeLessThan(100);
    });

    it('should return complete for full identity', () => {
      const identity = {
        brand_name: 'Test Brand',
        website: 'https://example.com',
        industry: 'Tech',
        logo_url: 'https://example.com/logo.png'
      } as any;
      const result = validateIdentity(identity);
      expect(result.status).toBe('complete');
      expect(result.score).toBe(100);
      expect(result.missingFields).toHaveLength(0);
    });
  });

  describe('validateStrategy', () => {
    it('should handle undefined strategy', () => {
      const result = validateStrategy(undefined as any);
      expect(result.status).toBe('empty');
    });

    it('should identify missing strategy fields', () => {
      const strategy = {} as any;
      const result = validateStrategy(strategy);
      expect(result.status).toBe('empty');
      expect(result.missingFields).toContain('Nombre de Metodologia');
      expect(result.missingFields).toContain('Pilares de Metodologia');
    });

    it('should return complete for full strategy', () => {
      const strategy = {
        methodology_name: 'Method',
        methodology_pillars: [{ id: '1', title: 'Pillar' }]
      } as any;
      const result = validateStrategy(strategy);
      expect(result.status).toBe('complete');
      expect(result.score).toBe(100);
    });
  });

  describe('validateStory', () => {
    it('should identify missing story fields', () => {
      const story = { origin_story: 'Once upon a time' } as any;
      const result = validateStory(story);
      expect(result.status).toBe('partial'); // 50%
      expect(result.missingFields).toContain('Hitos Importantes');
      expect(result.score).toBe(50);
    });

    it('should return complete for full story', () => {
      const story = {
        origin_story: 'Story',
        milestones: ['2023 Started']
      } as any;
      const result = validateStory(story);
      expect(result.status).toBe('complete');
      expect(result.score).toBe(100);
    });
  });

  describe('validateVisuals', () => {
    it('should identify missing visuals', () => {
      const visuals = { primary_color: '#000' } as any;
      const result = validateVisuals(visuals);
      expect(result.status).toBe('partial');
      expect(result.missingFields).toContain('Color de Acento');
      expect(result.missingFields).toContain('Fuente de Títulos');
    });

    it('should return complete for full visuals', () => {
      const visuals = {
        primary_color: '#000',
        accent_color: '#fff',
        font_heading: 'Sans',
        font_body: 'Serif'
      } as any;
      const result = validateVisuals(visuals);
      expect(result.status).toBe('complete');
      expect(result.score).toBe(100);
    });
  });

  describe('validateTeam', () => {
    it('should handle empty team', () => {
      const result = validateTeam([]);
      expect(result.status).toBe('empty');
      expect(result.score).toBe(0);
    });

    it('should handle incomplete team members', () => {
      const team = [{ name: 'Member', role: 'Dev' }] as any; // Missing photo
      const result = validateTeam(team);
      expect(result.status).toBe('partial');
      expect(result.score).toBe(50);
      expect(result.missingFields[0]).toContain('Miembros incompletos');
    });

    it('should return complete for valid team', () => {
      const team = [{ name: 'Member', role: 'Dev', headshot_url: 'img.jpg' }] as any;
      const result = validateTeam(team);
      expect(result.status).toBe('complete');
      expect(result.score).toBe(100);
    });
  });

  describe('validateContact', () => {
    it('should require email and one social', () => {
      const contact = { support_email: 'test@test.com' } as any;
      const result = validateContact(contact);
      expect(result.status).toBe('partial'); // 1 of 2 fields (email, social)
      expect(result.missingFields).toContain('Instagram o LinkedIn');
      expect(result.score).toBe(50);
    });

    it('should return complete with email and linkedin', () => {
      const contact = {
        support_email: 'test@test.com',
        social_linkedin: 'linkedin.com'
      } as any;
      const result = validateContact(contact);
      expect(result.status).toBe('complete');
      expect(result.score).toBe(100);
    });
  });

  describe('validateAuthority', () => {
    it('should handle empty vault', () => {
      const result = validateAuthority([]);
      expect(result.status).toBe('empty');
      expect(result.score).toBe(0);
    });

    it('should return complete with items', () => {
      const vault = [{ id: '1', entity_name: 'Press' }] as any;
      const result = validateAuthority(vault);
      expect(result.status).toBe('complete');
      expect(result.score).toBe(100);
    });
  });
});
