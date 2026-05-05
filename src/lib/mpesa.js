// utils/mpesa.js
const MPESA_CONFIG = {
  baseUrl: import.meta.env.VITE_MPESA_BASE_URL,
  consumerKey: import.meta.env.VITE_MPESA_CONSUMER_KEY,
  consumerSecret: import.meta.env.VITE_MPESA_CONSUMER_SECRET,
  passKey: import.meta.env.VITE_MPESA_PASSKEY,
  shortCode: import.meta.env.VITE_MPESA_SHORTCODE,
  callbackUrl: import.meta.env.VITE_MPESA_CALLBACK_URL,
};

  

class MpesaService {
  constructor() {
    this.accessToken = null;
    this.tokenExpiry = null;
  }

  async getAccessToken() {
    if (this.accessToken && this.tokenExpiry && Date.now() < this.tokenExpiry) {
      return this.accessToken;
    }

    try {
      const credentials = btoa(`${MPESA_CONFIG.consumerKey}:${MPESA_CONFIG.consumerSecret}`);
      const response = await fetch(`${MPESA_CONFIG.baseUrl}/oauth/v1/generate?grant_type=client_credentials`, {
        method: 'GET',
        headers: {
          'Authorization': `Basic ${credentials}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get M-Pesa access token');
      }

      const data = await response.json();
      this.accessToken = data.access_token;
      this.tokenExpiry = Date.now() + (data.expires_in * 1000) - 60000; 
      return this.accessToken;
    } catch (error) {
      console.error('M-Pesa token error:', error);
      throw error;
    }
  }

  async initiateSTKPush(phoneNumber, amount, accountReference, transactionDesc) {
    try {
      const token = await this.getAccessToken();
      
      const formattedPhone = this.formatPhoneNumber(phoneNumber);
      const timestamp = this.getCurrentTimestamp();
      const password = this.generatePassword(timestamp);

      const requestData = {
        BusinessShortCode: MPESA_CONFIG.shortCode,
        Password: password,
        Timestamp: timestamp,
        TransactionType: 'CustomerPayBillOnline',
        Amount: Math.floor(amount), 
        PartyA: formattedPhone,
        PartyB: MPESA_CONFIG.shortCode,
        PhoneNumber: formattedPhone,
        CallBackURL: MPESA_CONFIG.callbackUrl,
        AccountReference: accountReference,
        TransactionDesc: transactionDesc
      };

      const response = await fetch(`${MPESA_CONFIG.baseUrl}/mpesa/stkpush/v1/processrequest`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.errorMessage || 'STK Push failed');
      }

      const data = await response.json();
      return {
        success: true,
        checkoutRequestID: data.CheckoutRequestID,
        merchantRequestID: data.MerchantRequestID,
        responseCode: data.ResponseCode,
        responseDescription: data.ResponseDescription
      };

    } catch (error) {
      console.error('M-Pesa STK Push error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async checkTransactionStatus(checkoutRequestID) {
    try {
      const token = await this.getAccessToken();
      const timestamp = this.getCurrentTimestamp();
      const password = this.generatePassword(timestamp);

      const requestData = {
        BusinessShortCode: MPESA_CONFIG.shortCode,
        Password: password,
        Timestamp: timestamp,
        CheckoutRequestID: checkoutRequestID
      };

      const response = await fetch(`${MPESA_CONFIG.baseUrl}/mpesa/stkpushquery/v1/query`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error('Failed to check transaction status');
      }

      const data = await response.json();
      return data;

    } catch (error) {
      console.error('Transaction status check error:', error);
      throw error;
    }
  }

  formatPhoneNumber(phone) {
    let formatted = phone.replace(/\s+/g, '');
    
    if (formatted.startsWith('0')) {
      formatted = '254' + formatted.substring(1);
    } else if (formatted.startsWith('+')) {
      formatted = formatted.substring(1);
    }
    
    return formatted;
  }

  getCurrentTimestamp() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hour = String(now.getHours()).padStart(2, '0');
  const minute = String(now.getMinutes()).padStart(2, '0');
  const second = String(now.getSeconds()).padStart(2, '0');

  return `${year}${month}${day}${hour}${minute}${second}`;
}


  generatePassword(timestamp) {
    const stringToEncode = MPESA_CONFIG.shortCode + MPESA_CONFIG.passKey + timestamp;
    return btoa(stringToEncode);
  }
}

export const mpesaService = new MpesaService();