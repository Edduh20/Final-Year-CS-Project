import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { 
    Gavel, 
    AlertTriangle, 
    Plus, 
    Clock, 
    CheckCircle, 
    XCircle,
    Search,
    FileText,
    User,
    MapPin,
    MessageSquare,
    ChevronDown,
    ChevronUp,
    Edit
} from 'lucide-react';

const SubmitCaseModal = ({ onClose, onCaseSubmitted }) => {
    const [formData, setFormData] = useState({
        land_record_parcel: '',
        case_type: 'dispute',
        case_title: '',
        case_description: '',
        case_priority: 'medium'
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!formData.land_record_parcel || !formData.case_title || !formData.case_description) {
            setError('Please fill in all required fields');
            return;
        }

        setLoading(true);
        try {
            const submissionData = {
                land_record_parcel: formData.land_record_parcel.trim(),
                case_type: formData.case_type,
                case_title: formData.case_title.trim(),
                case_description: formData.case_description.trim(),
                case_priority: formData.case_priority
            };
            
            if (formData.evidence_document_id && formData.evidence_document_id.trim()) {
                submissionData.evidence_document_id = formData.evidence_document_id.trim();
            }
            
            await api.submitLegalCase(submissionData);
            onCaseSubmitted();
            onClose();
        } catch (err) {
            setError(err.message || 'Failed to submit case');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center p-6 border-b border-emerald-200 sticky top-0 bg-white">
                    <h2 className="text-2xl font-bold text-emerald-800">Submit Legal Case</h2>
                    <button onClick={onClose} className="text-emerald-500 hover:text-emerald-700 transition-colors">
                        <XCircle className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Land Record Parcel Number *
                        </label>
                        <input
                            type="text"
                            value={formData.land_record_parcel}
                            onChange={(e) => setFormData({...formData, land_record_parcel: e.target.value})}
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                            placeholder="Enter parcel number (e.g., LR/ISIOLO/9169/141)"
                            required
                        />
                        <p className="text-xs text-slate-500 mt-1">
                            Enter the parcel number
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Case Type *
                        </label>
                        <select
                            value={formData.case_type}
                            onChange={(e) => setFormData({...formData, case_type: e.target.value})}
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                        >
                            <option value="dispute">Boundary Dispute</option>
                            <option value="inheritance">Inheritance Dispute</option>
                            <option value="fraud">Fraud Case</option>
                            <option value="multiple_claim">Multiple Ownership Claim</option>
                            <option value="encroachment">Encroachment</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Case Title *
                        </label>
                        <input
                            type="text"
                            value={formData.case_title}
                            onChange={(e) => setFormData({...formData, case_title: e.target.value})}
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                            placeholder="Brief case title"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Case Description *
                        </label>
                        <textarea
                            value={formData.case_description}
                            onChange={(e) => setFormData({...formData, case_description: e.target.value})}
                            rows={4}
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                            placeholder="Detailed description of the legal case..."
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Priority
                        </label>
                        <select
                            value={formData.case_priority}
                            onChange={(e) => setFormData({...formData, case_priority: e.target.value})}
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                        >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="urgent">Urgent</option>
                        </select>
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 border border-emerald-300 text-emerald-700 rounded-lg hover:bg-emerald-50 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 bg-emerald-600 text-white py-2 rounded-lg font-semibold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                    Submitting...
                                </>
                            ) : (
                                <>
                                    <Gavel className="w-4 h-4" />
                                    Submit Case
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

const CaseDetailsModal = ({ caseItem, onClose, onCaseUpdated, user }) => {
    const [statusUpdate, setStatusUpdate] = useState({
        status: caseItem.status,
        land_officer_notes: caseItem.land_officer_notes || ''
    });
    const [updatingStatus, setUpdatingStatus] = useState(false);
    const [error, setError] = useState('');

    const handleStatusUpdate = async () => {
        setUpdatingStatus(true);
        setError('');
        
        try {
            await api.updateLegalCaseStatus(caseItem.id, statusUpdate);
            onCaseUpdated();
        } catch (err) {
            setError(err.message || 'Failed to update case status');
        } finally {
            setUpdatingStatus(false);
        }
    };

    const getStatusBadge = (status) => {
        const badges = {
            submitted: { icon: Clock, color: 'bg-amber-100 text-amber-700', label: 'Submitted' },
            under_review: { icon: AlertTriangle, color: 'bg-blue-100 text-blue-700', label: 'Under Review' },
            resolved: { icon: CheckCircle, color: 'bg-green-100 text-green-700', label: 'Resolved' },
            dismissed: { icon: XCircle, color: 'bg-slate-100 text-slate-700', label: 'Dismissed' },
        };
        return badges[status] || badges.submitted;
    };

    const getPriorityBadge = (priority) => {
        const priorities = {
            low: 'bg-green-100 text-green-700',
            medium: 'bg-amber-100 text-amber-700',
            high: 'bg-orange-100 text-orange-700',
            urgent: 'bg-red-100 text-red-700',
        };
        return priorities[priority] || priorities.medium;
    };

    const statusBadge = getStatusBadge(caseItem.status);
    const StatusIcon = statusBadge.icon;

    const canManageCase = ['land_officer', 'legal_officer'].includes(user?.role);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center p-6 border-b border-emerald-200 sticky top-0 bg-white">
                    <h2 className="text-2xl font-bold text-emerald-800">Case Details</h2>
                    <button onClick={onClose} className="text-emerald-500 hover:text-emerald-700 transition-colors">
                        <XCircle className="w-6 h-6" />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Case Header */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h3 className="text-xl font-semibold text-slate-800 mb-2">{caseItem.title}</h3>
                            <p className="text-slate-600 capitalize">{caseItem.case_type?.replace('_', ' ')}</p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${statusBadge.color}`}>
                                <StatusIcon className="w-4 h-4" />
                                {statusBadge.label}
                            </span>
                            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${getPriorityBadge(caseItem.priority)}`}>
                                <StatusIcon className="w-4 h-4" />
                                {caseItem.priority}
                            </span>
                        </div>
                    </div>

                    {/* Case Description */}
                    <div>
                        <h4 className="font-semibold text-slate-700 mb-2">Case Description</h4>
                        <p className="text-slate-600 bg-slate-50 p-4 rounded-lg">{caseItem.description}</p>
                    </div>

                    {/* Land Record Details */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 className="font-semibold text-slate-700 mb-3">Land Record</h4>
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <MapPin className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-600">
                                        <strong>Parcel:</strong> {caseItem.land_record_details?.parcel_number || 'N/A'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <FileText className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-600">
                                        <strong>Deed:</strong> {caseItem.land_record_details?.deed_number || 'N/A'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <User className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-600">
                                        <strong>Location:</strong> {caseItem.land_record_details?.location || 'N/A'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <User className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-600">
                                        <strong>Owner:</strong> {caseItem.land_record_details?.current_owner || 'N/A'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 className="font-semibold text-slate-700 mb-3">Case Information</h4>
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <User className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-600">
                                        <strong>Submitted By:</strong> {caseItem.legal_officer?.full_name || 'N/A'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <User className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-600">
                                        <strong>Legal Officer:</strong> {caseItem.legal_officer?.full_name || 'Not Assigned'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-600">
                                        <strong>Created:</strong> {new Date(caseItem.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Case Management Section for Officers/Admin */}
                    {canManageCase && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 className="font-semibold text-slate-700 mb-3">Case Management</h4>
                            {error && (
                                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 mb-3">
                                    {error}
                                </div>
                            )}
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">
                                        Update Status
                                    </label>
                                    <select
                                        value={statusUpdate.status}
                                        onChange={(e) => setStatusUpdate({...statusUpdate, status: e.target.value})}
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                                    >
                                        <option value="submitted">Submitted</option>
                                        <option value="under_review">Under Review</option>
                                        <option value="resolved">Resolved</option>
                                        <option value="dismissed">Dismissed</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">
                                        Officer Notes
                                    </label>
                                    <textarea
                                        value={statusUpdate.land_officer_notes}
                                        onChange={(e) => setStatusUpdate({...statusUpdate, land_officer_notes: e.target.value})}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                                        placeholder="Add case notes or updates..."
                                    />
                                </div>
                                <button
                                    onClick={handleStatusUpdate}
                                    disabled={updatingStatus}
                                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                                >
                                    {updatingStatus ? (
                                        <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                            Updating...
                                        </>
                                    ) : (
                                        <>
                                            <CheckCircle className="w-4 h-4" />
                                            Update Case
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Officer Notes */}
                    {caseItem.land_officer_notes && (
                        <div>
                            <h4 className="font-semibold text-slate-700 mb-2">Officer Notes & Updates</h4>
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <p className="text-slate-700 whitespace-pre-wrap">{caseItem.land_officer_notes}</p>
                            </div>
                        </div>
                    )}

                    {/* Case Timeline */}
                    <div>
                        <h4 className="font-semibold text-slate-700 mb-3">Case Timeline</h4>
                        <div className="space-y-3">
                            <div className="flex items-start gap-3">
                                <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2"></div>
                                <div>
                                    <p className="font-medium text-slate-800">Case Submitted</p>
                                    <p className="text-sm text-slate-500">
                                        {new Date(caseItem.created_at).toLocaleDateString()} at{' '}
                                        {new Date(caseItem.created_at).toLocaleTimeString()}
                                    </p>
                                </div>
                            </div>
                            {caseItem.updated_at !== caseItem.created_at && (
                                <div className="flex items-start gap-3">
                                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                                    <div>
                                        <p className="font-medium text-slate-800">Last Updated</p>
                                        <p className="text-sm text-slate-500">
                                            {new Date(caseItem.updated_at).toLocaleDateString()} at{' '}
                                            {new Date(caseItem.updated_at).toLocaleTimeString()}
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default function LegalCasesPage() {
    const { user } = useAuth();
    const [cases, setCases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showSubmitModal, setShowSubmitModal] = useState(false);
    const [selectedCase, setSelectedCase] = useState(null);
    const [expandedCase, setExpandedCase] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [downloadingReport, setDownloadingReport] = useState(false);

    useEffect(() => {
        fetchCases();
    }, []);

    const fetchCases = async () => {
        try {
            const data = await api.getLegalCases();
            setCases(data);
        } catch (error) {
            console.error('Error fetching cases:', error);
            setCases([]);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        const badges = {
            submitted: { icon: Clock, color: 'bg-amber-100 text-amber-700', label: 'Submitted' },
            under_review: { icon: AlertTriangle, color: 'bg-blue-100 text-blue-700', label: 'Under Review' },
            resolved: { icon: CheckCircle, color: 'bg-green-100 text-green-700', label: 'Resolved' },
            dismissed: { icon: XCircle, color: 'bg-slate-100 text-slate-700', label: 'Dismissed' },
        };
        return badges[status] || badges.submitted;
    };

    const getPriorityBadge = (priority) => {
        const priorities = {
            low: 'bg-green-100 text-green-700',
            medium: 'bg-amber-100 text-amber-700',
            high: 'bg-orange-100 text-orange-700',
            urgent: 'bg-red-100 text-red-700',
        };
        return priorities[priority] || priorities.medium;
    };

    const toggleExpandCase = (caseId) => {
        setExpandedCase(expandedCase === caseId ? null : caseId);
    };

    const handleDownloadReport = async () => {
        setDownloadingReport(true);
        try {
            const params = {};
            if (searchTerm) params.searchTerm = searchTerm;
            
            await api.downloadLegalCasesReport(params);
        } catch (error) {
            console.error('Error downloading legal cases report:', error);
            alert('Failed to download report: ' + error.message);
        } finally {
            setDownloadingReport(false);
        }
    };

    // Check user roles and cases
    const canSubmitCases = user?.role === 'legal_officer';
    const isUserView = user?.role === 'user' || user?.role === 'admin';
    const isOfficerView = ['land_officer', 'legal_officer'].includes(user?.role);
    const hasCases = cases.length > 0;

    // Filter cases based on search
    const filteredCases = cases.filter(caseItem => 
        caseItem.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        caseItem.land_record_details?.parcel_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        caseItem.case_type?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Show loading state
    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
                    {isUserView ? 'My Legal Cases' : 'Legal Cases Management'}
                </h1>
                
                <div className="flex items-center gap-4">
                    {/* Search for officers/admin and users with cases */}
                    {(isOfficerView || (isUserView && hasCases)) && (
                        <div className="relative">
                            <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                            <input
                                type="text"
                                placeholder="Search cases..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                            />
                        </div>
                    )}
                    
                    {/* Download Report Button */}
                    {(isOfficerView || (isUserView && hasCases)) && (
                        <button
                            onClick={handleDownloadReport}
                            disabled={downloadingReport}
                            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
                        >
                            {downloadingReport ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                    Downloading...
                                </>
                            ) : (
                                <>
                                    <FileText className="w-5 h-5" />
                                    Download Report
                                </>
                            )}
                        </button>
                    )}
                    
                    {canSubmitCases && (
                        <button
                            onClick={() => setShowSubmitModal(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 transition-colors"
                        >
                            <Plus className="w-5 h-5" />
                            Submit New Case
                        </button>
                    )}
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                {isUserView ? (
                    /* User View - Card Layout */
                    filteredCases.length === 0 ? (
                        <div className="text-center py-12">
                            <Gavel className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-slate-600 mb-2">No Legal Cases</h3>
                            <p className="text-slate-500 max-w-md mx-auto">
                                {searchTerm ? 'No cases match your search.' : 'You don\'t have any active legal cases. Legal cases are created by officers when there are disputes or issues with your land records.'}
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {filteredCases.map((caseItem) => {
                                const statusBadge = getStatusBadge(caseItem.status);
                                const StatusIcon = statusBadge.icon;
                                const isExpanded = expandedCase === caseItem.id;

                                return (
                                    <div key={caseItem.id} className="border border-slate-200 rounded-lg hover:shadow-md transition-shadow">
                                        {/* Case Header */}
                                        <div 
                                            className="p-4 cursor-pointer"
                                            onClick={() => toggleExpandCase(caseItem.id)}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="font-semibold text-slate-800 text-lg mb-1">
                                                            {caseItem.title}
                                                        </h3>
                                                        <p className="text-slate-600 text-sm capitalize mb-2">
                                                            {caseItem.case_type?.replace('_', ' ')}
                                                        </p>
                                                        <div className="flex items-center gap-4 text-sm text-slate-500">
                                                            <span className="flex items-center gap-1">
                                                                <MapPin className="w-4 h-4" />
                                                                Parcel: {caseItem.land_record_details?.parcel_number || 'N/A'}
                                                            </span>
                                                            <span>
                                                                Created: {new Date(caseItem.created_at).toLocaleDateString()}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium capitalize ${getPriorityBadge(caseItem.priority)}`}>
                                                        {caseItem.priority}
                                                    </span>
                                                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusBadge.color}`}>
                                                        <StatusIcon className="w-3 h-3" />
                                                        {statusBadge.label}
                                                    </span>
                                                    {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Expanded Details */}
                                        {isExpanded && (
                                            <div className="px-4 pb-4 border-t border-slate-100 pt-4">
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                                                    <div>
                                                        <h4 className="font-medium text-slate-700 mb-2">Case Description</h4>
                                                        <p className="text-slate-600 text-sm">{caseItem.description}</p>
                                                    </div>
                                                    <div>
                                                        <h4 className="font-medium text-slate-700 mb-2">Case Information</h4>
                                                        <div className="space-y-2 text-sm text-slate-600">
                                                            <div className="flex items-center gap-2">
                                                                <User className="w-4 h-4 text-slate-400" />
                                                                <span>Officer: {caseItem.legal_officer?.full_name || 'Not assigned'}</span>
                                                            </div>
                                                            {caseItem.land_officer_notes && (
                                                                <div>
                                                                    <p className="font-medium mb-1">Officer Notes:</p>
                                                                    <p className="text-slate-500 bg-slate-50 p-2 rounded">
                                                                        {caseItem.land_officer_notes}
                                                                    </p>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => setSelectedCase(caseItem)}
                                                        className="flex items-center gap-2 px-3 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700"
                                                    >
                                                        <MessageSquare className="w-4 h-4" />
                                                        View Details
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )
                ) : (
                    /* Officer/Admin View - Table Layout */
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-slate-200">
                            <thead className="bg-slate-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Case Details</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Land Record</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Priority</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Status</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200">
                                {filteredCases.map((caseItem) => {
                                    const statusBadge = getStatusBadge(caseItem.status);
                                    const StatusIcon = statusBadge.icon;
                                    
                                    return (
                                        <tr key={caseItem.id} className="hover:bg-slate-50">
                                            <td className="px-4 py-3">
                                                <div>
                                                    <p className="font-semibold text-slate-800">{caseItem.title}</p>
                                                    <p className="text-sm text-slate-600 capitalize">{caseItem.case_type?.replace('_', ' ') || 'N/A'}</p>
                                                    <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                                                        {caseItem.description}
                                                    </p>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    
                                                    <div>
                                                        <p className="font-medium text-slate-800">
                                                            {caseItem.land_record_details?.parcel_number || 'N/A'}
                                                        </p>
                                                        <p className="text-sm text-slate-600">
                                                            {caseItem.land_record_details?.location || 'N/A'}
                                                        </p>
                                                        <p className="text-xs text-slate-500">
                                                            Owner: {caseItem.land_record_details?.current_owner || 'N/A'}
                                                        </p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium capitalize ${getPriorityBadge(caseItem.priority)}`}>
                                                    {caseItem.priority}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusBadge.color}`}>
                                                    <StatusIcon className="w-3 h-3" />
                                                    {statusBadge.label}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-slate-600">
                                                {new Date(caseItem.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-4 py-3">
                                                <button
                                                    onClick={() => setSelectedCase(caseItem)}
                                                    className="flex items-center gap-1 px-3 py-1 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700"
                                                >
                                                    <Edit className="w-3 h-3" />
                                                    Manage
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>

                        {filteredCases.length === 0 && (
                            <div className="text-center py-12">
                                <Gavel className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                                <p className="text-slate-600">
                                    {searchTerm ? 'No cases match your search' : 'No legal cases found'}
                                </p>
                                <p className="text-sm text-slate-500 mt-1">
                                    {user?.role === 'legal_officer' || user?.role === 'admin'
                                        ? "Submit a legal case to flag land records for review."
                                        : "No legal cases require your attention."
                                    }
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {showSubmitModal && (
                <SubmitCaseModal
                    onClose={() => setShowSubmitModal(false)}
                    onCaseSubmitted={fetchCases}
                />
            )}

            {selectedCase && (
                <CaseDetailsModal
                    caseItem={selectedCase}
                    user={user}
                    onClose={() => {
                        setSelectedCase(null);
                        fetchCases(); 
                    }}
                    onCaseUpdated={fetchCases}
                />
            )}
        </div>
    );
}