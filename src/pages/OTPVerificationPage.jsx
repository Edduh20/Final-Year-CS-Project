import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import OTPVerification from './OTPVerification';

export default function OTPVerificationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const [email, setEmail] = useState(location.state?.email || '');

  const handleVerified = () => {
    navigate('/login', { 
      replace: true,
      state: { 
        message: 'Email verified successfully! Please log in.',
        verifiedEmail: email
      } 
    });
  };

  const handleBack = () => {
    navigate('/login', { replace: true });
  };

  return (
    <OTPVerification 
      email={email}
      onVerified={handleVerified}
      onBack={handleBack}
    />
  );
}