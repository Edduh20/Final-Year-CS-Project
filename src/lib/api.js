const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class APIClient {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;

    const tokens = localStorage.getItem('auth_tokens');
    if (tokens) {
      const parsed = JSON.parse(tokens);
      this.accessToken = parsed.access;
      this.refreshToken = parsed.refresh;
    }
  }

  setTokens(tokens) {
    this.accessToken = tokens.access;
    this.refreshToken = tokens.refresh;
    localStorage.setItem('auth_tokens', JSON.stringify(tokens));
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('auth_tokens');
  }

  async request(endpoint, options = {}) {
    const headers = {
      ...(options.headers || {}),
    };

  
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle token refresh on 401
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        return fetch(`${API_URL}${endpoint}`, { ...options, headers });
      }
    }

    return response;
  }

  async refreshAccessToken() {
  if (!this.refreshToken) return false;

  try {
    const response = await fetch(`${API_URL}/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: this.refreshToken }),
    });

    const data = await response.json();

    if (response.ok && data.access) {
      this.setAccessToken(data.access);
      return true;
    } else {
      console.error("Token refresh failed:", data);
      this.clearTokens();
      window.location.href = "/login";
      return false;
    }
  } catch (err) {
    console.error("Refresh token error:", err);
    this.clearTokens();
    window.location.href = "/login";
    return false;
  }
}


  async login(email, password) {
  const response = await fetch(`${API_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    if (data.error?.includes('Email not verified') || data.requires_otp) {
      const error = new Error(data.error || 'Email not verified');
      error.requires_otp = true;
      error.email = email;
      throw error;
    }
    
    throw new Error(data.error || 'Login failed');
  }

  this.setTokens({ access: data.access, refresh: data.refresh });
  
  return data;
}

  // OTP Verification Methods 
  async verifyOTP(email, otp) {
    const response = await fetch(`${API_URL}/auth/verify-otp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'OTP verification failed');
    }

    return data;
  }

  async resendOTP(email) {
    const response = await fetch(`${API_URL}/auth/resend-otp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to resend OTP');
    }

    return data;
  }

  async register(userData) {
    const response = await fetch(`${API_URL}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Registration failed');
    }

    const data = await response.json();
    if (data.access && data.refresh) {
      this.setTokens({ access: data.access, refresh: data.refresh });
    }
    return data;
  }

  async getCurrentUser() {
    const response = await this.request('/auth/me/');
    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }
    return response.json();
  }

  async updateCurrentUser(data) {
    
    const response = await this.request('/users/update_profile/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Update user error response:', errorData);
      
      let errorMessage = 'Failed to update profile';
      
      if (errorData.error) {
        errorMessage = errorData.error;
      } else if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (response.status === 400) {
        errorMessage = 'Invalid data provided';
      } else if (response.status === 401) {
        errorMessage = 'Please log in again';
      } else if (response.status === 403) {
        errorMessage = 'You do not have permission to update this profile';
      }
      
      throw new Error(errorMessage);
    }
    
    const result = await response.json();
    return result;
  }

  async logout() {
    try {
      await this.request('/auth/logout/', { method: 'POST' });
    } finally {
      this.clearTokens();
    }
  }

  // User Management
  async getUsers(params) {
    const queryString = params ? '?' + new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v != null)
    ).toString() : '';
    const response = await this.request(`/users/${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch users');
    return response.json();
  }

  async updateUser(id, userData) {
    const response = await this.request(`/users/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error('Update user error:', error);
      throw new Error(error.error || error.detail || 'Failed to update user');
    }
    
    return response.json();
  }

  async createUser(userData) {
    const response = await this.request('/users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error('Create user error:', error);
      throw new Error(error.error || error.detail || 'Failed to create user');
    }
    
    return response.json();
  }

  async deleteUser(id) {
    const response = await this.request(`/users/${id}/`, {
      method: 'DELETE',
    });
    
    if (response.status === 204 || response.status === 200) {
      return { success: true, message: 'User deleted successfully' };
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Delete user error:', errorData);
      throw new Error(errorData.error || errorData.detail || 'Failed to delete user');
    }
    
    try {
      return await response.json();
    } catch {
      return { success: true, message: 'User deleted successfully' };
    }
  }

  async getUserCount() {
    const response = await this.request('/users/count/');
    if (!response.ok) throw new Error('Failed to get user count');
    return response.json();
  }

  // Land Records
  async getLandRecords(params) {
    const queryString = params
      ? '?' +
        new URLSearchParams(
          Object.entries(params).filter(([_, v]) => v != null)
        ).toString()
      : '';
    const response = await this.request(`/land-records/${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch land records');

    const data = await response.json();

    const recordsArray = Array.isArray(data.results)
      ? data.results
      : Array.isArray(data)
      ? data
      : data.records || [];

    return recordsArray.map((record) => ({
      ...record,
      status: record.status || record.verification_status || 'pending',
    }));
  }

  // Search Land Records by ID number
  async searchLandRecords(query) {
    const response = await this.request(`/land-records/search/?id_number=${query}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to search land records');
    }

    return response.json();
  }

  async getLandRecord(id) {
    const response = await this.request(`/land-records/${id}/`);
    if (!response.ok) throw new Error('Failed to fetch land record');
    return response.json();
  }
  

  async createLandRecord(data) {
    const response = await this.request('/land-records/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create land record');
    }
    return response.json();
  }

  // Land Record Submission for Users
  async submitForVerification(data) {
    const response = await this.request('/land-records/submit-verification/', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to submit record for verification');
    }

    return response.json();
  }

  async updateLandRecord(id, data) {
    const response = await this.request(`/land-records/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update land record');
    return response.json();
  }

  async getLandRecordStats() {
    const response = await this.request('/dashboard/statistics/');
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  }

  async updateLandRecordStatus(id, status) {
    const response = await this.request(`/land-records/${id}/update_status/`, {
      method: 'POST',
      body: JSON.stringify({ verification_status: status }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || 'Failed to update record status');
    }

    const updated = await response.json();
    return {
      ...updated,
      status: updated.status || updated.verification_status || status,
    };
  }

  
  async downloadTransactionReport(params = {}) {
  
  const queryParams = {};
  
  // Only admins can filter by county
  if (params?.county && params.county !== 'all') queryParams.county = params.county;
  if (params?.status && params.status !== 'all') queryParams.status = params.status;
  if (params?.searchTerm) queryParams.search = params.searchTerm;
  if (params?.period && params.period !== 'all_time') queryParams.period = params.period;

  const queryString = Object.keys(queryParams).length > 0
      ? '?' + new URLSearchParams(queryParams).toString()
      : '';

  const response = await this.request(`/reports/transactions/${queryString}`, {
      method: 'GET',
  });

  
  if (!response.ok) {
      const errorText = await response.text();
      console.error("API: Download failed:", response.status, errorText);
      throw new Error(`Failed to download transaction report: ${response.status} ${errorText}`);
  }

  const blob = await response.blob();
  
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  
  let filename = `Transaction_Report_`;
  if (params.county && params.county !== 'all') {
    filename += `${params.county}_`;
  }
  filename += `${new Date().toISOString().split('T')[0]}.pdf`;
  
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
  
}
  
  async acceptTransfer(token, action) {
    const response = await this.request(`/transfers/accept/${token}/`, {
      method: 'POST',
      body: JSON.stringify({ action })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to process transfer');
    }
    return response.json();
  }

  // Get transfer details for email acceptance
  async getTransferDetails(token) {
    const response = await this.request(`/transfers/details/${token}/`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch transfer details');
    }
    return response.json();
  }

 async downloadLandRecordsReport(params = {}) {
  
  const queryParams = {};
  if (params?.searchTerm) queryParams.search = params.searchTerm;
  if (params?.status && params.status !== 'all') queryParams.status = params.status;
  if (params?.county && params.county !== 'all') queryParams.county = params.county;

  const queryString = Object.keys(queryParams).length > 0
      ? '?' + new URLSearchParams(queryParams).toString()
      : '';

  const response = await this.request(`/land-records/download-report/${queryString}`, {
      method: 'GET',
  });

  
  if (!response.ok) {
      const errorText = await response.text();
      console.error("API: Download failed:", response.status, errorText);
      throw new Error(`Failed to download land records report: ${response.status} ${errorText}`);
  }

  const blob = await response.blob();
  
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Land_Records_Report_${params.county || 'all'}_${new Date().toISOString().split('T')[0]}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
  
}
  

  async downloadDeed(recordId) {
    const response = await this.request(`/land-records/${recordId}/download-deed/`);
    if (!response.ok) throw new Error('Failed to download deed');
    return response.blob();
  }

  // Documents
async getDocuments(params = {}) {;
  
  const queryString = params ? '?' + new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v != null)
  ).toString() : '';
  
  const response = await this.request(`/documents/${queryString}`);
  
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('API: Failed to fetch documents:', response.status, errorText);
    throw new Error(`Failed to fetch documents: ${response.status}`);
  }

  const data = await response.json();
  
  return data;
}

  async getDocument(id) {
    const response = await this.request(`/documents/${id}/`);
    if (!response.ok) throw new Error('Failed to fetch document');
    return response.json();
  }

  async uploadDocument(formData) {
    const response = await this.request('/documents/', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      console.error("Upload failed:", data);
      throw new Error(data.error || JSON.stringify(data) || "Failed to upload document");
    }
    return data;
  }



  async verifyDocument(id, data) {
    const response = await this.request(`/documents/${id}/verify/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to verify document');
    return response.json();
  }

  // Verification Results
  async getVerificationResult(documentId) {
    const response = await this.request(`/documents/${documentId}/verification-result/`);
    if (!response.ok) throw new Error('Failed to fetch verification results');
    return response.json();
  }

  // Payments (Simulation)
  async initiatePayment(data) {
    const response = await this.request('/payments/initiate-verification/', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to initiate payment');
    }
    return response.json();
  }
  // Delete Verification Record
async deleteVerification(documentId) {
  const response = await this.request(`/verification/delete/${documentId}/`, {
    method: 'DELETE',
  });

  if (response.status === 204 || response.status === 200) {
    return { success: true, message: 'Verification deleted successfully' };
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to delete verification record');
  }

  return response.json();
}


  // Transactions
async getAllTransactions(params = {}) {
  
  let allTransactions = [];
  let nextPage = `${API_URL}/transactions/`;
  let pageCount = 0;

  const queryParams = new URLSearchParams();
  if (params.status) queryParams.append('status', params.status);
  if (params.search) queryParams.append('search', params.search);
  if (params.county) queryParams.append('county', params.county);
  
  const initialQueryString = queryParams.toString();
  if (initialQueryString) {
    nextPage = `${nextPage}?${initialQueryString}`;
  }

  while (nextPage) {
    pageCount++;
    
    const response = await fetch(nextPage, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
      },
    });

    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) continue;
      else break;
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch transactions: ${response.status}`);
    }

    const data = await response.json();
    
    const pageTransactions = data.results || data.transactions || data;
    const transactionsArray = Array.isArray(pageTransactions)
      ? pageTransactions
      : [pageTransactions];
    
    allTransactions = [...allTransactions, ...transactionsArray];
    
    nextPage = data.next;
    
    if (pageCount > 20) {
      console.warn("⚠️ Safety limit reached for transactions");
      break;
    }
  }

  return allTransactions;
}
async getTransactions(params) {
  const queryString = params ? '?' + new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v != null)
  ).toString() : '';
  
  const response = await this.request(`/transactions/${queryString}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch transactions');
  }
  
  const data = await response.json();
  
  let transactionsArray = [];
  
  if (Array.isArray(data)) {
    transactionsArray = data;
  } else if (data.results && Array.isArray(data.results)) {
    transactionsArray = data.results;
  } else if (data.transactions && Array.isArray(data.transactions)) {
    transactionsArray = data.transactions;
  } else if (typeof data === 'object') {
    transactionsArray = [data];
  }
  
  

  transactionsArray.forEach((t, i) => {
    
  });
  
  return transactionsArray;
}

  async createTransaction(data) {
    const response = await this.request('/transactions/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create transaction');
    }
    return response.json();
  }

  async updateTransaction(id, data) {
    const response = await this.request(`/transactions/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update transaction');
    return response.json();
  }

  async getRecentTransactions(days = 30) {
    const response = await this.request(`/transactions/recent/?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch recent transactions');
    return response.json();
  }

  async approveTransaction(id, data) {
    
    const response = await this.request(`/transactions/${id}/approve-legal/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error(" Approve transaction error:", errorData);
      throw new Error(errorData.error || errorData.detail || 'Failed to approve transaction');
    }
    
    const result = await response.json();
    return result;
  }

  async rejectTransaction(id, reason) {
    
    const response = await this.request(`/transactions/${id}/approve-legal/`, {
      method: 'POST',
      body: JSON.stringify({
        status: 'rejected',
        legal_notes: reason
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error(" Reject transaction error:", errorData);
      throw new Error(errorData.error || errorData.detail || 'Failed to reject transaction');
    }
    
    const result = await response.json();
    return result;
  }

  // Notifications
  async getAllNotifications() {
  
  let allNotifications = [];
  let nextPage = `${API_URL}/notifications/`;
  let pageCount = 0;

  while (nextPage) {
    pageCount++;
    
    const response = await fetch(nextPage, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
      },
    });

    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) continue;
      else break;
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch notifications: ${response.status}`);
    }

    const data = await response.json();
    
    const pageNotifications = data.results || data.notifications || data;
    const notificationsArray = Array.isArray(pageNotifications) 
      ? pageNotifications 
      : [pageNotifications];
    
    allNotifications = [...allNotifications, ...notificationsArray];
    
    nextPage = data.next;
    
    if (pageCount > 20) {
      console.warn("⚠️ Safety limit reached for notifications");
      break;
    }
  }

  return allNotifications;
}

  async getNotifications() {
    const response = await this.request('/notifications/');
    if (!response.ok) throw new Error('Failed to fetch notifications');
    return response.json();
  }

  async markNotificationAsRead(id) {
    const response = await this.request(`/notifications/${id}/mark_read/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Mark as read failed:', response.status, errorText);
      throw new Error('Failed to mark notification as read');
    }
    return response.json();
  }

  async markAllNotificationsAsRead() {
    const response = await this.request('/notifications/mark_all_read/', {
      method: 'POST',
    });
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Mark all as read failed:', response.status, errorText);
      throw new Error('Failed to mark all notifications as read');
    }
    return response.json();
  }

  async deleteNotification(id) {
    const response = await this.request(`/notifications/${id}/`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete notification');
    return response.ok;
  }

  // Dashboard
  async getDashboardStats() {
    const response = await this.request('/dashboard/statistics/');
    if (!response.ok) throw new Error('Failed to fetch dashboard stats');
    return response.json();
  }

  // User Management API  
  async downloadUserReport() {
    const response = await this.request('/reports/users/');
    if (!response.ok) throw new Error('Failed to download user report');
    return response.blob();
  }

  
  // Revenue
  async getOfficerRevenue() {
    const response = await this.request('/transfers/my-commissions/');
    if (!response.ok) throw new Error('Failed to fetch commissions');
    return response.json();
  }
  async getMyCommissions(params = {}) {
  const queryString = params ? '?' + new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v != null)
  ).toString() : '';
  
  const response = await this.request(`/transfers/my-commissions/${queryString}`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to fetch commissions');
  }
  
  return response.json();
}

  async downloadRevenueReport(params = {}) {
  
  const queryParams = {};
  if (params?.county && params.county !== 'all') queryParams.county = params.county;
  if (params?.period && params.period !== 'all_time') queryParams.period = params.period;

  const queryString = Object.keys(queryParams).length > 0
      ? '?' + new URLSearchParams(queryParams).toString()
      : '';

  const response = await this.request(`/reports/commissions/${queryString}`, {
      method: 'GET',
  });

  
  if (!response.ok) {
      const errorText = await response.text();
      console.error("API: Revenue report download failed:", response.status, errorText);
      throw new Error(`Failed to download revenue report: ${response.status} ${errorText}`);
  }

  const blob = await response.blob();
  
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  
  // Generate appropriate filename
  let filename = `Revenue_Report_`;
  if (params.county && params.county !== 'all') {
    filename += `${params.county}_`;
  }
  filename += `${new Date().toISOString().split('T')[0]}.pdf`;
  
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
  
}


  
  async initiateTransferPayment(transferData) {
    const response = await this.request('/payments/initiate-transfer/', {
      method: 'POST',
      body: JSON.stringify(transferData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to initiate transfer payment');
    }
    return response.json();
  }

  // Document Verification Payment Methods
async initiateDocumentPayment(documentId, phoneNumber) {
  
  const response = await this.request('/payments/initiate-verification/', {
    method: 'POST',
    body: JSON.stringify({
      document_id: documentId,
      phone_number: phoneNumber
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('Document payment initiation failed:', errorData);
    throw new Error(errorData.error || 'Failed to initiate document payment');
  }

  const result = await response.json();
  
  return result;
}

async checkPaymentStatus(checkoutRequestId) {

  const response = await this.request(`/payments/check-status/${checkoutRequestId}/`, {
    method: 'GET'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('Payment status check failed:', errorData);
    throw new Error(errorData.error || 'Failed to check payment status');
  }

  const result = await response.json();
  
  return result;
}


  async initiateTransferPayment(transferData) {
    const response = await this.request('/payments/initiate-transfer/', {
      method: 'POST',
      body: JSON.stringify(transferData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to initiate transfer payment');
    }
    return response.json();
  }

  async checkPaymentStatus(checkoutRequestId) {
    const response = await this.request(`/payments/check-status/${checkoutRequestId}/`, {
      method: 'GET'
    });

    if (!response.ok) {
      throw new Error('Failed to check payment status');
    }
    return response.json();
  }

  // ===================== LEGAL CASES =====================

  // Fetch all legal cases (GET /legal-cases/)
  async getLegalCases() {
    const response = await this.request('/legal-cases/', {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to fetch legal cases');
    }

    return response.json();
  }

  // Submit a new legal case (POST /legal-cases/)
  async submitLegalCase(caseData) {
    const response = await this.request('/legal-cases/submit/', {
      method: 'POST',
      body: JSON.stringify(caseData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to submit legal case');
    }

    return response.json();
  }

  // Fetch details of a single case 
  async getLegalCase(caseId) {
    const response = await this.request(`/legal-cases/${caseId}/`, {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to fetch case details');
    }

    return response.json();
  }

  // Update case status or resolution (for officers)
  async updateLegalCase(caseId, data) {
    const response = await this.request(`/legal-cases/${caseId}/update-status/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Failed to update legal case');
    }

    return response.json();
  }

  async updateLegalCaseStatus(caseId, data) {
  const response = await this.request(`/legal-cases/${caseId}/update-status/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to update case status');
  }

  return response.json();
}

 async getOwnershipHistory(recordId) {
  const response = await this.request(`/land-records/${recordId}/ownership-history/`);

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || "Failed to fetch ownership history");
  }

  return response.json();
}
 

  async downloadLegalCasesReport(params = {}) {
    
    const queryParams = {};
    if (params?.searchTerm) queryParams.search = params.searchTerm;
    if (params?.status && params.status !== 'all') queryParams.status = params.status;

    const queryString = Object.keys(queryParams).length > 0
        ? '?' + new URLSearchParams(queryParams).toString()
        : '';

    const response = await this.request(`/reports/legal-cases/${queryString}`, {
        method: 'GET',
    });

    
    if (!response.ok) {
        const errorText = await response.text();
        console.error("API: Legal cases download failed:", response.status, errorText);
        throw new Error(`Failed to download legal cases report: ${response.status} ${errorText}`);
    }

    const blob = await response.blob();
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // Generate filename 
    let filename = `Legal_Cases_Report_`;
    if (params.status && params.status !== 'all') {
      filename += `${params.status}_`;
    }
    filename += `${new Date().toISOString().split('T')[0]}.pdf`;
    
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    
  }
  

  // Get Kenya counties 
  async getCounties() {
    // Return the list of Kenya counties
    return [
      { value: 'nairobi', label: 'Nairobi' },
      { value: 'mombasa', label: 'Mombasa' },
      { value: 'kwale', label: 'Kwale' },
      { value: 'kilifi', label: 'Kilifi' },
      { value: 'tana_river', label: 'Tana River' },
      { value: 'lamu', label: 'Lamu' },
      { value: 'taita_taveta', label: 'Taita Taveta' },
      { value: 'garissa', label: 'Garissa' },
      { value: 'wajir', label: 'Wajir' },
      { value: 'mandera', label: 'Mandera' },
      { value: 'marsabit', label: 'Marsabit' },
      { value: 'isiolo', label: 'Isiolo' },
      { value: 'meru', label: 'Meru' },
      { value: 'tharaka_nithi', label: 'Tharaka-Nithi' },
      { value: 'embu', label: 'Embu' },
      { value: 'kitui', label: 'Kitui' },
      { value: 'machakos', label: 'Machakos' },
      { value: 'makueni', label: 'Makueni' },
      { value: 'nyandarua', label: 'Nyandarua' },
      { value: 'nyeri', label: 'Nyeri' },
      { value: 'kirinyaga', label: 'Kirinyaga' },
      { value: 'muranga', label: 'Murang\'a' },
      { value: 'kiambu', label: 'Kiambu' },
      { value: 'turkana', label: 'Turkana' },
      { value: 'west_pokot', label: 'West Pokot' },
      { value: 'samburu', label: 'Samburu' },
      { value: 'trans_nzoia', label: 'Trans Nzoia' },
      { value: 'uasin_gishu', label: 'Uasin Gishu' },
      { value: 'elgeyo_marakwet', label: 'Elgeyo-Marakwet' },
      { value: 'nandi', label: 'Nandi' },
      { value: 'baringo', label: 'Baringo' },
      { value: 'laikipia', label: 'Laikipia' },
      { value: 'nakuru', label: 'Nakuru' },
      { value: 'narok', label: 'Narok' },
      { value: 'kajiado', label: 'Kajiado' },
      { value: 'kericho', label: 'Kericho' },
      { value: 'bomet', label: 'Bomet' },
      { value: 'kakamega', label: 'Kakamega' },
      { value: 'vihiga', label: 'Vihiga' },
      { value: 'bungoma', label: 'Bungoma' },
      { value: 'busia', label: 'Busia' },
      { value: 'siaya', label: 'Siaya' },
      { value: 'kisumu', label: 'Kisumu' },
      { value: 'homa_bay', label: 'Homa Bay' },
      { value: 'migori', label: 'Migori' },
      { value: 'kisii', label: 'Kisii' },
      { value: 'nyamira', label: 'Nyamira' },
    ];
  }


async getAllLandRecords(params = {}) {
  
  let allRecords = [];
  let nextPage = `${API_URL}/land-records/`;
  let pageCount = 0;


  const queryParams = new URLSearchParams();
  if (params.page_size) queryParams.append('page_size', params.page_size);
  if (params.status) queryParams.append('status', params.status);
  if (params.search) queryParams.append('search', params.search);
  
  const initialQueryString = queryParams.toString();
  if (initialQueryString) {
    nextPage = `${nextPage}?${initialQueryString}`;
  }

  while (nextPage) {
    pageCount++;
    
    const response = await fetch(nextPage, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
      },
    });

    // Handle token expiration
    if (response.status === 401 || response.status === 403) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) continue; 
      else break;
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch land records: ${response.status}`);
    }

    const data = await response.json();
    

    const pageRecords = data.results || data.records || [];
    
    allRecords = [...allRecords, ...pageRecords];
    
    nextPage = data.next;
    
    if (pageCount > 10) {
      console.warn(" Safety limit reached - stopping pagination");
      break;
    }
  }

  
  const normalizedRecords = allRecords.map((record) => ({
    ...record,
    status: record.status || record.verification_status || 'pending',
  }));

  return normalizedRecords;
}
  

  // Get county-specific revenue data
  async getCountyRevenue(county = null) {
    const queryString = county ? `?county=${county}` : '';
    const response = await this.request(`/revenue/county/${queryString}`);
    if (!response.ok) throw new Error('Failed to fetch county revenue');
    return response.json();
  }

  // Get officer assignments by county
  async getOfficersByCounty(county) {
    const response = await this.request(`/users/by-county/?county=${county}`);
    if (!response.ok) throw new Error('Failed to fetch officers by county');
    return response.json();
  }
  async getAllUsers() {
  let allUsers = [];
  let nextPage = `${API_URL}/users/`;

  while (nextPage) {
    const response = await fetch(nextPage, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
      },
    });


    if (response.status === 401 || response.status === 403) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) continue; 
      else break;
    }

    const data = await response.json();
    allUsers = [...allUsers, ...(data.results || [])];
    nextPage = data.next;
  }

  return allUsers;
}


  // Utility
  isAuthenticated() {
    return this.accessToken !== null;
  }

  getAccessToken() {
    return this.accessToken;
  }
}

export const apiClient = new APIClient();
export default apiClient;