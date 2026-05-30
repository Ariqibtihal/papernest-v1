import { apiClient } from '@/lib/axios';
import type { User, Token, LoginCredentials, RegisterCredentials } from '@/types/auth';

/**
 * Auth client.
 *
 * Refresh and logout send the refresh_token in the JSON body — never as a
 * URL query param. URL params end up in browser history, server access
 * logs, and proxy logs, leaking long-lived credentials.
 */
export const authService = {
  async register(credentials: RegisterCredentials): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', credentials);
    return response.data;
  },

  async login(credentials: LoginCredentials): Promise<Token> {
    const response = await apiClient.post<Token>('/auth/login', credentials);
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<Token> {
    const response = await apiClient.post<Token>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken });
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};
