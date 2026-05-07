import { useState, useEffect } from 'react';
import { Send, AlertTriangle, DollarSign, User, X, CheckCircle, Phone } from 'lucide-react';
import api from '../lib/api';

export default function TransferModal({ landRecord, onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    to_owner_id_number: '',
    transaction_type: 'transfer',
    amount: '',
    phone_number: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [checkoutRequestId, setCheckoutRequestId] = useState('');
  const [showPaymentProcessing, setShowPaymentProcessing] = useState(false);
  const [ownerInfo, setOwnerInfo] = useState(null);
  const [transferCompleted, setTransferCompleted] = useState(false); 

  const transferFees = {
    legal_officer:400, 
    land_officer: 600,  
  };
  const totalTransferFee = transferFees.legal_officer + transferFees.land_officer;

  useEffect(() => {
    
  }, []);

  // Check if land can be transferred
  if (landRecord.has_legal_case || landRecord.status === 'flagged') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl max-w-md w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-red-600">Transfer Blocked</h2>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
              <X className="w-6 h-6" />
            </button>
          </div>
          
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
            <div>
              <p className="font-semibold text-red-800 mb-2">
                This property cannot be transferred
              </p>
              <p className="text-sm text-red-700">
                {landRecord.legal_case_description || 
                 'This land has an active legal case or is flagged. Transfer is not allowed until resolved.'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full mt-6 px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const verifyIdNumber = async () => {
    if (!formData.to_owner_id_number) {
      setError('Please enter an ID number');
      return false;
    }

    try {
      setLoading(true);
      setError('');
      
      const idNumber = formData.to_owner_id_number.trim();

      const response = await api.request(`/users/?id_number=${idNumber}`);
      
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const responseText = await response.text();
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        throw new Error('Invalid server response');
      }

      let usersArray = [];

      if (Array.isArray(data)) {
        usersArray = data;
      } else if (data && typeof data === 'object') {
        if (Array.isArray(data.results)) {
          usersArray = data.results;
        } else if (Array.isArray(data.users)) {
          usersArray = data.users;
        } else if (Array.isArray(data.data)) {
          usersArray = data.data;
        } else if (data.id || data.user_id) {
          usersArray = [data];
        } else {
          const keys = Object.keys(data);
          const arrayKey = keys.find(key => Array.isArray(data[key]));
          if (arrayKey) {
            usersArray = data[arrayKey];
          }
        }
      }


      if (usersArray.length > 0) {
        const user = usersArray[0];
        setOwnerInfo(user);
        return true;
      } else {
        setError(`No user found with ID number: ${idNumber}`);
        return false;
      }

    } catch (error) {
      console.error("Verification error:", error);
      setError(error.message || 'Failed to verify ID number');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleContinueToPayment = async () => {
    const verified = await verifyIdNumber();
    if (verified) {
      setFormData(prev => ({
        ...prev,
        amount: totalTransferFee.toString()
      }));
      setStep(2);
    }
  };

  const pollPaymentStatus = async (checkoutId) => {
    
    let attempts = 0;
    const maxAttempts = 30;
    
    const checkStatus = async () => {
      attempts++;
      
      try {
        const statusResult = await api.checkPaymentStatus(checkoutId);
        
        if (statusResult.status === 'completed') {
          setShowPaymentProcessing(false);
          setLoading(false);
          setTransferCompleted(true); 
          setStep(3);
          return true;
        } else if (statusResult.status === 'failed') {
          setError('Payment failed. Please try again.');
          setShowPaymentProcessing(false);
          setLoading(false);
          return true;
        } else if (attempts >= maxAttempts) {
          setError('Payment timeout. Please check your phone and try again.');
          setShowPaymentProcessing(false);
          setLoading(false);
          return true;
        } else {
          setTimeout(checkStatus, 1000);
          return false;
        }
      } catch (error) {
        console.error("Error checking payment status:", error);
        if (attempts >= maxAttempts) {
          setError('Failed to verify payment status. Please contact support.');
          setShowPaymentProcessing(false);
          setLoading(false);
          return true;
        } else {
          setTimeout(checkStatus, 1000);
          return false;
        }
      }
    };
    
    await checkStatus();
  };

  const handlePayment = async () => {
    setError('');

    // Validation
    if (!formData.phone_number) {
      setError('Please enter your M-Pesa phone number');
      return;
    }

    const amount = parseFloat(formData.amount);
    if (amount < totalTransferFee) {
      setError(`Amount must be at least KES ${totalTransferFee} to cover transfer fees`);
      return;
    }

    if (!ownerInfo) {
      setError('Recipient information is missing. Please go back and verify the ID again.');
      return;
    }

    setLoading(true);

    try {
      

      const paymentResult = await api.initiateTransferPayment({
        land_record_id: landRecord.id,
        to_owner_id_number: formData.to_owner_id_number,
        transaction_type: formData.transaction_type,
        amount: amount,
        phone_number: formData.phone_number,
      });


      if (paymentResult.success) {
        if (paymentResult.checkout_request_id && paymentResult.checkout_request_id.startsWith('SIMULATED_')) {
          
          setShowPaymentProcessing(false);
          setLoading(false);
          setError('');
          setTransferCompleted(true); 
          setStep(3);

          return;
        } else {
          setCheckoutRequestId(paymentResult.checkout_request_id);
          setShowPaymentProcessing(true);
          await pollPaymentStatus(paymentResult.checkout_request_id);
        }
      } else {
        setError(paymentResult.error || 'Payment initiation failed');
      }

    } catch (err) {
      console.error("Payment error:", err);
      setError(err.message || 'Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };


  const handleSuccessClose = () => {
    if (transferCompleted && onSuccess) {
      onSuccess(); 
    }
    onClose(); 
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-slate-800">
            {step === 3 ? 'Transfer Successful' : 'Initiate Land Transfer'}
          </h2>
          <button 
            onClick={step === 3 ? handleSuccessClose : onClose} 
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="px-6 pt-4">
          <div className="flex items-center justify-between mb-6">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    s <= step
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {s}
                </div>
                {s < 3 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      s < step ? 'bg-emerald-600' : 'bg-slate-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Step 1: Property Details & New Owner */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                <h3 className="font-semibold text-slate-800 mb-3">Property Details</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-slate-600">Parcel Number</p>
                    <p className="font-semibold">{landRecord.parcel_number}</p>
                  </div>
                  <div>
                    <p className="text-slate-600">Deed Number</p>
                    <p className="font-semibold">{landRecord.deed_number}</p>
                  </div>
                  <div>
                    <p className="text-slate-600">Location</p>
                    <p className="font-semibold">{landRecord.location}</p>
                  </div>
                  <div>
                    <p className="text-slate-600">Size</p>
                    <p className="font-semibold">{landRecord.size_hectares} Ha</p>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  New Owner ID Number * <User className="inline w-4 h-4" />
                </label>
                <input
                  type="text"
                  name="to_owner_id_number"
                  value={formData.to_owner_id_number}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  placeholder="Enter ID number"
                />
                <p className="text-xs text-slate-500 mt-1">
                  New owner must be registered in the system with their ID number.
                </p>
              </div>

              {ownerInfo && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-700">
                    <strong>Verified:</strong> {ownerInfo.full_name} 
                    {ownerInfo.phone_number && ` • ${ownerInfo.phone_number}`}
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Transaction Type
                </label>
                <select
                  name="transaction_type"
                  value={formData.transaction_type}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="transfer">Transfer</option>
                  <option value="sale">Sale</option>
                  <option value="gift">Gift</option>
                  <option value="inheritance">Inheritance</option>
                </select>
              </div>

              <button
                onClick={handleContinueToPayment}
                disabled={!formData.to_owner_id_number || loading}
                className="w-full bg-emerald-600 text-white py-3 rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Verifying ID...
                  </>
                ) : (
                  'Continue to Payment'
                )}
              </button>
            </div>
          )}

          {/* Step 2: Payment Details */}
          {step === 2 && !showPaymentProcessing && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <h3 className="font-semibold text-blue-800">ID Verified Successfully!</h3>
                </div>
                <p className="text-sm text-blue-700">
                  Transfer to: <strong>{ownerInfo?.full_name}</strong> (ID: {ownerInfo?.id_number})
                </p>
              </div>

              {/* Transfer Fee Breakdown */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                <h3 className="font-semibold text-slate-800 mb-3">Transfer Fees</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Legal Officer Fee:</span>
                    <span className="font-semibold">KES {transferFees.legal_officer}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Land Officer Fee:</span>
                    <span className="font-semibold">KES {transferFees.land_officer}</span>
                  </div>
                  <div className="flex justify-between border-t border-slate-300 pt-2">
                    <span className="text-slate-800 font-semibold">Total Required:</span>
                    <span className="text-green-600 font-bold">KES {totalTransferFee}</span>
                  </div>
                </div>
              </div>

              {/* Payment Form */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Transaction Type
                  </label>
                  <select
                    name="transaction_type"
                    value={formData.transaction_type}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="transfer">Transfer</option>
                    <option value="sale">Sale</option>
                    <option value="gift">Gift</option>
                    <option value="inheritance">Inheritance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Amount (KES) *
                  </label>
                  <input
                    type="number"
                    name="amount"
                    value={formData.amount}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    placeholder={`Minimum KES ${totalTransferFee}`}
                    min={totalTransferFee}
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Must cover transfer fees of KES {totalTransferFee}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    M-Pesa Phone Number *
                    <Phone className="inline w-4 h-4 ml-1" />
                  </label>
                  <input
                    type="tel"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    placeholder="07XXXXXXXX"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    You will receive an M-Pesa prompt on this number
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => setStep(1)}
                    className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50"
                  >
                    Back
                  </button>
                  <button
                    onClick={handlePayment}
                    disabled={!formData.phone_number || !formData.amount || loading}
                    className="flex-1 bg-emerald-600 text-white py-2 rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        Processing...
                      </>
                    ) : (
                      <>
                        <DollarSign className="w-5 h-5" />
                        Pay & Transfer
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Payment Processing */}
          {step === 2 && showPaymentProcessing && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-600 mx-auto mb-4"></div>
              <h3 className="text-xl font-bold text-slate-800 mb-2">Processing Payment</h3>
              <p className="text-slate-600 mb-4">
                Check your phone for M-Pesa STK Push
              </p>
              <div className="p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
                <p className="font-semibold mb-1">Instructions:</p>
                <ul className="list-disc list-inside space-y-1 text-left">
                  <li>Check your phone for M-Pesa prompt</li>
                  <li>Enter your M-Pesa PIN to complete payment</li>
                  <li>Transfer will auto-complete after payment</li>
                </ul>
              </div>
            </div>
          )}

          {/* Step 3: Success */}
          {step === 3 && (
            <div className="text-center py-8">
              <div className="flex justify-center mb-4">
                <div className="bg-green-100 p-4 rounded-full">
                  <CheckCircle className="w-12 h-12 text-green-600" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-slate-800 mb-2">Transfer Initiated Successfully!</h3>
              <p className="text-slate-600 mb-4">
                Your payment has been processed and the transfer to <strong>{ownerInfo?.full_name || ownerInfo?.user_full_name}</strong> has been initiated.
              </p>
              <div className="p-4 bg-slate-50 rounded-lg text-left text-sm text-slate-700">
                <p className="mb-2"><strong>What happens next:</strong></p>
                <ul className="list-disc list-inside space-y-1">
                  <li>The transfer will be processed automatically</li>
                  <li>Both parties will receive notifications</li>
                  <li>New deed number will be generated</li>
                  <li>Ownership will be updated in the system</li>
                </ul>
              </div>
              <button
                onClick={handleSuccessClose}
                className="w-full mt-6 bg-emerald-600 text-white py-3 rounded-lg font-semibold hover:bg-emerald-700"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}