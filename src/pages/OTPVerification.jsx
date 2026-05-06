import { useState } from 'react';
import { AlertCircle, Shield, RefreshCw, ArrowLeft, FileCheck2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function OTPVerification({ 
  email: propEmail = '', 
  onVerified, 
  onBack 
}) {
  const navigate = useNavigate();
  const [email, setEmail] = useState(propEmail);
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!email || !otp) {
      setError('Email and OTP are required');
      return;
    }

    if (otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);

    try {
      const API_URL = import.meta.env.VITE_API_URL;
      const response = await fetch(`${API_URL}/auth/verify-otp/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'OTP verification failed');
      }

      setSuccess('Email verified successfully! You can now log in.');
      
      if (onVerified) {
        setTimeout(() => {
          onVerified();
        }, 1500);
      } else {
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              message: 'Email verified successfully! Please log in.',
              verifiedEmail: email 
            } 
          });
        }, 1500);
      }

    } catch (err) {
      setError(err.message || 'Invalid or expired OTP. Please try again.');
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (!email) {
      setError('Please enter email first to resend OTP');
      return;
    }

    setResending(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_URL}/auth/resend-otp/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to resend OTP');
      }

      setSuccess('OTP has been resent to your email');
    } catch (err) {
      setError(err.message || 'Failed to resend OTP');
    } finally {
      setResending(false);
    }
  };

  const handleBackClick = () => {
    if (onBack) {
      onBack();
    } else {
      navigate('/login', { replace: true });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Back Button */}
          <button
            onClick={handleBackClick}
            className="mb-4 flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to login</span>
          </button>

          {/* Header */}
          <h1 className="text-3xl font-bold text-center text-emerald-800 mb-2">
            TitleGuard
          </h1>
          <h1 className="text-xl font-bold text-center text-slate-600 mb-2">
            Verify Your Email
          </h1>
          <p className="text-center text-slate-600 mb-8">
            Enter the 6-digit code sent to your email
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-start gap-2">
              <Shield className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-emerald-800">{success}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Input */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-shadow"
                placeholder="Enter your email"
                required
              />
            </div>

            {/* OTP Input */}
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-slate-700 mb-2 text-center">
                Enter OTP Code
              </label>
              <input
                id="otp"
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                className="w-full px-4 py-3 text-center text-2xl tracking-widest border-2 border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-shadow font-mono"
                placeholder="000000"
                autoComplete="off"
                required
              />
              <p className="text-xs text-slate-500 text-center mt-2">
                Code expires in 10 minutes
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !email || otp.length !== 6}
              className="w-full bg-emerald-600 text-white py-3 rounded-lg font-medium hover:bg-emerald-700 focus:ring-4 focus:ring-emerald-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-slate-600 mb-3">
              Didn't receive the code?
            </p>
            <button
              onClick={handleResendOTP}
              disabled={resending || !email}
              className="inline-flex items-center gap-2 text-emerald-600 hover:text-emerald-700 font-medium text-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${resending ? 'animate-spin' : ''}`} />
              {resending ? 'Resending...' : 'Resend OTP'}
            </button>
          </div>

          <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <p className="text-xs text-slate-600 text-center">
              <strong>Note:</strong> After verification, you will be redirected to login page.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}