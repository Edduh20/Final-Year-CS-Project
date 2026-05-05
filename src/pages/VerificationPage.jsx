import { useEffect, useState } from 'react';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Eye,
  X,
  FileUp,
  DollarSign,
  MapPin,
  AlertTriangle,
  User,
  Shield,
  Trash2,
  MessageSquare,
} from 'lucide-react';



const DeleteConfirmModal = ({ document, onClose, onConfirm, loading }) => {
  if (!document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="flex justify-between items-center p-5 border-b">
          <h2 className="text-lg font-bold text-slate-800">Delete Document</h2>
          <button onClick={onClose}>
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="flex items-start gap-3 bg-red-50 p-4 rounded-lg border border-red-200">
            <AlertTriangle className="w-6 h-6 text-red-600 mt-0.5" />
            <div>
              <p className="font-semibold text-red-800">This action is permanent</p>
              <p className="text-sm text-red-700">
                You are about to delete <strong>{document.file_name}</strong>. This cannot be undone.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 border rounded-lg"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              disabled={loading}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 flex items-center gap-2"
            >
              {loading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};



// Payment Modal Component
const PaymentModal = ({ document, onClose, onPaymentSuccess }) => {
  const [paymentStarted, setPaymentStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [showPhoneInput, setShowPhoneInput] = useState(true);
  const [checkoutRequestId, setCheckoutRequestId] = useState('');
  const [paymentStatus, setPaymentStatus] = useState('pending');


  const handlePayment = async () => {
    if (!phoneNumber) {
      setError('Please enter your phone number');
      setPaymentStarted(false);
      return;
    }

    const phoneRegex = /^(254|0)[17]\d{8}$/;
    if (!phoneRegex.test(phoneNumber.replace(/\s/g, ''))) {
      setError('Please enter a valid Kenyan phone number (e.g., 0712345678)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      
      const result = await api.initiateDocumentPayment(document.id, phoneNumber);
      

      if (result.success) {
        setCheckoutRequestId(result.checkout_request_id);
        setShowPhoneInput(false);
        pollPaymentStatus(result.checkout_request_id);
      } else {
        setError(result.error || 'Payment initiation failed');
        setLoading(false);
      }
    } catch (err) {
      console.error('Payment initiation error:', err);
      setError(err.message || 'Payment failed. Please try again.');
      setLoading(false);
    }
  };

  const pollPaymentStatus = async (checkoutId) => {
    let attempts = 0;
    const maxAttempts = 30;
    
    const checkStatus = async () => {
      attempts++;
      
      try {
        const status = await api.checkPaymentStatus(checkoutId);
        
        if (status.status === 'completed') {
          setPaymentStatus('completed');
          setLoading(false);
          
          setTimeout(() => {
            onPaymentSuccess();
            onClose();
          }, 2000);
          return;
        } else if (status.status === 'failed') {
          setPaymentStatus('failed');
          setError('Payment failed. Please try again.');
          setShowPhoneInput(true);
          setLoading(false);
          return;
        }
        
        if (attempts < maxAttempts && status.status === 'pending') {
          setTimeout(checkStatus, 6000);
        } else if (attempts >= maxAttempts) {
          setError('Payment timeout. Please check your phone and try again.');
          setShowPhoneInput(true);
          setLoading(false);
        }
      } catch (err) {
        console.error('Status check error:', err);
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 6000);
        } else {
          setError('Unable to verify payment status. Please contact support.');
          setShowPhoneInput(true);
          setLoading(false);
        }
      }
    };
    
    setTimeout(checkStatus, 6000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="flex justify-between items-center p-6 border-b border-slate-200">
          <h2 className="text-xl font-bold text-slate-800">
            {showPhoneInput ? 'M-Pesa Payment' : paymentStatus === 'completed' ? 'Payment Successful' : 'Processing Payment'}
          </h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-700">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4 p-4 bg-blue-50 rounded-lg">
            <text className="w-8 h-8 text-blue-600" />
            <div>
              <p className="font-semibold text-blue-800">Document Verification</p>
              <p className="text-2xl font-bold text-blue-600">KES 100</p>
              <p className="text-sm text-blue-600">For: {document.file_name || document.document_file_name}</p>
            </div>
          </div>

          {showPhoneInput ? (
            <>
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Enter M-Pesa Phone Number
                </label>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="0712345678 or 254712345678"
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Enter your Safaricom number to receive payment prompt
                </p>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  {error}
                </div>
              )}

              <button
                onClick={handlePayment}
                disabled={loading || !phoneNumber}
                className="w-full bg-emerald-600 text-white py-3 rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Initiating...
                  </>
                ) : (
                  <>
                    <text className="w-5 h-5" />
                    Pay KES 100 via M-Pesa
                  </>
                )}
              </button>
            </>
          ) : paymentStatus === 'completed' ? (
            <div className="text-center py-4">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <p className="text-slate-700 font-semibold mb-2">Payment Successful!</p>
              <p className="text-sm text-slate-600 mb-4">
                Your document is now being processed with OCR verification.
              </p>
              <p className="text-xs text-slate-500">
                You will be notified once the verification is complete.
              </p>
            </div>
          ) : (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
              <p className="text-slate-700 font-semibold mb-2">Check your phone</p>
              <p className="text-sm text-slate-600 mb-4">
                Enter your M-Pesa PIN to complete payment of KES 100
              </p>
              <p className="text-xs text-slate-500">
                Waiting for payment confirmation...
              </p>
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Upload Document Modal Component
const UploadDocumentModal = ({ onClose, onDocumentUploaded }) => {
  const [fileName, setFileName] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const uploadedFile = e.target.files[0];
      
      if (uploadedFile.size > 5 * 1024 * 1024) {
        setError('File size must be less than 5MB.');
        setFile(null);
        setFileName('');
        return;
      }
      
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
      if (!allowedTypes.includes(uploadedFile.type)) {
        setError('Only PDF, JPG, and PNG files are allowed.');
        setFile(null);
        setFileName('');
        return;
      }
      
      setFile(uploadedFile);
      setFileName(uploadedFile.name);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setLoading(true);

    try {

      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_file_name', fileName || file.name);
      formData.append('document_file_type', file.type || 'unknown');

    
      const result = await api.uploadDocument(formData);
      
      
      setSuccess('Document uploaded successfully! It is now pending payment for verification.');
      
      setFileName('');
      setFile(null);
      
      setTimeout(() => {
        onDocumentUploaded();
        onClose();
      }, 2000);
      
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload document. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b border-slate-200 sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-slate-800">Upload Document for Verification</h2>
          <button 
            onClick={handleClose} 
            disabled={loading}
            className="text-slate-500 hover:text-slate-700 disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Upload Failed</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg flex items-start gap-2">
              <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Success!</p>
                <p className="text-sm">{success}</p>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Select Document File *
            </label>
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-slate-400 transition-colors">
              <input
                type="file"
                onChange={handleFileChange}
                required
                disabled={loading}
                accept=".pdf,.jpg,.jpeg,.png"
                className="hidden"
                id="file-upload"
              />
              <label 
                htmlFor="file-upload" 
                className="cursor-pointer block"
              >
                <Upload className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                <p className="text-slate-600 font-medium">
                  {file ? file.name : 'Choose a file'}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  Click to browse or drag and drop
                </p>
                <p className="text-xs text-slate-400 mt-2">
                  PDF, JPG, PNG (Max 5MB)
                </p>
              </label>
            </div>
            
            {file && (
              <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="w-8 h-8 text-emerald-600" />
                    <div>
                      <p className="font-medium text-slate-800">{file.name}</p>
                      <p className="text-sm text-slate-500">
                        {Math.round(file.size / 1024)} KB • {file.type}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setFile(null);
                      setFileName('');
                    }}
                    disabled={loading}
                    className="text-slate-400 hover:text-slate-600 disabled:opacity-50"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-blue-800 mb-1">Verification Process</p>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Upload your land document (title deed, lease agreement, etc.)</li>
                  <li>• Pay KES 100 for OCR verification</li>
                  <li>• System will automatically match with database records</li>
                  <li>• Get instant verification result (Verified or Rejected)</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg font-medium hover:bg-slate-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !file}
              className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload Document
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Document Detail Modal Component
const DocumentDetailModal = ({ document, onClose, onPaymentInitiated }) => {
  const { user } = useAuth();
  
  const getStatusInfo = (status) => {
    const statusMap = {
      pending_payment: { 
        icon: Clock, 
        color: 'bg-amber-100 text-amber-700',
        label: 'Pending Payment',
        description: 'Payment required to start verification'
      },
      payment_completed: { 
        icon: Clock, 
        color: 'bg-blue-100 text-blue-700',
        label: 'Payment Completed', 
        description: 'Payment received, processing starting soon'
      },
      processing: { 
        icon: AlertCircle, 
        color: 'bg-blue-100 text-blue-700',
        label: 'Processing', 
        description: 'OCR verification in progress'
      },
      verified: { 
        icon: CheckCircle, 
        color: 'bg-green-100 text-green-700',
        label: 'Verified', 
        description: 'Document successfully verified'
      },
      rejected: { 
        icon: XCircle, 
        color: 'bg-red-100 text-red-700',
        label: 'Rejected', 
        description: 'Document verification failed'
      },
      needs_review: { 
        icon: AlertTriangle, 
        color: 'bg-orange-100 text-orange-700',
        label: 'Needs Review', 
        description: 'Manual review required'
      }
    };
    return statusMap[status] || statusMap.pending_payment;
  };

  const statusInfo = getStatusInfo(document.status);
  const StatusIcon = statusInfo.icon;


  const getPropertyDetails = () => {
    const ocrData = document.ocr_metadata || {};
    const landRecord = document.land_record;
    
    let location = ocrData.location || (landRecord ? landRecord.land_records_location : null) || 'Not extracted yet';
    location = location.replace(/\s+Size\s*:?\s*\d+\.?\d*\s*hectares?/i, '').trim();
    
    let ownerName = ocrData.owner_full_name || 'Not extracted yet';
    ownerName = ownerName.replace(/\s+Owner\s+ID\s+Number\s*:?\s*\d*/i, '').trim();
    
    return {
      parcelNumber: ocrData.parcel_number || 
                    (landRecord ? landRecord.land_records_parcel_number : null) ||
                    'Not extracted yet',
      deedNumber: ocrData.deed_number || 
                  (landRecord ? landRecord.land_records_deed_number : null) ||
                  'Not extracted yet',
      location: location,
      ownerName: ownerName,
      ownerId: ocrData.owner_id_number || 'Not extracted yet',
      landSize: ocrData.land_size || 'Not extracted yet'
    };
  };

  const propertyDetails = getPropertyDetails();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b border-slate-200 sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-slate-800">Document Details</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-700">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Document Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-emerald-100 rounded-lg">
                <FileText className="w-8 h-8 text-emerald-600" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-800">
                  {document.file_name}
                </h3>
                <p className="text-slate-600">
                  Uploaded on {new Date(document.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${statusInfo.color}`}>
              <StatusIcon className="w-4 h-4" />
              <span className="font-medium">{statusInfo.label}</span>
            </div>
          </div>

          {/* Status Description */}
          <div className="bg-slate-50 p-4 rounded-lg">
            <p className="text-slate-700">{statusInfo.description}</p>
          </div>

          {/* Property Details Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Document Information */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Document Information
              </h4>
              
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">File Type:</span>
                  <span className="font-medium">{document.file_type || 'N/A'}</span>
                </div>
                
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">Uploaded By:</span>
                  <span className="font-medium">
                    {document.uploaded_by?.user_full_name || 'You'}
                  </span>
                </div>
                
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">Upload Date:</span>
                  <span className="font-medium">
                    {new Date(document.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Property Information */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Property Information
              </h4>
              
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">Parcel Number:</span>
                  <span className="font-medium text-emerald-600">{propertyDetails.parcelNumber}</span>
                </div>
                
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">Deed Number:</span>
                  <span className="font-medium">{propertyDetails.deedNumber}</span>
                </div>
                
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">Location:</span>
                  <span className="font-medium">{propertyDetails.location}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Owner Details */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <User className="w-5 h-5" />
              Owner Details
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex justify-between py-2 border-b border-slate-200">
                <span className="text-slate-600">Owner Name:</span>
                <span className="font-medium">{propertyDetails.ownerName}</span>
              </div>
              
              <div className="flex justify-between py-2 border-b border-slate-200">
                <span className="text-slate-600">Land Size:</span>
                <span className="font-medium">{propertyDetails.landSize}</span>
              </div>
            </div>
          </div>

          {/* Verification Results with Mismatch Details */}
          {(document.verification_notes) && (
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                Verification Results
              </h4>
              
              <div className={`p-4 rounded-lg border ${
                document.status === 'verified' 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-start gap-2">
                  {document.status === 'verified' ? (
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className={`font-medium mb-2 ${
                      document.status === 'verified' ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {document.status === 'verified' ? 'Document Verified' : 'Document Rejected'}
                    </p>
                    
                    {/* Enhanced mismatch display */}
                    {document.status === 'rejected' && document.verification_notes.includes('🔍 Specific Mismatches Found:') ? (
                      <div className="space-y-3">
                        {/* Main rejection reason */}
                        <p className="text-red-700 whitespace-pre-line">
                          {document.verification_notes.split('Specific Mismatches Found:')[0].trim()}
                        </p>
                        
                        {/* Mismatch details */}
                        <div className="mt-3 p-3 bg-red-100 rounded border border-red-200">
                          <p className="text-sm font-semibold text-red-800 mb-2">🔍 Specific Mismatches Found:</p>
                          {document.verification_notes.split('\n').map((line, index) => {
                            if (line.trim().startsWith('•')) {
                              return (
                                <div key={index} className="ml-2 mb-2">
                                  <p className="text-red-700 font-medium text-sm">{line}</p>
                                </div>
                              );
                            }
                            else if (line.trim().startsWith('System:') || line.trim().startsWith('Document:')) {
                              return (
                                <p key={index} className="ml-4 text-red-600 text-xs">{line}</p>
                              );
                            }
                            return null;
                          })}
                        </div>
                      </div>
                    ) : (
                      <p className="text-slate-700 whitespace-pre-line">
                        {document.verification_notes}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Payment Button for Users */}
          {user?.role === 'user' && document.status === 'pending_payment' && (
            <div className="pt-6 border-t border-slate-200">
              <button
                onClick={() => onPaymentInitiated(document)}
                className="w-full bg-emerald-600 text-white py-4 rounded-lg font-semibold hover:bg-emerald-600 transition-colors flex items-center justify-center gap-3"
              >
                <text className="w-6 h-6" />
                <div className="text-left">
                  <p className="font-bold">Pay KES 100 for OCR Verification</p>
                  <p className="text-sm opacity-90">Start the automated verification process</p>
                </div>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main Verification Page Component
export default function VerificationPage() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentDocument, setPaymentDocument] = useState(null);
  const [error, setError] = useState('');
  const [deleteDoc, setDeleteDoc] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError('');
      
      const data = await api.getDocuments();
      
      let docs = [];
      if (Array.isArray(data)) {
        docs = data;
      } else if (data.results && Array.isArray(data.results)) {
        docs = data.results;
      } else if (data.documents && Array.isArray(data.documents)) {
        docs = data.documents;
      } else {
        console.warn('Unexpected documents response format:', data);
        docs = [];
      }
      
      setDocuments(docs);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError('Failed to load documents. Please try again.');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const confirmDelete = async () => {
  if (!deleteDoc) return;

  setIsDeleting(true);
  try {
    await api.deleteVerification(deleteDoc.id);
    setDeleteDoc(null);
    fetchDocuments();
  } catch (err) {
    console.error(err);
    alert('Failed to delete document');
  } finally {
    setIsDeleting(false);
  }
};


  const handleDocumentUploaded = () => {
    fetchDocuments();
  };

  const handlePaymentInitiated = (document) => {
    setPaymentDocument(document);
    setShowPaymentModal(true);
    setSelectedDoc(null);
  };

  const handlePaymentSuccess = () => {
    fetchDocuments();
    setShowPaymentModal(false);
    setPaymentDocument(null);
  };

   


  const getStatusInfo = (status) => {
    const statusMap = {
      pending_payment: { 
        icon: Clock, 
        color: 'bg-amber-100 text-amber-800 border border-amber-200',
        label: 'Pending Payment',
        description: 'Payment required'
      },
      payment_completed: { 
        icon: Clock, 
        color: 'bg-blue-100 text-blue-800 border border-blue-200',
        label: 'Payment Completed', 
        description: 'Processing starting soon'
      },
      processing: { 
        icon: AlertCircle, 
        color: 'bg-blue-100 text-blue-800 border border-blue-200',
        label: 'Processing', 
        description: 'OCR in progress'
      },
      verified: { 
        icon: CheckCircle, 
        color: 'bg-green-100 text-green-800 border border-green-200',
        label: 'Verified', 
        description: 'Document verified'
      },
      rejected: { 
        icon: XCircle, 
        color: 'bg-red-100 text-red-800 border border-red-200',
        label: 'Rejected', 
        description: 'Verification failed'
      },
      needs_review: { 
        icon: AlertTriangle, 
        color: 'bg-orange-100 text-orange-800 border border-orange-200',
        label: 'Needs Review', 
        description: 'Manual review required'
      }
    };
    return statusMap[status] || statusMap.pending_payment;
  };


  const getPropertyName = (doc) => {
    const ocrData = doc.ocr_metadata || {};
    const landRecord = doc.land_record;
    

    const parcelNumber = ocrData.parcel_number || 
                        (landRecord ? landRecord.land_records_parcel_number : null);
    
    if (parcelNumber) {
      return parcelNumber;
    }
    

    return ocrData.location || 
           (landRecord ? landRecord.land_records_location : null) ||
           'Scanning...';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
        <span className="ml-3 text-slate-600">Loading documents...</span>
      </div>
    );
  }

  const canUploadDocument = user?.role === 'user';

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
          <FileText className="w-8 h-8 text-emerald-600" />
          Document Verification
        </h1>
        
        {canUploadDocument && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 transition-colors"
          >
            <FileUp className="w-5 h-5" />
            Upload Document
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <p className="text-slate-600 mb-6">
          {user?.role === 'land_officer' || user?.role === 'admin'
            ? "Review and verify documents submitted by users."
            : "Upload documents for OCR verification. Pay KES 100 to start the process."
          }
        </p>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">Document Name</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">Property Name</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">Uploaded</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">Actions</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">Delete</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {documents.map((doc, index) => {
                const statusInfo = getStatusInfo(doc.status);
                const StatusIcon = statusInfo.icon;
                const propertyName = getPropertyName(doc);
                
                return (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    {/* Document Name */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
              
                        <div>
                          <div className="text-sm font-medium text-slate-900">
                            {doc.file_name || 'Unnamed Document'}
                          </div>
                          <div className="text-sm text-slate-500">
                            {doc.file_type || 'Document'}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Property Name */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        
                        <div>
                          <div className="text-sm font-medium text-slate-900">
                            {propertyName}
                          </div>
                          {doc.land_record?.land_records_location && (
                            <div className="text-xs text-slate-500">
                              {doc.land_record.land_records_location}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Upload Date */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-slate-900">
                        {doc.created_at ? 
                          new Date(doc.created_at).toLocaleDateString() : 
                          'N/A'}
                      </div>
                      <div className="text-xs text-slate-500">
                        {doc.created_at ? 
                          new Date(doc.created_at).toLocaleTimeString() : 
                          ''}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="px-4 py-3">
                      <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${statusInfo.color}`}>
                        <StatusIcon className="w-3 h-3" />
                        <span>{statusInfo.label}</span>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-2">
                        {/* View Button */}
                        <button
                          onClick={() => setSelectedDoc(doc)}
                          className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                        >
                          View Details
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex gap-2">
                    <button
                  onClick={() => setDeleteDoc(doc)}
                  className="p-2 text-slate-600 hover:text-red-600 transition-colors rounded-lg hover:bg-slate-100"
                >
                  <Trash2 className="w-4 h-4" />
                </button>

              </div>
                  </td>

                    
                  </tr>
                );
              })}
            </tbody>
          </table>

          {documents.length === 0 && (
            <div className="text-center py-16">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No documents found</h3>
              <p className="text-slate-600 max-w-md mx-auto">
                {canUploadDocument 
                  ? "Get started by uploading your first document for verification."
                  : "No documents have been submitted for verification yet."
                }
              </p>
              {canUploadDocument && (
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="mt-4 inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 transition-colors"
                >
                  <FileUp className="w-5 h-5" />
                  Upload Your First Document
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Upload Document Modal */}
      {showUploadModal && (
        <UploadDocumentModal
          onClose={() => setShowUploadModal(false)}
          onDocumentUploaded={handleDocumentUploaded}
        />
      )}

      {/* Payment Modal */}
      {showPaymentModal && paymentDocument && (
        <PaymentModal
          document={paymentDocument}
          onClose={() => {
            setShowPaymentModal(false);
            setPaymentDocument(null);
          }}
          onPaymentSuccess={handlePaymentSuccess}
        />
      )}

      {/* Enhanced Document Detail Modal */}
      {selectedDoc && (
        <DocumentDetailModal
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
          onPaymentInitiated={handlePaymentInitiated}
        />
      )}

          {deleteDoc && (
      <DeleteConfirmModal
        document={deleteDoc}
        onClose={() => setDeleteDoc(null)}
        onConfirm={confirmDelete}
        loading={isDeleting}
      />
    )}

    </div>
  );
}