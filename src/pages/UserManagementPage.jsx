import { toast } from "react-hot-toast";
import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Users, Plus, Search, Edit, Trash2, X, FileDown, Mail, Phone, Shield } from 'lucide-react';

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  /* DELETE STATE */
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const allUsers = await api.getAllUsers();
      setUsers(allUsers || []);
    } catch (error) {
      console.error("Error fetching users:", error);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      (user.full_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.id_number || '').toString().toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.phone_number || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const getRoleBadge = (role) => {
    const badges = {
      admin: 'bg-red-100 text-red-700 border border-red-200',
      land_officer: 'bg-blue-100 text-blue-700 border border-blue-200',
      legal_officer: 'bg-amber-100 text-amber-700 border border-amber-200',
      user: 'bg-slate-100 text-slate-700 border border-slate-200',
    };
    return badges[role] || badges.user;
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setShowEditModal(true);
  };

  /* DELETE HANDLERS */
  const openDeleteModal = (user) => {
    setDeleteTarget({ id: user.id, name: user.full_name });
  };

  const confirmDelete = async () => {
    try {
      setDeleting(true);
      await api.deleteUser(deleteTarget.id);
      toast.success(`User "${deleteTarget.name}" deleted successfully!`);
      setDeleteTarget(null);
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(error?.message || 'Failed to delete user.');
    } finally {
      setDeleting(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const blob = await api.downloadUserReport();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `user-management-report-${new Date().toISOString().split('T')[0]}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('User report downloaded successfully!');
    } catch (error) {
      console.error('Failed to download user report:', error);
      toast.error(error?.message || 'Failed to download user report.');
    }
  };

  // ---------------------------
  // ADD USER MODAL 
  // ---------------------------
  const AddUserModal = () => {
    const [formData, setFormData] = useState({
      email: '',
      password: '',
      full_name: '',
      role: 'user',
      phone_number: '',
      id_number: '',
      county: '',
    });
    const [file, setFile] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [counties, setCounties] = useState([]);

    useEffect(() => {
      fetchCounties();
    }, []);

    const fetchCounties = async () => {
      try {
        const data = await api.getCounties();
        setCounties(data || []);
      } catch (err) {
        console.error('Failed to fetch counties:', err);
        setCounties([]);
      }
    };


    const isMinimalUserFlow = (formData.role === 'user' && (!formData.email && !formData.password)) || !!file;
    const isOfficer = ['land_officer', 'legal_officer'].includes(formData.role);
    const isRegularCreationFlow = ['user', 'admin'].includes(formData.role) && !isMinimalUserFlow;

    const handleRoleChange = (newRole) => {
      let updatedFormData = { ...formData, role: newRole };

      if (!['land_officer', 'legal_officer'].includes(newRole)) {
        updatedFormData.county = '';
      }

      if (newRole === 'user') {
          updatedFormData.email = '';
          updatedFormData.password = '';
          updatedFormData.phone_number = '';
          updatedFormData.id_number = '';
      }

      const newRoleRequiresPassword = ['user', 'admin'].includes(newRole);

      if (['land_officer', 'legal_officer'].includes(newRole)) {
          updatedFormData.password = '';
      }
      

      if (newRole === 'admin') {
          updatedFormData.password = '';
      }
      
      setFile(null);
      
      setFormData(updatedFormData);
    };


    const handleSubmit = async (e) => {
      e.preventDefault();
      setSubmitting(true);
      setError('');

      try {
        if (isMinimalUserFlow) {
          if (file) {
            const fd = new FormData();
            fd.append('file', file);
            const res = await api.request('/users/admin/add-minimal/', {
              method: 'POST',
              body: fd,
            });
            try {
              const json = await res.json();
              if (!res.ok) throw new Error(json?.error || 'Upload failed');
              toast.success('Bulk placeholder users uploaded!');
            } catch (err) {
              if (res?.created || res?.errors) {
                if (res.errors?.length) {
                  toast.error('Uploaded with some errors; check console');
                  console.warn('Upload errors', res.errors);
                } else {
                  toast.success('Bulk placeholder users uploaded!');
                }
              } else {
                throw err;
              }
            }
          } else {
            if (!formData.full_name || !formData.id_number) {
              setError('Full name and ID number required for placeholder users.');
              setSubmitting(false);
              return;
            }
            const fd = new FormData();
            fd.append('full_name', formData.full_name);
            fd.append('id_number', formData.id_number);
            const res2 = await api.request('/users/admin/add-minimal/', { method: 'POST', body: fd });
            try {
              const j = await res2.json();
              if (!res2.ok) throw new Error(j?.error || 'Failed.');
              toast.success('User added successfully!');
            } catch (err) {
              if (res2?.message || res2?.created) {
                toast.success('User added successfully!');
              } else throw err;
            }
          }
        }

        // ---------- Officer creation (OTP flow) ----------
        else if (isOfficer) {
          if (!formData.email || !formData.full_name || !formData.id_number) {
            setError('Email, full name and ID number are required for officers.');
            setSubmitting(false);
            return;
          }
          if (!formData.county) {
            setError('County is required for officers.');
            setSubmitting(false);
            return;
          }


          const payload = {
            email: formData.email,
            full_name: formData.full_name,
            role: formData.role,
            phone_number: formData.phone_number || undefined,
            id_number: formData.id_number || undefined,
            county: formData.county || undefined,
          };

          const resp = await api.request('/auth/create-officer/', {
            method: 'POST',
            body: JSON.stringify(payload),
          });


          try {
            const json = await resp.json();
            if (!resp.ok) throw new Error(json?.error || 'Failed to create officer');
            toast.success(`User (${formData.role}) created — OTP / temp password will be sent to email.`);
          } catch (err) {
            if (resp?.message || resp?.user) {
              toast.success(`User (${formData.role}) created — OTP / temp password will be sent to email.`);
            } else throw err;
          }
        }

        // ---------- Regular full user / Admin creation (Password flow) ----------
        else if (isRegularCreationFlow) {
          if (!formData.email || !formData.password || !formData.full_name) {
            setError('Email, password and full name are required for full users/admins.');
            setSubmitting(false);
            return;
          }
          await api.createUser({
            email: formData.email,
            password: formData.password,
            full_name: formData.full_name,
            role: formData.role,
            phone_number: formData.phone_number || undefined,
            id_number: formData.id_number || undefined,
          });
          toast.success(`User (${formData.role}) created successfully!`);
        }


        setShowAddModal(false);
        setFormData({
          email: '',
          password: '',
          full_name: '',
          role: 'user',
          phone_number: '',
          id_number: '',
          county: '',
        });
        setFile(null);
        fetchUsers();
      } catch (err) {
        console.error('Error creating user:', err);
        setError(err?.message || String(err) || 'Failed to create user');
        toast.error(err?.message || 'Failed to create user');
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white">
            <h2 className="text-xl font-bold text-slate-800">
              { isMinimalUserFlow ? 'Add User' : 'Add New User' }
            </h2>
            <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-600">
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}

            {/* role selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Role *</label>
              <select
                value={formData.role}
                onChange={(e) => handleRoleChange(e.target.value)} 
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              >
                <option value="user">User</option>
                <option value="land_officer">Land Officer</option>
                <option value="legal_officer">Legal Officer</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            {/* Conditional fields based on flow */}
            { isMinimalUserFlow ? (
              <>
                {/* Minimal fields */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Full Name *</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="John Doe"
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">ID Number *</label>
                  <input
                    type="text"
                    value={formData.id_number}
                    onChange={(e) => setFormData({ ...formData, id_number: e.target.value })}
                    placeholder="12345678"
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Or Upload CSV/Excel</label>
                  <input
                    type="file"
                    accept=".csv,.xls,.xlsx"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="w-full text-sm text-slate-600 border border-slate-300 rounded-lg p-2"
                  />
                  <p className="text-xs text-slate-500 mt-1">File should contain <code>full_name</code> and <code>id_number</code> columns.</p>
                </div>
              </>
            ) : (
              <>
                {/* Full user / officer / admin fields */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Full Name *</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="John Doe"
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Email *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder={isOfficer ? "officer@example.com" : "user/admin@example.com"}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                

                {!isOfficer && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Password *</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder={"Minimum 6 characters"}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                )}
                {isOfficer && (
                    <p className="text-sm text-slate-500 mt-1">A temporary password / OTP will be sent to the officer's email upon creation.</p>
                )}


                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number { isOfficer ? '*' : '(optional)' }</label>
                    <input
                      type="tel"
                      value={formData.phone_number}
                      onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                      placeholder="+254..."
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">ID Number *</label>
                    <input
                      type="text"
                      value={formData.id_number}
                      onChange={(e) => setFormData({ ...formData, id_number: e.target.value })}
                      placeholder="12345678"
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                {/* County only for officers */}
                {isOfficer && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">County Assignment *</label>
                    <select
                      required
                      value={formData.county}
                      onChange={(e) => setFormData({ ...formData, county: e.target.value })}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    >
                      <option value="">Select a county</option>
                      {counties.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                    <p className="text-xs text-slate-500 mt-1">Officer will handle transactions only in this county</p>
                  </div>
                )}
              </>
            )}

            <div className="flex gap-3 pt-4">
              <button type="button" onClick={() => setShowAddModal(false)} className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50">Cancel</button>
              <button type="submit" disabled={submitting} className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50">{submitting ? 'Saving...' : 'Save'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // ---------------------------
  // EDIT USER MODAL 
  // ---------------------------
  const EditUserModal = () => {
    if (!editingUser) return null;

    const [formData, setFormData] = useState({
      full_name: editingUser.full_name || '',
      role: editingUser.role || 'user',
      phone_number: editingUser.phone_number || '',
      id_number: editingUser.id_number || '',
      email: editingUser.email || '',
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async () => {
      setSubmitting(true);
      setError('');
      try {
        const payload = {
          full_name: formData.full_name,
          role: formData.role,
          phone_number: formData.phone_number || undefined,
          id_number: formData.id_number || undefined,
          email: formData.email || undefined,
        };
        await api.updateUser(editingUser.id, payload);
        toast.success('User updated successfully!');
        setShowEditModal(false);
        setEditingUser(null);
        fetchUsers();
      } catch (err) {
        console.error('Error updating user:', err);
        setError(err?.message || 'Failed to update user');
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-xl max-w-lg w-full">
          <div className="p-6 border-b flex justify-between items-center">
            <h2 className="text-xl font-bold text-slate-800">Edit User</h2>
            <button onClick={() => { setShowEditModal(false); setEditingUser(null); }} className="text-slate-400 hover:text-slate-600">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-6 space-y-4">
            {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Full Name *</label>
              <input type="text" value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} className="w-full px-4 py-2 border rounded-lg" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full px-4 py-2 border rounded-lg" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
                <input type="tel" value={formData.phone_number} onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })} className="w-full px-4 py-2 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">ID Number</label>
                <input type="text" value={formData.id_number} onChange={(e) => setFormData({ ...formData, id_number: e.target.value })} className="w-full px-4 py-2 border rounded-lg" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Role *</label>
              <select value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })} className="w-full px-4 py-2 border rounded-lg">
                <option value="user">User</option>
                <option value="land_officer">Land Officer</option>
                <option value="legal_officer">Legal Officer</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            <div className="flex gap-3 pt-4">
              <button onClick={() => { setShowEditModal(false); setEditingUser(null); }} className="flex-1 px-4 py-2 border rounded-lg">Cancel</button>
              <button onClick={handleSubmit} disabled={submitting} className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg">{submitting ? 'Updating...' : 'Update User'}</button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ---------------------------
  // RENDER
  // ---------------------------
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">User Management</h1>
          <p className="text-slate-600 mt-1">Manage system users and roles</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleDownloadReport} className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg">
            <FileDown className="w-5 h-5" />
            Download Report
          </button>
          <button onClick={() => setShowAddModal(true)} className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Add User
          </button>
        </div>
      </div>

      {/* STATS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {['admin', 'land_officer', 'legal_officer', 'user'].map((role) => {
          const count = users.filter(u => u.role === role).length;
          return (
            <div key={role} className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${getRoleBadge(role)}`}>
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-800">{count}</p>
                  <p className="text-sm text-slate-600 capitalize">{role.replace('_', ' ')}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* TABLE */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input type="text" placeholder="Search by name, email, ID, or phone..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500" />
          </div>

          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500">
            <option value="all">All Roles</option>
            <option value="admin">Admin</option>
            <option value="land_officer">Land Officer</option>
            <option value="legal_officer">Legal Officer</option>
            <option value="user">User</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-y border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">User</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">Contact</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">Role</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">Created</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div>
                        <p className="font-medium text-slate-800">{user.full_name}</p>
                        <p className="text-sm text-slate-500">{user.id_number || 'No ID'}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Mail className="w-4 h-4" />
                        {user.email || '—'}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Phone className="w-4 h-4" />
                        {user.phone_number || '—'}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getRoleBadge(user.role)}`}>
                      {user.role.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">{new Date(user.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button onClick={() => handleEdit(user)} className="p-2 text-slate-600 hover:text-emerald-600 rounded-lg hover:bg-slate-100"><Edit className="w-4 h-4" /></button>
                      <button
                        onClick={() => openDeleteModal(user)}
                        className="p-2 text-slate-600 hover:text-red-600 rounded-lg hover:bg-slate-100"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>

                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredUsers.length === 0 && (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No users found</p>
            </div>
          )}
        </div>
      </div>
     {deleteTarget && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
    <div className="bg-white rounded-xl max-w-md w-full shadow-xl border border-slate-200">
      
      {/* Header */}
      <div className="p-6 border-b border-slate-200 flex items-center gap-3">
        <div className="p-2 rounded-full bg-red-100 text-red-600">
          <Trash2 className="w-5 h-5" />
        </div>
        <h2 className="text-lg font-bold text-slate-800">
          Delete User
        </h2>
      </div>

      {/* Body */}
      <div className="p-6">
        <p className="text-slate-600 leading-relaxed">
          You are about to permanently delete the user
          <span className="font-semibold text-slate-800">
            {" "}“{deleteTarget.name}”
          </span>.
          <br />
          <span className="text-red-600 font-medium">
            This action cannot be undone.
          </span>
        </p>
      </div>

      {/* Footer */}
      <div className="p-6 pt-0 flex gap-3">
        <button
          onClick={() => setDeleteTarget(null)}
          disabled={deleting}
          className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50"
        >
          Cancel
        </button>

        <button
          onClick={confirmDelete}
          disabled={deleting}
          className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
        >
          {deleting ? 'Deleting…' : 'Delete User'}
        </button>
      </div>
    </div>
  </div>
)}



      {showAddModal && <AddUserModal />}
      {showEditModal && <EditUserModal />}
    </div>
  );
}