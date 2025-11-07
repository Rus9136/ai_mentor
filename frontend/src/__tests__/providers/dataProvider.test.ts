import { describe, it, expect, beforeEach, vi } from 'vitest';
import { dataProvider, customizeTextbook } from '../../providers/dataProvider';
import * as authProvider from '../../providers/authProvider';

// Mock fetch globally
global.fetch = vi.fn();

// Mock getAuthToken
vi.spyOn(authProvider, 'getAuthToken');

// Mock errorTranslations utility
vi.mock('../../utils/errorTranslations', () => ({
  handleFetchError: vi.fn(async (response) => {
    throw new Error(`HTTP error! status: ${response.status}`);
  }),
}));

describe('dataProvider', () => {
  beforeEach(() => {
    // Clear localStorage and reset mocks
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('getList', () => {
    it('should throw error if no token', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue(null);

      await expect(
        dataProvider.getList('schools', {
          pagination: { page: 1, perPage: 10 },
          sort: { field: 'id', order: 'ASC' },
          filter: {},
        })
      ).rejects.toThrow('Токен аутентификации не найден');
    });

    it('should fetch schools with pagination, sorting, and filtering', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockSchools = [
        { id: 1, name: 'School A', code: 'SA', is_active: true },
        { id: 2, name: 'School B', code: 'SB', is_active: true },
        { id: 3, name: 'School C', code: 'SC', is_active: false },
        { id: 4, name: 'Test School', code: 'TS', is_active: true },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSchools,
      });

      const result = await dataProvider.getList('schools', {
        pagination: { page: 1, perPage: 2 },
        sort: { field: 'name', order: 'ASC' },
        filter: { is_active: true },
      });

      // Check fetch call
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/schools',
        {
          headers: {
            Authorization: 'Bearer test_token',
          },
        }
      );

      // Client-side filtering (only active schools)
      expect(result.data).toHaveLength(2); // page 1, perPage 2
      expect(result.total).toBe(3); // Total active schools

      // Client-side sorting (School A, School B, Test School)
      expect(result.data[0].name).toBe('School A');
      expect(result.data[1].name).toBe('School B');
    });

    it('should filter schools by search query', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockSchools = [
        { id: 1, name: 'School A', code: 'SA', is_active: true },
        { id: 2, name: 'Test School', code: 'TS', is_active: true },
        { id: 3, name: 'Another School', code: 'AS', is_active: true },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSchools,
      });

      const result = await dataProvider.getList('schools', {
        pagination: { page: 1, perPage: 10 },
        sort: { field: 'id', order: 'ASC' },
        filter: { q: 'test' },
      });

      // Should find school by name or code containing "test"
      expect(result.data).toHaveLength(1);
      expect(result.data[0].name).toBe('Test School');
    });

    it('should fetch textbooks with global endpoint', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockTextbooks = [
        { id: 1, title: 'Algebra 7', subject: 'math', grade_level: 7 },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTextbooks,
      });

      await dataProvider.getList('textbooks', {
        pagination: { page: 1, perPage: 10 },
        sort: { field: 'id', order: 'ASC' },
        filter: {},
      });

      // Should use global endpoint
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/global/textbooks',
        expect.any(Object)
      );
    });

    it('should fetch students with school endpoint', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockStudents = [
        {
          id: 1,
          student_code: 'STU001',
          grade_level: 7,
          user: { first_name: 'John', last_name: 'Doe', email: 'john@test.com', is_active: true },
        },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStudents,
      });

      await dataProvider.getList('students', {
        pagination: { page: 1, perPage: 10 },
        sort: { field: 'id', order: 'ASC' },
        filter: {},
      });

      // Should use school endpoint
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/school/students',
        expect.any(Object)
      );
    });
  });

  describe('getOne', () => {
    it('should fetch single school', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockSchool = { id: 1, name: 'Test School', code: 'TS' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSchool,
      });

      const result = await dataProvider.getOne('schools', { id: 1 });

      expect(result.data).toEqual(mockSchool);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/schools/1',
        expect.any(Object)
      );
    });

    it('should use global endpoint for textbooks', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockTextbook = { id: 1, title: 'Algebra 7' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTextbook,
      });

      await dataProvider.getOne('textbooks', { id: 1 });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/global/textbooks/1',
        expect.any(Object)
      );
    });

    it('should use school endpoint for students', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockStudent = { id: 1, student_code: 'STU001' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStudent,
      });

      await dataProvider.getOne('students', { id: 1 });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/school/students/1',
        expect.any(Object)
      );
    });
  });

  describe('create', () => {
    it('should create school', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const newSchool = { name: 'New School', code: 'NS', region: 'Test Region' };
      const createdSchool = { id: 5, ...newSchool };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => createdSchool,
      });

      const result = await dataProvider.create('schools', { data: newSchool });

      expect(result.data).toEqual(createdSchool);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/schools',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer test_token',
          },
          body: JSON.stringify(newSchool),
        }
      );
    });

    it('should create textbook with global endpoint', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const newTextbook = { title: 'Physics 8', subject: 'physics', grade_level: 8 };
      const createdTextbook = { id: 10, ...newTextbook };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => createdTextbook,
      });

      await dataProvider.create('textbooks', { data: newTextbook });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/global/textbooks',
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should create student with school endpoint', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const newStudent = { student_code: 'STU999', grade_level: 7 };
      const createdStudent = { id: 99, ...newStudent };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => createdStudent,
      });

      await dataProvider.create('students', { data: newStudent });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/school/students',
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('update', () => {
    it('should update school', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const updatedData = { name: 'Updated School', code: 'US' };
      const updatedSchool = { id: 1, ...updatedData };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => updatedSchool,
      });

      const result = await dataProvider.update('schools', {
        id: 1,
        data: updatedData,
        previousData: { id: 1, name: 'Old School', code: 'OS' },
      });

      expect(result.data).toEqual(updatedSchool);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/schools/1',
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer test_token',
          },
          body: JSON.stringify(updatedData),
        }
      );
    });

    it('should update textbook with global endpoint', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const updatedTextbook = { id: 1, title: 'Updated Algebra 7' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => updatedTextbook,
      });

      await dataProvider.update('textbooks', {
        id: 1,
        data: { title: 'Updated Algebra 7' },
        previousData: { id: 1, title: 'Algebra 7' },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/global/textbooks/1',
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });

  describe('delete', () => {
    it('should delete school', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1 }),
      });

      const result = await dataProvider.delete('schools', { id: 1, previousData: {} });

      expect(result.data).toEqual({ id: 1 });
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/schools/1',
        {
          method: 'DELETE',
          headers: {
            Authorization: 'Bearer test_token',
          },
        }
      );
    });

    it('should delete textbook with global endpoint', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1 }),
      });

      await dataProvider.delete('textbooks', { id: 1, previousData: {} });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/admin/global/textbooks/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('getMany', () => {
    it('should fetch multiple resources', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      const mockSchools = [
        { id: 1, name: 'School A' },
        { id: 2, name: 'School B' },
      ];

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSchools[0],
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSchools[1],
        });

      const result = await dataProvider.getMany('schools', { ids: [1, 2] });

      expect(result.data).toHaveLength(2);
      expect(result.data[0].name).toBe('School A');
      expect(result.data[1].name).toBe('School B');
    });

    it('should handle failed requests gracefully', async () => {
      vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: 1, name: 'School A' }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
        });

      const result = await dataProvider.getMany('schools', { ids: [1, 2] });

      // Should filter out failed requests
      expect(result.data).toHaveLength(1);
      expect(result.data[0].name).toBe('School A');
    });
  });
});

describe('customizeTextbook', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should fork global textbook successfully', async () => {
    vi.mocked(authProvider.getAuthToken).mockReturnValue('test_token');

    const customizedTextbook = {
      id: 100,
      title: 'Algebra 7 (Custom)',
      is_customized: true,
      global_textbook_id: 1,
      school_id: 3,
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => customizedTextbook,
    });

    const result = await customizeTextbook(1, {
      title: 'Algebra 7 (Custom)',
      copy_content: true,
    });

    expect(result).toEqual(customizedTextbook);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/admin/school/textbooks/1/customize',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test_token',
        },
        body: JSON.stringify({
          title: 'Algebra 7 (Custom)',
          copy_content: true,
        }),
      }
    );
  });

  it('should throw error if no token', async () => {
    vi.mocked(authProvider.getAuthToken).mockReturnValue(null);

    await expect(
      customizeTextbook(1, { title: 'Custom', copy_content: true })
    ).rejects.toThrow('Токен аутентификации не найден');
  });
});
