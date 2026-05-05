import { useEffect, useState } from 'react';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Bell, CheckCircle, AlertCircle, Info, XCircle, Check, Trash2 } from 'lucide-react';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setError(null);
      setLoading(true);
      
      const data = await api.getAllNotifications();
      
      setNotifications(data);
    } catch (error) {
      setError(error.message || 'Failed to load notifications');
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      console.log('Marking notification as read:', id);
      

      try {
        const result = await api.markNotificationAsRead(id);
        console.log('Mark as read result:', result);
      } catch (markError) {
        console.warn('Primary mark as read failed, trying update method:', markError);
        
        await api.updateNotification(id, { read: true });
      }
      
      await fetchNotifications();
      
    } catch (error) {
      console.error('Error marking notification as read:', error);
      alert(`Failed to mark as read: ${error.message || 'Please try again'}`);
    }
  };

  const markAllAsRead = async () => {
    try {
      
      try {
        const result = await api.markAllNotificationsAsRead();
      } catch (bulkError) {
        console.warn('Bulk mark as read failed, marking individually:', bulkError);
        
        const unreadNotifications = notifications.filter(n => !n.read);
        for (const notification of unreadNotifications) {
          try {
            await api.markNotificationAsRead(notification.id);
          } catch (individualError) {
            console.warn(`Failed to mark notification ${notification.id} as read:`, individualError);
          }
        }
      }
      
      await fetchNotifications();
      
    } catch (error) {
      console.error('Error marking all as read:', error);
      alert(`Failed to mark all as read: ${error.message || 'Please try again'}`);
    }
  };

  const deleteNotification = async (id) => {
    try {
      await api.deleteNotification(id);
      fetchNotifications();
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const filteredNotifications = notifications.filter((n) =>
    filter === 'all' ? true : !n.read
  );
  
  const unreadCount = notifications.filter(n => !n.read).length;

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return { Icon: CheckCircle, color: 'text-green-600 bg-green-50' };
      case 'warning':
        return { Icon: AlertCircle, color: 'text-amber-600 bg-amber-50' };
      case 'error':
        return { Icon: XCircle, color: 'text-red-600 bg-red-50' };
      case 'info':
      default:
        return { Icon: Info, color: 'text-blue-600 bg-blue-50' };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-red-800 mb-2">Failed to Load Notifications</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchNotifications}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-slate-800">Notifications</h1>
        {notifications.length > 0 && (
          <button
            onClick={markAllAsRead}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
          >
            <Check className="w-4 h-4" />
            Mark All as Read
          </button>
        )}
      </div>

      <div className="flex gap-4 border-b border-slate-200">
        <button
          onClick={() => setFilter('all')}
          className={`pb-2 font-medium ${
            filter === 'all'
              ? 'text-emerald-600 border-b-2 border-emerald-600'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`pb-2 font-medium flex items-center gap-1 ${
            filter === 'unread'
              ? 'text-emerald-600 border-b-2 border-emerald-600'
              : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          Unread
          {unreadCount > 0 && (
            <span className="ml-1 px-2 py-0.5 text-xs font-semibold bg-red-500 text-white rounded-full">
              {unreadCount}
            </span>
          )}
        </button>
      </div>

      <div className="space-y-4">
        {filteredNotifications.map((notification) => {
          const { Icon, color } = getNotificationIcon(notification.type);
          const date = new Date(notification.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' - ' + new Date(notification.created_at).toLocaleDateString();

          return (
            <div
              key={notification.id}
              className={`bg-white rounded-xl shadow-sm border ${
                notification.read ? 'border-slate-200' : 'border-emerald-300 ring-1 ring-emerald-300'
              } hover:shadow-md transition-shadow`}
            >
              <div className="p-4 flex gap-4">
                <div className={`p-3 rounded-lg ${color} h-min`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-grow">
                  {notification.title && (
                    <p className={`font-semibold mb-1 ${notification.read ? 'text-slate-800' : 'text-emerald-700'}`}>
                      {notification.title}
                    </p>
                  )}
                  <p className={`${notification.read ? 'text-slate-600' : 'text-slate-800'}`}>
                    {notification.message}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {date}
                  </p>
                </div>
                <div className="flex-shrink-0 flex items-center">
                  <div className="flex gap-1">
                    {!notification.read && (
                      <button
                        onClick={() => markAsRead(notification.id)}
                        className="p-1.5 text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 rounded transition-colors"
                        title="Mark as read"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteNotification(notification.id)}
                      className="p-1.5 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete"
                      >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {filteredNotifications.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
            <Bell className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-800 mb-2">No notifications</h3>
            <p className="text-slate-600">
              {filter === 'unread'
                ? "You're all caught up! No unread notifications."
                : "You don't have any notifications yet."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}